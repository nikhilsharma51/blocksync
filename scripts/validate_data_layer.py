"""
repo/scripts/validate_data_layer.py
==================================
End-to-end validation for the BlockSync data layer.

Checks:
  - dataset files exist and parse as JSON
  - task/window/conflict counts are internally consistent
  - required IDs, ranges, and corridor references are valid
  - summary metadata matches the generated dataset
  - the three demo scenarios are present in the task data

Run from repo root:
    python scripts/validate_data_layer.py
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def validate_tasks(tasks: list[dict]) -> None:
    assert_true(len(tasks) > 0, "No tasks were loaded.")

    ids = [t["id"] for t in tasks]
    assert_true(len(ids) == len(set(ids)), "Duplicate task IDs detected.")

    for idx, task in enumerate(tasks):
        task_id = task.get("id", idx)

        department_code = task.get("department_code") or task.get("department")
        corridor_code = task.get("corridor_code") or task.get("corridor")
        assert_true(department_code, f"Task {task_id} is missing department code.")
        assert_true(corridor_code, f"Task {task_id} is missing corridor code.")
        assert_true(task.get("defect_type"), f"Task {task_id} is missing defect_type.")
        assert_true(task["severity"] in range(1, 6), f"Task {task_id} severity out of range: {task['severity']}")
        assert_true(task["days_overdue"] >= 0, f"Task {task_id} overdue days cannot be negative")
        assert_true(15 <= task["est_duration_min"] <= 600, f"Task {task_id} duration out of expected range")
        assert_true(0.0 <= float(task["criticality_score"]) <= 100.0, f"Task {task_id} score out of range")
        if "priority_level" in task:
            assert_true(task["priority_level"] in {"P0", "P1", "P2"}, f"Task {task_id} invalid priority: {task['priority_level']}")

    integrated_pair = [t for t in tasks if t.get("is_compatible_with")]
    assert_true(any(integrated_pair), "No compatible task pair found; integrated-block scenario is missing.")

    safety_before = [
        t for t in tasks
        if "fracture" in (t.get("defect_type") or "").lower() or "rail" in (t.get("defect_type") or "").lower()
    ]
    assert_true(safety_before, "No rail-fracture style defect found for safety-override scenario.")

    impossible = [t for t in tasks if t["est_duration_min"] >= 360]
    assert_true(impossible, "No long-duration task present for impossible-window scenario.")


def validate_windows(windows: list[dict]) -> None:
    assert_true(len(windows) > 0, "No windows were loaded.")

    ids = [w["id"] for w in windows]
    assert_true(len(ids) == len(set(ids)), "Duplicate window IDs detected.")

    for window in windows:
        assert_true(window["corridor_id"] > 0, f"Window {window['id']} has invalid corridor_id")
        assert_true(window.get("start_time"), f"Window {window['id']} missing start_time")
        assert_true(window.get("end_time"), f"Window {window['id']} missing end_time")

        start = datetime.fromisoformat(window["start_time"])
        end = datetime.fromisoformat(window["end_time"])
        assert_true(end > start, f"Window {window['id']} has invalid time range")
        duration = (end - start).total_seconds() / 60
        assert_true(duration > 0, f"Window {window['id']} has zero or negative duration")


def validate_conflicts(conflicts: list[dict], tasks: list[dict], windows: list[dict]) -> None:
    task_ids = {t["id"] for t in tasks}
    corridor_ids = {w["corridor_id"] for w in windows}

    for conflict in conflicts:
        assert_true(conflict["task_a_id"] in task_ids, f"Conflict references unknown task_a_id {conflict['task_a_id']}")
        assert_true(conflict["task_b_id"] in task_ids, f"Conflict references unknown task_b_id {conflict['task_b_id']}")
        assert_true(conflict["corridor_id"] in corridor_ids, f"Conflict references unknown corridor_id {conflict['corridor_id']}")
        assert_true(conflict["overlap_duration_min"] > 0, f"Conflict {conflict['id']} has invalid overlap duration")


def validate_summary(summary: dict, task_count: int, window_count: int, conflict_count: int) -> None:
    assert_true(summary.get("total_tasks") == task_count, f"Summary tasks mismatch: {summary.get('total_tasks')} != {task_count}")
    assert_true(summary.get("total_windows") == window_count, f"Summary windows mismatch: {summary.get('total_windows')} != {window_count}")
    assert_true(summary.get("total_conflicts") == conflict_count, f"Summary conflicts mismatch: {summary.get('total_conflicts')} != {conflict_count}")
    priority_breakdown = summary.get("tasks_by_priority") or summary.get("priority_breakdown")
    assert_true(priority_breakdown, "Summary is missing priority breakdown data.")


def main() -> None:
    task_path = DATA_DIR / "tasks.json"
    windows_path = DATA_DIR / "windows.json"
    conflicts_path = DATA_DIR / "conflict_pairs.json"
    summary_path = DATA_DIR / "seed_summary.json"

    for path in (task_path, windows_path, conflicts_path, summary_path):
        assert_true(path.exists(), f"Missing required dataset file: {path}")

    tasks = load_json(task_path)
    windows = load_json(windows_path)
    conflicts = load_json(conflicts_path)
    summary = load_json(summary_path)

    validate_tasks(tasks)
    validate_windows(windows)
    validate_conflicts(conflicts, tasks, windows)
    validate_summary(summary, len(tasks), len(windows), len(conflicts))

    print("Data layer validation passed.")
    print(f"Tasks: {len(tasks)}")
    print(f"Windows: {len(windows)}")
    print(f"Conflicts: {len(conflicts)}")
    print(f"Priority mix: {summary.get('tasks_by_priority', summary.get('priority_breakdown', summary.get('priority_breakdown_summary', {})))}")


if __name__ == "__main__":
    try:
        main()
    except AssertionError as exc:
        raise SystemExit(f"Validation failed: {exc}")
