"""
backend/core/explainer.py
=========================
BlockSync Gemini AI Explainability Module
Branch: hriday-dataset | Author: Hriday

Converts the CP-SAT optimizer's JSON output into human-readable, two-sentence
explanations that a Section Controller can understand and judges can interrogate.

USAGE
-----
Set the environment variable before running:
    export GEMINI_API_KEY="your-key-here"        # Linux / macOS
    $env:GEMINI_API_KEY = "your-key-here"        # PowerShell (Windows)

Then call generate_explanation() with a task assignment dict, or use the
batch helper generate_batch_explanations() for multiple tasks at once.

FALLBACK
--------
If GEMINI_API_KEY is unset or the API call fails, a deterministic rule-based
explanation is generated locally — so the demo never crashes during a live judge Q&A.

MODEL
-----
Uses gemini-2.5-flash via the google-genai (v1.x) SDK.
Install: pip install google-genai==1.16.0
"""

from __future__ import annotations

import os
import json
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# System prompt (locked — matches the Master Plan specification)
# ---------------------------------------------------------------------------
SYSTEM_PROMPT = """
You are an AI assistant for an Indian Railways Section Controller.
A mathematical optimization engine (CP-SAT / OR-Tools) has just generated a
maintenance block schedule for the Delhi Division, Northern Railway.

Your job is to explain WHY a specific maintenance task was assigned its particular
time slot. Write exactly TWO sentences. Be professional, concise, and factual.

Rules:
1. Always reference the task's Criticality Score, Severity (out of 5), and
   overdue days in your justification.
2. Use Indian Railways terminology (e.g., "block section", "OHE isolation",
   "speed restriction", "P-Way gang", "TRD crew").
3. If the task is marked is_integrated_block=True, explicitly state that it was
   merged with another department's task into an Integrated Joint Block, and
   quantify the corridor downtime saved.
4. If the task was deferred (status=Deferred), explain the mathematical reason
   (infeasible constraint) and when it is next recommended.
5. Never invent facts. Only use the data provided in the JSON.
""".strip()


# ---------------------------------------------------------------------------
# Rule-based fallback (no API key required)
# ---------------------------------------------------------------------------
def _rule_based_explanation(task_data: dict) -> str:
    """
    Deterministic fallback explanation generated purely from the task dict.
    Mirrors the Gemini output style but requires no network call.
    """
    task_id    = task_data.get("task_id", "Unknown")
    defect     = task_data.get("defect", "maintenance work")
    severity   = task_data.get("severity", "N/A")
    overdue    = task_data.get("days_overdue", 0)
    score      = task_data.get("score", "N/A")
    integrated = task_data.get("is_integrated_block", False)
    merged_with = task_data.get("merged_with", None)
    status     = task_data.get("status", "Scheduled")
    saved_min  = task_data.get("downtime_saved_minutes", 0)

    if status == "Deferred":
        reason  = task_data.get("mathematical_reason", "no suitable window was available")
        next_wn = task_data.get("next_recommended_window", "the next available window")
        return (
            f"Task {task_id} ({defect}) could not be scheduled in the current planning "
            f"horizon because {reason}. "
            f"It has been deferred to {next_wn} and will be re-evaluated in the next "
            f"CP-SAT run with an elevated priority weight."
        )

    overdue_text = (
        f"It is {overdue} days overdue, placing it above routine maintenance in the "
        "objective function."
    ) if overdue > 0 else (
        "Although not yet overdue, its high severity triggered immediate scheduling."
    )

    integration_text = ""
    if integrated and merged_with:
        integration_text = (
            f" This task was merged into an Integrated Joint Block with {merged_with}, "
            f"saving {saved_min} minutes of corridor downtime by sharing a single "
            "traction power isolation."
        )

    return (
        f"Task {task_id} ({defect}, Severity {severity}/5, Score {score}/100) was "
        f"prioritised for this slot by the CP-SAT optimizer due to its elevated "
        f"criticality score, which reflects both its safety severity rating and "
        f"backlog status. "
        f"{overdue_text}{integration_text}"
    )


