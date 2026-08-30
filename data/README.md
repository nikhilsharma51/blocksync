# BlockSync — Dataset Reference

**Branch:** `hriday-dataset` | **Author:** Hriday (Data & Pitch Lead)

This directory contains the complete synthetic dataset for the BlockSync SIH 2026 demo. Every file here is generated deterministically by `scripts/generate_demo_data.py` using `RANDOM_SEED = 42`, so the output is reproducible on any machine.

---

## Files

| File | Records | Description |
|------|---------|-------------|
| `tasks.json` | 150 | Maintenance tasks from TMS / SMMS / TDMS |
| `windows.json` | 148 | COA block windows (free maintenance slots) |
| `conflict_pairs.json` | 17 | Pre-detected scheduling conflicts |
| `seed_summary.json` | — | Statistics + jury-hook scenario map |

---

## Regenerating the Dataset

```bash
# From the repo root:
python scripts/generate_demo_data.py --verbose
```

Output is written directly to `data/`. The random seed is fixed so results are identical every run.

---

## tasks.json — Field Reference

Each task object has the following fields:

| Field | Type | Description |
|-------|------|-------------|
| `id` | `string` | Unique task ID — format `DEPT-NNNN` e.g. `TRK-1001` |
| `department_id` | `int` | FK → departments table (1=TRK, 2=SNT, 3=OHE) |
| `department_code` | `string` | `TRK` \| `SNT` \| `OHE` |
| `department_name` | `string` | Full department name |
| `corridor_id` | `int` | FK → corridors table |
| `corridor_code` | `string` | e.g. `NDLS-GZB-UP` |
| `corridor_name` | `string` | Human-readable section name |
| `defect_code` | `string` | Source system defect reference code |
| `defect_type` | `string` | Nature of the defect (from real IR vocabulary) |
| `defect_category` | `string` | Category (e.g. `IMR Critical Defect`) |
| `source_system` | `string` | `TMS` (Track) \| `SMMS` (Signal) \| `TDMS` (OHE) |
| `severity` | `int` | 1–5 (5 = Safety-critical / Immediate Removal) |
| `days_overdue` | `int` | Days past the scheduled maintenance deadline |
| `reported_date` | `string` | ISO date the defect was logged |
| `est_duration_min` | `int` | Estimated block duration in minutes |
| `requested_start` | `string` | ISO-8601 UTC datetime the department requested |
| `requested_end` | `string` | `requested_start + est_duration_min` |
| `criticality_score` | `float` | **0–100** — output of the scoring engine |
| `priority_level` | `string` | `P0` (≥80) \| `P1` (≥50) \| `P2` (<50) |
| `score_severity_component` | `float` | W_SEV × norm_severity contribution |
| `score_overdue_component` | `float` | W_OVD × norm_overdue contribution |
| `score_traffic_component` | `float` | W_TRF × norm_traffic contribution |
| `score_formula` | `string` | Human-readable formula string for UI tooltip |
| `is_compatible_with` | `string\|null` | Dept code this task can merge with (Joint Block) |
| `status` | `string` | `Pending` \| `Clashed` \| `Deferred` |
| `power_disconnection_required` | `bool` | Whether 25kV OHE must be isolated |
| `speed_restriction_afterwards` | `string\|null` | Post-work caution order |
| `crew_size` | `int` | Number of personnel required |
| `supervisor` | `string` | Responsible SSE / ADEN |
| `required_machine` | `string\|null` | Track machine / tower wagon needed |

---

## windows.json — Field Reference

| Field | Type | Description |
|-------|------|-------------|
| `id` | `int` | Unique window ID |
| `corridor_id` | `int` | FK → corridors |
| `corridor_code` | `string` | e.g. `NDLS-GZB-UP` |
| `corridor_name` | `string` | Full name |
| `window_label` | `string` | `Night Gold Window` \| `Early Morning Window` \| `Midday Freight Window` |
| `start_time` | `string` | ISO-8601 UTC |
| `end_time` | `string` | ISO-8601 UTC |
| `duration_min` | `int` | Window length in minutes |
| `source` | `string` | `COA_Timetable_Gap` \| `Freight_Lull` |
| `is_available` | `bool` | Whether the window is still free |

---

## conflict_pairs.json — Field Reference

| Field | Type | Description |
|-------|------|-------------|
| `id` | `string` | `conf-NNNN` |
| `task_a_id` | `string` | First conflicting task |
| `task_b_id` | `string` | Second conflicting task |
| `corridor_id` | `int` | Corridor where the clash occurs |
| `corridor_name` | `string` | |
| `overlap_start` | `string` | ISO-8601 start of overlap window |
| `overlap_end` | `string` | ISO-8601 end of overlap window |
| `overlap_duration_min` | `int` | |
| `conflict_severity` | `string` | `Critical` \| `High` \| `Moderate` |
| `conflict_type` | `string` | `Physical Line Occupancy` \| `Power/OHE Dependency` \| `Signal Interlocking` |
| `resolution_strategy` | `string` | Human-readable optimizer hint |
| `task_a_score` | `float` | Criticality score of task A |
| `task_b_score` | `float` | Criticality score of task B |

