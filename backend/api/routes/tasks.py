"""
backend/api/routes/tasks.py
============================
GET /api/v1/tasks/pending
GET /api/v1/tasks/{task_id}
GET /api/v1/tasks

Note: GET /api/v1/conflicts lives in optimize.py (same API prefix).

Branch: hriday-dataset | Author: Hriday

Serves the raw, unoptimized maintenance task data from data/tasks.json.
This is what the frontend Conflict Gantt reads to render the "red" timeline.
"""

from __future__ import annotations

import json
import os
from functools import lru_cache
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from backend.api.schemas import (
    PendingTaskResponse,
    PendingTasksEnvelope,
    ScoreBreakdown,
)

router = APIRouter(prefix="/tasks", tags=["Tasks"])

# ---------------------------------------------------------------------------
# Data loading (cached — file is read once at startup)
# ---------------------------------------------------------------------------

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "..", "data")


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


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _task_to_response(t: dict) -> PendingTaskResponse:
    breakdown = t.get("score_breakdown") or {}
    score_bd = None
    sev_comp = t.get("score_severity_component")
    if sev_comp is not None:
        score_bd = ScoreBreakdown(
            severity_component = sev_comp,
            overdue_component  = t.get("score_overdue_component", 0.0),
            traffic_component  = t.get("score_traffic_component", 0.0),
            total_score        = t.get("criticality_score", 0.0),
            formula            = t.get("score_formula", ""),
        )

    return PendingTaskResponse(
        id                           = t["id"],
        department                   = t.get("department_code", t.get("department", "")),
        corridor                     = t.get("corridor_code", t.get("corridor", "")),
        corridor_name                = t.get("corridor_name", ""),
        defect_type                  = t.get("defect_type", ""),
        severity                     = t["severity"],
        days_overdue                 = t["days_overdue"],
        est_duration_min             = t["est_duration_min"],
        criticality_score            = t.get("criticality_score", 0.0),
        priority                     = t.get("priority_level", "P2"),
        status                       = t.get("status", "Pending"),
        requested_start              = t.get("requested_start", ""),
        requested_end                = t.get("requested_end", ""),
        is_compatible_with           = t.get("is_compatible_with"),
        power_disconnection_required = t.get("power_disconnection_required", False),
        crew_size                    = t.get("crew_size"),
        supervisor                   = t.get("supervisor"),
        required_machine             = t.get("required_machine"),
        score_breakdown              = score_bd,
    )


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.get(
    "/pending",
    response_model=PendingTasksEnvelope,
    summary="Get all pending/clashed maintenance tasks",
    description=(
        "Returns all unscheduled maintenance tasks sorted by criticality_score descending. "
        "The frontend Conflict Gantt reads this to render the initial red timeline. "
        "Filter by department or corridor using query params."
    ),
)
def get_pending_tasks(
    department: Optional[str] = Query(
        None,
        description="Filter by department code: TRK | SNT | OHE",
        examples=["TRK"],
    ),
    corridor: Optional[str] = Query(
        None,
        description="Filter by corridor code, e.g. NDLS-GZB-UP",
    ),
    min_score: Optional[float] = Query(
        None,
        ge=0, le=100,
        description="Only return tasks with criticality_score >= this value",
    ),
    priority: Optional[str] = Query(
        None,
        description="Filter by priority tier: P0 | P1 | P2",
    ),
    status: Optional[str] = Query(
        None,
        description="Filter by status: Pending | Clashed | Deferred",
    ),
    limit: int = Query(default=200, ge=1, le=500, description="Max records to return"),
) -> PendingTasksEnvelope:
    tasks = _load_tasks()

    # Apply filters
    result = []
    for t in tasks:
        # Status filter — default shows Pending and Clashed
        task_status = t.get("status", "Pending")
        if status:
            if task_status != status:
                continue
        else:
            if task_status not in ("Pending", "Clashed"):
                continue

        if department and t.get("department_code", t.get("department")) != department:
            continue
        if corridor and t.get("corridor_code", t.get("corridor")) != corridor:
            continue
        if min_score is not None and t.get("criticality_score", 0.0) < min_score:
            continue
        if priority and t.get("priority_level") != priority:
            continue

        result.append(t)

    # Sort by criticality_score descending (highest priority first)
    result.sort(key=lambda x: x.get("criticality_score", 0.0), reverse=True)
    result = result[:limit]

    return PendingTasksEnvelope(
        status="success",
        count=len(result),
        data=[_task_to_response(t) for t in result],
    )


@router.get(
    "/{task_id}",
    response_model=PendingTaskResponse,
    summary="Get a single task by ID",
)
def get_task_by_id(task_id: str) -> PendingTaskResponse:
    tasks = _load_tasks()
    for t in tasks:
        if t["id"] == task_id:
            return _task_to_response(t)
    raise HTTPException(status_code=404, detail=f"Task '{task_id}' not found.")


@router.get(
    "",
    response_model=PendingTasksEnvelope,
    summary="Get all tasks (any status)",
    description="Returns every task regardless of status. Useful for admin / seed verification.",
)
def get_all_tasks(
    limit: int = Query(default=200, ge=1, le=500),
) -> PendingTasksEnvelope:
    tasks = _load_tasks()
    sorted_tasks = sorted(tasks, key=lambda x: x.get("criticality_score", 0.0), reverse=True)
    page = sorted_tasks[:limit]
    return PendingTasksEnvelope(
        status="success",
        count=len(page),
        data=[_task_to_response(t) for t in page],
    )
