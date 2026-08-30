"""
scripts/generate_demo_data.py
==============================
BlockSync Synthetic Dataset Generator
Branch: hriday-dataset | Author: Hriday

Generates 150+ realistic maintenance tasks and COA block windows for the
Indian Railways Delhi Division. Outputs:
    data/tasks.json          — all maintenance tasks with criticality scores
    data/windows.json        — all available COA block windows
    data/conflict_pairs.json — pre-detected scheduling conflicts
    data/seed_summary.json   — statistics summary for the seed loader

The script hard-codes the 3 "Jury-Hook" demo scenarios that make the
BlockSync demo compelling to judges, then fills the remainder with
statistically realistic noise to make the Gantt charts look busy.

Run from the repo root:
    python scripts/generate_demo_data.py

Or with verbose output:
    python scripts/generate_demo_data.py --verbose
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from datetime import datetime, timedelta, timezone
from typing import Any

# ---------------------------------------------------------------------------
# Allow running from repo root without installing the package
# ---------------------------------------------------------------------------
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from backend.core.scoring import (
    calculate_criticality_score,
    calculate_criticality_score_full,
    classify_priority,
    traffic_weight_from_asset_class,
)

# ---------------------------------------------------------------------------
# Reproducibility seed — keep this fixed so the dataset is deterministic
# ---------------------------------------------------------------------------
RANDOM_SEED = 42
random.seed(RANDOM_SEED)

# ---------------------------------------------------------------------------
# Master configuration
# ---------------------------------------------------------------------------
BASE_DATE = datetime(2026, 9, 2, 0, 0, 0, tzinfo=timezone.utc)   # Monday
PLAN_HORIZON_DAYS = 7                                              # Mon–Sun
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "data")

CORRIDORS: list[dict] = [
    {
        "id":           1,
        "code":         "NDLS-GZB-UP",
        "name":         "New Delhi - Ghaziabad (UP Main)",
        "line_type":    "UP",
        "asset_class":  "Mainline Trunk",
        "traffic_weight": 1.0,
        "speed_limit":  130,
    },
    {
        "id":           2,
        "code":         "NDLS-GZB-DN",
        "name":         "New Delhi - Ghaziabad (DOWN Main)",
        "line_type":    "DOWN",
        "asset_class":  "Mainline Trunk",
        "traffic_weight": 1.0,
        "speed_limit":  130,
    },
    {
        "id":           3,
        "code":         "GZB-ALJN-UP",
        "name":         "Ghaziabad - Aligarh (UP Main)",
        "line_type":    "UP",
        "asset_class":  "Mainline Trunk",
        "traffic_weight": 1.0,
        "speed_limit":  160,
    },
    {
        "id":           4,
        "code":         "GZB-ALJN-DN",
        "name":         "Ghaziabad - Aligarh (DOWN Main)",
        "line_type":    "DOWN",
        "asset_class":  "Mainline Trunk",
        "traffic_weight": 1.0,
        "speed_limit":  160,
    },
    {
        "id":           5,
        "code":         "ALJN-TDL-BOTH",
        "name":         "Aligarh - Tundla Junction",
        "line_type":    "BOTH",
        "asset_class":  "Mainline Trunk",
        "traffic_weight": 0.9,
        "speed_limit":  140,
    },
    {
        "id":           6,
        "code":         "TDL-CNB-BOTH",
        "name":         "Tundla - Kanpur Central",
        "line_type":    "BOTH",
        "asset_class":  "Mainline Trunk",
        "traffic_weight": 0.9,
        "speed_limit":  140,
    },
    {
        "id":           7,
        "code":         "DLI-RE-SL",
        "name":         "Delhi - Rewari (Single Line)",
        "line_type":    "SINGLE",
        "asset_class":  "Branch Line",
        "traffic_weight": 0.7,
        "speed_limit":  100,
    },
    {
        "id":           8,
        "code":         "CNB-YARD",
        "name":         "Kanpur Central Yard & Loop Lines",
        "line_type":    "BOTH",
        "asset_class":  "Yard/Loop",
        "traffic_weight": 0.3,
        "speed_limit":  30,
    },
]

# Department definitions
DEPARTMENTS: list[dict] = [
    {"id": 1, "code": "TRK", "name": "Engineering (Track)",    "source_system": "TMS"},
    {"id": 2, "code": "SNT", "name": "Signal & Telecom (S&T)", "source_system": "SMMS"},
    {"id": 3, "code": "OHE", "name": "Traction (OHE/TRD)",    "source_system": "TDMS"},
]

# Defect catalogue: (defect_type, base_severity, base_duration_min, category, recommended_action)
DEFECT_CATALOGUE: dict[str, list[tuple]] = {
    "TRK": [
        ("Weld / Rail Fracture",               5, 180, "IMR Critical Defect",           "Execute AT Thermit weld with tensor puller; impose 30 km/h caution order until completion."),
        ("Ballast Deep Screening (BCM)",        3, 240, "Track Geometry Defect",         "Deploy Ballast Cleaning Machine; restore ballast profile and compaction."),
        ("Tamping — CST-9 / 09-3X",            2, 120, "Routine Geometry Maintenance",  "Deploy dynamic continuous tamping machine; restore track geometry."),
        ("USFD Testing (Ultrasonic Flaw)",      3, 120, "Periodic Rail Integrity Audit", "Manual USFD trolley run along both rail tables; tag defective rails."),
        ("Turnout / Crossover Renewal",         4, 180, "Switch & Crossing Renewal",     "Crane replacement of worn CMS frog; re-align switch rails and check rail."),
        ("Rail End Hardening & Weld Grinding",  3,  90, "Weld Quality Deviation",        "Grind flash-butt weld to profile; apply end-hardening paste."),
        ("PSC Sleeper Replacement",             4, 150, "Sleeper Defect",                "Replace deteriorated wooden sleepers with PSC/composite sleepers."),
        ("Check Rail Clearance Adjustment",     3,  90, "Gauge / Clearance Issue",       "Adjust check rail fixing bolts; verify clearance within 41–48 mm spec."),
        ("Bridge Approach Track Renewal",       5, 180, "OBS Critical — Bridge Defect",  "Full sleeper replacement at bridge approach; restore cant and alignment."),
        ("LWR Destressing",                     3, 240, "Long Welded Rail Thermal Stress","Destress LWR rail section using tensor; cut and re-weld to neutral temperature."),
        ("Fish-plate / Joggled Joint Renewal",  2,  60, "Joint Defect",                  "Replace cracked fish-plates; torque all bolts to specification."),
        ("Spot Tamping",                        2,  60, "Routine Spot Maintenance",      "Spot tamp isolated low joints; restore vertical geometry."),
    ],
    "SNT": [
        ("Point Motor Replacement",             5,  90, "Interlocking Point Failure",    "Replace 110V DC Siemens point motor; calibrate FPL and detection."),
        ("Track Circuit Failure (Red Drop)",    4,  60, "Track Vacancy Detection Flaw",  "Restore insulated rail joints; replace tuning unit if shunting fault confirmed."),
        ("Axle Counter Reset & Calibration",    4,  75, "Track Vacancy Detection Flaw",  "Replace transducer sensor heads; re-evaluate reset count in BPAC."),
        ("Signal Aspect LED Change",            2,  45, "Signal Head Defect",            "Replace failed LED module in signal head; verify aspect sequence."),
        ("Relay Room — Battery Bank Testing",   1, 210, "Auxiliary Power Audit",         "Quarterly discharge test of IPS battery bank; log cell voltages."),
        ("OFC Cable Jointing",                  3,  90, "Telecom Cable Defect",          "Re-joint damaged OFC cable splice; restore STM-1 / IP connectivity."),
        ("Level Crossing Gate Motor Overhaul",  3, 120, "LC Gate Mechanism Defect",      "Overhaul electric gate motor; test auto-lifting under train approach."),
        ("Route Relay Interlocking (RRI) Test", 2, 120, "Interlocking Annual Test",      "Annual functional test of all routes in RRI panel; update test register."),
        ("BPAC / ATP System Reset",             4,  60, "Automatic Train Protection",    "Reset ATP on-board system after ground sensor fault; verify target speed compliance."),
        ("Facing Point Lock (FPL) Calibration", 4,  75, "Signal Point Lock Fault",       "Adjust lock stretcher bar; ground lock test under 5 traversals."),
    ],
    "OHE": [
        ("Catenary Wire Snapping / Emergency Repair", 5, 180, "OHE Emergency — Train Detention",   "Replace snapped contact wire span; re-tension adjacent spans to ATD spec."),
        ("Pantograph Entanglement Clearance",          5, 120, "Traction Emergency",                "Clear entangled OHE; replace contact wire and re-check stagger."),
        ("Insulator Flashover / Replacement",          4, 120, "Traction Insulation Defect",        "Replace porcelain disc insulator; earth test and HV proof test."),
        ("Bracket Assembly Adjustment",                2,  90, "Catenary Geometry Defect",          "Adjust cantilever bracket; restore contact wire stagger within ±100 mm."),
        ("Contact Wire Sag / Height Adjustment",       3, 120, "Catenary Sag Defect",               "Adjust auto-tensioning device (ATD); restore wire height to 5.5–6.0 m spec."),
        ("Earth Bond / Mast Earthing Inspection",      3,  90, "Traction Earthing Defect",          "Replace copper earth bond strips; test resistance < 10 Ohms."),
        ("Section Insulator / Overlap Adjustment",     3,  90, "Neutral Section Issue",             "Adjust section insulator position; verify neutral zone compliance."),
        ("Feeder Cable Termination Renewal",           4, 150, "Feeding Cable Defect",              "Re-terminate 25 kV feeder cable at substation gantry; IR test."),
        ("Dropper / Current-Carrying Wire Replacement",3, 120, "Catenary Dropper Defect",           "Replace fatigued copper droppers; calibrate ATD and check wire tension."),
        ("OHE Tower Wagon Maintenance Window",         2, 120, "Scheduled OHE Patrol",             "Monthly patrol inspection from tower wagon; log defects and temporary repairs."),
    ],
}

# Crew configurations by department
CREW_CONFIGS: dict[str, list[dict]] = {
    "TRK": [
        {"size": 12, "supervisor": "SSE (P-Way) Anand Vihar",        "machine": "Amsler Rail Tensor & Flash Butt Weld Gang"},
        {"size": 14, "supervisor": "SSE (Track Machines) Dadri",     "machine": "Plasser 09-3X Tamping Machine"},
        {"size":  8, "supervisor": "SSE (USFD) Delhi Division",      "machine": "Digital Ultrasonic Flaw Detector Trolley"},
        {"size": 16, "supervisor": "ADEN Etawah",                    "machine": "Bridge Tamping & Sleeper Insertion Unit"},
        {"size": 15, "supervisor": "SSE (P-Way) Hathras",            "machine": "10T Track Rail Crane & Spot Tamper"},
        {"size": 10, "supervisor": "SSE (P-Way) Ghaziabad",          "machine": "Ballast Cleaning Machine (BCM)"},
        {"size":  6, "supervisor": "SSE (P-Way) Aligarh Section",    "machine": "Joint Grinding Power Pack"},
    ],
    "SNT": [
        {"size": 5, "supervisor": "SSE (Signal/Auto) Delhi Jn",      "machine": "Digital Signal Analyzer & Sensor Torque Rig"},
        {"size": 6, "supervisor": "SSE (Signal) Khurja Junction",    "machine": "Signal Diagnostic & Cable Megger Set"},
        {"size": 4, "supervisor": "SSE (Signal/Tele) Shikohabad",    "machine": "OFC Fusion Splicer & OTDR"},
        {"size": 6, "supervisor": "SSE (Signal) Hathras",            "machine": "Signal Diagnostic Rig"},
        {"size": 5, "supervisor": "JE (Signal) Ghaziabad",           "machine": "Point Motor Test Bench"},
    ],
    "OHE": [
        {"size": 8, "supervisor": "SSE (TRD/OHE) Ghaziabad Yard",   "machine": "OHE 8-Wheeler Tower Wagon #1402"},
        {"size": 6, "supervisor": "SSE (TRD) Shikohabad",           "machine": "Ladder Trolley & Earthing Rods"},
        {"size": 8, "supervisor": "SSE (TRD) Aligarh",              "machine": "OHE Tower Car #1209"},
        {"size": 9, "supervisor": "SSE (TRD) Kanpur",               "machine": "Tower Wagon & Wire Reel Trailer"},
        {"size": 7, "supervisor": "JE (TRD) Tundla",                "machine": "OHE Maintenance Tower Trolley"},
    ],
}

# Power disconnection required by defect type keyword
POWER_DISCONNECTION_KEYWORDS = {
    "TRK": ["Fracture", "Weld", "Bridge", "PSC Sleeper", "Turnout", "LWR"],
    "SNT": [],   # Signal work rarely needs OHE off
    "OHE": True, # OHE work ALWAYS needs power off
}

# Compatible department pairings (for Integrated Joint Block logic)
COMPATIBILITY_MAP: dict[str, str | None] = {
    "TRK": "OHE",   # Track and OHE share power isolation
    "OHE": "TRK",
    "SNT": None,    # Signal rarely merges
}

# Speed restrictions after work, by defect type keyword
SPEED_RESTRICTIONS: dict[str, str] = {
    "Fracture":    "45 km/h for 24h, then normal speed",
    "Weld":        "30 km/h for 4h post-weld; normal after cool-down inspection",
    "Tamping":     "75 km/h for 48h",
    "Crossover":   "30 km/h for 24h",
    "Bridge":      "30 km/h for 12h",
    "Screening":   "Normal speed restored immediately",
    "Sleeper":     "50 km/h for 24h",
    "LWR":         "Normal speed after stress-free certification",
}

# Window types mapped to hour ranges
WINDOW_TYPES: list[dict] = [
    {"label": "Night Gold Window",      "start_hour": 2,  "end_hour": 6,  "source": "COA_Timetable_Gap"},
    {"label": "Early Morning Window",   "start_hour": 5,  "end_hour": 8,  "source": "COA_Timetable_Gap"},
    {"label": "Midday Freight Window",  "start_hour": 13, "end_hour": 16, "source": "Freight_Lull"},
]


# ===========================================================================
# WINDOW GENERATOR
# ===========================================================================

def generate_windows() -> list[dict]:
    """
    Generate COA block windows for all corridors across the 7-day planning horizon.
    Each corridor gets 2–3 windows per day depending on its traffic density.
    The Sunday window on high-traffic corridors is extended to a 5-hour Mega Block.
    """
    windows: list[dict] = []
    w_id = 1

    for corridor in CORRIDORS:
        for day_offset in range(PLAN_HORIZON_DAYS):
            day_date = BASE_DATE + timedelta(days=day_offset)
            is_sunday = day_date.weekday() == 6  # Sunday = 6

            for wtype in WINDOW_TYPES:
                # High-traffic corridors don't get midday freight windows Mon–Fri
                if (
                    wtype["label"] == "Midday Freight Window"
                    and corridor["traffic_weight"] >= 1.0
                    and not is_sunday
                    and day_date.weekday() < 5
                ):
                    continue

                start_h = wtype["start_hour"]
                end_h   = wtype["end_hour"]

                # Sunday Mega Block: extend Night Gold Window by 3 hours on trunk lines
                if is_sunday and wtype["label"] == "Night Gold Window" and corridor["traffic_weight"] >= 0.9:
                    end_h = 7

                # Yard lines always get wider windows
                if corridor["asset_class"] == "Yard/Loop":
                    end_h = min(end_h + 2, 23)

                start_dt = day_date + timedelta(hours=start_h)
                end_dt   = day_date + timedelta(hours=end_h)
                duration = int((end_dt - start_dt).total_seconds() / 60)

                windows.append({
                    "id":           w_id,
                    "corridor_id":  corridor["id"],
                    "corridor_code": corridor["code"],
                    "corridor_name": corridor["name"],
                    "window_label": wtype["label"],
                    "start_time":   start_dt.isoformat(),
                    "end_time":     end_dt.isoformat(),
                    "duration_min": duration,
                    "source":       wtype["source"],
                    "is_available": True,
                })
                w_id += 1

    return windows


# ===========================================================================
# TASK BUILDER HELPERS
# ===========================================================================

def _dept_id(code: str) -> int:
    return next(d["id"] for d in DEPARTMENTS if d["code"] == code)


def _corridor_by_id(cid: int) -> dict:
    return next(c for c in CORRIDORS if c["id"] == cid)


def _pick_crew(dept: str) -> dict:
    return random.choice(CREW_CONFIGS[dept])


def _needs_power(dept: str, defect_type: str) -> bool:
    if dept == "OHE":
        return True
    keywords = POWER_DISCONNECTION_KEYWORDS.get(dept, [])
    return any(kw.lower() in defect_type.lower() for kw in keywords)


def _speed_restriction(defect_type: str) -> str | None:
    for kw, restriction in SPEED_RESTRICTIONS.items():
        if kw.lower() in defect_type.lower():
            return restriction
    return None


def _build_task(
    task_id: str,
    dept_code: str,
    corridor_id: int,
    defect_tuple: tuple,
    days_overdue: int,
    req_start: datetime,
    severity_override: int | None = None,
    compatible_with: str | None = None,
    status: str = "Pending",
) -> dict:
    """Construct a fully-populated task dict."""
    defect_type, base_sev, base_dur, category, rec_action = defect_tuple
    severity = severity_override if severity_override is not None else base_sev
    corridor = _corridor_by_id(corridor_id)
    crew     = _pick_crew(dept_code)
    dept     = next(d for d in DEPARTMENTS if d["code"] == dept_code)

    result = calculate_criticality_score_full(
        severity=severity,
        days_overdue=days_overdue,
        traffic_weight=corridor["traffic_weight"],
    )

    # Derive compatible_with from map if not explicitly set
    compat = compatible_with if compatible_with is not None else (
        COMPATIBILITY_MAP.get(dept_code) if random.random() < 0.3 else None
    )

    return {
        "id":                  task_id,
        "department_id":       dept["id"],
        "department_code":     dept_code,
        "department_name":     dept["name"],
        "corridor_id":         corridor_id,
        "corridor_code":       corridor["code"],
        "corridor_name":       corridor["name"],
        "defect_code":         f"{dept['source_system']}-{dept_code}-{task_id.split('-')[1]}",
        "defect_type":         defect_type,
        "defect_category":     category,
        "source_system":       dept["source_system"],
        "description":         f"{defect_type} on {corridor['name']} — {category}.",
        "recommended_action":  rec_action,
        "severity":            severity,
        "days_overdue":        days_overdue,
        "reported_date":       (req_start - timedelta(days=days_overdue + random.randint(1, 5))).strftime("%Y-%m-%d"),
        "est_duration_min":    base_dur,
        "requested_start":     req_start.isoformat(),
        "requested_end":       (req_start + timedelta(minutes=base_dur)).isoformat(),
        "criticality_score":   result.total_score,
        "priority_level":      result.priority_level,
        "score_severity_component": result.weighted_severity,
        "score_overdue_component":  result.weighted_overdue,
        "score_traffic_component":  result.weighted_traffic,
        "score_formula":       result.formula,
        "is_compatible_with":  compat,
        "status":              status,
        "power_disconnection_required": _needs_power(dept_code, defect_type),
        "speed_restriction_afterwards": _speed_restriction(defect_type),
        "crew_size":           crew["size"],
        "supervisor":          crew["supervisor"],
        "required_machine":    crew.get("machine"),
    }


# ===========================================================================
# TASK GENERATOR
# ===========================================================================

def generate_tasks() -> list[dict]:
    tasks: list[dict] = []
    counters = {"TRK": 1000, "SNT": 2000, "OHE": 3000}

    def next_id(dept: str) -> str:
        tid = f"{dept}-{counters[dept]}"
        counters[dept] += 1
        return tid

    # -----------------------------------------------------------------------
    # SCENARIO 1 — THE INTEGRATED BLOCK  (Jury-Hook A)
    # -----------------------------------------------------------------------
    # Track and OHE both request the exact same corridor (NDLS-GZB-UP) at the
    # exact same time (Monday 02:00). The optimizer merges them into one block.
    #
    # Both tasks are given high severity/overdue so they appear at the top of
    # the priority queue and get processed consecutively by the scheduler.
    # Severity 4 + 7 days overdue on Mainline = score ~84 (P0).
    # -----------------------------------------------------------------------
    s1_start = BASE_DATE + timedelta(hours=2)          # Mon 02:00

    t1 = _build_task(
        task_id       = next_id("TRK"),                # TRK-1000
        dept_code     = "TRK",
        corridor_id   = 1,                             # NDLS-GZB-UP
        defect_tuple  = DEFECT_CATALOGUE["TRK"][2],    # Tamping
        days_overdue  = 7,
        req_start     = s1_start,
        severity_override = 4,
        compatible_with   = "OHE",
        status        = "Clashed",
    )
    t1["joint_pair_id"] = "S1"   # Explicit pairing key for the scheduler
    tasks.append(t1)

    t2 = _build_task(
        task_id       = next_id("OHE"),                # OHE-3000
        dept_code     = "OHE",
        corridor_id   = 1,                             # NDLS-GZB-UP
        defect_tuple  = DEFECT_CATALOGUE["OHE"][2],    # Insulator Flashover
        days_overdue  = 6,
        req_start     = s1_start,
        severity_override = 4,
        compatible_with   = "TRK",
        status        = "Clashed",
    )
    t2["joint_pair_id"] = "S1"   # Explicit pairing key for the scheduler
    tasks.append(t2)

    # -----------------------------------------------------------------------
    # SCENARIO 2 — THE SAFETY OVERRIDE  (Jury-Hook B)
    # -----------------------------------------------------------------------
    # S&T requests a routine LED change (Sev 1, 0 overdue) at 13:00 Tue on
    # DLI-RE. Track requests a Rail Fracture repair (Sev 5, 15 overdue) at
    # the exact same slot. Criticality engine scores Track ~80, Signal ~14.
    # The optimizer gives the slot to Track — proving safety-first logic.
    # -----------------------------------------------------------------------
    s2_start = BASE_DATE + timedelta(days=1, hours=13)  # Tue 13:00

    tasks.append(_build_task(
        task_id       = next_id("SNT"),                # SNT-2000
        dept_code     = "SNT",
        corridor_id   = 7,                             # DLI-RE-SL
        defect_tuple  = DEFECT_CATALOGUE["SNT"][3],    # Signal LED Change
        days_overdue  = 0,
        req_start     = s2_start,
        severity_override = 1,
        compatible_with   = None,
        status        = "Clashed",
    ))

    tasks.append(_build_task(
        task_id       = next_id("TRK"),                # TRK-1001
        dept_code     = "TRK",
        corridor_id   = 7,                             # DLI-RE-SL
        defect_tuple  = DEFECT_CATALOGUE["TRK"][0],    # Weld / Rail Fracture
        days_overdue  = 15,
        req_start     = s2_start,
        severity_override = 5,
        compatible_with   = None,
        status        = "Clashed",
    ))

    # -----------------------------------------------------------------------
    # SCENARIO 3 — THE IMPOSSIBLE TASK  (Jury-Hook C)
    # -----------------------------------------------------------------------
    # Track requests a 6-hour Deep Screening block on NDLS-GZB-UP.
    # Every window available on that corridor is ≤ 4 hours.
    # Optimizer outputs this task in "unscheduled" with a clear reason.
    # -----------------------------------------------------------------------
    s3_start = BASE_DATE + timedelta(days=2, hours=10)  # Wed 10:00

    impossible_task = _build_task(
        task_id       = next_id("TRK"),                # TRK-1002
        dept_code     = "TRK",
        corridor_id   = 1,                             # NDLS-GZB-UP
        defect_tuple  = DEFECT_CATALOGUE["TRK"][1],    # Ballast Deep Screening (BCM)
        days_overdue  = 2,
        req_start     = s3_start,
        severity_override = 3,
        compatible_with   = None,
        status        = "Deferred",
    )
    # Override duration to 360 min (6 hours) to guarantee infeasibility.
    # The criticality_score was already calculated correctly in _build_task()
    # and is unaffected by duration — no score recalculation needed.
    impossible_task["est_duration_min"] = 360
    impossible_task["requested_end"]    = (
        s3_start + timedelta(minutes=360)
    ).isoformat()
    # Recalculate score (duration doesn't affect score but we want consistency)
    tasks.append(impossible_task)

    # -----------------------------------------------------------------------
    # ADDITIONAL HIGH-PRIORITY SCENARIOS — enrich the Gantt with drama
    # -----------------------------------------------------------------------

    # Scenario 4: Bridge approach fracture — highest possible score
    s4_start = BASE_DATE + timedelta(days=0, hours=1)
    tasks.append(_build_task(
        task_id       = next_id("TRK"),
        dept_code     = "TRK",
        corridor_id   = 6,                             # TDL-CNB
        defect_tuple  = DEFECT_CATALOGUE["TRK"][8],    # Bridge Approach Track Renewal
        days_overdue  = 17,
        req_start     = s4_start,
        severity_override = 5,
        compatible_with   = "OHE",
        status        = "Clashed",
    ))

    tasks.append(_build_task(
        task_id       = next_id("OHE"),
        dept_code     = "OHE",
        corridor_id   = 6,
        defect_tuple  = DEFECT_CATALOGUE["OHE"][5],    # Earth Bond Inspection
        days_overdue  = 8,
        req_start     = s4_start + timedelta(minutes=30),
        severity_override = 3,
        compatible_with   = "TRK",
        status        = "Clashed",
    ))

    # Scenario 5: Three-department crossover clash on ALJN-TDL
    s5_start = BASE_DATE + timedelta(days=0, hours=2)
    tasks.append(_build_task(
        task_id       = next_id("TRK"),
        dept_code     = "TRK",
        corridor_id   = 5,
        defect_tuple  = DEFECT_CATALOGUE["TRK"][4],    # Turnout Renewal
        days_overdue  = 13,
        req_start     = s5_start,
        severity_override = 5,
        compatible_with   = "OHE",
        status        = "Clashed",
    ))

    tasks.append(_build_task(
        task_id       = next_id("SNT"),
        dept_code     = "SNT",
        corridor_id   = 5,
        defect_tuple  = DEFECT_CATALOGUE["SNT"][9],    # FPL Calibration
        days_overdue  = 6,
        req_start     = s5_start + timedelta(minutes=30),
        severity_override = 4,
        compatible_with   = None,
        status        = "Clashed",
    ))

    tasks.append(_build_task(
        task_id       = next_id("OHE"),
        dept_code     = "OHE",
        corridor_id   = 5,
        defect_tuple  = DEFECT_CATALOGUE["OHE"][6],    # Section Insulator Adjustment
        days_overdue  = 3,
        req_start     = s5_start,
        severity_override = 3,
        compatible_with   = "TRK",
        status        = "Clashed",
    ))

    # Scenario 6: Axle counter vs USFD clash on NDLS-GZB-DN
    s6_start = BASE_DATE + timedelta(days=0, hours=2)
    tasks.append(_build_task(
        task_id       = next_id("SNT"),
        dept_code     = "SNT",
        corridor_id   = 2,
        defect_tuple  = DEFECT_CATALOGUE["SNT"][2],    # Axle Counter Reset
        days_overdue  = 11,
        req_start     = s6_start,
        severity_override = 5,
        compatible_with   = None,
        status        = "Clashed",
    ))

    tasks.append(_build_task(
        task_id       = next_id("TRK"),
        dept_code     = "TRK",
        corridor_id   = 2,
        defect_tuple  = DEFECT_CATALOGUE["TRK"][3],    # USFD Testing
        days_overdue  = 4,
        req_start     = s6_start,
        severity_override = 3,
        compatible_with   = None,
        status        = "Clashed",
    ))

    # Scenario 7: OHE catenary snap on GZB-ALJN-UP + Track weld clash
    s7_start = BASE_DATE + timedelta(days=0, hours=1, minutes=30)
    tasks.append(_build_task(
        task_id       = next_id("OHE"),
        dept_code     = "OHE",
        corridor_id   = 3,
        defect_tuple  = DEFECT_CATALOGUE["OHE"][8],    # Dropper Replacement
        days_overdue  = 7,
        req_start     = s7_start,
        severity_override = 4,
        compatible_with   = "TRK",
        status        = "Clashed",
    ))

    tasks.append(_build_task(
        task_id       = next_id("TRK"),
        dept_code     = "TRK",
        corridor_id   = 3,
        defect_tuple  = DEFECT_CATALOGUE["TRK"][5],    # Rail End Hardening
        days_overdue  = 5,
        req_start     = s7_start + timedelta(minutes=30),
        severity_override = 4,
        compatible_with   = "OHE",
        status        = "Clashed",
    ))

    # -----------------------------------------------------------------------
    # RANDOM NOISE — fill up to 150+ total tasks
    # -----------------------------------------------------------------------
    # Overdue distribution weights: mostly fresh, some overdue, a few very overdue
    overdue_pool = (
        [0] * 12 +
        [1, 2, 3] * 6 +
        [5, 7, 9] * 4 +
        [14, 21, 28] * 2 +
        [30, 35, 45]
    )

    target_total = 150
    while len(tasks) < target_total:
        dept_code  = random.choices(["TRK", "SNT", "OHE"], weights=[5, 3, 4])[0]
        corridor   = random.choice(CORRIDORS)
        defect     = random.choice(DEFECT_CATALOGUE[dept_code])
        overdue    = random.choice(overdue_pool)

        # Vary severity slightly around the base defect severity
        base_sev   = defect[1]
        severity   = min(5, max(1, base_sev + random.randint(-1, 1)))

        # Scatter requests across the 7-day horizon at random hours
        day_offset = random.randint(0, PLAN_HORIZON_DAYS - 1)
        hour       = random.randint(0, 22)
        req_start  = BASE_DATE + timedelta(days=day_offset, hours=hour)

        dept_obj   = next(d for d in DEPARTMENTS if d["code"] == dept_code)
        task_id    = next_id(dept_code)

        # Avoid duplicate IDs (paranoia check)
        existing_ids = {t["id"] for t in tasks}
        if task_id in existing_ids:
            continue

        tasks.append(_build_task(
            task_id          = task_id,
            dept_code        = dept_code,
            corridor_id      = corridor["id"],
            defect_tuple     = defect,
            days_overdue     = overdue,
            req_start        = req_start,
            severity_override = severity,
            compatible_with  = None,
            status           = "Pending",
        ))

    return tasks


# ===========================================================================
# CONFLICT PAIR DETECTOR
# ===========================================================================

def detect_conflicts(tasks: list[dict]) -> list[dict]:
    """
    Identify all pairs of tasks that clash on the same corridor with
    overlapping requested time windows. Returns a list of conflict pair dicts.
    """
    conflicts: list[dict] = []
    pending = [t for t in tasks if t["status"] in ("Clashed", "Pending")]
    conf_id = 1

    for i, task_a in enumerate(pending):
        for task_b in pending[i + 1:]:
            if task_a["corridor_id"] != task_b["corridor_id"]:
                continue
            if task_a["department_code"] == task_b["department_code"]:
                continue  # same-dept conflicts are handled by the dept internally

            a_start = datetime.fromisoformat(task_a["requested_start"])
            a_end   = datetime.fromisoformat(task_a["requested_end"])
            b_start = datetime.fromisoformat(task_b["requested_start"])
            b_end   = datetime.fromisoformat(task_b["requested_end"])

            overlap_start = max(a_start, b_start)
            overlap_end   = min(a_end,   b_end)

            if overlap_end <= overlap_start:
                continue   # No actual overlap

            overlap_min = int((overlap_end - overlap_start).total_seconds() / 60)

            # Determine conflict severity
            max_score = max(task_a["criticality_score"], task_b["criticality_score"])
            if max_score >= 80:
                conf_sev = "Critical"
            elif max_score >= 50:
                conf_sev = "High"
            else:
                conf_sev = "Moderate"

            # Determine conflict type
            a_dept = task_a["department_code"]
            b_dept = task_b["department_code"]
            if "OHE" in (a_dept, b_dept):
                conflict_type = "Power/OHE Dependency"
            elif "SNT" in (a_dept, b_dept):
                conflict_type = "Signal Interlocking"
            else:
                conflict_type = "Physical Line Occupancy"

            # Resolution strategy hint
            a_compat = task_a.get("is_compatible_with")
            b_compat = task_b.get("is_compatible_with")
            if (a_compat == b_dept) or (b_compat == a_dept):
                resolution = (
                    f"Merge into Integrated Joint Block on {task_a['corridor_name']}. "
                    f"Shared traction power isolation saves ~{overlap_min} minutes corridor downtime."
                )
            else:
                # Higher-score task keeps the slot; lower is re-sequenced
                winner = task_a if task_a["criticality_score"] >= task_b["criticality_score"] else task_b
                loser  = task_b if winner["id"] == task_a["id"] else task_a
                resolution = (
                    f"Priority-based de-confliction: {winner['id']} (Score {winner['criticality_score']}) "
                    f"retains the window. {loser['id']} (Score {loser['criticality_score']}) "
                    f"rescheduled to next available window."
                )

            conflicts.append({
                "id":                   f"conf-{conf_id:04d}",
                "task_a_id":            task_a["id"],
                "task_b_id":            task_b["id"],
                "corridor_id":          task_a["corridor_id"],
                "corridor_name":        task_a["corridor_name"],
                "overlap_start":        overlap_start.isoformat(),
                "overlap_end":          overlap_end.isoformat(),
                "overlap_duration_min": overlap_min,
                "conflict_severity":    conf_sev,
                "conflict_type":        conflict_type,
                "resolution_strategy":  resolution,
                "task_a_score":         task_a["criticality_score"],
                "task_b_score":         task_b["criticality_score"],
            })
            conf_id += 1

            # Only upgrade status to Clashed — never overwrite Deferred or Scheduled
            if task_a["status"] == "Pending":
                task_a["status"] = "Clashed"
            if task_b["status"] == "Pending":
                task_b["status"] = "Clashed"

    return conflicts


# ===========================================================================
# SEED SUMMARY
# ===========================================================================

def build_summary(tasks: list[dict], windows: list[dict], conflicts: list[dict]) -> dict:
    scores = [t["criticality_score"] for t in tasks]
    by_dept: dict[str, int] = {}
    by_status: dict[str, int] = {}
    by_priority: dict[str, int] = {}
    for t in tasks:
        by_dept[t["department_code"]]  = by_dept.get(t["department_code"], 0) + 1
        by_status[t["status"]]         = by_status.get(t["status"], 0) + 1
        by_priority[t["priority_level"]] = by_priority.get(t["priority_level"], 0) + 1

    return {
        "generated_at":         datetime.now(timezone.utc).isoformat(),
        "random_seed":          RANDOM_SEED,
        "base_date":            BASE_DATE.isoformat(),
        "plan_horizon_days":    PLAN_HORIZON_DAYS,
        "total_tasks":          len(tasks),
        "total_windows":        len(windows),
        "total_conflicts":      len(conflicts),
        "tasks_by_department":  by_dept,
        "tasks_by_status":      by_status,
        "tasks_by_priority":    by_priority,
        "score_min":            round(min(scores), 2),
        "score_max":            round(max(scores), 2),
        "score_avg":            round(sum(scores) / len(scores), 2),
        "jury_hook_scenarios": {
            "scenario_1_integrated_block": {
                "task_a": "TRK-1000",
                "task_b": "OHE-3000",
                "corridor": "NDLS-GZB-UP",
                "description": "Track and OHE clash at same time on same corridor — optimizer merges into one Integrated Joint Block."
            },
            "scenario_2_safety_override": {
                "task_low_score":  "SNT-2000",
                "task_high_score": "TRK-1001",
                "corridor": "DLI-RE-SL",
                "description": "Rail Fracture (Sev 5, 15 overdue) beats Signal LED change (Sev 1, 0 overdue) for the same slot."
            },
            "scenario_3_impossible_task": {
                "task_id": "TRK-1002",
                "corridor": "NDLS-GZB-UP",
                "requested_duration_min": 360,
                "max_available_window_min": 240,
                "description": "6-hour request on a corridor with max 4-hour windows — graceful deferral with reason."
            }
        }
    }


# ===========================================================================
# MAIN
# ===========================================================================

def main(verbose: bool = False) -> None:
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    if verbose:
        print("BlockSync Demo Dataset Generator")
        print("=" * 50)

    # --- Generate ---
    if verbose:
        print("Generating COA block windows...")
    windows  = generate_windows()

    if verbose:
        print(f"  {len(windows)} windows across {PLAN_HORIZON_DAYS} days × {len(CORRIDORS)} corridors")
        print("Generating maintenance tasks...")
    tasks    = generate_tasks()

    if verbose:
        print(f"  {len(tasks)} tasks generated")
        print("Detecting conflicts...")
    conflicts = detect_conflicts(tasks)

    if verbose:
        print(f"  {len(conflicts)} conflict pairs detected")

    summary  = build_summary(tasks, windows, conflicts)

    # --- Write outputs ---
    outputs = {
        "tasks.json":          tasks,
        "windows.json":        windows,
        "conflict_pairs.json": conflicts,
        "seed_summary.json":   summary,
    }

    for filename, data in outputs.items():
        path = os.path.join(OUTPUT_DIR, filename)
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2, ensure_ascii=False)
        if verbose:
            print(f"  Written → {path}")

    # --- Print summary ---
    print(f"\n✓ Dataset generated successfully.")
    print(f"  Tasks:     {summary['total_tasks']}")
    print(f"  Windows:   {summary['total_windows']}")
    print(f"  Conflicts: {summary['total_conflicts']}")
    print(f"  Scores:    min={summary['score_min']}  avg={summary['score_avg']}  max={summary['score_max']}")
    print(f"  Priority breakdown: {summary['tasks_by_priority']}")
    print(f"\n  Jury-hook scenarios:")
    for name, sc in summary["jury_hook_scenarios"].items():
        print(f"    [{name}] {sc['description']}")
    print(f"\n  Output files in: {os.path.abspath(OUTPUT_DIR)}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="BlockSync Demo Dataset Generator")
    parser.add_argument("--verbose", "-v", action="store_true", help="Print detailed progress")
    args = parser.parse_args()
    main(verbose=args.verbose)
