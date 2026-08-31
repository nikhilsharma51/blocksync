"""
BlockSync Database Seeding Script
==================================
Loads synthetic data from JSON files into Supabase.

Usage:
    python -m backend.core.seed_db --verbose

This script:
1. Loads tasks.json, windows.json, conflicts.json from data/
2. Upserts them into Supabase tables
3. Falls back to JSON file storage if Supabase unavailable
"""

import json
import os
import logging
import sys
from pathlib import Path
from typing import Optional

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s — %(levelname)s — %(message)s",
)
logger = logging.getLogger(__name__)

# Paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"


def load_json(filename: str) -> list[dict]:
    """Load a JSON file from data/."""
    path = DATA_DIR / filename
    if not path.exists():
        raise FileNotFoundError(
            f"{path} not found. Run: python scripts/generate_demo_data.py"
        )
    
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def seed_departments() -> int:
    """Ensure departments table has entries."""
    try:
        from backend.core.database import db
        
        if not db.is_available():
            logger.warning("Database not available, skipping departments seeding")
            return 0
        
        depts = [
            {"code": "TRK", "name": "Engineering (Track)", "color_hex": "#F59E0B"},
            {"code": "SNT", "name": "Signal & Telecom (S&T)", "color_hex": "#3B82F6"},
            {"code": "OHE", "name": "Traction (OHE/TRD)", "color_hex": "#10B981"},
        ]
        
        for dept in depts:
            try:
                db.client.table("departments").upsert({
                    "code": dept["code"],
                    "name": dept["name"],
                    "color_hex": dept["color_hex"],
                }).execute()
            except Exception as exc:
                logger.error(f"Failed to insert department {dept['code']}: {exc}")
        
        logger.info(f"✓ Departments seeded ({len(depts)} total)")
        return len(depts)
    
    except Exception as exc:
        logger.error(f"Failed to seed departments: {exc}")
        return 0


def seed_corridors() -> int:
    """Ensure corridors table has entries."""
    try:
        from backend.core.database import db
        
        if not db.is_available():
            logger.warning("Database not available, skipping corridors seeding")
            return 0
        
        corridors = [
            {"code": "NDLS-GZB-UP",   "name": "New Delhi - Ghaziabad (UP Main)",      "traffic_weight": 1.0, "asset_class": "Mainline Trunk"},
            {"code": "NDLS-GZB-DN",   "name": "New Delhi - Ghaziabad (DOWN Main)",    "traffic_weight": 1.0, "asset_class": "Mainline Trunk"},
            {"code": "GZB-ALJN-UP",   "name": "Ghaziabad - Aligarh (UP Main)",        "traffic_weight": 1.0, "asset_class": "Mainline Trunk"},
            {"code": "GZB-ALJN-DN",   "name": "Ghaziabad - Aligarh (DOWN Main)",      "traffic_weight": 1.0, "asset_class": "Mainline Trunk"},
            {"code": "ALJN-TDL-BOTH", "name": "Aligarh - Tundla Junction",            "traffic_weight": 0.9, "asset_class": "Mainline Trunk"},
            {"code": "TDL-CNB-BOTH",  "name": "Tundla - Kanpur Central",              "traffic_weight": 0.9, "asset_class": "Mainline Trunk"},
            {"code": "DLI-RE-SL",     "name": "Delhi - Rewari (Single Line)",         "traffic_weight": 0.7, "asset_class": "Branch Line"},
            {"code": "CNB-YARD",      "name": "Kanpur Central Yard & Loop Lines",     "traffic_weight": 0.3, "asset_class": "Yard/Loop"},
        ]
        
        for corridor in corridors:
            try:
                db.client.table("corridors").upsert({
                    "code": corridor["code"],
                    "name": corridor["name"],
                    "traffic_weight": corridor["traffic_weight"],
                    "asset_class": corridor["asset_class"],
                    "line_type": "UP" if "UP" in corridor["code"] else ("DOWN" if "DN" in corridor["code"] else ("SINGLE" if "SL" in corridor["code"] else "BOTH")),
                }).execute()
            except Exception as exc:
                logger.error(f"Failed to insert corridor {corridor['code']}: {exc}")
        
        logger.info(f"✓ Corridors seeded ({len(corridors)} total)")
        return len(corridors)
    
    except Exception as exc:
        logger.error(f"Failed to seed corridors: {exc}")
        return 0


