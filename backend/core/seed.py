"""
backend/core/seed.py
=====================
BlockSync Supabase / PostgreSQL Seed Loader
Branch: hriday-dataset | Author: Hriday

Reads the generated JSON files (data/tasks.json, data/windows.json) and
inserts them into the Supabase (PostgreSQL) database.

Prerequisites:
  1. Run migrations/001_initial_schema.sql in Supabase SQL editor first
  2. Set environment variables:
        SUPABASE_URL      = https://xxxx.supabase.co
        SUPABASE_KEY      = your-service-role-key   (NOT the anon key)
     OR for direct psycopg2:
        DATABASE_URL      = postgresql://user:pass@host:5432/dbname

Usage:
    # Via Supabase REST client (recommended for SIH demo):
    python -m backend.core.seed

    # Dry run (validate only, no DB writes):
    python -m backend.core.seed --dry-run

    # Re-seed (truncates existing data first):
    python -m backend.core.seed --reset
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone

# Allow running from repo root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from backend.core.validator import audit_dataset

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data")


# ---------------------------------------------------------------------------
# Data loaders
# ---------------------------------------------------------------------------

def load_dataset() -> tuple[list[dict], list[dict], list[dict]]:
    """Load tasks, windows, and conflicts from data/. Raises if files missing."""
    def _load(name: str) -> list[dict]:
        path = os.path.join(DATA_DIR, name)
        if not os.path.exists(path):
            raise FileNotFoundError(
                f"{name} not found. Run: python scripts/generate_demo_data.py"
            )
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)

    return _load("tasks.json"), _load("windows.json"), _load("conflict_pairs.json")


# ---------------------------------------------------------------------------
# Supabase REST seeder (uses supabase-py client)
# ---------------------------------------------------------------------------

def seed_via_supabase(tasks: list[dict], windows: list[dict], conflicts: list[dict], reset: bool = False) -> None:
    """
    Insert data using the supabase-py client.
    Requires SUPABASE_URL and SUPABASE_KEY environment variables.
    """
    try:
        from supabase import create_client, Client  # type: ignore
    except ImportError:
        print("ERROR: supabase package not installed. Run: pip install supabase==2.10.0")
        sys.exit(1)

    url = os.environ.get("SUPABASE_URL", "").strip()
    key = os.environ.get("SUPABASE_KEY", "").strip()

    if not url or not key:
        print("ERROR: SUPABASE_URL and SUPABASE_KEY environment variables must be set.")
        print("  Copy .env.example to .env and fill in your credentials.")
        sys.exit(1)

    print(f"Connecting to Supabase: {url[:40]}...")
    client: Client = create_client(url, key)

    if reset:
        print("Resetting tables (truncate)...")
        for table in ["block_assignments", "unscheduled_tasks", "conflict_pairs",
                       "maintenance_tasks", "block_windows", "corridors", "departments"]:
            try:
                client.table(table).delete().neq("id", -999999).execute()
                print(f"  Cleared {table}")
            except Exception as e:
                print(f"  Could not clear {table}: {e}")

    # --- Seed block_windows ---
    print(f"Inserting {len(windows)} block windows...")
    window_rows = []
    for w in windows:
        window_rows.append({
            "id":           w["id"],
            "corridor_id":  w["corridor_id"],
            "window_label": w.get("window_label", "Night Gold Window"),
            "start_time":   w["start_time"],
            "end_time":     w["end_time"],
            "source":       w.get("source", "COA_Timetable_Gap"),
            "is_available": w.get("is_available", True),
        })
    _batch_upsert(client, "block_windows", window_rows, batch_size=50)
    print(f"  ✓ {len(window_rows)} windows inserted")

    # --- Seed maintenance_tasks ---
    print(f"Inserting {len(tasks)} maintenance tasks...")
    task_rows = []
    for t in tasks:
        task_rows.append({
            "id":                    t["id"],
            "department_id":         t["department_id"],
            "corridor_id":           t["corridor_id"],
            "defect_code":           t.get("defect_code"),
            "defect_type":           t["defect_type"],
            "defect_category":       t.get("defect_category"),
            "source_system":         t.get("source_system", "TMS"),
            "description":           t.get("description"),
            "recommended_action":    t.get("recommended_action"),
            "severity":              t["severity"],
            "days_overdue":          t["days_overdue"],
            "reported_date":         t.get("reported_date"),
            "est_duration_min":      t["est_duration_min"],
            "requested_start":       t.get("requested_start"),
            "criticality_score":     t.get("criticality_score"),
            "score_severity_component": t.get("score_severity_component"),
            "score_overdue_component":  t.get("score_overdue_component"),
            "score_traffic_component":  t.get("score_traffic_component"),
            "score_formula":         t.get("score_formula"),
            "is_compatible_with":    t.get("is_compatible_with"),
            "priority_level":        t.get("priority_level", "P1"),
            "status":                t.get("status", "Pending"),
            "crew_size":             t.get("crew_size"),
            "supervisor":            t.get("supervisor"),
            "required_machine":      t.get("required_machine"),
            "power_disconnection_required": t.get("power_disconnection_required", False),
            "speed_restriction_afterwards": t.get("speed_restriction_afterwards"),
        })
    _batch_upsert(client, "maintenance_tasks", task_rows, batch_size=50)
    print(f"  ✓ {len(task_rows)} tasks inserted")

    # --- Seed conflict_pairs ---
    print(f"Inserting {len(conflicts)} conflict pairs...")
    conflict_rows = []
    for c in conflicts:
        conflict_rows.append({
            "task_a_id":            c["task_a_id"],
            "task_b_id":            c["task_b_id"],
            "corridor_id":          c["corridor_id"],
            "overlap_start":        c["overlap_start"],
            "overlap_end":          c["overlap_end"],
            "overlap_duration_min": c["overlap_duration_min"],
            "conflict_severity":    c["conflict_severity"],
            "conflict_type":        c["conflict_type"],
            "resolution_strategy":  c.get("resolution_strategy"),
        })
    if conflict_rows:
        _batch_upsert(client, "conflict_pairs", conflict_rows, batch_size=50)
    print(f"  ✓ {len(conflict_rows)} conflict pairs inserted")

    print("\n✓ Supabase seed complete.")


def _batch_upsert(client, table: str, rows: list[dict], batch_size: int = 50) -> None:
    """Insert rows in batches to avoid Supabase request size limits."""
    for i in range(0, len(rows), batch_size):
        batch = rows[i : i + batch_size]
        try:
            client.table(table).upsert(batch).execute()
        except Exception as e:
            print(f"  ERROR batch {i//batch_size + 1} on {table}: {e}")
            raise


# ---------------------------------------------------------------------------
# psycopg2 seeder (direct PostgreSQL — alternative to Supabase client)
# ---------------------------------------------------------------------------

def seed_via_psycopg2(tasks: list[dict], windows: list[dict], conflicts: list[dict], reset: bool = False) -> None:
    """
    Insert data using psycopg2 directly.
    Requires DATABASE_URL environment variable.
    """
    try:
        import psycopg2                          # type: ignore
        import psycopg2.extras as extras         # type: ignore
    except ImportError:
        print("ERROR: psycopg2 package not installed. Run: pip install psycopg2-binary==2.9.10")
        sys.exit(1)

    db_url = os.environ.get("DATABASE_URL", "").strip()
    if not db_url:
        print("ERROR: DATABASE_URL environment variable must be set.")
        sys.exit(1)

    print(f"Connecting via psycopg2...")
    conn = psycopg2.connect(db_url)
    cur  = conn.cursor()

    try:
        if reset:
            print("Truncating tables...")
            cur.execute("""
                TRUNCATE block_assignments, unscheduled_tasks, conflict_pairs,
                         maintenance_tasks, block_windows
                RESTART IDENTITY CASCADE
            """)
            conn.commit()
            print("  ✓ Tables cleared")

        # Insert block_windows
        print(f"Inserting {len(windows)} windows...")
        window_data = [
            (
                w["id"], w["corridor_id"], w.get("window_label", "Night Gold Window"),
                w["start_time"], w["end_time"], w.get("source", "COA_Timetable_Gap"),
                w.get("is_available", True),
            )
            for w in windows
        ]
        extras.execute_values(cur, """
            INSERT INTO block_windows (id, corridor_id, window_label, start_time, end_time, source, is_available)
            VALUES %s
            ON CONFLICT (id) DO NOTHING
        """, window_data)

        # Insert maintenance_tasks
        print(f"Inserting {len(tasks)} tasks...")
        task_data = [
            (
                t["id"], t["department_id"], t["corridor_id"],
                t.get("defect_code"), t["defect_type"], t.get("defect_category"),
                t.get("source_system", "TMS"), t.get("description"), t.get("recommended_action"),
                t["severity"], t["days_overdue"], t.get("reported_date"),
                t["est_duration_min"], t.get("requested_start"),
                t.get("criticality_score"), t.get("score_severity_component"),
                t.get("score_overdue_component"), t.get("score_traffic_component"),
                t.get("score_formula"), t.get("is_compatible_with"),
                t.get("priority_level", "P1"), t.get("status", "Pending"),
                t.get("crew_size"), t.get("supervisor"), t.get("required_machine"),
                t.get("power_disconnection_required", False), t.get("speed_restriction_afterwards"),
            )
            for t in tasks
        ]
        extras.execute_values(cur, """
            INSERT INTO maintenance_tasks (
                id, department_id, corridor_id, defect_code, defect_type, defect_category,
                source_system, description, recommended_action, severity, days_overdue,
                reported_date, est_duration_min, requested_start, criticality_score,
                score_severity_component, score_overdue_component, score_traffic_component,
                score_formula, is_compatible_with, priority_level, status,
                crew_size, supervisor, required_machine, power_disconnection_required,
                speed_restriction_afterwards
            ) VALUES %s
            ON CONFLICT (id) DO NOTHING
        """, task_data)

        # Insert conflict pairs
        if conflicts:
            print(f"Inserting {len(conflicts)} conflict pairs...")
            conflict_data = [
                (
                    c["task_a_id"], c["task_b_id"], c["corridor_id"],
                    c["overlap_start"], c["overlap_end"], c["overlap_duration_min"],
                    c["conflict_severity"], c["conflict_type"], c.get("resolution_strategy"),
                )
                for c in conflicts
            ]
            extras.execute_values(cur, """
                INSERT INTO conflict_pairs (
                    task_a_id, task_b_id, corridor_id,
                    overlap_start, overlap_end, overlap_duration_min,
                    conflict_severity, conflict_type, resolution_strategy
                ) VALUES %s
                ON CONFLICT DO NOTHING
            """, conflict_data)

        conn.commit()
        print("\n✓ psycopg2 seed complete.")

    except Exception as e:
        conn.rollback()
        print(f"ERROR during seeding: {e}")
        raise
    finally:
        cur.close()
        conn.close()


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="BlockSync Database Seed Loader")
    parser.add_argument("--dry-run", action="store_true", help="Validate only — do not write to DB")
    parser.add_argument("--reset",   action="store_true", help="Truncate existing data before seeding")
    parser.add_argument("--method",  choices=["supabase", "psycopg2", "auto"], default="auto",
                        help="Connection method (default: auto-detect from env vars)")
    args = parser.parse_args()

    print("BlockSync Database Seed Loader")
    print("=" * 50)

    # Load data
    print("Loading dataset...")
    tasks, windows, conflicts = load_dataset()
    print(f"  {len(tasks)} tasks, {len(windows)} windows, {len(conflicts)} conflict pairs loaded.")

    # Validate
    print("Validating...")
    task_report, window_report = audit_dataset(tasks, windows)

    if task_report.invalid > 0:
        print(f"WARNING: {task_report.invalid} tasks failed validation. Failed IDs: {task_report.failed_ids[:5]}")
        if not args.dry_run:
            response = input("Continue seeding with validation errors? [y/N]: ")
            if response.lower() != "y":
                print("Aborted.")
                sys.exit(1)

    if args.dry_run:
        print("\n[DRY RUN] Validation complete. No data written to database.")
        return

    # Determine connection method
    method = args.method
    if method == "auto":
        if os.environ.get("SUPABASE_URL"):
            method = "supabase"
        elif os.environ.get("DATABASE_URL"):
            method = "psycopg2"
        else:
            print(
                "ERROR: Neither SUPABASE_URL nor DATABASE_URL is set.\n"
                "Set one of them before running the seed loader.\n"
                "Copy .env.example → .env and fill in credentials."
            )
            sys.exit(1)

    print(f"\nUsing connection method: {method}")
    if method == "supabase":
        seed_via_supabase(tasks, windows, conflicts, reset=args.reset)
    else:
        seed_via_psycopg2(tasks, windows, conflicts, reset=args.reset)


if __name__ == "__main__":
    main()
