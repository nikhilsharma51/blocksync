"""
backend/api/routes/corridors.py
================================
GET /api/v1/corridors
GET /api/v1/corridors/availability
GET /api/v1/corridors/{corridor_code}/windows

Branch: hriday-dataset | Author: Hriday

Serves COA block windows from data/windows.json.
The CP-SAT optimizer reads /availability to find free slots for tasks.
"""

from __future__ import annotations

import json
import os
from functools import lru_cache
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from backend.api.schemas import (
    CorridorWindowResponse,
    CorridorAvailabilityEnvelope,
)

router = APIRouter(prefix="/corridors", tags=["Corridors & Windows"])

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "..", "data")


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


# Corridor metadata — mirrors the DB corridors table; no separate file needed
CORRIDORS_META: list[dict] = [
    {"code": "NDLS-GZB-UP",   "name": "New Delhi - Ghaziabad (UP Main)",      "asset_class": "Mainline Trunk", "traffic_weight": 1.0, "speed_limit": 130},
    {"code": "NDLS-GZB-DN",   "name": "New Delhi - Ghaziabad (DOWN Main)",    "asset_class": "Mainline Trunk", "traffic_weight": 1.0, "speed_limit": 130},
    {"code": "GZB-ALJN-UP",   "name": "Ghaziabad - Aligarh (UP Main)",        "asset_class": "Mainline Trunk", "traffic_weight": 1.0, "speed_limit": 160},
    {"code": "GZB-ALJN-DN",   "name": "Ghaziabad - Aligarh (DOWN Main)",      "asset_class": "Mainline Trunk", "traffic_weight": 1.0, "speed_limit": 160},
    {"code": "ALJN-TDL-BOTH", "name": "Aligarh - Tundla Junction",            "asset_class": "Mainline Trunk", "traffic_weight": 0.9, "speed_limit": 140},
    {"code": "TDL-CNB-BOTH",  "name": "Tundla - Kanpur Central",              "asset_class": "Mainline Trunk", "traffic_weight": 0.9, "speed_limit": 140},
    {"code": "DLI-RE-SL",     "name": "Delhi - Rewari (Single Line)",         "asset_class": "Branch Line",    "traffic_weight": 0.7, "speed_limit": 100},
    {"code": "CNB-YARD",      "name": "Kanpur Central Yard & Loop Lines",     "asset_class": "Yard/Loop",      "traffic_weight": 0.3, "speed_limit":  30},
]

_CORRIDOR_CODE_MAP: dict[str, dict] = {c["code"]: c for c in CORRIDORS_META}


def _window_to_response(w: dict) -> CorridorWindowResponse:
    return CorridorWindowResponse(
        window_id    = w["id"],
        corridor_id  = w.get("corridor_code", str(w.get("corridor_id", ""))),
        corridor_name= w.get("corridor_name", ""),
        window_label = w.get("window_label", "Night Gold Window"),
        start_time   = w["start_time"],
        end_time     = w["end_time"],
        duration_min = w["duration_min"],
        source       = w.get("source", "COA_Timetable_Gap"),
        is_available = w.get("is_available", True),
    )


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.get(
    "",
    summary="List all corridors with metadata",
    response_model=list[dict],
    description="Returns all track sections / block sections managed in this division.",
)
def list_corridors(
    asset_class: Optional[str] = Query(
        None,
        description="Filter by asset class: 'Mainline Trunk' | 'Branch Line' | 'Yard/Loop'",
    ),
) -> list[dict]:
    if asset_class:
        return [c for c in CORRIDORS_META if c["asset_class"] == asset_class]
    return CORRIDORS_META


@router.get(
    "/availability",
    response_model=CorridorAvailabilityEnvelope,
    summary="Get all available COA block windows",
    description=(
        "Returns every open maintenance window granted by the Controller of Accounts (COA). "
        "The optimizer ONLY assigns tasks to windows returned by this endpoint. "
        "Filter by corridor_code or date to narrow results."
    ),
)
def get_availability(
    corridor_code: Optional[str] = Query(
        None,
        description="Filter by corridor code, e.g. NDLS-GZB-UP",
    ),
    date: Optional[str] = Query(
        None,
        description="Filter to windows starting on this date (YYYY-MM-DD)",
    ),
    window_label: Optional[str] = Query(
        None,
        description="Filter by window type, e.g. 'Night Gold Window'",
    ),
    min_duration: Optional[int] = Query(
        None,
        ge=15,
        description="Only return windows with duration_min >= this value",
    ),
) -> CorridorAvailabilityEnvelope:
    windows = _load_windows()

    result = []
    for w in windows:
        if not w.get("is_available", True):
            continue
        if corridor_code and w.get("corridor_code") != corridor_code:
            continue
        if date and not w["start_time"].startswith(date):
            continue
        if window_label and w.get("window_label") != window_label:
            continue
        if min_duration is not None and w["duration_min"] < min_duration:
            continue
        result.append(w)

    # Sort chronologically
    result.sort(key=lambda x: x["start_time"])

    return CorridorAvailabilityEnvelope(
        status="success",
        count=len(result),
        data=[_window_to_response(w) for w in result],
    )


@router.get(
    "/{corridor_code}/windows",
    response_model=CorridorAvailabilityEnvelope,
    summary="Get all windows for a specific corridor",
)
def get_corridor_windows(
    corridor_code: str,
    date: Optional[str] = Query(None, description="Filter to windows on this date YYYY-MM-DD"),
    min_duration: Optional[int] = Query(None, ge=15),
) -> CorridorAvailabilityEnvelope:
    if corridor_code not in _CORRIDOR_CODE_MAP:
        raise HTTPException(
            status_code=404,
            detail=f"Corridor '{corridor_code}' not found. Valid codes: {list(_CORRIDOR_CODE_MAP.keys())}",
        )

    windows = _load_windows()
    result = [
        w for w in windows
        if w.get("corridor_code") == corridor_code
        and w.get("is_available", True)
        and (not date or w["start_time"].startswith(date))
        and (min_duration is None or w["duration_min"] >= min_duration)
    ]
    result.sort(key=lambda x: x["start_time"])

    return CorridorAvailabilityEnvelope(
        status="success",
        count=len(result),
        data=[_window_to_response(w) for w in result],
    )


@router.get(
    "/{corridor_code}",
    summary="Get metadata for a single corridor",
    response_model=dict,
)
def get_corridor(corridor_code: str) -> dict:
    if corridor_code not in _CORRIDOR_CODE_MAP:
        raise HTTPException(
            status_code=404,
            detail=f"Corridor '{corridor_code}' not found.",
        )
    return _CORRIDOR_CODE_MAP[corridor_code]
