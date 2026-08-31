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

This is intentionally a greedy heuristic (not full CP-SAT) so the demo
works without the OR-Tools package installed. When Member 1 (Mathematician)
integrates CP-SAT, they replace the _greedy_schedule() function body only —
the request/response contracts remain identical.

CP-SAT integration contract
-----------------------------
Replace _greedy_schedule(tasks, windows) with your CP-SAT model.
It must return (assignments: list[dict], unscheduled: list[dict], stats: dict).
Assignment dict required keys:
    task_id, department, corridor, corridor_name, defect_type,
    criticality_score, assigned_start (ISO str), assigned_end (ISO str),
    is_integrated (bool), joint_block_id (str|None),
    merged_departments (list[str]), window_type (str), ai_explanation (None)
Stats dict required keys:
    conflicts_resolved, joint_blocks_formed, downtime_saved_hours,
    total_tasks_scheduled, total_tasks_unscheduled, constraints_evaluated
"""

from __future__ import annotations

import json
import os
import time
import uuid
from datetime import datetime, timedelta, timezone
from functools import lru_cache
from typing import Optional

from fastapi import APIRouter, Body, HTTPException, Query

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
from backend.core.explainer import generate_explanation
from backend.core.optimizer import solve_cpsat, ORTOOLS_AVAILABLE

router = APIRouter(tags=["Optimizer & Explainability"])

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "..", "data")


# ---------------------------------------------------------------------------
# Data loaders (cached — file is read once at startup)
# ---------------------------------------------------------------------------

@lru_cache(maxsize=1)
def _load_tasks() -> list[dict]:
    path = os.path.join(DATA_DIR, "tasks.json")
    if not os.path.exists(path):
        raise RuntimeError(
            f"data/tasks.json not found at {path}. "
            "Run: python scripts/generate_demo_data.py"
        )
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


@lru_cache(maxsize=1)
def _load_windows() -> list[dict]:
    path = os.path.join(DATA_DIR, "windows.json")
    if not os.path.exists(path):
        raise RuntimeError(
            f"data/windows.json not found at {path}. "
            "Run: python scripts/generate_demo_data.py"
        )
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

def _find_earliest_slot(
    w_start: datetime,
    w_end: datetime,
    duration_min: int,
    bookings: list[tuple[datetime, datetime]],
) -> datetime | None:
    """
    Find the earliest start time within [w_start, w_end] where a block of
    duration_min minutes fits without overlapping any existing booking.

    Returns the start datetime if a slot is found, or None if the window
    is fully booked.
    """
    slot_start = w_start
    # Process bookings in chronological order
    for b_start, b_end in sorted(bookings, key=lambda x: x[0]):
        if slot_start >= b_end:
            # Already past this booking — keep scanning
            continue
        if slot_start + timedelta(minutes=duration_min) <= b_start:
            # Task fits in the gap before this booking
            break
        # No room before this booking — push slot_start to after it
        slot_start = b_end

    # Final check: slot must end before the window closes
    if slot_start + timedelta(minutes=duration_min) <= w_end:
        return slot_start
    return None


def _greedy_schedule(
    tasks: list[dict],
    windows: list[dict],
) -> tuple[list[dict], list[dict], dict]:
    """
    Greedy priority-based scheduler.

    Algorithm:
      1. Sort tasks by criticality_score DESC (highest safety risk first).
      2. For each task, iterate over available windows on its corridor
         sorted by start_time ASC (earliest first).
      3. Find the earliest free slot inside each window using _find_earliest_slot().
      4. Assign the task to the first window where a slot is found.
      5. Apply Integrated Joint Block: if the task has is_compatible_with set,
         check if a compatible-dept task is already in the same window and not
         yet merged; if so, merge them into a named Joint Block.
      6. Tasks that can't fit anywhere go into unscheduled with a precise reason.

    Returns: (assignments, unscheduled, stats_dict)
    """
    # Index windows by corridor_id, sorted chronologically
    windows_by_corridor: dict[int, list[dict]] = {}
    for w in windows:
        cid = w["corridor_id"]
        windows_by_corridor.setdefault(cid, []).append(w)
    for cid in windows_by_corridor:
        windows_by_corridor[cid].sort(key=lambda x: x["start_time"])

    # Per-CORRIDOR booking ledger (not per-window) to prevent cross-window overlaps.
    # Two windows on the same corridor can overlap in time (e.g. Night Gold 02:00-06:00
    # and Early Morning 05:00-08:00 share 05:00-06:00), so we must track bookings
    # at the corridor level, not the window level.
    corridor_bookings: dict[int, list[tuple[datetime, datetime]]] = {}

    # Per-window assignment list for Joint Block detection
    assignments_by_window: dict[int, list[dict]] = {}

    assignments:  list[dict] = []
    unscheduled:  list[dict] = []

    # Highest criticality first; break ties by longer duration (fills windows better)
    sorted_tasks = sorted(
        tasks,
        key=lambda t: (-(t.get("criticality_score") or 0), -(t.get("est_duration_min") or 0)),
    )

    # ---- Pre-assignment pass for compatible pairs (Integrated Joint Blocks) ----
    # Before the main loop, find all (task_a, task_b) pairs where:
    #   - task_a.is_compatible_with == task_b.department
    #   - task_b.is_compatible_with == task_a.department
    #   - same corridor
    # Force-assign them to the same earliest window that fits BOTH durations.
    # Mark them so the main loop skips them (they're already handled).
    pre_assigned: set[str] = set()

    # Build a map: task_id → task for fast lookup
    task_by_id = {t["id"]: t for t in sorted_tasks}

    for task in list(sorted_tasks):
        if task["id"] in pre_assigned:
            continue
        compat_dept = task.get("is_compatible_with")
        if not compat_dept:
            continue

        task_dept = task.get("department_code", task.get("department", ""))

        # Find best companion (highest score, same corridor, reciprocal compat)
        # UNLESS the task has an explicit joint_pair_id — then find that exact partner
        companion: dict | None = None
        best_score = -1.0
        explicit_pair_id = task.get("joint_pair_id")
        for other in sorted_tasks:
            if other["id"] in pre_assigned or other["id"] == task["id"]:
                continue
            other_dept = other.get("department_code", other.get("department", ""))
            if explicit_pair_id and other.get("joint_pair_id") == explicit_pair_id:
                # Explicit pairing — use this partner regardless of score
                companion = other
                break
            if (not explicit_pair_id
                    and other_dept == compat_dept
                    and other.get("corridor_id") == task.get("corridor_id")
                    and other.get("is_compatible_with") == task_dept):
                s = other.get("criticality_score", 0.0)
                if s > best_score:
                    best_score = s
                    companion = other

        if companion is None:
            continue

        # Find earliest window on this corridor fitting both tasks
        corridor_id_pair = task["corridor_id"]
        dur_a = task["est_duration_min"]
        dur_b = companion["est_duration_min"]
        total_dur = dur_a + dur_b  # Need room for both (sequential within block)

        assigned_pair = False
        for window in windows_by_corridor.get(corridor_id_pair, []):
            w_id    = window["id"]
            w_start = datetime.fromisoformat(window["start_time"])
            w_end   = datetime.fromisoformat(window["end_time"])

            if window["duration_min"] < total_dur:
                continue

            # Find slot for task A
            slot_a = _find_earliest_slot(
                w_start, w_end, dur_a,
                corridor_bookings.get(corridor_id_pair, []),
            )
            if slot_a is None:
                continue

            # Find slot for task B right after A
            temp_bookings = list(corridor_bookings.get(corridor_id_pair, []))
            temp_bookings.append((slot_a, slot_a + timedelta(minutes=dur_a)))
            slot_b = _find_earliest_slot(
                w_start, w_end, dur_b, temp_bookings,
            )
            if slot_b is None:
                continue

            # Both fit — book them
            jb_id = f"JB-{w_id:03d}"
            merged = sorted([task_dept, compat_dept])

            corridor_bookings.setdefault(corridor_id_pair, []).append(
                (slot_a, slot_a + timedelta(minutes=dur_a))
            )
            corridor_bookings[corridor_id_pair].append(
                (slot_b, slot_b + timedelta(minutes=dur_b))
            )

            h_a = slot_a.hour
            wtype = "Night Gold Window" if 1 <= h_a < 8 else (
                "Early Morning Window" if 8 <= h_a < 12 else "Midday Freight Window"
            )

            for (t_obj, slot_s, slot_e) in [
                (task, slot_a, slot_a + timedelta(minutes=dur_a)),
                (companion, slot_b, slot_b + timedelta(minutes=dur_b)),
            ]:
                a_entry = {
                    "task_id":            t_obj["id"],
                    "department":         t_obj.get("department_code", t_obj.get("department", "")),
                    "corridor":           t_obj.get("corridor_code", ""),
                    "corridor_name":      t_obj.get("corridor_name", ""),
                    "defect_type":        t_obj.get("defect_type", ""),
                    "criticality_score":  t_obj.get("criticality_score", 0.0),
                    "assigned_start":     slot_s.isoformat(),
                    "assigned_end":       slot_e.isoformat(),
                    "is_integrated":      True,
                    "joint_block_id":     jb_id,
                    "merged_departments": merged,
                    "window_type":        wtype,
                    "ai_explanation":     None,
                    "_task_ref":  t_obj,
                    "_window_id": w_id,
                }
                assignments.append(a_entry)
                assignments_by_window.setdefault(w_id, []).append(a_entry)

            pre_assigned.add(task["id"])
            pre_assigned.add(companion["id"])
            assigned_pair = True
            break

        # If the pair couldn't be pre-assigned together, let main loop handle them
        # individually (they may not form a joint block but will still be scheduled)

    # Remove pre-assigned tasks from main loop iteration
    sorted_tasks = [t for t in sorted_tasks if t["id"] not in pre_assigned]

    for task in sorted_tasks:
        corridor_id  = task["corridor_id"]
        duration_min = task["est_duration_min"]
        task_id      = task["id"]
        compat_dept  = task.get("is_compatible_with")
        req_start_str = task.get("requested_start")

        available_windows = windows_by_corridor.get(corridor_id, [])
        assigned = False

        # ---- Window ordering strategy ----
        # Priority 1: Windows that already contain a compatible companion task
        #             (enables Integrated Joint Block — Scenario 1)
        # Priority 2: Windows whose start_time is on the same calendar day as
        #             the task's requested_start (honours the original request)
        # Priority 3: Any other windows (earliest first)

        preferred_window_ids: list[int] = []
        if compat_dept:
            for w_id, w_assignments in assignments_by_window.items():
                for prev in w_assignments:
                    if (prev.get("department") == compat_dept
                            and not prev.get("joint_block_id")):
                        w_obj = next((w for w in available_windows if w["id"] == w_id), None)
                        if w_obj is not None:
                            preferred_window_ids.append(w_id)
                            break

        # Requested-day preference
        req_day: str | None = req_start_str[:10] if req_start_str else None
        requested_day_windows = [
            w for w in available_windows
            if w["id"] not in preferred_window_ids
            and req_day is not None
            and w["start_time"].startswith(req_day)
        ]
        other_windows = [
            w for w in available_windows
            if w["id"] not in preferred_window_ids
            and w not in requested_day_windows
        ]
        preferred_windows = [w for w in available_windows if w["id"] in preferred_window_ids]
        ordered_windows   = preferred_windows + requested_day_windows + other_windows

        for window in ordered_windows:
            w_id    = window["id"]
            w_start = datetime.fromisoformat(window["start_time"])
            w_end   = datetime.fromisoformat(window["end_time"])

            # Quick rejection: even an empty window can't fit this task
            if window["duration_min"] < duration_min:
                continue

            slot_start = _find_earliest_slot(
                w_start, w_end, duration_min,
                corridor_bookings.get(corridor_id, []),
            )
            if slot_start is None:
                continue  # Window fully booked by corridor-level constraints

            slot_end = slot_start + timedelta(minutes=duration_min)

            # Book the slot at the corridor level (prevents cross-window overlaps)
            corridor_bookings.setdefault(corridor_id, []).append((slot_start, slot_end))

            # ---- Integrated Joint Block detection ----
            is_integrated  = False
            joint_block_id: Optional[str] = None
            merged_depts:   list[str]     = []

            compat_dept = task.get("is_compatible_with")
            if compat_dept:
                for prev in assignments_by_window.get(w_id, []):
                    prev_dept = prev.get("department")
                    # Only merge if: right dept, not already merged, no existing joint block
                    if prev_dept == compat_dept and not prev.get("joint_block_id"):
                        is_integrated  = True
                        joint_block_id = f"JB-{w_id:03d}"
                        task_dept      = task.get("department_code", task.get("department", ""))
                        merged_depts   = sorted([task_dept, prev_dept])
                        # Update the already-assigned companion task
                        prev["is_integrated"]      = True
                        prev["joint_block_id"]     = joint_block_id
                        prev["merged_departments"] = merged_depts
                        break

            # Determine window type label from hour of day
            h = slot_start.hour
            if 1 <= h < 8:
                window_type = "Night Gold Window"
            elif 8 <= h < 12:
                window_type = "Early Morning Window"
            else:
                window_type = "Midday Freight Window"

            assignment = {
                "task_id":            task_id,
                "department":         task.get("department_code", task.get("department", "")),
                "corridor":           task.get("corridor_code", ""),
                "corridor_name":      task.get("corridor_name", ""),
                "defect_type":        task.get("defect_type", ""),
                "criticality_score":  task.get("criticality_score", 0.0),
                "assigned_start":     slot_start.isoformat(),
                "assigned_end":       slot_end.isoformat(),
                "is_integrated":      is_integrated,
                "joint_block_id":     joint_block_id,
                "merged_departments": merged_depts,   # always a list, never None
                "window_type":        window_type,
                "ai_explanation":     None,
                # Internal references — stripped before building responses
                "_task_ref":  task,
                "_window_id": w_id,
            }

            assignments.append(assignment)
            assignments_by_window.setdefault(w_id, []).append(assignment)
            assigned = True
            break   # Move on to next task

        if not assigned:
            max_window = max(
                (w["duration_min"] for w in available_windows),
                default=0,
            )
            corridor_code = task.get("corridor_code", "")

            if not available_windows:
                reason = (
                    f"No COA windows exist for corridor '{corridor_code}' "
                    "in the planning horizon."
                )
            elif duration_min > max_window:
                reason = (
                    f"No continuous window available for requested duration "
                    f"({duration_min} mins). Longest available window on "
                    f"{corridor_code} is {max_window} mins."
                )
            else:
                reason = (
                    f"All windows on {corridor_code} are fully booked by "
                    f"higher-priority tasks (Score "
                    f"{task.get('criticality_score', 0):.1f}). "
                    "Task deferred to next planning cycle."
                )

            unscheduled.append({
                "task_id":                 task_id,
                "department":              task.get("department_code", ""),
                "defect_type":             task.get("defect_type", ""),
                "criticality_score":       task.get("criticality_score", 0.0),
                "requested_duration_min":  duration_min,
                "reason":                  reason,
                "deferred_to":             "Next planning cycle (Week 37 or Sunday Mega Block)",
                "next_recommended_window": _suggest_next_window(task, windows),
            })

    # ---- Compute stats ----
    # Count unique joint blocks formed (not individual tasks in them)
    joint_block_ids = {
        a["joint_block_id"] for a in assignments if a.get("joint_block_id")
    }
    # Downtime saved = sum of the shorter task in each joint block pair
    # Approximation: sum durations of integrated tasks / 2 per block
    integrated_by_block: dict[str, list[dict]] = {}
    for a in assignments:
        jbid = a.get("joint_block_id")
        if jbid:
            integrated_by_block.setdefault(jbid, []).append(a)

    downtime_saved_min = 0.0
    for jbid, members in integrated_by_block.items():
        durations = [
            a["_task_ref"].get("est_duration_min", 0) for a in members
        ]
        # Saving = duration of the shorter task (avoided second corridor closure)
        downtime_saved_min += min(durations)

    stats = {
        "conflicts_resolved":      len(joint_block_ids),  # resolved = unique joint blocks
        "joint_blocks_formed":     len(joint_block_ids),
        "downtime_saved_hours":    round(downtime_saved_min / 60, 2),
        "total_tasks_scheduled":   len(assignments),
        "total_tasks_unscheduled": len(unscheduled),
        "constraints_evaluated":   len(tasks) * max(len(windows), 1),
    }

    return assignments, unscheduled, stats


def _suggest_next_window(task: dict, windows: list[dict]) -> str:
    """
    Find the EARLIEST available window on the task's corridor that is long
    enough to fit the task's requested duration.
    """
    corridor_id = task["corridor_id"]
    dur         = task["est_duration_min"]
    candidates  = [
        w for w in windows
        if w["corridor_id"] == corridor_id and w["duration_min"] >= dur
    ]
    if not candidates:
        return "No suitable window found — request emergency block grant from COA."
    earliest = min(candidates, key=lambda x: x["start_time"])
    return f"{earliest['start_time'][:10]} {earliest['window_label']}"


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.post(
    "/optimize",
    response_model=OptimizeResponse,
    summary="Run the maintenance block optimizer",
    description=(
        "Runs a greedy priority-based scheduler (ready for CP-SAT replacement). "
        "Returns optimized assignments, unscheduled tasks, and solver stats. "
        "Scenario 3 (TRK-1002) will always appear in 'unscheduled'. "
        "Scenario 1 (TRK-1000 + OHE-3000) will always appear as an Integrated Joint Block."
    ),
)
def run_optimizer(
    body: OptimizeRequest = Body(default_factory=OptimizeRequest),
) -> OptimizeResponse:
    t0    = time.perf_counter()
    tasks = list(_load_tasks())   # copy so filters don't mutate the cache
    wins  = list(_load_windows())

    # Apply request filters
    if body.task_ids:
        tasks = [t for t in tasks if t["id"] in body.task_ids]
    else:
        tasks = [t for t in tasks if t.get("status") in ("Pending", "Clashed", "Deferred")]

    if body.corridor_ids:
        tasks = [t for t in tasks if t.get("corridor_code") in body.corridor_ids]

    if body.plan_date:
        wins = [w for w in wins if w["start_time"].startswith(body.plan_date)]

    if ORTOOLS_AVAILABLE:
        assignments, unscheduled, stats = solve_cpsat(tasks, wins, max_solve_seconds=body.max_solve_seconds)
    else:
        assignments, unscheduled, stats = _greedy_schedule(tasks, wins)
    solve_time = round(time.perf_counter() - t0, 3)

    plan_id = f"PLAN-{uuid.uuid4().hex[:5].upper()}"

    # Build response objects — strip internal tracking keys
    assignment_responses: list[AssignedTaskResponse] = []
    for a in assignments:
        a.pop("_task_ref",   None)
        a.pop("_window_id",  None)
        # Filter to only keys that exist in AssignedTaskResponse
        filtered = {k: v for k, v in a.items() if k in AssignedTaskResponse.model_fields}
        assignment_responses.append(AssignedTaskResponse(**filtered))

    unscheduled_responses = [UnscheduledTaskResponse(**u) for u in unscheduled]

    total_conflicts = len(_load_conflicts())

    solver_stats = SolverStatsResponse(
        status                  = "OPTIMAL" if not unscheduled else "FEASIBLE",
        solve_time_seconds      = solve_time,
        conflicts_resolved      = stats["conflicts_resolved"],
        total_conflicts         = total_conflicts,
        joint_blocks_formed     = stats["joint_blocks_formed"],
        downtime_saved_hours    = stats["downtime_saved_hours"],
        total_tasks_scheduled   = stats["total_tasks_scheduled"],
        total_tasks_unscheduled = stats["total_tasks_unscheduled"],
        constraints_evaluated   = stats["constraints_evaluated"],
        objective_value         = round(
            sum(a.criticality_score for a in assignment_responses), 2
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
        "Calls the Gemini 2.5 Flash API (or rule-based fallback if GEMINI_API_KEY "
        "is not set) to produce a two-sentence explanation of why a task was "
        "scheduled as it was. Set GEMINI_API_KEY in .env to enable live AI explanations."
    ),
)
def explain_assignment(body: ExplainRequest) -> ExplainResponse:
    task_data   = body.model_dump()
    explanation = generate_explanation(task_data)
    generated_by = (
        "gemini-2.5-flash"
        if os.environ.get("GEMINI_API_KEY", "").strip()
        else "rule-based-fallback"
    )
    return ExplainResponse(
        task_id      = body.task_id,
        explanation  = explanation,
        generated_by = generated_by,
    )


@router.get(
    "/conflicts",
    response_model=ConflictsEnvelope,
    summary="Get all pre-detected scheduling conflicts",
    description=(
        "Returns the conflict pairs detected by the data generator. "
        "Used to populate the red Conflict Gantt on the frontend. "
        "17 conflicts are pre-detected across all 150 tasks."
    ),
)
def get_conflicts(
    corridor: Optional[str] = Query(
        None, description="Filter by corridor_name substring"
    ),
    severity: Optional[str] = Query(
        None, description="Filter by severity: Critical | High | Moderate"
    ),
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