def seed_tasks(verbose: bool = False) -> int:
    """Load tasks.json into maintenance_tasks table."""
    try:
        from backend.core.database import db
        from backend.core.scoring import calculate_criticality_score_full
        
        if not db.is_available():
            logger.warning("Database not available, skipping tasks seeding")
            return 0
        
        tasks = load_json("tasks.json")
        count = 0
        
        for idx, task in enumerate(tasks):
            try:
                # Enrich with scoring if needed
                if "criticality_score" not in task or task["criticality_score"] is None:
                    result = calculate_criticality_score_full(
                        severity=int(task.get("severity", 1)),
                        days_overdue=int(task.get("days_overdue", 0)),
                        traffic_weight=float(task.get("traffic_weight", 0.6)),
                    )
                    task["criticality_score"] = result.total_score
                    task["priority_level"] = result.priority_level
                
                # Map department code to ID
                dept_map = {"TRK": 1, "SNT": 2, "OHE": 3}
                dept_id = dept_map.get(task.get("department_code", "TRK"), 1)
                
                # Upsert task
                db.client.table("maintenance_tasks").upsert({
                    "id": task["id"],
                    "department_id": dept_id,
                    "corridor_id": task.get("corridor_id", 1),
                    "defect_code": task.get("defect_code"),
                    "defect_type": task.get("defect_type", "Unknown"),
                    "defect_category": task.get("defect_category"),
                    "source_system": task.get("source_system", "TMS"),
                    "description": task.get("description"),
                    "recommended_action": task.get("recommended_action"),
                    "severity": int(task.get("severity", 1)),
                    "days_overdue": int(task.get("days_overdue", 0)),
                    "reported_date": task.get("reported_date"),
                    "est_duration_min": int(task.get("est_duration_min", 120)),
                    "requested_start": task.get("requested_start"),
                    "criticality_score": float(task.get("criticality_score", 0.0)),
                    "score_severity_component": float(task.get("score_severity_component", 0.0)),
                    "score_overdue_component": float(task.get("score_overdue_component", 0.0)),
                    "score_traffic_component": float(task.get("score_traffic_component", 0.0)),
                    "score_formula": task.get("score_formula", ""),
                    "is_compatible_with": task.get("is_compatible_with"),
                    "priority_level": task.get("priority_level", "P2"),
                    "status": task.get("status", "Pending"),
                    "crew_size": task.get("crew_size"),
                    "supervisor": task.get("supervisor"),
                    "required_machine": task.get("required_machine"),
                    "power_disconnection_required": bool(task.get("power_disconnection_required", False)),
                    "speed_restriction_afterwards": task.get("speed_restriction_afterwards"),
                }, match="id").execute()
                
                count += 1
                if verbose and count % 20 == 0:
                    logger.info(f"  ... {count}/{len(tasks)} tasks")
            
            except Exception as exc:
                logger.error(f"Failed to insert task {task.get('id')}: {exc}")
        
        logger.info(f"✓ Tasks seeded ({count}/{len(tasks)} total)")
        return count
    
    except Exception as exc:
        logger.error(f"Failed to seed tasks: {exc}")
        return 0


