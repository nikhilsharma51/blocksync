# BlockSync — Data Layer Reference

**Branch:** `hriday-dataset` | **Owner:** Hriday (Data & Pitch Lead)
**For:** All team members — Frontend (Member 3), Backend/DB (Member 2), Mathematician/CP-SAT (Member 1)

---

## What this branch delivers

Everything the rest of the team needs to start building, without waiting for a real database.

| What | Where | Use it for |
|------|-------|------------|
| 150 maintenance tasks (JSON) | `data/tasks.json` | Feed the frontend Gantt chart |
| 148 COA block windows (JSON) | `data/windows.json` | Feed the optimizer |
| 17 conflict pairs (JSON) | `data/conflict_pairs.json` | Feed the Conflict view |
| PostgreSQL schema | `migrations/001_initial_schema.sql` | Run in Supabase SQL editor |
| Scoring engine | `backend/core/scoring.py` | Import directly — no setup |
| Gemini explainer | `backend/core/explainer.py` | Requires `GEMINI_API_KEY` |
| FastAPI server | `backend/main.py` | `uvicorn backend.main:app --reload` |
| DB seed loader | `backend/core/seed.py` | Seeds Supabase from the JSON files |

---

## Quickstart (5 minutes)

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Regenerate the dataset (already done — only needed if you want fresh data)
python scripts/generate_demo_data.py --verbose

# 3. Start the API server
uvicorn backend.main:app --reload --port 8000

# 4. Open interactive docs
# http://localhost:8000/docs
```

### Seed the Supabase database

```bash
# Copy the env template and fill in your credentials
copy .env.example .env

# Run the migration first (paste migrations/001_initial_schema.sql into Supabase SQL editor)
# Then seed:
python -m backend.core.seed

# Dry run (validate without writing):
python -m backend.core.seed --dry-run

# Full reset + re-seed:
python -m backend.core.seed --reset
```

---

## API Endpoints

Base URL (local): `http://localhost:8000/api/v1`

### Tasks

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/tasks/pending` | All unscheduled tasks, sorted by score ↓ |
| `GET` | `/tasks/pending?department=TRK` | Filter by department |
| `GET` | `/tasks/pending?min_score=80` | Filter P0 tasks only |
| `GET` | `/tasks/{task_id}` | Single task detail |
| `GET` | `/tasks` | All tasks (any status) |

### Corridors & Windows

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/corridors` | All 8 corridors with metadata |
| `GET` | `/corridors/availability` | All open COA windows |
| `GET` | `/corridors/availability?corridor_code=NDLS-GZB-UP` | Windows for one corridor |
| `GET` | `/corridors/{code}/windows` | Same, path-param style |

### Optimizer

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/optimize` | Run the scheduler — returns assignments + unscheduled |
| `GET` | `/conflicts` | Pre-detected conflict pairs |
| `POST` | `/explain` | Generate Gemini AI explanation for one task |
| `GET` | `/health` | Health check + dataset stats |

### Example: Fetch pending tasks

```bash
curl http://localhost:8000/api/v1/tasks/pending
```

```json
{
  "status": "success",
  "count": 148,
  "data": [
    {
      "id": "TRK-1003",
      "department": "TRK",
      "corridor": "TDL-CNB-BOTH",
      "corridor_name": "Tundla - Kanpur Central",
      "defect_type": "Bridge Approach Track Renewal",
      "severity": 5,
      "days_overdue": 17,
      "est_duration_min": 180,
      "criticality_score": 100.0,
      "priority": "P0",
      "status": "Clashed",
      "requested_start": "2026-09-02T01:00:00+00:00",
      "requested_end": "2026-09-02T04:00:00+00:00",
      "is_compatible_with": "OHE",
      "power_disconnection_required": true
    }
  ]
}
```

### Example: Run the optimizer

```bash
curl -X POST http://localhost:8000/api/v1/optimize \
  -H "Content-Type: application/json" \
  -d '{"plan_date": "2026-09-02", "max_solve_seconds": 30}'
```

```json
{
  "status": "success",
  "plan_id": "PLAN-A3F2B",
  "assignments": [
    {
      "task_id": "TRK-1000",
      "department": "TRK",
      "corridor": "NDLS-GZB-UP",
      "assigned_start": "2026-09-02T02:00:00+00:00",
      "assigned_end": "2026-09-02T04:00:00+00:00",
      "is_integrated": true,
      "joint_block_id": "JB-001",
      "merged_departments": ["TRK", "OHE"],
      "window_type": "Night Gold Window"
    }
  ],
  "unscheduled": [
    {
      "task_id": "TRK-1002",
      "reason": "No continuous window available for requested duration (360 mins). Longest available window on NDLS-GZB-UP is 300 mins.",
      "next_recommended_window": "2026-09-06 Night Gold Window"
    }
  ],
  "solver_stats": {
    "status": "FEASIBLE",
    "solve_time_seconds": 0.021,
    "joint_blocks_formed": 4,
    "downtime_saved_hours": 3.5,
    "total_tasks_scheduled": 148,
    "total_tasks_unscheduled": 2
  }
}
```

---

## The 3 Demo Scenarios (For the 5-Minute Pitch)

### Scenario 1 — Integrated Block

**Tasks:** `TRK-1000` (Tamping, NDLS-GZB-UP, Mon 02:00) + `OHE-3000` (Insulator, NDLS-GZB-UP, Mon 02:00)

Both departments requested the exact same corridor at the exact same time. Instead of granting two separate blocks (two power isolations, two train halts), the optimizer detects `is_compatible_with: OHE` and `is_compatible_with: TRK` and merges them into **Joint Block JB-001** — saving ≥120 minutes of corridor downtime.

> **Judge question:** "Why did you merge these?"
> **Answer:** "Both tasks require 25kV OHE isolation on the same track section. Granting them together wastes zero additional corridor time versus granting them separately."

---

### Scenario 2 — Safety Override

**Tasks:** `SNT-2000` (Signal LED, score **23.0**) vs `TRK-1001` (Rail Fracture, score **76.5**) — same slot, same corridor.

The traditional first-come-first-served system would give the slot to whoever submitted first. BlockSync's scoring engine gives it to Track because a live rail fracture (53.5 points higher) is a safety emergency. Signal is rescheduled to the very next available window.

> **Judge question:** "Isn't this unfair to Signal?"
> **Answer:** "No — Signal gets the next free window, just not this one. A broken rail at speed is an immediate derailment risk; a signal LED change is not."

---

### Scenario 3 — Graceful Degradation

**Task:** `TRK-1002` (Deep Screening, 360 min requested, NDLS-GZB-UP)

The longest available COA window on that corridor is 300 minutes. The CP-SAT constraint `task_duration ≤ window_length` is provably infeasible. The app outputs this task in the `unscheduled` array with a plain-English explanation and a recommended next window — it does **not** crash, silently drop it, or over-compress the task into an impossibly short window.

> **Judge question:** "What happens if the AI can't solve it?"
> **Answer:** "It tells you exactly why, and when the next viable window is. The human controller makes the final call."

---

## The Criticality Scoring Formula

```
Score = (0.45 × norm_severity) + (0.35 × norm_overdue) + (0.20 × norm_traffic)

