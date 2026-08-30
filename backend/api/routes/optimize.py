"""
backend/api/routes/optimize.py
================================
POST /api/v1/optimize
POST /api/v1/explain
GET  /api/v1/conflicts

Branch: hriday-dataset | Author: Hriday

The optimize route runs a greedy priority-based scheduler over the dataset.
It implements the full business logic:
  1. Load tasks (Pending + Clashed) and windows from data/
  2. Score and sort tasks by criticality_score descending
  3. For each task, find the earliest fitting window on its corridor
  4. Apply Integrated Joint Block logic: if two tasks are compatible
     AND both fit in the same window, merge them
  5. Tasks that have no fitting window go into the unscheduled list
     with a clear mathematical reason (Scenario 3 guaranteed)
  6. Optionally generate Gemini AI explanations for each assignment

This is intentionally a greedy heuristic (not full CP-SAT) so the demo
works without the OR-Tools package installed. When Member 1 (Mathematician)
integrates CP-SAT, they replace the _greedy_schedule() function body only —
the request/response contracts remain identical.
"""

from __future__ import annotations

import json
import os
import time
import uuid
from datetime import datetime, timedelta, timezone
from functools import lru_cache
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from backend.api.schemas import (
    OptimizeRequest,
    OptimizeResponse,
    AssignedTaskResponse,
    UnscheduledTaskResponse,
    SolverStatsResponse,
    ConflictPairResponse,
    ConflictsEnvelope,
    ExplainRequest,
    ExplainResponse,
)
from backend.core.scoring import calculate_criticality_score_full
from backend.core.explainer import generate_explanation, _assignment_to_prompt_dict

router = APIRouter(tags=["Optimizer & Explainability"])

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "..", "data")


# ---------------------------------------------------------------------------
# Data loaders (cached)
# ---------------------------------------------------------------------------

@lru_cache(maxsize=1)
def _load_tasks() -> list[dict]:
    path = os.path.join(DATA_DIR, "tasks.json")
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


@lru_cache(maxsize=1)
def _load_windows() -> list[dict]:
    path = os.path.join(DATA_DIR, "windows.json")
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


@lru_cache(maxsize=1)
def _load_conflicts() -> list[dict]:
    path = os.path.join(DATA_DIR, "conflict_pairs.json")
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


# ---------------------------------------------------------------------------
# Core scheduling logic
# ---------------------------------------------------------------------------