def seed_windows(verbose: bool = False) -> int:
    """Load windows.json into block_windows table."""
    try:
        from backend.core.database import db
        
        if not db.is_available():
            logger.warning("Database not available, skipping windows seeding")
            return 0
        
        windows = load_json("windows.json")
        count = 0
        
        for idx, window in enumerate(windows):
            try:
                db.client.table("block_windows").upsert({
                    "id": window.get("id"),
                    "corridor_id": int(window.get("corridor_id", 1)),
                    "corridor_code": str(window.get("corridor_code", "")),
                    "corridor_name": str(window.get("corridor_name", "")),
                    "window_label": str(window.get("window_label", "Night Gold Window")),
                    "start_time": str(window.get("start_time")),
                    "end_time": str(window.get("end_time")),
                    "source": str(window.get("source", "COA_Timetable_Gap")),
                    "is_available": bool(window.get("is_available", True)),
                }, match="id").execute()
                
                count += 1
                if verbose and count % 30 == 0:
                    logger.info(f"  ... {count}/{len(windows)} windows")
            
            except Exception as exc:
                logger.error(f"Failed to insert window {window.get('id')}: {exc}")
        
        logger.info(f"✓ Windows seeded ({count}/{len(windows)} total)")
        return count
    
    except Exception as exc:
        logger.error(f"Failed to seed windows: {exc}")
        return 0


def seed_conflicts(verbose: bool = False) -> int:
    """Load conflict_pairs.json into conflict_pairs table."""
    try:
        from backend.core.database import db
        
        if not db.is_available():
            logger.warning("Database not available, skipping conflicts seeding")
            return 0
        
        conflicts = load_json("conflict_pairs.json")
        count = 0
        
        for conflict in conflicts:
            try:
                db.client.table("conflict_pairs").upsert({
                    "id": conflict.get("id"),
                    "task_a_id": conflict.get("task_a_id"),
                    "task_b_id": conflict.get("task_b_id"),
                    "corridor_id": int(conflict.get("corridor_id", 1)),
                    "overlap_start": conflict.get("overlap_start"),
                    "overlap_end": conflict.get("overlap_end"),
                    "overlap_duration_min": int(conflict.get("overlap_duration_min", 0)),
                    "conflict_severity": conflict.get("conflict_severity", "Moderate"),
                    "conflict_type": conflict.get("conflict_type", "Physical Line Occupancy"),
                    "resolution_strategy": conflict.get("resolution_strategy", "Reschedule"),
                }, match="id").execute()
                
                count += 1
            
            except Exception as exc:
                logger.error(f"Failed to insert conflict {conflict.get('id')}: {exc}")
        
        logger.info(f"✓ Conflicts seeded ({count}/{len(conflicts)} total)")
        return count
    
    except Exception as exc:
        logger.error(f"Failed to seed conflicts: {exc}")
        return 0


def main(verbose: bool = False):
    """Seed the entire database."""
    logger.info("=" * 80)
    logger.info("BlockSync Database Seeding Script")
    logger.info("=" * 80)
    
    try:
        # Check if Supabase is available
        try:
            from backend.core.database import db
            if not db.is_available():
                logger.warning(
                    "\n⚠️  Supabase is not configured. To enable database seeding:\n"
                    "   1. Set SUPABASE_URL and SUPABASE_KEY in backend/.env\n"
                    "   2. Ensure the schema exists (run migrations/001_initial_schema.sql)\n"
                    "   3. Run this script again\n"
                )
                return
        except Exception as exc:
            logger.error(f"Failed to initialize database connection: {exc}")
            return
        
        logger.info("\nSeeding lookup tables...")
        seed_departments()
        seed_corridors()
        
        logger.info("\nSeeding main data tables...")
        tasks_count = seed_tasks(verbose)
        windows_count = seed_windows(verbose)
        conflicts_count = seed_conflicts(verbose)
        
        logger.info("\n" + "=" * 80)
        logger.info("✓ Seeding complete!")
        logger.info(f"  - Tasks: {tasks_count}")
        logger.info(f"  - Windows: {windows_count}")
        logger.info(f"  - Conflicts: {conflicts_count}")
        logger.info("=" * 80 + "\n")
    
    except Exception as exc:
        logger.error(f"\n✗ Seeding failed: {exc}\n")
        sys.exit(1)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="BlockSync Database Seeding Script"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output (progress updates)"
    )
    
    args = parser.parse_args()
    main(verbose=args.verbose)
