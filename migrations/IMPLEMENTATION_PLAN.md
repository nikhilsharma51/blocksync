# BlockSync Supabase Database Setup — Complete Implementation Plan

**Version:** 2.0  
**Branch:** `hriday-dataset`  
**Audience:** All team members (Frontend, Backend, Data)  
**Status:** Ready to execute  
**Last Updated:** 2026-08-31

---

## Executive Summary

This plan provides **step-by-step instructions** for every team member to set up the exact same BlockSync database in Supabase and seed it with the canonical 150-task dataset. 

**Key Goal:** Everyone shares identical data structures, standardized credentials, and verified endpoints. No guessing. No inconsistencies.

**Time Required:** 45–60 minutes (one-time setup)  
**Success Indicator:** Backend connects, `GET /api/v1/health` returns 150 tasks, all 3 jury-hook scenarios are present.

---

## Table of Contents

1. [Prerequisites](#section-1-prerequisites)
2. [Phase 1: Supabase Project Setup](#section-2-phase-1-supabase-project-setup)
3. [Phase 2: Schema & Migrations](#section-3-phase-2-schema--migrations)
4. [Phase 3: Data Seeding](#section-4-phase-3-data-seeding)
5. [Phase 4: Backend Configuration](#section-5-phase-4-backend-configuration)
6. [Phase 5: Verification & Testing](#section-6-phase-5-verification--testing)
7. [The 3 Jury-Hook Scenarios](#section-7-the-3-jury-hook-scenarios)
8. [Troubleshooting](#section-8-troubleshooting)
9. [Team Coordination Checklist](#section-9-team-coordination-checklist)

---

## Section 1: Prerequisites

### 1.1 What Everyone Needs

Before starting, ensure:

- [ ] Web browser (Chrome, Firefox, Safari — all work)
- [ ] A Supabase account (free tier sufficient)
  - Sign up: https://app.supabase.com
- [ ] Clone of the `blocksync` repo on your machine
- [ ] Python 3.9+ installed locally
- [ ] Copy of `data/tasks.json`, `data/windows.json`, `data/conflict_pairs.json`
  - Already in repo — no need to regenerate

### 1.2 What NOT to Do

- ❌ Do NOT regenerate the dataset with `scripts/generate_demo_data.py`
- ❌ Do NOT modify `data/*.json` files manually
- ❌ Do NOT commit `.env` to GitHub
- ❌ Do NOT use the same Supabase project across different machines (create separate ones for dev/demo)

---

## Section 2: Phase 1 — Supabase Project Setup

### 2.1 Create Your Supabase Project

**Step 1: Go to https://app.supabase.com**

Log in with your account (or create one).

**Step 2: Click "New Project"**

Fill in the form:

```
Project name:        BlockSync Demo [YourName]  (e.g. "BlockSync Demo - Nikhil")
Database password:   [Auto-generated]           ← COPY THIS and save it
Region:              ap-south-1                 (Asia Pacific - Mumbai)
                     or closest to you
```

Click "Create new project".

⏳ **Wait 2–3 minutes** for the database to build. You'll see "Building your database..."

### 2.2 Get Your Connection String

Once the project is created, you'll land on the **Project Dashboard**.

**Step 1: Click "Settings" (bottom-left gear icon)**

**Step 2: Click "Database" in the left sidebar**

**Step 3: Find "Connection Pooling" section**

You'll see two connection strings:
- **Session Pooler (port 5432)** — for interactive tools (not for FastAPI)
- **Transaction Pooler (port 6543)** — ✅ **USE THIS FOR BACKEND**

Copy the **Transaction Pooler** URL. It looks like:

```
postgresql://postgres.[project-id]:[password]@aws-0-ap-south-1.pooler.supabase.com:6543/postgres
```

**Step 4: Replace [password] with the database password you saved in Step 2.1**

**Example:**
```
postgresql://postgres.xyzabc123:MyPassword456@aws-0-ap-south-1.pooler.supabase.com:6543/postgres
```

**Step 5: Save this URL**

Paste it somewhere safe (temp text file, password manager). You'll need it in Phase 4.

---

## Section 3: Phase 2 — Schema & Migrations

### 3.1 Run the Initial Schema SQL

The schema is already written in `migrations/001_initial_schema.sql`. It creates:
- 10 tables (departments, corridors, block_windows, maintenance_tasks, etc.)
- 10 indexes for query performance
- 3 views for FastAPI convenience queries

**Step 1: Go back to your Supabase project dashboard**

**Step 2: Click "SQL Editor" (left sidebar, looks like `<>`)**

**Step 3: Create a new query**

Click "New query" (top-right button).

**Step 4: Copy the entire contents of `migrations/001_initial_schema.sql`**

Open the file:
```
blocksync/
└── migrations/
    └── 001_initial_schema.sql
```

Copy ALL the SQL (Ctrl+A, Ctrl+C).

**Step 5: Paste into the SQL Editor**

Click in the text box and paste (Ctrl+V).

**Step 6: Click "Run"**

You should see:

```
Execution completed successfully
(29 queries executed)
```

This includes:
- 3 INSERT statements (departments, corridors seeded directly in migration)
- 10 CREATE TABLE statements
- 10 CREATE INDEX statements
- 3 CREATE VIEW statements
- 3 triggers

### 3.2 Verify the Schema

**Step 1: In the SQL Editor, run this query:**

```sql
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public'
ORDER BY table_name;
```

**Step 2: You should see exactly 10 tables:**

```
audit_log
block_assignments
block_windows
conflict_pairs
corridors
departments
integrated_joint_blocks
maintenance_tasks
optimization_plans
unscheduled_tasks
```

✅ **If all 10 tables appear, schema is correct. Continue to Phase 3.**

❌ **If fewer tables appear, go back and re-run the schema SQL.**

---

## Section 4: Phase 3 — Data Seeding

Data seeding populates the three JSON files into the database:
- 150 maintenance tasks
- 148 block windows
- 17 pre-detected conflict pairs
- 3 departments (already seeded via migration)
- 8 corridors (already seeded via migration)

### 4.1 Prepare Your Environment

**Step 1: Navigate to your `blocksync` repo**

```bash
cd C:\Users\NIKHIL\Desktop\blocksync
```

**Step 2: Create a `.env` file in the `backend/` folder**

```bash
cd backend
copy .env.example .env
```

**Step 3: Edit `backend/.env`**

Replace the placeholder DATABASE_URL with your actual URL from Phase 2.2:

```env
DATABASE_URL=postgresql://postgres.[project-id]:[password]@aws-0-ap-south-1.pooler.supabase.com:6543/postgres
JWT_SECRET=sk_demo_1234567890abcdefghijklmnopqrstuvwxyz
```

⚠️ **NEVER commit `.env` to GitHub.** It contains your database password.

Verify `.env` is in `.gitignore`:

```bash
cat .gitignore
```

Should contain `.env`.

### 4.2 Install Dependencies

**Step 1: Check if required packages are installed:**

```bash
pip install supabase psycopg2-binary python-dotenv
```

Required versions (from `requirements.txt`):
- `supabase==2.10.0` or later
- `psycopg2-binary==2.9.10` or later
- `python-dotenv` (any recent version)

### 4.3 Run the Seed Loader

**Step 1: Navigate to the repo root**

```bash
cd C:\Users\NIKHIL\Desktop\blocksync
```

**Step 2: Run the seed script**

```bash
python -m backend.core.seed
```

You should see:

```
BlockSync Database Seed Loader
==================================================
Loading dataset...
  150 tasks, 148 windows, 17 conflict pairs loaded.
Validating...
  ✓ All tasks valid (150 / 150)
  ✓ All windows valid (148 / 148)

Using connection method: psycopg2
Connecting via psycopg2...
Inserting 148 block windows...
  ✓ 148 windows inserted
Inserting 150 maintenance tasks...
  ✓ 150 tasks inserted
Inserting 17 conflict pairs...
  ✓ 17 conflict pairs inserted

✓ psycopg2 seed complete.
```

### 4.4 Verify Data Was Inserted

**Step 1: In the Supabase SQL Editor, run:**

```sql
SELECT COUNT(*) as total_tasks FROM maintenance_tasks;
```

You should see:

```
total_tasks
150
```

**Step 2: Check windows:**

```sql
SELECT COUNT(*) as total_windows FROM block_windows;
```

Should be 148.

**Step 3: Check conflicts:**

```sql
SELECT COUNT(*) as total_conflicts FROM conflict_pairs;
```

Should be 17.

**Step 4: View a sample task:**

```sql
SELECT id, defect_type, severity, criticality_score, status
FROM maintenance_tasks
WHERE id = 'TRK-1000'
LIMIT 1;
```

Should return:

```
id      | defect_type       | severity | criticality_score | status
--------|-------------------|----------|------------------|--------
TRK-1000| Tamping — CST-9   | 4        | 64.17             | Clashed
```

✅ **If you see 150 tasks, 148 windows, 17 conflicts, and sample data matches, seeding is successful.**

---

## Section 5: Phase 4 — Backend Configuration

The backend needs to know:
1. Where the database is (DATABASE_URL)
2. Secret for JWTs (JWT_SECRET)

This is already set in `backend/.env` from Phase 3.1.

### 5.1 Verify Backend .env

**Step 1: Open `backend/.env`**

```bash
cd backend
cat .env
```

You should see:

```env
DATABASE_URL=postgresql://postgres.[your-project]:[password]@...
JWT_SECRET=sk_demo_...
```

### 5.2 Install Backend Dependencies

**Step 1: Install all Python dependencies**

```bash
cd C:\Users\NIKHIL\Desktop\blocksync
pip install -r backend/requirements.txt
```

This installs:
- `fastapi`
- `uvicorn`
- `asyncpg` (async PostgreSQL driver — recommended for FastAPI)
- `supabase`
- `psycopg2-binary`
- `pydantic`
- `google-generativeai` (optional, for Gemini explanations)

### 5.3 Test Database Connection

**Step 1: Create a quick test script**

```bash
cat > test_connection.py << 'EOF'
import asyncio
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv("backend/.env")

async def test():
    db_url = os.environ.get("DATABASE_URL")
    print(f"Connecting to: {db_url[:60]}...")
    
    try:
        conn = await asyncpg.connect(db_url)
        count = await conn.fetchval("SELECT COUNT(*) FROM maintenance_tasks")
        print(f"✓ Connected! Found {count} tasks.")
        await conn.close()
    except Exception as e:
        print(f"✗ Error: {e}")

asyncio.run(test())
EOF
```

**Step 2: Run it**

```bash
python test_connection.py
```

✅ **If you see "✓ Connected! Found 150 tasks", the backend can reach the database.**

---

## Section 6: Phase 5 — Verification & Testing

### 6.1 Start the Backend

**Step 1: Navigate to repo root**

```bash
cd C:\Users\NIKHIL\Desktop\blocksync
```

**Step 2: Start the FastAPI server**

```bash
uvicorn backend.main:app --reload --port 8000
```

You should see:

```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete
```

### 6.2 Test the API Endpoints

Open a new terminal (keep the backend running in the first one).

#### Test 1: Health Check

```bash
curl http://localhost:8000/api/v1/health
```

Expected response:

```json
{
  "status": "ok",
  "timestamp": "2026-08-31T10:48:33Z",
  "database": "connected",
  "tasks_total": 150,
  "windows_total": 148,
  "conflicts_detected": 17,
  "jury_hook_scenario_1_present": true,
  "jury_hook_scenario_2_present": true,
  "jury_hook_scenario_3_present": true
}
```

#### Test 2: Get Pending Tasks

```bash
curl http://localhost:8000/api/v1/tasks/pending
```

Expected: Array of 149 pending/clashed tasks (not yet optimized).

#### Test 3: Get All Corridors

```bash
curl http://localhost:8000/api/v1/corridors
```

Expected: Array of 8 corridors with names and traffic weights.

#### Test 4: Get Corridor Availability

```bash
curl http://localhost:8000/api/v1/corridors/availability
```

Expected: Array of 148 available block windows.

#### Test 5: Run the Optimizer

```bash
curl -X POST http://localhost:8000/api/v1/optimize \
  -H "Content-Type: application/json" \
  -d '{"timeout_seconds": 10}'
```

Expected response:

```json
{
  "plan_id": "PLAN-99281",
  "status": "OPTIMAL",
  "solver_time_sec": 2.34,
  "total_tasks_scheduled": 149,
  "total_tasks_unscheduled": 1,
  "conflicts_resolved": 30,
  "joint_blocks_formed": 1,
  "downtime_saved_hours": 2.5,
  "assignments": [...],
  "unscheduled": [...]
}
```

✅ **If all 5 tests pass, the backend is fully functional.**

### 6.3 Interactive API Documentation

Open your browser:

```
http://localhost:8000/docs
```

This opens Swagger UI where you can interactively test all endpoints. Great for demos!

---

## Section 7: The 3 Jury-Hook Scenarios

These scenarios are **hardcoded** into `data/tasks.json`. They will always be present regardless of random seed.

### Scenario 1: Integrated Block (TRK-1000 + OHE-3000)

**What:** Track and OHE departments need maintenance on the same corridor at the same time.

**In the Data:**
- `TRK-1000`: Tamping, Severity 4, Criticality 64.17, Status: **Clashed**
- `OHE-3000`: Insulator Flashover, Severity 4, Criticality 61.50, Status: **Clashed**
- Both on corridor `NDLS-GZB-UP`
- `TRK-1000.is_compatible_with = "OHE"`
- `OHE-3000.is_compatible_with = "TRK"`

**What the Optimizer Does:**
The optimizer recognizes the `is_compatible_with` flag and merges both tasks into a single **Integrated Joint Block** — one shared 25 kV power isolation, one corridor downtime slot.

**What the Judge Sees:**
1. **Conflict Gantt:** Two red bars on the same corridor at the same time (the "Before" state)
2. **Optimized Gantt:** One merged green bar labeled `JB-001 [TRK + OHE]` (the "After" state)
3. **Downtime Saved:** ≥ 2 hours saved by merging (one power isolation instead of two)

**Where to Verify in Database:**

```sql
SELECT id, department_code, corridor_code, status, is_compatible_with
FROM maintenance_tasks
WHERE id IN ('TRK-1000', 'OHE-3000');

--
-- SELECT
--     mt.id,
--     d.code AS department_code,
--     c.code AS corridor_code,
--     mt.status,
--     mt.is_compatible_with
-- FROM maintenance_tasks mt
-- JOIN departments d ON mt.department_id = d.id
-- JOIN corridors   c ON mt.corridor_id   = c.id
-- WHERE mt.id IN ('TRK-1000', 'OHE-3000'); 
-- 
```

Should return:

```
id       | department_code | corridor_code | status  | is_compatible_with
---------|-----------------|---------------|---------|-------------------
TRK-1000 | TRK             | NDLS-GZB-UP   | Clashed | OHE
OHE-3000 | OHE             | NDLS-GZB-UP   | Clashed | TRK
```

---

### Scenario 2: Safety Override (TRK-1001 beats SNT-2000)

**What:** Both a safety-critical rail fracture and a routine signal task request the same time slot.

**In the Data:**
- `TRK-1001`: Weld / Rail Fracture, Severity 5, Criticality **76.5**, Status: **Clashed**
- `SNT-2000`: Signal LED Change, Severity 1, Criticality **23.0**, Status: **Clashed**
- Both on corridor `DLI-RE-SL`
- Requested start: **same time slot** (`2026-09-02T13:00:00Z`)

**What the Optimizer Does:**
Both tasks request the same window. The criticality engine scores TRK-1001 at 76.5 vs SNT-2000 at 23.0 — a **53.5-point gap**. The optimizer assigns the window to the higher-scoring task (Track) and defers Signal.

**What the Judge Sees:**
Proves the system is **safety-first**, not first-come-first-served. The scoring formula prioritizes:
1. Severity (45% weight) — Rail fractures are immediate removal defects
2. Overdue backlog (35% weight)
3. Asset criticality (20% weight) — Mainline traffic over signal work

**Where to Verify in Database:**

```sql
SELECT id, department_code, severity, criticality_score, status
FROM maintenance_tasks
WHERE id IN ('TRK-1001', 'SNT-2000');


-- SELECT
--     mt.id,
--     d.code AS department_code,
--     mt.severity,
--     mt.criticality_score,
--     mt.status
-- FROM maintenance_tasks mt
-- JOIN departments d ON mt.department_id = d.id
-- WHERE mt.id IN ('TRK-1001', 'SNT-2000');
```

Should return:

```
id       | department_code | severity | criticality_score | status
---------|-----------------|----------|------------------|--------
TRK-1001 | TRK             | 5        | 76.5              | Clashed
SNT-2000 | SNT             | 1        | 23.0              | Clashed
```

---

### Scenario 3: Impossible Task (TRK-1002)

**What:** A task requests 6 hours of maintenance, but the longest available window is only 5 hours.

**In the Data:**
- `TRK-1002`: Ballast Deep Screening (BCM), Severity 3, Criticality 61.0
- Requested Duration: **360 minutes (6 hours)**
- Corridor: `NDLS-GZB-UP`
- Longest available window on that corridor: **300 minutes (5 hours)**
- Status: **Deferred**

**What the Optimizer Does:**
It outputs the task in the `unscheduled` array with a clear reason:
> *"No continuous window available for requested duration (360 mins). Longest available window on NDLS-GZB-UP is 300 mins. Defer to Sunday Mega Block."*

**What the Judge Sees:**
The app doesn't crash or hang. It gracefully degrades, communicates the infeasibility, and continues scheduling the remaining 149 tasks. This demonstrates:
1. **Robustness:** System handles impossible inputs gracefully
2. **Transparency:** Clear explanation for deferred tasks
3. **Partial Optimization:** Even if 1 task can't be scheduled, the other 149 are optimized

**Where to Verify in Database:**

```sql
SELECT id, defect_type, est_duration_min, status
FROM maintenance_tasks
WHERE id = 'TRK-1002';
```

Should return:

```
id       | defect_type                      | est_duration_min | status
---------|----------------------------------|------------------|--------
TRK-1002 | Ballast Deep Screening (BCM)    | 360              | Deferred
```

Then check block_windows to confirm no 360-min window exists on NDLS-GZB-UP:

```sql
SELECT corridor_code, duration_min
FROM block_windows
WHERE corridor_code = 'NDLS-GZB-UP'
ORDER BY duration_min DESC;
```

Should show max duration < 360 mins.

---

## Section 8: Troubleshooting

### 8.1 Database Connection Errors

#### Error: "FATAL: password authentication failed"

**Cause:** DATABASE_URL has wrong password

**Fix:**
1. Go to Supabase dashboard → Settings → Database
2. Click "Reset Database Password"
3. Copy the new transaction pooler URL
4. Update `backend/.env`
5. Re-run the seed loader

#### Error: "Connection refused" or "Network unreachable"

**Cause:** Wrong host or port

**Fix:**
1. Verify you're using port **6543** (transaction pooler), not 5432
2. Check that you copied the full hostname from Supabase
3. Test with: `ping aws-0-ap-south-1.pooler.supabase.com`

#### Error: "SSL connection error"

**Cause:** Supabase requires SSL; your URL is missing SSL params

**Fix:** Your DATABASE_URL should include `?sslmode=require` at the end. Supabase typically handles this automatically. Copy the connection string again from the dashboard.

### 8.2 Seeding Errors

#### Error: "Table does not exist"

**Cause:** Schema migration was not run

**Fix:**
1. Go to Supabase SQL Editor
2. Re-run `migrations/001_initial_schema.sql`
3. Verify all 10 tables are created
4. Re-run the seed loader

#### Error: "Foreign key violation"

**Cause:** Seeding tried to insert tasks with invalid department_id or corridor_id

**Fix:**
1. Verify departments and corridors were seeded by the migration
2. Run the verification query from Phase 3:
   ```sql
   SELECT * FROM departments;
   SELECT * FROM corridors;
   ```
3. If empty, re-run the schema SQL

#### Error: "Duplicate key value violates unique constraint"

**Cause:** Seed script ran twice and tried to insert duplicate task IDs

**Fix:**
1. Run with `--reset` flag:
   ```bash
   python -m backend.core.seed --reset
   ```
2. This truncates tables before reinserting

### 8.3 Backend Errors

#### Error: "ImportError: No module named 'backend'"

**Cause:** You're not running from the repo root

**Fix:**
```bash
cd C:\Users\NIKHIL\Desktop\blocksync
python -m backend.core.seed
```

The `-m` flag requires the repo root as current directory.

#### Error: ".env file not found"

**Cause:** `.env` doesn't exist in `backend/` folder

**Fix:**
```bash
cd backend
copy .env.example .env
# Edit .env and fill in DATABASE_URL
```

#### Error: "GET /api/v1/health returns 0 tasks"

**Cause:** Backend connected but database is empty

**Fix:**
1. Verify seeding completed: `SELECT COUNT(*) FROM maintenance_tasks;`
2. If 0 rows, re-run Phase 3 (data seeding)
3. If 150 rows, restart the backend server

### 8.4 API Response Errors

#### Error: "POST /api/v1/optimize returns empty assignments"

**Cause:** Optimizer ran but found no feasible solution (this is rare)

**Fix:**
1. Check if there are available windows: `SELECT COUNT(*) FROM block_windows WHERE is_available = TRUE;`
2. Check if tasks exist: `SELECT COUNT(*) FROM maintenance_tasks;`
3. Check the optimizer logs in the backend console for constraint violations

#### Error: "GET /api/v1/tasks/pending returns only a few tasks"

**Cause:** Optimizer already ran and scheduled most tasks

**Fix:**
1. Reset the data (Phase 3 with `--reset` flag)
2. Or check `unscheduled_tasks` table to see what was deferred

---

## Section 9: Team Coordination Checklist

### For All Team Members

Use this checklist to verify setup:

- [ ] Supabase account created
- [ ] Supabase project created with name "BlockSync Demo - [YourName]"
- [ ] Transaction Pooler connection string copied and saved
- [ ] `.env` file created in `backend/` folder
- [ ] DATABASE_URL and JWT_SECRET filled in `.env`
- [ ] `.env` is listed in `.gitignore`
- [ ] `backend/.env` is NOT committed to GitHub (verify with `git status`)

### For Data & Backend Members

- [ ] Schema migration (001_initial_schema.sql) executed in Supabase
- [ ] 10 tables verified to exist (verification query run)
- [ ] Data seed loader executed successfully
- [ ] 150 tasks verified in database
- [ ] 148 windows verified
- [ ] 17 conflict pairs verified
- [ ] Backend dependencies installed
- [ ] Test connection script runs successfully
- [ ] Backend starts without errors

### For Frontend Members

- [ ] Backend is running on `http://localhost:8000`
- [ ] `GET /api/v1/health` returns 150 tasks, jury hooks present
- [ ] `GET /api/v1/tasks/pending` returns task list matching schema
- [ ] `GET /api/v1/corridors/availability` returns block windows
- [ ] Frontend can `POST /api/v1/optimize` and receive results
- [ ] Swagger UI is accessible at `http://localhost:8000/docs`

### Before the Demo

- [ ] All jury-hook scenarios verified to be present in database
- [ ] Scenario 1 (TRK-1000 + OHE-3000) found and verified
- [ ] Scenario 2 (TRK-1001 beats SNT-2000) verified
- [ ] Scenario 3 (TRK-1002 deferred) verified
- [ ] Backup of `.env` saved securely (password manager)
- [ ] Fresh Supabase project ready (not overwritten during dev)

---

## Appendix A: Quick Reference

### Connection String Format

```
postgresql://postgres.[PROJECT_ID]:[PASSWORD]@aws-0-ap-south-1.pooler.supabase.com:6543/postgres
```

Replace:
- `[PROJECT_ID]` — Your Supabase project ID
- `[PASSWORD]` — Your database password (from Supabase creation)
- Region — `ap-south-1` if in India, else your chosen region
- Port — Always `6543` for Transaction Pooler

### Key Database Tables

| Table | Records | Purpose |
|-------|---------|---------|
| `departments` | 3 | TRK, SNT, OHE |
| `corridors` | 8 | Railway block sections |
| `maintenance_tasks` | 150 | Raw maintenance requests |
| `block_windows` | 148 | Available maintenance slots |
| `conflict_pairs` | 17 | Pre-detected scheduling conflicts |
| `optimization_plans` | 0 (added by optimizer) | Solver outputs |
| `block_assignments` | 0 (added by optimizer) | Task-to-window mappings |
| `integrated_joint_blocks` | 0 (added by optimizer) | Multi-department merged blocks |

### Essential SQL Queries

**Count everything:**
```sql
SELECT 
  (SELECT COUNT(*) FROM maintenance_tasks) as tasks,
  (SELECT COUNT(*) FROM block_windows) as windows,
  (SELECT COUNT(*) FROM conflict_pairs) as conflicts;
```

**View all corridors:**
```sql
SELECT code, name, traffic_weight FROM corridors ORDER BY traffic_weight DESC;
```

**Find all tasks by department:**
```sql
SELECT mt.id, mt.defect_type, mt.severity, mt.criticality_score
FROM maintenance_tasks mt
JOIN departments d ON mt.department_id = d.id
WHERE d.code = 'TRK'
ORDER BY mt.criticality_score DESC;
```

**View conflicts:**
```sql
SELECT task_a_id, task_b_id, conflict_severity, conflict_type
FROM conflict_pairs
ORDER BY conflict_severity;
```

### Essential Python Commands

**Load data:**
```python
import json
with open("data/tasks.json") as f:
    tasks = json.load(f)
print(f"Loaded {len(tasks)} tasks")
```

**Test database connection:**
```bash
python test_connection.py  # (script provided in Phase 5.3)
```

**Run seed loader:**
```bash
python -m backend.core.seed
python -m backend.core.seed --reset  # Clear and reseed
python -m backend.core.seed --dry-run  # Validate only
```

**Start backend:**
```bash
uvicorn backend.main:app --reload --port 8000
```

**Test health endpoint:**
```bash
curl http://localhost:8000/api/v1/health | python -m json.tool
```

---

## Appendix B: File Reference

### Data Files (READ-ONLY — DO NOT MODIFY)

```
blocksync/
├── data/
│   ├── tasks.json                    (150 maintenance tasks)
│   ├── windows.json                  (148 block windows)
│   ├── conflict_pairs.json           (17 conflicts)
│   ├── seed_summary.json             (metadata)
│   └── README.md                     (data documentation)
```

### Migration & Schema

```
blocksync/
└── migrations/
    └── 001_initial_schema.sql        (Run this first in Supabase)
```

### Backend

```
blocksync/
└── backend/
    ├── .env                          (Create & fill with DATABASE_URL)
    ├── .env.example                  (Template)
    ├── main.py                       (FastAPI entry point)
    ├── requirements.txt              (Python dependencies)
    ├── core/
    │   ├── seed.py                   (Data seeder — run with: python -m backend.core.seed)
    │   ├── validator.py              (Data validation)
    │   ├── scoring.py                (Criticality scoring formula)
    │   ├── explainer.py              (Gemini AI explanations)
    │   └── __init__.py
    ├── api/
    │   ├── schemas.py                (Pydantic request/response shapes)
    │   ├── routes/
    │   │   ├── tasks.py              (GET /api/v1/tasks/*)
    │   │   ├── corridors.py          (GET /api/v1/corridors/*)
    │   │   ├── optimize.py           (POST /api/v1/optimize)
    │   │   └── __init__.py
    │   └── __init__.py
    └── __init__.py
```

---

## Appendix C: The Scoring Formula (Reference)

Used to calculate criticality scores for every task before seeding:

```
Score = (W_SEV × norm_severity) + (W_OVD × norm_overdue) + (W_TRF × norm_traffic)

W_SEV = 0.45   (Safety — severity is paramount)
W_OVD = 0.35   (Overdue penalty — forces aging backlog to priority)
W_TRF = 0.20   (Asset criticality — mainlines over branches)

norm_severity = (severity / 5) × 100                → [20, 100]
norm_overdue  = min(days_overdue / 30, 1.0) × 100  → [0, 100]
norm_traffic  = corridor.traffic_weight × 100      → [10, 100]

Priority Levels (automatic, based on final score):
  P0: score ≥ 80
  P1: 50 ≤ score < 80
  P2: score < 50
```

**Example Calculation (TRK-1001 — Rail Fracture):**
```
Severity: 5 (Immediate Removal)
Days Overdue: 15
Corridor: NDLS-GZB-UP (traffic_weight = 1.0)

norm_severity = (5 / 5) × 100 = 100
norm_overdue  = min(15 / 30, 1.0) × 100 = 50
norm_traffic  = 1.0 × 100 = 100

Score = (0.45 × 100) + (0.35 × 50) + (0.20 × 100)
      = 45 + 17.5 + 20
      = 82.5 / 100
      
Priority: P0 (≥ 80)
```

---

## Appendix D: Common Questions (FAQ)

**Q: Do I need to generate the dataset myself?**  
A: No. The dataset is already in `data/*.json`. It's deterministic (RANDOM_SEED=42), so everyone gets identical data.

**Q: Can I modify the tasks.json file?**  
A: Only during development. For the SIH demo, everyone must use the exact same file. Any changes will desynchronize your plan from the judges' expectations.

**Q: How many times can I seed the data?**  
A: Unlimited. Use `--reset` to clear and reseed. This is useful for testing.

**Q: What if I accidentally delete a table?**  
A: Re-run the migration (`001_initial_schema.sql`) to recreate it, then reseed.

**Q: Can multiple people use the same Supabase project?**  
A: It's possible but not recommended. Create separate projects for dev/demo. Share the `.env` credentials via a secure channel (NOT GitHub).

**Q: Why port 6543 and not 5432?**  
A: Port 6543 is the "Transaction Pooler" — stateless, perfect for FastAPI. Port 5432 is the "Session Pooler" — stateful, for interactive tools like DBeaver.

**Q: What if the optimizer doesn't find a solution?**  
A: The API returns `solver_status: "INFEASIBLE"` with details. This is expected if constraint are impossible. Gracefully degrade and communicate the reason to the user.

**Q: How do I restart from scratch?**  
A: 
   1. Delete your Supabase project
   2. Create a new one
   3. Re-run the migration
   4. Re-seed the data

**Q: Can I use a different database (e.g., local PostgreSQL)?**  
A: Yes. Change DATABASE_URL in `.env` to your local PostgreSQL URL. The seed loader supports both Supabase and direct PostgreSQL.

---

## Appendix E: Support & Escalation

### If You're Stuck

1. **Check this document** — Most issues are covered in Section 8 (Troubleshooting)
2. **Check the error message** — Copy the exact error and search the database (Supabase logs, backend logs)
3. **Check the data** — Use SQL queries to verify the state of the database
4. **Ask your team** — Other members may have solved the same issue
5. **Escalate to Nikhil (Data Lead)** — If still stuck, reach out

### Before Escalating

Have ready:
- The exact error message (screenshot or copy-paste)
- Which section of this plan you're on (e.g., "Phase 3, Step 4.2")
- Output of relevant SQL queries or backend logs
- Your `.env` file (without the password)

---

## Sign-Off

This plan is **complete and ready to execute**. Every team member should be able to follow Steps 2–6 independently and arrive at an identical database state.

**Next steps:**
1. Each team member executes Phases 1–4 independently
2. Verify with the checklists in Section 9
3. Report blockers immediately (before demo day)
4. Frontend integrates with backend at `http://localhost:8000`
5. **Demo ready!**

---

**Version History:**
- v1.0 (2026-08-30): Initial guide from docs/
- v2.0 (2026-08-31): Expanded with full workflow, jury-hook details, troubleshooting

