"""
backend/core/validator.py
==========================
BlockSync Data Integrity Validator
Branch: hriday-dataset | Author: Hriday

Validates task and window dicts before they are inserted into the database
or returned through the API. Catches bad data at the boundary so the optimizer
and frontend never receive malformed input.

Used by:
  - backend/core/seed.py   — validates every row before INSERT
  - scripts/generate_demo_data.py — optional post-generation audit
  - FastAPI routes          — validates incoming request bodies
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


# ---------------------------------------------------------------------------
# Result containers
# ---------------------------------------------------------------------------

@dataclass
class ValidationError:
    field: str
    message: str

    def __str__(self) -> str:
        return f"[{self.field}] {self.message}"


@dataclass
class ValidationResult:
    is_valid: bool = True
    errors: list[ValidationError] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def add_error(self, field: str, message: str) -> None:
        self.errors.append(ValidationError(field, message))
        self.is_valid = False

    def add_warning(self, message: str) -> None:
        self.warnings.append(message)

    def __str__(self) -> str:
        lines = []
        if self.is_valid:
            lines.append("✓ Valid")
        else:
            lines.append(f"✗ Invalid ({len(self.errors)} error(s))")
        for e in self.errors:
            lines.append(f"  ERROR: {e}")
        for w in self.warnings:
            lines.append(f"  WARN:  {w}")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Constants (must match scoring.py and generate_demo_data.py)
# ---------------------------------------------------------------------------

VALID_DEPT_CODES     = {"TRK", "SNT", "OHE"}
VALID_SOURCE_SYSTEMS = {"TMS", "SMMS", "TDMS"}
VALID_STATUSES       = {"Pending", "Clashed", "Scheduled", "Merged", "Deferred", "Approved"}
VALID_PRIORITY       = {"P0", "P1", "P2"}
VALID_LINE_TYPES     = {"UP", "DOWN", "BOTH", "SINGLE"}
VALID_ASSET_CLASSES  = {"Mainline Trunk", "Branch Line", "Yard/Loop"}
VALID_WINDOW_LABELS  = {
    "Night Gold Window",
    "Early Morning Window",
    "Midday Freight Window",
    "Emergency Window",
    "Sunday Mega Block",
}

MIN_DURATION_MIN = 15      # shorter than this is almost certainly a data error
MAX_DURATION_MIN = 600     # 10 hours — realistic upper bound for any single block
MAX_SEVERITY     = 5
MIN_SEVERITY     = 1
MAX_SCORE        = 100.0
MIN_SCORE        = 0.0


# ---------------------------------------------------------------------------
# Individual field validators (reusable)
# ---------------------------------------------------------------------------

def _validate_iso_datetime(value: Any, field_name: str, result: ValidationResult) -> datetime | None:
    """Parse and validate an ISO-8601 datetime string. Returns the parsed datetime or None."""
    if value is None:
        result.add_error(field_name, "Required field is missing or null.")
        return None
    if not isinstance(value, str):
        result.add_error(field_name, f"Expected ISO string, got {type(value).__name__}.")
        return None
    try:
        dt = datetime.fromisoformat(value)
        # Warn if no timezone info — the DB stores TIMESTAMPTZ
        if dt.tzinfo is None:
            result.add_warning(f"{field_name}: datetime has no timezone info — assuming UTC.")
        return dt
    except ValueError:
        result.add_error(field_name, f"Cannot parse '{value}' as ISO-8601 datetime.")
        return None


def _validate_int_range(
    value: Any, field_name: str, lo: int, hi: int, result: ValidationResult
) -> bool:
    if not isinstance(value, int):
        result.add_error(field_name, f"Expected int, got {type(value).__name__}.")
        return False
    if not lo <= value <= hi:
        result.add_error(field_name, f"Value {value} out of range [{lo}, {hi}].")
        return False
    return True


def _validate_float_range(
    value: Any, field_name: str, lo: float, hi: float, result: ValidationResult
) -> bool:
    if not isinstance(value, (int, float)):
        result.add_error(field_name, f"Expected numeric, got {type(value).__name__}.")
        return False
    if not lo <= float(value) <= hi:
        result.add_error(field_name, f"Value {value} out of range [{lo}, {hi}].")
        return False
    return True


def _validate_str_in_set(
    value: Any, field_name: str, allowed: set[str], result: ValidationResult
) -> bool:
    if not isinstance(value, str):
        result.add_error(field_name, f"Expected str, got {type(value).__name__}.")
        return False
    if value not in allowed:
        result.add_error(field_name, f"'{value}' is not one of {sorted(allowed)}.")
        return False
    return True


def _validate_non_empty_str(value: Any, field_name: str, result: ValidationResult) -> bool:
    if not isinstance(value, str) or not value.strip():
        result.add_error(field_name, "Required non-empty string is missing or blank.")
        return False
    return True


# ---------------------------------------------------------------------------
# Task validator
# ---------------------------------------------------------------------------

def validate_task(task: dict) -> ValidationResult:
    """
    Validate a single maintenance task dict.

    Checks all required fields, types, ranges, and logical consistency
    (e.g. requested_end must be after requested_start).

    :param task: Dict as produced by generate_demo_data.py / API request body
    :return: ValidationResult with is_valid flag and list of errors/warnings
    """
    r = ValidationResult()

    # --- ID ---
    tid = task.get("id", "")
    if not isinstance(tid, str) or not tid.strip():
        r.add_error("id", "Task ID is missing or blank.")
    else:
        # Must match pattern DEPT-NNNN
        parts = tid.split("-")
        if len(parts) != 2 or parts[0] not in VALID_DEPT_CODES:
            r.add_error("id", f"'{tid}' doesn't match expected format DEPT-NNNN (e.g. TRK-1001).")

    # --- Department ---
    dept = task.get("department_code") or task.get("department", "")
    _validate_str_in_set(dept, "department_code", VALID_DEPT_CODES, r)

    # --- Source system cross-check ---
    src = task.get("source_system", "")
    if src:
        _validate_str_in_set(src, "source_system", VALID_SOURCE_SYSTEMS, r)

    # --- Corridor ---
    corridor_id = task.get("corridor_id")
    if corridor_id is None:
        r.add_error("corridor_id", "Required field missing.")
    elif not isinstance(corridor_id, int) or corridor_id < 1:
        r.add_error("corridor_id", f"Expected positive int, got {corridor_id!r}.")

    # --- Defect ---
    _validate_non_empty_str(task.get("defect_type", ""), "defect_type", r)

    # --- Severity ---
    _validate_int_range(task.get("severity", 0), "severity", MIN_SEVERITY, MAX_SEVERITY, r)

    # --- Days overdue ---
    overdue = task.get("days_overdue", -1)
    if not isinstance(overdue, int) or overdue < 0:
        r.add_error("days_overdue", f"Expected int >= 0, got {overdue!r}.")
    elif overdue > 365:
        r.add_warning("days_overdue: value > 365 days is unusual — verify data source.")

    # --- Duration ---
    dur = task.get("est_duration_min", 0)
    _validate_int_range(dur, "est_duration_min", MIN_DURATION_MIN, MAX_DURATION_MIN, r)

    # --- Criticality score ---
    score = task.get("criticality_score")
    if score is not None:
        _validate_float_range(score, "criticality_score", MIN_SCORE, MAX_SCORE, r)

    # --- Priority level ---
    priority = task.get("priority_level", "")
    if priority:
        _validate_str_in_set(priority, "priority_level", VALID_PRIORITY, r)

    # --- Status ---
    status = task.get("status", "")
    if status:
        _validate_str_in_set(status, "status", VALID_STATUSES, r)

    # --- Timing: parse and check start/end ordering ---
    req_start = _validate_iso_datetime(task.get("requested_start"), "requested_start", r)
    req_end   = _validate_iso_datetime(task.get("requested_end"),   "requested_end",   r)

    if req_start and req_end:
        if req_end <= req_start:
            r.add_error("requested_end", "requested_end must be strictly after requested_start.")
        else:
            actual_dur = (req_end - req_start).total_seconds() / 60
            expected   = task.get("est_duration_min", 0)
            if abs(actual_dur - expected) > 1:
                r.add_warning(
                    f"Time window ({actual_dur:.0f} min) doesn't match "
                    f"est_duration_min ({expected} min). Check data."
                )

    # --- is_compatible_with cross-check ---
    compat = task.get("is_compatible_with")
    if compat is not None:
        if compat not in VALID_DEPT_CODES:
            r.add_error("is_compatible_with", f"'{compat}' is not a valid department code.")
        dept_code = task.get("department_code") or task.get("department", "")
        if compat == dept_code:
            r.add_error("is_compatible_with", "A task cannot be compatible with its own department.")

    # --- Score / priority consistency ---
    if score is not None and priority:
        expected_priority = (
            "P0" if score >= 80 else ("P1" if score >= 50 else "P2")
        )
        if priority != expected_priority:
            r.add_warning(
                f"priority_level '{priority}' doesn't match score {score} "
                f"(expected '{expected_priority}'). Recheck or regenerate."
            )

    return r


# ---------------------------------------------------------------------------
# Window validator
# ---------------------------------------------------------------------------

def validate_window(window: dict) -> ValidationResult:
    """
    Validate a single COA block window dict.

    :param window: Dict as produced by generate_demo_data.py / API request body
    :return: ValidationResult
    """
    r = ValidationResult()

    # --- ID ---
    wid = window.get("id")
    if wid is None or not isinstance(wid, int) or wid < 1:
        r.add_error("id", f"Expected positive int window ID, got {wid!r}.")

    # --- Corridor ---
    corridor_id = window.get("corridor_id")
    if corridor_id is None or not isinstance(corridor_id, int) or corridor_id < 1:
        r.add_error("corridor_id", "Required positive int corridor_id missing.")

    # --- Label ---
    label = window.get("window_label", "")
    if label:
        if label not in VALID_WINDOW_LABELS:
            r.add_warning(f"window_label '{label}' is non-standard — accepted but check spelling.")

    # --- Timing ---
    start = _validate_iso_datetime(window.get("start_time"), "start_time", r)
    end   = _validate_iso_datetime(window.get("end_time"),   "end_time",   r)

    if start and end:
        if end <= start:
            r.add_error("end_time", "end_time must be strictly after start_time.")
        else:
            duration_min = int((end - start).total_seconds() / 60)
            declared     = window.get("duration_min")
            if declared is not None and abs(declared - duration_min) > 1:
                r.add_warning(
                    f"duration_min {declared} doesn't match computed {duration_min} min. "
                    "The generated column in the DB will override this."
                )
            if duration_min < 15:
                r.add_warning(f"Window is only {duration_min} min — too short for any maintenance task.")
            if duration_min > 600:
                r.add_warning(f"Window is {duration_min} min (>{600}) — unusually long, verify.")

    # --- is_available ---
    avail = window.get("is_available")
    if avail is not None and not isinstance(avail, bool):
        r.add_error("is_available", f"Expected bool, got {type(avail).__name__}.")

    return r


# ---------------------------------------------------------------------------
# Batch validators
# ---------------------------------------------------------------------------

@dataclass
class BatchValidationReport:
    total: int = 0
    valid: int = 0
    invalid: int = 0
    total_errors: int = 0
    total_warnings: int = 0
    failed_ids: list[str] = field(default_factory=list)

    def __str__(self) -> str:
        pct = (self.valid / self.total * 100) if self.total else 0
        return (
            f"BatchValidation: {self.valid}/{self.total} valid ({pct:.1f}%) | "
            f"{self.total_errors} errors | {self.total_warnings} warnings"
            + (f" | Failed: {self.failed_ids[:5]}{'...' if len(self.failed_ids) > 5 else ''}"
               if self.failed_ids else "")
        )


def validate_tasks_batch(tasks: list[dict], raise_on_error: bool = False) -> BatchValidationReport:
    """
    Validate a list of task dicts.

    :param tasks:          List of task dicts
    :param raise_on_error: If True, raises ValueError on the first invalid task
    :return:               BatchValidationReport summary
    """
    report = BatchValidationReport(total=len(tasks))
    for task in tasks:
        result = validate_task(task)
        report.total_errors   += len(result.errors)
        report.total_warnings += len(result.warnings)
        if result.is_valid:
            report.valid += 1
        else:
            report.invalid += 1
            report.failed_ids.append(task.get("id", "?"))
            if raise_on_error:
                raise ValueError(
                    f"Task '{task.get('id')}' failed validation:\n{result}"
                )
    return report


def validate_windows_batch(windows: list[dict], raise_on_error: bool = False) -> BatchValidationReport:
    """
    Validate a list of window dicts.

    :param windows:        List of window dicts
    :param raise_on_error: If True, raises ValueError on the first invalid window
    :return:               BatchValidationReport summary
    """
    report = BatchValidationReport(total=len(windows))
    for window in windows:
        result = validate_window(window)
        report.total_errors   += len(result.errors)
        report.total_warnings += len(result.warnings)
        if result.is_valid:
            report.valid += 1
        else:
            report.invalid += 1
            report.failed_ids.append(str(window.get("id", "?")))
            if raise_on_error:
                raise ValueError(
                    f"Window '{window.get('id')}' failed validation:\n{result}"
                )
    return report


# ---------------------------------------------------------------------------
# Full dataset audit (called by seed.py before any DB write)
# ---------------------------------------------------------------------------

def audit_dataset(tasks: list[dict], windows: list[dict]) -> tuple[BatchValidationReport, BatchValidationReport]:
    """
    Run full validation over the generated dataset.
    Prints a summary and returns both reports.

    :return: (task_report, window_report)
    """
    print("Running dataset audit...")
    task_report   = validate_tasks_batch(tasks)
    window_report = validate_windows_batch(windows)

    print(f"  Tasks:   {task_report}")
    print(f"  Windows: {window_report}")

    if task_report.invalid > 0 or window_report.invalid > 0:
        print("  ⚠  Validation issues found. Review failed IDs before seeding.")
    else:
        print("  ✓  All records passed validation.")

    return task_report, window_report


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import json, os

    data_dir = os.path.join(os.path.dirname(__file__), "..", "..", "data")
    tasks_path   = os.path.join(data_dir, "tasks.json")
    windows_path = os.path.join(data_dir, "windows.json")

    if not os.path.exists(tasks_path):
        print("data/tasks.json not found — run scripts/generate_demo_data.py first.")
    else:
        tasks   = json.load(open(tasks_path))
        windows = json.load(open(windows_path))
        audit_dataset(tasks, windows)

        # Test an intentionally broken task
        print("\nTesting broken task (expect errors):")
        broken = {
            "id": "BAD-9999",
            "department_code": "XYZ",
            "corridor_id": -1,
            "defect_type": "",
            "severity": 7,
            "days_overdue": -3,
            "est_duration_min": 5,
            "requested_start": "not-a-date",
            "requested_end": "2026-09-02T01:00:00Z",
            "criticality_score": 150.0,
            "priority_level": "P9",
            "status": "Unknown",
            "is_compatible_with": "XYZ",
        }
        result = validate_task(broken)
        print(result)
