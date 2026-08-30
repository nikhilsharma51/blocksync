"""
backend/api/schemas.py
=======================
BlockSync Pydantic Response & Request Schemas
Branch: hriday-dataset | Author: Hriday

These schemas are the canonical JSON contracts between the backend and
the frontend. Every key name here matches exactly what the frontend
(src/data/mockRailwayData.ts) and the Gantt chart components expect.

IMPORTANT: Do not rename fields without coordinating with Member 3 (Frontend).
The GET /api/v1/tasks/pending and POST /api/v1/optimize response shapes
are locked by the spec in docs/Data Layer Architecture & Specifications.txt.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, Field, field_validator, model_validator


# ===========================================================================
# SHARED / PRIMITIVE SCHEMAS
# ===========================================================================

class DepartmentEnum(str):
    TRK = "TRK"
    SNT = "SNT"
    OHE = "OHE"


class PriorityEnum(str):
    P0 = "P0"
    P1 = "P1"
    P2 = "P2"


class StatusEnum(str):
    Pending   = "Pending"
    Clashed   = "Clashed"
    Scheduled = "Scheduled"
    Merged    = "Merged"
    Deferred  = "Deferred"
    Approved  = "Approved"


# ---------------------------------------------------------------------------
# Score breakdown — embedded in task responses for frontend tooltip
# ---------------------------------------------------------------------------
class ScoreBreakdown(BaseModel):
    severity_component: float = Field(..., description="Weighted severity score (W_SEV × norm_severity)")
    overdue_component:  float = Field(..., description="Weighted overdue penalty (W_OVD × norm_overdue)")
    traffic_component:  float = Field(..., description="Weighted traffic score (W_TRF × norm_traffic)")
    total_score:        float = Field(..., ge=0, le=100, description="Final 0–100 criticality score")
    formula:            str   = Field(..., description="Human-readable formula string")


# ===========================================================================
# TASK SCHEMAS
# ===========================================================================

class TaskBase(BaseModel):
    """Minimum fields shared by request and response task shapes."""
    id:               str   = Field(..., examples=["TRK-1001"])
    department:       str   = Field(..., examples=["TRK"])
    corridor:         str   = Field(..., examples=["NDLS-GZB-UP"])
    corridor_name:    str   = Field(..., examples=["New Delhi - Ghaziabad (UP Main)"])
    defect_type:      str   = Field(..., examples=["Weld / Rail Fracture"])
    severity:         int   = Field(..., ge=1, le=5)
    days_overdue:     int   = Field(..., ge=0)
    est_duration_min: int   = Field(..., gt=0)
    criticality_score: float = Field(..., ge=0, le=100)
    priority:         str   = Field(..., examples=["P0"])
    status:           str   = Field(..., examples=["Clashed"])


class PendingTaskResponse(TaskBase):
    """
    Shape returned by GET /api/v1/tasks/pending

    Matches the frontend's MaintenanceTask shape for the Conflict Gantt.
    The frontend uses requested_start / requested_end to position the bar.
    """
    requested_start:  str   = Field(..., description="ISO-8601 UTC datetime")
    requested_end:    str   = Field(..., description="ISO-8601 UTC datetime")
    is_compatible_with: Optional[str] = Field(None, description="Department code this task can share a block with")
    power_disconnection_required: bool = Field(False)
    crew_size:        Optional[int]  = None
    supervisor:       Optional[str]  = None
    required_machine: Optional[str]  = None
    score_breakdown:  Optional[ScoreBreakdown] = None

    class Config:
        json_schema_extra = {
            "example": {
                "id": "TRK-1001",
                "department": "TRK",
                "corridor": "NDLS-GZB-UP",
                "corridor_name": "New Delhi - Ghaziabad (UP Main)",
                "defect_type": "Weld / Rail Fracture",
                "severity": 5,
                "days_overdue": 15,
                "est_duration_min": 180,
                "criticality_score": 76.5,
                "priority": "P0",
                "status": "Clashed",
                "requested_start": "2026-09-03T13:00:00+00:00",
                "requested_end": "2026-09-03T16:00:00+00:00",
                "is_compatible_with": None,
                "power_disconnection_required": True,
            }
        }


class PendingTasksEnvelope(BaseModel):
    """Envelope for GET /api/v1/tasks/pending"""
    status: str = Field(default="success")
    count:  int = Field(..., description="Total tasks in response")
    data:   list[PendingTaskResponse]


# ===========================================================================
# WINDOW / CORRIDOR SCHEMAS
# ===========================================================================

class CorridorWindowResponse(BaseModel):
    """
    Shape returned by GET /api/v1/corridors/availability

    The optimizer reads these to know where tasks can be scheduled.
    """
    window_id:     int   = Field(..., description="Unique window ID")
    corridor_id:   str   = Field(..., description="Corridor code, e.g. NDLS-GZB-UP")
    corridor_name: str
    window_label:  str   = Field(..., examples=["Night Gold Window"])
    start_time:    str   = Field(..., description="ISO-8601 UTC")
    end_time:      str   = Field(..., description="ISO-8601 UTC")
    duration_min:  int   = Field(..., description="Window length in minutes")
    source:        str   = Field(..., examples=["COA_Timetable_Gap"])
    is_available:  bool  = True

    class Config:
        json_schema_extra = {
            "example": {
                "window_id": 1,
                "corridor_id": "NDLS-GZB-UP",
                "corridor_name": "New Delhi - Ghaziabad (UP Main)",
                "window_label": "Night Gold Window",
                "start_time": "2026-09-02T02:00:00+00:00",
                "end_time": "2026-09-02T06:00:00+00:00",
                "duration_min": 240,
                "source": "COA_Timetable_Gap",
                "is_available": True,
            }
        }


class CorridorAvailabilityEnvelope(BaseModel):
    """Envelope for GET /api/v1/corridors/availability"""
    status: str = Field(default="success")
    count:  int
    data:   list[CorridorWindowResponse]


# ===========================================================================
# OPTIMIZE REQUEST / RESPONSE SCHEMAS
# ===========================================================================

class OptimizeRequest(BaseModel):
    """
    Body for POST /api/v1/optimize

    The frontend sends this after the user clicks 'Run Optimizer'.
    task_ids is optional — if omitted, all Pending/Clashed tasks are optimized.
    """
    task_ids:          Optional[list[str]] = Field(None, description="Subset of task IDs to optimize; omit for all pending")
    corridor_ids:      Optional[list[str]] = Field(None, description="Restrict to these corridors")
    plan_date:         Optional[str]       = Field(None, description="ISO date for the planning horizon, e.g. 2026-09-02")
    max_solve_seconds: int                 = Field(default=30, ge=1, le=300, description="CP-SAT solver time limit")

    class Config:
        json_schema_extra = {
            "example": {
                "plan_date": "2026-09-02",
                "max_solve_seconds": 30,
            }
        }


class AssignedTaskResponse(BaseModel):
    """
    A single scheduled task in the optimizer output.
    Matches the frontend's OptimizedAssignment shape.
    """
    task_id:            str
    department:         str
    corridor:           str
    corridor_name:      str
    defect_type:        str
    criticality_score:  float
    assigned_start:     str   = Field(..., description="ISO-8601 UTC")
    assigned_end:       str   = Field(..., description="ISO-8601 UTC")
    is_integrated:      bool  = False
    joint_block_id:     Optional[str] = None
    merged_departments: list[str] = Field(default_factory=list, description="Departments in this joint block; empty list if not integrated")
    window_type:        str   = "Night Gold Window"
    ai_explanation:     Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "task_id": "TRK-1000",
                "department": "TRK",
                "corridor": "NDLS-GZB-UP",
                "corridor_name": "New Delhi - Ghaziabad (UP Main)",
                "defect_type": "Routine Tamping",
                "criticality_score": 43.83,
                "assigned_start": "2026-09-02T02:00:00+00:00",
                "assigned_end": "2026-09-02T04:00:00+00:00",
                "is_integrated": True,
                "joint_block_id": "JB-01",
                "merged_departments": ["TRK", "OHE"],
                "window_type": "Night Gold Window",
                "ai_explanation": "Task TRK-1000 was prioritised for the 02:00 window due to its compatibility with OHE task OHE-3000, enabling an Integrated Joint Block that saves 120 minutes of corridor downtime.",
            }
        }


class UnscheduledTaskResponse(BaseModel):
    """
    A task the optimizer could not fit. Proves graceful degradation.
    Scenario 3 (TRK-1002) must appear here during the demo.
    """
    task_id:                   str
    department:                str
    defect_type:               str
    criticality_score:         float
    requested_duration_min:    int
    reason:                    str   = Field(..., description="Human-readable infeasibility reason")
    deferred_to:               Optional[str] = None
    next_recommended_window:   Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "task_id": "TRK-1002",
                "department": "TRK",
                "defect_type": "Ballast Deep Screening (BCM)",
                "criticality_score": 49.33,
                "requested_duration_min": 360,
                "reason": "No continuous window available for requested duration (360 mins). Longest available window on NDLS-GZB-UP is 300 mins.",
                "deferred_to": "Week 37, Sunday Mega Block",
                "next_recommended_window": "Sep 06, 2026 01:00–07:00 AM",
            }
        }


class SolverStatsResponse(BaseModel):
    """CP-SAT solver metrics returned with every optimize response."""
    status:                    str   = "OPTIMAL"
    solve_time_seconds:        float
    conflicts_resolved:        int
    total_conflicts:           int
    joint_blocks_formed:       int
    downtime_saved_hours:      float
    total_tasks_scheduled:     int
    total_tasks_unscheduled:   int
    constraints_evaluated:     int
    objective_value:           float


class OptimizeResponse(BaseModel):
    """
    Envelope for POST /api/v1/optimize

    This is the exact shape the frontend Optimized Gantt reads.
    """
    status:       str   = Field(default="success")
    plan_id:      str   = Field(..., description="Unique plan identifier, e.g. PLAN-99281")
    assignments:  list[AssignedTaskResponse]
    unscheduled:  list[UnscheduledTaskResponse]
    solver_stats: SolverStatsResponse

    class Config:
        json_schema_extra = {
            "example": {
                "status": "success",
                "plan_id": "PLAN-99281",
                "assignments": [],
                "unscheduled": [],
                "solver_stats": {
                    "status": "OPTIMAL",
                    "solve_time_seconds": 1.84,
                    "conflicts_resolved": 17,
                    "total_conflicts": 17,
                    "joint_blocks_formed": 4,
                    "downtime_saved_hours": 8.5,
                    "total_tasks_scheduled": 147,
                    "total_tasks_unscheduled": 3,
                    "constraints_evaluated": 256,
                    "objective_value": 8441.6,
                }
            }
        }


# ===========================================================================
# CONFLICT SCHEMAS
# ===========================================================================

class ConflictPairResponse(BaseModel):
    """Used by GET /api/v1/conflicts"""
    id:                    str
    task_a_id:             str
    task_b_id:             str
    corridor_name:         str
    overlap_start:         str
    overlap_end:           str
    overlap_duration_min:  int
    conflict_severity:     str
    conflict_type:         str
    resolution_strategy:   str
    task_a_score:          float
    task_b_score:          float


class ConflictsEnvelope(BaseModel):
    status: str = Field(default="success")
    count:  int
    data:   list[ConflictPairResponse]


# ===========================================================================
# EXPLAINABILITY SCHEMA
# ===========================================================================

class ExplainRequest(BaseModel):
    """Body for POST /api/v1/explain"""
    task_id:               str
    defect:                str
    severity:              int
    days_overdue:          int
    score:                 float
    corridor:              str
    assigned_start:        str
    assigned_end:          str
    is_integrated_block:   bool              = False
    merged_with:           Optional[str]     = None
    status:                str               = "Scheduled"
    downtime_saved_minutes: int              = 0
    mathematical_reason:   Optional[str]     = None
    next_recommended_window: Optional[str]   = None


class ExplainResponse(BaseModel):
    """Response for POST /api/v1/explain"""
    task_id:     str
    explanation: str
    generated_by: str = "gemini-2.5-flash"


# ===========================================================================
# HEALTH CHECK
# ===========================================================================

class HealthResponse(BaseModel):
    status:  str = "ok"
    version: str = "0.1.0"
    dataset: dict[str, Any] = Field(default_factory=dict)
