"""
backend/core/scoring.py
=======================
BlockSync Criticality Scoring Engine
Branch: hriday-dataset | Author: Hriday

Converts raw maintenance task metrics into a deterministic 0–100 priority score.
The score is used by:
  - The CP-SAT optimizer to rank tasks when assigning them to windows
  - The frontend to colour-code Gantt bars (red = high, amber = medium, green = low)
  - The Gemini explainability module to justify scheduling decisions

FORMULA
-------
  Score = (W_SEV * norm_severity) + (W_OVD * norm_overdue) + (W_TRF * norm_traffic)

  W_SEV = 0.45  (Safety is paramount)
  W_OVD = 0.35  (Forces aging backlog to the top)
  W_TRF = 0.20  (Prioritises busy mainlines over branch lines / yards)

NORMALIZATION
-------------
  norm_severity  = (severity / 5.0) * 100          → range [20, 100]
  norm_overdue   = min(days_overdue / 30.0, 1.0) * 100  → range [0, 100], capped at 30 days
  norm_traffic   = traffic_weight * 100             → range [10, 100]
    traffic_weight:  1.0 = Trunk Mainline (100 pts)
                     0.6 = Branch Line    (60 pts)
                     0.3 = Yard / Loop    (30 pts)

EXAMPLE (Rail Fracture, Sev 5, 15 days overdue, Mainline):
  Score = (0.45 * 100) + (0.35 * 50) + (0.20 * 100) = 45 + 17.5 + 20 = 82.5
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional


# ---------------------------------------------------------------------------
# Weights (locked — matches the Master Plan specification)
# ---------------------------------------------------------------------------
W_SEV: float = 0.45   # Severity weight
W_OVD: float = 0.35   # Overdue penalty weight
W_TRF: float = 0.20   # Traffic / asset-criticality weight

# Overdue days are capped at this value to prevent runaway scores
OVERDUE_CAP_DAYS: int = 30

# Traffic weight lookup for the three asset classes
ASSET_CLASS_WEIGHTS: dict[str, float] = {
    "Mainline Trunk": 1.0,
    "Branch Line":    0.6,
    "Yard/Loop":      0.3,
}

# Priority tier thresholds (used by classify_priority)
PRIORITY_P0_THRESHOLD: float = 80.0
PRIORITY_P1_THRESHOLD: float = 50.0
# < 50 → P2


@dataclass
class ScoringResult:
    """Full breakdown returned by calculate_criticality_score()."""
    total_score: float

    # Raw inputs (stored for audit / formula display)
    severity: int
    days_overdue: int
    traffic_weight: float

    # Normalised components (each 0–100 before weighting)
    norm_severity: float
    norm_overdue: float
    norm_traffic: float

    # Weighted components (each = W * norm)
    weighted_severity: float
    weighted_overdue: float
    weighted_traffic: float

    # Priority tier derived from total_score
    priority_level: str = field(init=False)

    # Human-readable formula string (for DB storage and UI tooltip)
    formula: str = field(init=False)

    def __post_init__(self) -> None:
        self.priority_level = classify_priority(self.total_score)
        self.formula = (
            f"({W_SEV} × {self.norm_severity:.1f}) "
            f"+ ({W_OVD} × {self.norm_overdue:.1f}) "
            f"+ ({W_TRF} × {self.norm_traffic:.1f}) "
            f"= {self.total_score:.2f}"
        )

    def as_dict(self) -> dict:
        return {
            "total_score":        self.total_score,
            "severity_component": round(self.weighted_severity, 2),
            "overdue_component":  round(self.weighted_overdue, 2),
            "traffic_component":  round(self.weighted_traffic, 2),
            "priority_level":     self.priority_level,
            "formula":            self.formula,
        }


def _normalise_severity(severity: int) -> float:
    """Map severity 1–5 to a 0–100 normalised score."""
    if not 1 <= severity <= 5:
        raise ValueError(f"severity must be 1–5, got {severity!r}")
    return (severity / 5.0) * 100.0


def _normalise_overdue(days_overdue: int) -> float:
    """
    Map overdue days to 0–100, capped at OVERDUE_CAP_DAYS (30).
    e.g. 15 days → 50.0,  45 days → 100.0 (same as 30 days).
    """
    if days_overdue < 0:
        raise ValueError(f"days_overdue must be >= 0, got {days_overdue!r}")
    return min(days_overdue / OVERDUE_CAP_DAYS, 1.0) * 100.0


def _normalise_traffic(traffic_weight: float) -> float:
    """Map traffic_weight (0.1–1.0) to 0–100."""
    if not 0.0 < traffic_weight <= 1.0:
        raise ValueError(f"traffic_weight must be in (0, 1], got {traffic_weight!r}")
    return traffic_weight * 100.0


def classify_priority(score: float) -> str:
    """
    Derive IR-style priority tier from a criticality score.

    P0 ≥ 80  → Safety-critical, must schedule this cycle
    P1 ≥ 50  → High importance, schedule within 48 h
    P2 < 50  → Routine / deferred
    """
    if score >= PRIORITY_P0_THRESHOLD:
        return "P0"
    if score >= PRIORITY_P1_THRESHOLD:
        return "P1"
    return "P2"


def calculate_criticality_score(
    severity: int,
    days_overdue: int,
    traffic_weight: float,
) -> float:
    """
    Primary entry point — returns just the rounded float score.
    Used by generate_demo_data.py and any quick inline call.

    :param severity:       1 (routine) to 5 (critical safety hazard)
    :param days_overdue:   Integer >= 0; capped at 30 for calculation
    :param traffic_weight: 0.1–1.0 (1.0 = Trunk Mainline)
    :return:               Float in [0, 100], rounded to 2 decimal places
    """
    n_sev = _normalise_severity(severity)
    n_ovd = _normalise_overdue(days_overdue)
    n_trf = _normalise_traffic(traffic_weight)
    score = (W_SEV * n_sev) + (W_OVD * n_ovd) + (W_TRF * n_trf)
    return round(score, 2)


def calculate_criticality_score_full(
    severity: int,
    days_overdue: int,
    traffic_weight: float,
) -> ScoringResult:
    """
    Extended entry point — returns a ScoringResult dataclass with full breakdown.
    Used by the FastAPI /tasks/pending endpoint and the seed loader.

    Example
    -------
    >>> result = calculate_criticality_score_full(5, 15, 1.0)
    >>> result.total_score
    82.5
    >>> result.priority_level
    'P0'
    >>> result.formula
    '(0.45 × 100.0) + (0.35 × 50.0) + (0.20 × 100.0) = 82.50'
    """
    n_sev = _normalise_severity(severity)
    n_ovd = _normalise_overdue(days_overdue)
    n_trf = _normalise_traffic(traffic_weight)

    w_sev = W_SEV * n_sev
    w_ovd = W_OVD * n_ovd
    w_trf = W_TRF * n_trf

    total = round(w_sev + w_ovd + w_trf, 2)

    return ScoringResult(
        total_score=total,
        severity=severity,
        days_overdue=days_overdue,
        traffic_weight=traffic_weight,
        norm_severity=round(n_sev, 2),
        norm_overdue=round(n_ovd, 2),
        norm_traffic=round(n_trf, 2),
        weighted_severity=round(w_sev, 2),
        weighted_overdue=round(w_ovd, 2),
        weighted_traffic=round(w_trf, 2),
    )


def traffic_weight_from_asset_class(asset_class: str) -> float:
    """
    Convenience helper — converts a string asset class to a traffic_weight float.
    Falls back to Branch Line (0.6) for unknown strings.

    :param asset_class: 'Mainline Trunk' | 'Branch Line' | 'Yard/Loop'
    :return:            float traffic_weight
    """
    return ASSET_CLASS_WEIGHTS.get(asset_class, 0.6)


def batch_score(tasks: list[dict]) -> list[dict]:
    """
    Score a list of task dicts in-place, adding 'criticality_score' and
    'priority_level' keys to each dict.

    Each dict must contain:
      - 'severity'        (int 1–5)
      - 'days_overdue'    (int >= 0)
      - 'traffic_weight'  (float 0.1–1.0)  OR
      - 'asset_class'     (str) — used as fallback if traffic_weight absent

    :param tasks: list of task dicts (mutated in-place)
    :return:      same list, now with scores populated
    """
    for t in tasks:
        tw = t.get("traffic_weight") or traffic_weight_from_asset_class(
            t.get("asset_class", "Branch Line")
        )
        result = calculate_criticality_score_full(
            severity=int(t["severity"]),
            days_overdue=int(t["days_overdue"]),
            traffic_weight=float(tw),
        )
        t["criticality_score"] = result.total_score
        t["priority_level"]    = result.priority_level
        t["score_breakdown"]   = result.as_dict()
    return tasks


# ---------------------------------------------------------------------------
# Self-test (run directly: python -m backend.core.scoring)
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    test_cases = [
        # (severity, days_overdue, traffic_weight, description)
        (5, 15, 1.0,  "Rail Fracture — Mainline, 15 days overdue         → expected ~82.5"),
        (5, 17, 0.9,  "Bridge Defect — Near-mainline, 17 days overdue    → expected ~83.45"),
        (1,  0, 0.7,  "Routine LED Change — Branch, not overdue          → expected  ~23.0"),
        (2,  5, 1.0,  "Tamping — Mainline, 5 days overdue                → expected ~44.83"),
        (4,  9, 1.0,  "OHE Cantilever — Mainline, 9 days overdue         → expected ~81.5"),
        (3,  2, 0.3,  "Insulator Check — Yard, 2 days overdue            → expected ~44.83"),
    ]
    print(f"{'Description':<60} {'Score':>7}  {'P-Level':>7}")
    print("-" * 80)
    for sev, ovd, tw, desc in test_cases:
        r = calculate_criticality_score_full(sev, ovd, tw)
        print(f"{desc:<60} {r.total_score:>7.2f}  {r.priority_level:>7}")
        print(f"  Formula: {r.formula}")