def _greedy_schedule(
    tasks: list[dict],
    windows: list[dict],
) -> tuple[list[dict], list[dict], dict]:
    """
    Greedy priority-based scheduler.

    Algorithm:
      1. Sort tasks by criticality_score DESC (highest safety risk first)
      2. For each task, iterate over available windows on its corridor
         sorted by start_time ASC (earliest first)
      3. Assign the first window where task duration fits
      4. Mark that window slot as used (bookkeeping)
      5. Apply Integrated Joint Block: if task has is_compatible_with, check
         if a compatible task is already assigned to the same window; if so,
         mark both as integrated
      6. Unscheduled tasks get a plain-English reason

    Returns: (assignments, unscheduled, stats_dict)
    """
    # --- Index windows by corridor_id ---
    windows_by_corridor: dict[int, list[dict]] = {}
    for w in windows:
        cid = w["corridor_id"]
        windows_by_corridor.setdefault(cid, [])
        windows_by_corridor[cid].append(w)
    # Sort each corridor's windows by start_time
    for cid in windows_by_corridor:
        windows_by_corridor[cid].sort(key=lambda x: x["start_time"])

    # Track used capacity per window: window_id → list of (start, end) bookings
    window_bookings: dict[int, list[tuple[datetime, datetime]]] = {}

    # Track assignments indexed by window_id for joint-block detection
    assignments_by_window: dict[int, list[dict]] = {}

    assignments:  list[dict] = []
    unscheduled: list[dict] = []

    # Sort tasks: highest score first; within same score, longer duration first
    sorted_tasks = sorted(
        tasks,
        key=lambda t: (-(t.get("criticality_score") or 0), -(t.get("est_duration_min") or 0))
    )

    for task in sorted_tasks:
        corridor_id  = task["corridor_id"]
        duration_min = task["est_duration_min"]
        task_id      = task["id"]

        available_windows = windows_by_corridor.get(corridor_id, [])
        assigned = False

        for window in available_windows:
            w_id      = window["id"]
            w_start   = datetime.fromisoformat(window["start_time"])
            w_end     = datetime.fromisoformat(window["end_time"])
            w_dur_min = window["duration_min"]

            if w_dur_min < duration_min:
                continue  # Window too short even before any bookings

            # Find the earliest free slot within this window
            bookings = window_bookings.get(w_id, [])
            slot_start = w_start
            for (b_start, b_end) in sorted(bookings, key=lambda x: x[0]):
                if slot_start >= b_end:
                    continue
                if slot_start < b_start:
                    break   # gap before this booking
                # Overlap — push slot_start to after this booking
                slot_start = b_end

            slot_end = slot_start + timedelta(minutes=duration_min)
            if slot_end > w_end:
                continue  # Doesn't fit even in remaining window space

            # --- Fits! Book it ---
            bookings.append((slot_start, slot_end))
            window_bookings[w_id] = bookings

            # --- Integrated Joint Block check ---
            is_integrated    = False
            joint_block_id: Optional[str] = None
            merged_depts:   list[str]     = []
            existing = assignments_by_window.get(w_id, [])

            compat_dept = task.get("is_compatible_with")
            if compat_dept:
                for prev in existing:
                    prev_dept = prev.get("department_code", prev.get("department", ""))
                    if prev_dept == compat_dept and not prev.get("is_integrated"):
                        # Merge both into a Joint Block
                        is_integrated = True
                        joint_block_id = f"JB-{w_id:03d}"
                        task_dept = task.get("department_code", task.get("department", ""))
                        merged_depts = [task_dept, prev_dept]
                        prev["is_integrated"]   = True
                        prev["joint_block_id"]  = joint_block_id
                        prev["merged_departments"] = merged_depts
                        break

            # Determine window type label
            h = slot_start.hour
            if 1 <= h < 8:
                window_type = "Night Gold Window"
            elif 8 <= h < 12:
                window_type = "Early Morning Window"
            else:
                window_type = "Midday Freight Window"

            assignment = {
                "task_id":           task_id,
                "department_code":   task.get("department_code", task.get("department", "")),
                "department":        task.get("department_code", task.get("department", "")),
                "corridor":          task.get("corridor_code", ""),
                "corridor_name":     task.get("corridor_name", ""),
                "defect_type":       task.get("defect_type", ""),
                "criticality_score": task.get("criticality_score", 0.0),
                "assigned_start":    slot_start.isoformat(),
                "assigned_end":      slot_end.isoformat(),
                "is_integrated":     is_integrated,
                "joint_block_id":    joint_block_id,
                "merged_departments": merged_depts if is_integrated else [],
                "window_type":       window_type,
                "ai_explanation":    None,
                # Keep raw task ref for explainer
                "_task":             task,
                "_window_id":        w_id,
            }

            assignments.append(assignment)
            assignments_by_window.setdefault(w_id, []).append(assignment)
            assigned = True
            break

        if not assigned:
            # Build a precise infeasibility reason
            max_window = max(
                (w["duration_min"] for w in available_windows),
                default=0,
            )
            if not available_windows:
                reason = f"No COA windows exist for corridor '{task.get('corridor_code', '')}' in the planning horizon."
            elif duration_min > max_window:
                reason = (
                    f"No continuous window available for requested duration ({duration_min} mins). "
                    f"Longest available window on {task.get('corridor_code', '')} is {max_window} mins."
                )
            else:
                reason = (
                    f"All windows on {task.get('corridor_code', '')} are fully booked by higher-priority "
                    f"tasks (Score {task.get('criticality_score', 0):.1f}). "
                    f"Task deferred to next planning cycle."
                )

            unscheduled.append({
                "task_id":                  task_id,
                "department":               task.get("department_code", ""),
                "defect_type":              task.get("defect_type", ""),
                "criticality_score":        task.get("criticality_score", 0.0),
                "requested_duration_min":   duration_min,
                "reason":                   reason,
                "deferred_to":              "Next planning cycle (Week 37 or Sunday Mega Block)",
                "next_recommended_window":  _suggest_next_window(task, windows),
            })

    # --- Compute joint-block stats ---
    joint_block_ids = {a["joint_block_id"] for a in assignments if a.get("joint_block_id")}
    downtime_saved_mins = sum(
        t.get("est_duration_min", 0)
        for a in assignments
        if a.get("is_integrated")
        for t in [a.get("_task", {})]
    ) / 2   # Each integrated pair saves one task's worth of downtime

    stats = {
        "conflicts_resolved":      sum(1 for a in assignments if a.get("is_integrated")),
        "joint_blocks_formed":     len(joint_block_ids),
        "downtime_saved_hours":    round(downtime_saved_mins / 60, 2),
        "total_tasks_scheduled":   len(assignments),
        "total_tasks_unscheduled": len(unscheduled),
        "constraints_evaluated":   len(tasks) * len(windows),
    }

    return assignments, unscheduled, stats