---

## The Scoring Formula

```
Score = (W_SEV × norm_severity) + (W_OVD × norm_overdue) + (W_TRF × norm_traffic)

W_SEV = 0.45   (Safety — severity is paramount)
W_OVD = 0.35   (Overdue penalty — forces aging backlog to top)
W_TRF = 0.20   (Asset criticality — mainlines over branch lines)

norm_severity = (severity / 5) × 100        → [20, 100]
norm_overdue  = min(days_overdue / 30, 1.0) × 100  → [0, 100], capped at 30 days
norm_traffic  = traffic_weight × 100         → [10, 100]

traffic_weight:  Mainline Trunk = 1.0
                 Branch Line (standard) = 0.6
                 DLI-RE-SL (intermediate branch) = 0.7
                 Yard / Loop    = 0.3
```

**Example — Rail Fracture (Sev 5, 15 days overdue, Mainline):**
```
Score = (0.45 × 100) + (0.35 × 50) + (0.20 × 100)
      = 45 + 17.5 + 20
      = 82.5 / 100  →  P0
```

---

## The 3 Jury-Hook Scenarios

These are hardcoded into `scripts/generate_demo_data.py` and will always be present regardless of the random seed.

### Scenario 1 — The Integrated Block (`TRK-1000` + `OHE-3000`)

| | TRK-1000 | OHE-3000 |
|--|----------|----------|
| Defect | Routine Tamping | Insulator Flashover |
| Severity | 2 | 2 |
| Corridor | NDLS-GZB-UP | NDLS-GZB-UP |
| Requested Start | 2026-09-02 02:00 | 2026-09-02 02:00 |
| `is_compatible_with` | `OHE` | `TRK` |
| Status | `Clashed` | `Clashed` |

**What the optimizer does:** Merges both into one Integrated Joint Block — one shared 25kV power isolation, one corridor downtime slot. Saves ≥120 minutes vs. granting separate blocks.

**What the judge sees:** The "Before" Gantt shows two red bars on the same corridor at the same time. The "After" Gantt shows a single merged green bar labelled `JB-001 [TRK + OHE]`.

---

### Scenario 2 — The Safety Override (`TRK-1001` beats `SNT-2000`)

| | SNT-2000 | TRK-1001 |
|--|----------|----------|
| Defect | Signal LED Change | Weld / Rail Fracture |
| Severity | 1 | 5 |
| Days Overdue | 0 | 15 |
| Score | **23.0** | **76.5** |
| Corridor | DLI-RE-SL | DLI-RE-SL |
| Requested Start | Same slot (Tue 13:00) | Same slot (Tue 13:00) |

**What the optimizer does:** Both tasks request the exact same window. The criticality engine scores TRK-1001 at 76.5 vs SNT-2000 at 23.0 — a **53.5-point gap**. Track gets the slot; Signal is rescheduled to the next available window.

**What the judge sees:** Proves the system is safety-first, not first-come-first-served.

---

### Scenario 3 — The Impossible Task (`TRK-1002`)

| Field | Value |
|-------|-------|
| Task ID | `TRK-1002` |
| Defect | Ballast Deep Screening (BCM) |
| Requested Duration | **360 min (6 hours)** |
| Longest Available Window on NDLS-GZB-UP | **300 min (5 hours)** |
| Status | `Deferred` |

**What the optimizer does:** Outputs `TRK-1002` in the `unscheduled` array with the reason:
> *"No continuous window available for requested duration (360 mins). Longest available window on NDLS-GZB-UP is 300 mins."*

**What the judge sees:** The app doesn't crash. It communicates the infeasibility clearly, defers the task to the Sunday Mega Block, and continues scheduling the remaining 149 tasks.

---

## Corridor Reference

| Code | Name | Asset Class | Traffic Weight | Speed |
|------|------|-------------|----------------|-------|
| `NDLS-GZB-UP` | New Delhi - Ghaziabad (UP Main) | Mainline Trunk | 1.0 | 130 km/h |
| `NDLS-GZB-DN` | New Delhi - Ghaziabad (DOWN Main) | Mainline Trunk | 1.0 | 130 km/h |
| `GZB-ALJN-UP` | Ghaziabad - Aligarh (UP Main) | Mainline Trunk | 1.0 | 160 km/h |
| `GZB-ALJN-DN` | Ghaziabad - Aligarh (DOWN Main) | Mainline Trunk | 1.0 | 160 km/h |
| `ALJN-TDL-BOTH` | Aligarh - Tundla Junction | Mainline Trunk | 0.9 | 140 km/h |
| `TDL-CNB-BOTH` | Tundla - Kanpur Central | Mainline Trunk | 0.9 | 140 km/h |
| `DLI-RE-SL` | Delhi - Rewari (Single Line) | Branch Line | 0.7 | 100 km/h |
| `CNB-YARD` | Kanpur Central Yard | Yard/Loop | 0.3 | 30 km/h |
