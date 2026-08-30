"""
backend/main.py
================
BlockSync FastAPI Application Entry Point
Branch: hriday-dataset | Author: Hriday

Start the server:
    uvicorn backend.main:app --reload --port 8000

Interactive docs:
    http://localhost:8000/docs      (Swagger UI)
    http://localhost:8000/redoc     (ReDoc)

All routes:
    GET  /api/v1/tasks/pending              → Conflict Gantt data
    GET  /api/v1/tasks/{task_id}            → Single task detail
    GET  /api/v1/tasks                      → All tasks
    GET  /api/v1/corridors                  → Corridor metadata
    GET  /api/v1/corridors/availability     → COA windows for optimizer
    GET  /api/v1/corridors/{code}/windows   → Windows for one corridor
    POST /api/v1/optimize                   → Run scheduler
    GET  /api/v1/conflicts                  → Pre-detected conflicts
    POST /api/v1/explain                    → Gemini AI explanation
    GET  /api/v1/health                     → Health check + dataset stats
"""

from __future__ import annotations

import json
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.routes import tasks as tasks_router
from backend.api.routes import corridors as corridors_router
from backend.api.routes import optimize as optimize_router
from backend.api.schemas import HealthResponse

# ---------------------------------------------------------------------------
# App instance
# ---------------------------------------------------------------------------

app = FastAPI(
    title="BlockSync Data & Optimization API",
    description=(
        "Indian Railways Maintenance Block Scheduling System — Data Layer.\n\n"
        "Provides the dataset, scoring engine, and greedy optimizer for the "
        "SIH 2026 BlockSync demo. The `/optimize` endpoint implements the "
        "priority-based scheduler; plug in OR-Tools CP-SAT as a drop-in "
        "replacement in `backend/api/routes/optimize.py`.\n\n"
        "**Branch:** `hriday-dataset` | **Author:** Hriday (Data & Pitch Lead)"
    ),
    version="0.1.0",
    contact={
        "name": "Hriday — BlockSync Data Layer",
        "url":  "https://github.com/nikhilsharma51/blocksync",
    },
    license_info={
        "name": "MIT",
    },
)

# ---------------------------------------------------------------------------
# CORS — allow the Next.js frontend on localhost:3000 during development
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",   # Next.js dev server
        "http://localhost:3001",
        "https://blocksync.vercel.app",   # Production (update when deployed)
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------

API_PREFIX = "/api/v1"

app.include_router(tasks_router.router,     prefix=API_PREFIX)
app.include_router(corridors_router.router, prefix=API_PREFIX)
app.include_router(optimize_router.router,  prefix=API_PREFIX)

# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


@app.get(
    "/api/v1/health",
    response_model=HealthResponse,
    tags=["Health"],
    summary="API health check and dataset statistics",
)
def health_check() -> HealthResponse:
    dataset_stats: dict = {}
    try:
        summary_path = os.path.join(DATA_DIR, "seed_summary.json")
        if os.path.exists(summary_path):
            with open(summary_path, encoding="utf-8") as fh:
                summary = json.load(fh)
            dataset_stats = {
                "total_tasks":     summary.get("total_tasks", 0),
                "total_windows":   summary.get("total_windows", 0),
                "total_conflicts": summary.get("total_conflicts", 0),
                "score_min":       summary.get("score_min", 0),
                "score_max":       summary.get("score_max", 0),
                "score_avg":       summary.get("score_avg", 0),
                "generated_at":    summary.get("generated_at", ""),
            }
    except Exception:
        dataset_stats = {"error": "Could not load seed_summary.json"}

    return HealthResponse(
        status  = "ok",
        version = "0.1.0",
        dataset = dataset_stats,
    )


@app.get("/", include_in_schema=False)
def root():
    return {
        "message": "BlockSync API is running.",
        "docs":    "/docs",
        "health":  "/api/v1/health",
    }