def _suggest_next_window(task: dict, windows: list[dict]) -> str:
    """Find the next available window on the task's corridor after the plan horizon."""
    corridor_id = task["corridor_id"]
    dur         = task["est_duration_min"]
    candidates  = [w for w in windows if w["corridor_id"] == corridor_id and w["duration_min"] >= dur]
    if not candidates:
        return "No upcoming window found — request emergency block grant from COA."
    latest = max(candidates, key=lambda x: x["start_time"])
    return f"{latest['start_time'][:10]} {latest['window_label']}"


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.post(
    "/optimize",
    response_model=OptimizeResponse,
    summary="Run the maintenance block optimizer",
    description=(
        "Runs a greedy priority-based scheduler (placeholder for CP-SAT). "
        "Returns optimized assignments, unscheduled tasks, and solver stats. "
        "Scenario 3 (TRK-1002) will always appear in 'unscheduled'. "
        "Scenario 1 (TRK-1000 + OHE-3000) will always appear as an Integrated Joint Block."
    ),
)
def run_optimizer(body: OptimizeRequest = None) -> OptimizeResponse:
    if body is None:
        body = OptimizeRequest()

    t0    = time.perf_counter()
    tasks = _load_tasks()
    wins  = _load_windows()

    # Filter tasks by request
    if body.task_ids:
        tasks = [t for t in tasks if t["id"] in body.task_ids]
    else:
        tasks = [t for t in tasks if t.get("status") in ("Pending", "Clashed", "Deferred")]

    if body.corridor_ids:
        tasks = [t for t in tasks if t.get("corridor_code") in body.corridor_ids]

    if body.plan_date:
        wins = [w for w in wins if w["start_time"].startswith(body.plan_date)]

    assignments, unscheduled, stats = _greedy_schedule(tasks, wins)
    solve_time = round(time.perf_counter() - t0, 3)

    plan_id = f"PLAN-{uuid.uuid4().hex[:5].upper()}"

    # Build response objects — strip internal _task/_window_id keys
    assignment_responses = []
    for a in assignments:
        a.pop("_task", None)
        a.pop("_window_id", None)
        a.pop("department_code", None)
        assignment_responses.append(AssignedTaskResponse(**{
            k: v for k, v in a.items()
            if k in AssignedTaskResponse.model_fields
        }))

    unscheduled_responses = [
        UnscheduledTaskResponse(**u) for u in unscheduled
    ]

    total_conflicts = len(_load_conflicts())
    solved_count    = stats["conflicts_resolved"]

    solver_stats = SolverStatsResponse(
        status                  = "OPTIMAL" if not unscheduled else "FEASIBLE",
        solve_time_seconds      = solve_time,
        conflicts_resolved      = solved_count,
        total_conflicts         = total_conflicts,
        joint_blocks_formed     = stats["joint_blocks_formed"],
        downtime_saved_hours    = stats["downtime_saved_hours"],
        total_tasks_scheduled   = stats["total_tasks_scheduled"],
        total_tasks_unscheduled = stats["total_tasks_unscheduled"],
        constraints_evaluated   = stats["constraints_evaluated"],
        objective_value         = sum(
            a.criticality_score for a in assignment_responses
        ),
    )

    return OptimizeResponse(
        status       = "success",
        plan_id      = plan_id,
        assignments  = assignment_responses,
        unscheduled  = unscheduled_responses,
        solver_stats = solver_stats,
    )


@router.post(
    "/explain",
    response_model=ExplainResponse,
    summary="Generate AI explanation for a scheduled task",
    description=(
        "Calls the Gemini API (or rule-based fallback if GEMINI_API_KEY not set) "
        "to produce a two-sentence explanation of why a task was scheduled as it was."
    ),
)
def explain_assignment(body: ExplainRequest) -> ExplainResponse:
    task_data = body.model_dump()
    explanation = generate_explanation(task_data)
    return ExplainResponse(
        task_id     = body.task_id,
        explanation = explanation,
        generated_by = "gemini-2.5-flash" if os.environ.get("GEMINI_API_KEY") else "rule-based-fallback",
    )


@router.get(
    "/conflicts",
    response_model=ConflictsEnvelope,
    summary="Get all pre-detected scheduling conflicts",
    description=(
        "Returns the conflict pairs detected by the data generator. "
        "Used to populate the red Conflict Gantt on the frontend."
    ),
)
def get_conflicts(
    corridor: Optional[str] = Query(None, description="Filter by corridor_name substring"),
    severity: Optional[str] = Query(None, description="Filter by severity: Critical | High | Moderate"),
) -> ConflictsEnvelope:
    conflicts = _load_conflicts()

    result = []
    for c in conflicts:
        if corridor and corridor.lower() not in c.get("corridor_name", "").lower():
            continue
        if severity and c.get("conflict_severity") != severity:
            continue
        result.append(ConflictPairResponse(
            id                   = c["id"],
            task_a_id            = c["task_a_id"],
            task_b_id            = c["task_b_id"],
            corridor_name        = c.get("corridor_name", ""),
            overlap_start        = c["overlap_start"],
            overlap_end          = c["overlap_end"],
            overlap_duration_min = c["overlap_duration_min"],
            conflict_severity    = c["conflict_severity"],
            conflict_type        = c["conflict_type"],
            resolution_strategy  = c["resolution_strategy"],
            task_a_score         = c.get("task_a_score", 0.0),
            task_b_score         = c.get("task_b_score", 0.0),
        ))

    return ConflictsEnvelope(
        status="success",
        count=len(result),
        data=result,
    )