# ---------------------------------------------------------------------------
# Gemini-backed explanation
# ---------------------------------------------------------------------------
def generate_explanation(task_data: dict) -> str:
    """
    Generate a two-sentence AI explanation for a scheduled / deferred task.

    :param task_data: Dict with keys such as:
        task_id, defect, severity, days_overdue, score,
        is_integrated_block, merged_with, corridor, assigned_start,
        assigned_end, status, downtime_saved_minutes, mathematical_reason,
        next_recommended_window
    :return: Two-sentence explanation string.
    """
    api_key = os.environ.get("GEMINI_API_KEY", "").strip()

    if not api_key:
        logger.warning(
            "GEMINI_API_KEY not set — using rule-based fallback explanation for %s.",
            task_data.get("task_id", "unknown"),
        )
        return _rule_based_explanation(task_data)

    try:
        from google import genai as google_genai  # type: ignore

        client = google_genai.Client(api_key=api_key)
        prompt = (
            f"{SYSTEM_PROMPT}\n\n"
            f"Explain this maintenance block assignment:\n"
            f"{json.dumps(task_data, indent=2)}"
        )
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        )
        text = response.text.strip() if response.text else ""
        if text:
            return text
        # Empty response — fall through to fallback
        logger.warning("Gemini returned empty text for task %s.", task_data.get("task_id"))
        return _rule_based_explanation(task_data)

    except ImportError:
        logger.error(
            "google-genai package not installed. "
            "Run: pip install google-genai==1.16.0"
        )
        return _rule_based_explanation(task_data)

    except Exception as exc:  # noqa: BLE001
        logger.error(
            "Gemini API call failed for task %s: %s. Falling back to rule-based.",
            task_data.get("task_id", "unknown"),
            exc,
        )
        return _rule_based_explanation(task_data)


def generate_batch_explanations(assignments: list[dict]) -> list[dict]:
    """
    Add ai_explanation key to each assignment dict in a list.

    Processes each assignment sequentially (Gemini free-tier rate limits
    make parallelism undesirable; paid-tier users can swap in asyncio).

    :param assignments: List of assignment dicts (mutated in-place)
    :return: Same list, each dict now has 'ai_explanation' populated
    """
    for assignment in assignments:
        task_data = _assignment_to_prompt_dict(assignment)
        assignment["ai_explanation"] = generate_explanation(task_data)
    return assignments


def _assignment_to_prompt_dict(assignment: dict) -> dict:
    """
    Extract the minimal keys needed for the Gemini prompt from a full
    block_assignments row / OptimizedAssignment dict.
    """
    task = assignment.get("task", assignment)  # handle both flat and nested dicts
    return {
        "task_id":               task.get("id") or assignment.get("task_id"),
        "defect":                task.get("defect_type") or task.get("title", "maintenance work"),
        "severity":              task.get("severity"),
        "days_overdue":          task.get("days_overdue") or task.get("defect", {}).get("overdueDays", 0),
        "score":                 task.get("criticality_score") or task.get("criticalityScore"),
        "corridor":              task.get("corridor_name") or task.get("corridorName"),
        "assigned_start":        assignment.get("assigned_start") or assignment.get("assignedStartHour"),
        "assigned_end":          assignment.get("assigned_end") or assignment.get("assignedEndHour"),
        "is_integrated_block":   assignment.get("is_integrated") or assignment.get("isIntegrated", False),
        "merged_with":           assignment.get("merged_with_task_id") or assignment.get("jointBlockId"),
        "status":                task.get("status", "Scheduled"),
        "downtime_saved_minutes": assignment.get("downtime_saved_minutes", 0),
        "mathematical_reason":   assignment.get("mathematical_reason", ""),
        "next_recommended_window": assignment.get("next_recommended_window", ""),
    }


# ---------------------------------------------------------------------------
# Self-test (run directly: python -m backend.core.explainer)
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    # Test 1: Integrated block
    mock_integrated = {
        "task_id": "TRK-1001",
        "defect": "Weld / Rail Fracture",
        "severity": 5,
        "days_overdue": 15,
        "score": 82.5,
        "is_integrated_block": True,
        "merged_with": "OHE-3001 (Insulator Cleaning)",
        "corridor": "NDLS-CNB (UP Main)",
        "assigned_start": "2026-09-02T02:00:00Z",
        "assigned_end": "2026-09-02T05:00:00Z",
        "status": "Merged",
        "downtime_saved_minutes": 120,
    }

    # Test 2: Deferred task
    mock_deferred = {
        "task_id": "TRK-1099",
        "defect": "Deep Screening (BCM)",
        "severity": 3,
        "days_overdue": 2,
        "score": 51.3,
        "is_integrated_block": False,
        "status": "Deferred",
        "mathematical_reason": "task_duration (360 min) > max available window (240 min) on NDLS-CNB-UP",
        "next_recommended_window": "Sep 06, 2026 01:00–07:00 AM (Sunday Mega Block)",
    }

    # Test 3: Safety override winner
    mock_safety_winner = {
        "task_id": "TRK-1002",
        "defect": "Rail Fracture at Bridge Approach",
        "severity": 5,
        "days_overdue": 15,
        "score": 80.75,
        "is_integrated_block": False,
        "corridor": "DLI-RE (Single Line)",
        "assigned_start": "2026-09-03T13:00:00Z",
        "assigned_end": "2026-09-03T16:00:00Z",
        "status": "Scheduled",
    }

    print("=" * 70)
    print("BlockSync Explainability Engine — Self-test (fallback mode)")
    print("=" * 70)
    for label, payload in [
        ("Integrated Joint Block", mock_integrated),
        ("Deferred Task",          mock_deferred),
        ("Safety Override Winner", mock_safety_winner),
    ]:
        print(f"\n[{label}]")
        print(generate_explanation(payload))
        print()
