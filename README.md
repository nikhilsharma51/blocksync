<div align="center">

# BlockSync

**An AI-assisted maintenance block planning prototype for Indian Railways.**

BlockSync explores how railway maintenance tasks can be prioritized and scheduled into available corridor windows, helping teams identify conflicts, coordinate compatible work, and understand why tasks are scheduled or deferred.

Built with **Next.js, React, TypeScript, FastAPI, Python, and JSON/PostgreSQL data sources**, the project combines a dashboard prototype with a REST API and a heuristic scheduling engine.

![Stack](https://img.shields.io/badge/Stack-Next.js%20%7C%20FastAPI%20%7C%20Python-2563eb)
![Language](https://img.shields.io/badge/Language-TypeScript%20%7C%20Python-blue)
![Status](https://img.shields.io/badge/Status-Incomplete%20%2F%20Discontinued-orange)

</div>

---

## Overview

Railway maintenance work must be coordinated around available block windows while accounting for task urgency, corridor availability, work duration, and potential conflicts between departments. Planning these activities manually can make conflicts and missed opportunities harder to identify.

BlockSync is a prototype for exploring a centralized planning workflow. It includes a dashboard for reviewing maintenance conflicts and proposed schedules, a FastAPI backend for querying tasks and corridor windows, and a greedy scheduling approach for generating candidate assignments.

**Project status:** This repository is an incomplete prototype and is no longer being actively developed. The interface and API demonstrate parts of the proposed workflow, but the project should not be treated as a production railway scheduling system.

## Key features

- **Maintenance task dataset** — sample task records with department, corridor, severity, overdue duration, and criticality information.
- **Conflict review** — inspect predefined task conflicts and compare the initial plan with proposed assignments.
- **Heuristic scheduling** — generate candidate assignments using a greedy, priority-based scheduler.
- **Corridor and block-window data** — retrieve corridor metadata and available maintenance windows.
- **Scheduling explanations** — generate rule-based explanations, with optional Gemini-backed explanations when configured.
- **Dashboard prototype** — includes conflict and optimized timelines, department intake, corridor map, safety dashboard, execution tracking, and explanation panels.
- **Dataset validation and tests** — includes validation utilities, seed data, and API endpoint tests.

> **Important:** The CP-SAT/OR-Tools optimizer is not integrated. The active scheduling logic is heuristic and should not be interpreted as a mathematically optimal or operationally validated plan. Some frontend views use local mock data and are not fully connected to backend workflows.

## Technical highlights

### Priority-based scheduling

The backend uses a greedy scheduling approach to place tasks into available corridor windows. It considers task priority and window availability and returns scheduled assignments alongside tasks that could not be placed. This is a prototype heuristic, not a complete constraint-programming solution.

### Criticality scoring

The backend includes scoring utilities that combine task characteristics to estimate criticality and classify priority. These scores help order tasks for review and scheduling.

### Explainability

The explanation endpoint supports human-readable reasons for scheduling decisions. A rule-based fallback is available when a Gemini API key is not configured or the external request fails.

### Data and database options

The repository contains JSON datasets for maintenance tasks, corridor windows, conflicts, and seed summaries. Database schema and seeding utilities are also included for a Supabase/PostgreSQL setup. The available runtime paths and database integration are not a fully hardened production deployment.

## Tech stack

| Layer | Technologies |
| --- | --- |
| Frontend | Next.js, React, TypeScript |
| UI and charts | Tailwind CSS, Recharts, Lucide React |
| API | Python, FastAPI, Uvicorn, Pydantic |
| Scheduling | Python greedy heuristic; CP-SAT integration is unfinished |
| Explainability | Rule-based explanations; optional Google Gemini API |
| Data | JSON datasets; optional Supabase/PostgreSQL integration |
| Testing | pytest, FastAPI test client, validation scripts |

## Architecture

```text
Browser
  |
  v
Next.js frontend
  |  HTTP requests (where integrated)
  v
FastAPI backend
  |-------------------|-------------------|
  v                   v                   v
Task and corridor   Scoring and         Scheduling and
API routes          validation          explanations
  |                                       |
  v                                       v
JSON datasets                         Greedy heuristic
  |
  v
Optional Supabase / PostgreSQL integration
```

The architecture represents the intended components. Not every frontend view is connected end-to-end to the API, and some screens currently rely on mock data.

## Run locally

### Prerequisites

- Python 3.11 or newer
- Node.js and npm
- Git
- Optional: Supabase/PostgreSQL credentials for database-related workflows
- Optional: Gemini API key for AI-generated explanations

### 1. Clone the repository

```bash
git clone https://github.com/nikhilsharma51/blocksync.git
cd blocksync
```

### 2. Start the backend

From the repository root:

```bash
python -m venv .venv
```

Activate the virtual environment.

**Windows PowerShell:**

```powershell
.venv\Scripts\Activate.ps1
```

**macOS/Linux:**

```bash
source .venv/bin/activate
```

Install dependencies and start the API:

```bash
pip install -r requirements.txt
uvicorn backend.main:app --reload --port 8000
```

The backend provides interactive API documentation at:

- Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)
- ReDoc: [http://localhost:8000/redoc](http://localhost:8000/redoc)
- Health check: [http://localhost:8000/api/v1/health](http://localhost:8000/api/v1/health)

### 3. Start the frontend

In a separate terminal:

```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

The frontend contains mock/demo data in some views. Running both applications locally does not imply that every screen is backed by live API data.

### Environment configuration

The backend includes `backend/.env.example` as a starting point for database configuration. Copy it to the appropriate local environment file only if you need those integrations, then replace all placeholder values with your own credentials. Set `GEMINI_API_KEY` if you want to try Gemini-backed explanations; rule-based fallback explanations are available without it.

Never commit real API keys, database passwords, service-role keys, or other secrets.

## API overview

Base URL: `http://localhost:8000/api/v1`

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `GET` | `/health` | API health and dataset summary |
| `GET` | `/tasks` | Retrieve maintenance tasks |
| `GET` | `/tasks/pending` | Retrieve pending/unscheduled tasks, with supported filters |
| `GET` | `/tasks/{task_id}` | Retrieve a task by ID |
| `GET` | `/corridors` | Retrieve corridor metadata |
| `GET` | `/corridors/availability` | Retrieve available corridor windows |
| `GET` | `/corridors/{code}/windows` | Retrieve windows for a corridor |
| `POST` | `/optimize` | Run the heuristic scheduler |
| `GET` | `/conflicts` | Retrieve predefined conflict pairs |
| `POST` | `/explain` | Generate an explanation for an assignment/task |

For exact request and response schemas, use the Swagger UI served by the running backend.

## Project structure

```text
blocksync/
├── backend/
│   ├── api/
│   │   ├── routes/           # Task, corridor, and optimization endpoints
│   │   └── schemas.py        # Pydantic request/response schemas
│   ├── core/
│   │   ├── scoring.py        # Criticality scoring and priority classification
│   │   ├── solver.py         # Solver interface and unfinished CP-SAT placeholder
│   │   ├── validator.py      # Task and window validation
│   │   ├── explainer.py      # Rule-based and optional Gemini explanations
│   │   └── seed.py           # Database seeding utilities
│   ├── main.py               # FastAPI application
│   └── requirements.txt      # Backend dependencies
├── frontend/
│   ├── src/app/              # Next.js app entry and global styles
│   ├── src/components/       # Dashboard, timeline, modal, and drawer components
│   ├── src/data/             # Frontend mock/demo data
│   └── package.json
├── data/
│   ├── tasks.json            # Sample maintenance tasks
│   ├── windows.json          # Sample corridor block windows
│   ├── conflict_pairs.json   # Precomputed conflict pairs
│   └── seed_summary.json     # Dataset summary
├── migrations/               # PostgreSQL schema and implementation notes
├── scripts/                  # Dataset generation and validation utilities
├── DATASET.md                # Dataset documentation
└── requirements.txt          # Python dependencies
```

## Validation and tests

The repository includes backend tests and validation scripts. From the repository root, with dependencies installed, you can try:

```bash
python -m pytest backend/tests
python scripts/validate_data_layer.py
python backend/test_quick_validation.py
```

These commands are provided as starting points; test results may depend on the local environment and configuration. No claim is made that the current repository passes every test or is suitable for production use.

## Limitations and project status

BlockSync remains unfinished. Known limitations include:

- The planned CP-SAT/OR-Tools constraint solver has not been integrated; the active optimizer uses a greedy heuristic.
- Some frontend screens use local mock data rather than a complete API-backed workflow.
- Database seeding and Supabase/PostgreSQL integration require separate configuration and have not been presented here as a verified production setup.
- Gemini explanations require a valid API key and network access; the rule-based fallback is less capable than a live model.
- End-to-end integration, operational validation, security hardening, and deployment configuration are incomplete.
- Scheduling outputs are illustrative and must not be used to make real railway maintenance or safety decisions.

## Possible future work

If development resumes, useful next steps would include:

- Integrate and test a real constraint solver such as OR-Tools CP-SAT.
- Connect dashboard workflows to the backend and replace mock data where appropriate.
- Verify database migrations, seeding, and error handling against a clean environment.
- Expand automated tests for scheduling constraints, conflicts, and failure cases.
- Add deployment configuration, security review, and operational validation.

## License

The backend documentation refers to an MIT license, but a root-level `LICENSE` file was not present in the supplied repository snapshot. Confirm the intended license and add the license file before claiming the entire repository is released under MIT.