norm_severity = (severity / 5) × 100
norm_overdue  = min(days_overdue / 30, 1.0) × 100     ← capped at 30 days
norm_traffic  = traffic_weight × 100
```

Implemented in `backend/core/scoring.py`. Import with:

```python
from backend.core.scoring import calculate_criticality_score, calculate_criticality_score_full
```

---

## Integrating with the CP-SAT Solver (For Member 1)

The `POST /api/v1/optimize` route currently uses a greedy heuristic. To swap in OR-Tools CP-SAT:

1. Install: `pip install ortools==9.11.4210`
2. Open `backend/api/routes/optimize.py`
3. Replace the `_greedy_schedule()` function body with your CP-SAT model
4. The function signature and return types **must not change** — everything else adapts automatically

The input the function receives:
- `tasks: list[dict]` — from `data/tasks.json` (all fields documented in `data/README.md`)
- `windows: list[dict]` — from `data/windows.json`

The output it must return:
- `assignments: list[dict]` — keys: `task_id`, `assigned_start`, `assigned_end`, `is_integrated`, `joint_block_id`, `merged_departments`, `window_type`
- `unscheduled: list[dict]` — keys: `task_id`, `department`, `defect_type`, `criticality_score`, `requested_duration_min`, `reason`
- `stats: dict` — keys: `conflicts_resolved`, `joint_blocks_formed`, `downtime_saved_hours`, `total_tasks_scheduled`, `total_tasks_unscheduled`, `constraints_evaluated`

---

## Integrating with the Frontend (For Member 3)

The frontend needs to point its data fetches at these endpoints:

| Frontend component | Endpoint |
|--------------------|----------|
| `ConflictGantt` | `GET /api/v1/tasks/pending` |
| `ConflictListPanel` | `GET /api/v1/conflicts` |
| `OptimizedGantt` | `POST /api/v1/optimize` (on "Run Optimizer" click) |
| `ExplainabilityDrawer` | `POST /api/v1/explain` (on task click) |
| `AppHeader` stats | `GET /api/v1/health` |

Until the backend is deployed, the existing `src/data/mockRailwayData.ts` continues to work — the `data/tasks.json` shape matches the `MaintenanceTask` TypeScript type exactly.

---

## Integrating with Supabase (For Member 2)

1. Run `migrations/001_initial_schema.sql` in the Supabase SQL editor — this creates all 9 tables, views, indexes and triggers
2. Set `SUPABASE_URL` and `SUPABASE_KEY` in `.env`
3. Run `python -m backend.core.seed` — seeds all 150 tasks and 148 windows
4. The FastAPI routes currently read from `data/*.json` files; swap `_load_tasks()` / `_load_windows()` in the route files to use `supabase.table("maintenance_tasks").select("*")` when ready

---

## File Tree

```
repo/
├── backend/
│   ├── __init__.py
│   ├── main.py                    ← FastAPI app entry point
│   ├── api/
│   │   ├── schemas.py             ← All Pydantic request/response models
│   │   └── routes/
│   │       ├── tasks.py           ← GET /tasks/pending
│   │       ├── corridors.py       ← GET /corridors/availability
│   │       └── optimize.py        ← POST /optimize, POST /explain, GET /conflicts
│   └── core/
│       ├── scoring.py             ← Criticality scoring engine
│       ├── explainer.py           ← Gemini AI explainability
│       ├── validator.py           ← Data integrity validation
│       └── seed.py                ← Supabase / psycopg2 seed loader
├── data/
│   ├── tasks.json                 ← 150 maintenance tasks (GENERATED)
│   ├── windows.json               ← 148 COA block windows (GENERATED)
│   ├── conflict_pairs.json        ← 17 conflict pairs (GENERATED)
│   ├── seed_summary.json          ← Stats + jury-hook map (GENERATED)
│   └── README.md                  ← Dataset field reference
├── migrations/
│   └── 001_initial_schema.sql     ← PostgreSQL DDL (run in Supabase)
├── scripts/
│   └── generate_demo_data.py      ← Dataset generator
├── frontend/                      ← Member 3's territory — DO NOT MODIFY
├── .env.example                   ← Copy to .env and fill credentials
├── requirements.txt               ← Python dependencies
└── DATASET.md                     ← This file
```
