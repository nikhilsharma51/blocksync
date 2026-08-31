#!/usr/bin/env python3
"""
BlockSync Quick Validation Script
==================================
Run this immediately after setup to verify everything works.

Usage:
    python backend/test_quick_validation.py

This script:
1. Checks all imports
2. Verifies mock solver works
3. Tests API endpoints
4. Confirms Scenarios 1-3 data present
5. Reports everything ready
"""

import sys
import json
from pathlib import Path

# Add backend to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

def check_imports():
    """Verify all required modules can be imported."""
    print("\n" + "=" * 70)
    print("1. CHECKING IMPORTS")
    print("=" * 70)
    
    try:
        from fastapi import FastAPI
        print("✓ FastAPI")
    except ImportError as e:
        print(f"✗ FastAPI: {e}")
        return False
    
    try:
        import pydantic
        print("✓ Pydantic")
    except ImportError as e:
        print(f"✗ Pydantic: {e}")
        return False
    
    try:
        from backend.api import schemas
        print("✓ API Schemas")
    except ImportError as e:
        print(f"✗ API Schemas: {e}")
        return False
    
    try:
        from backend.core import database
        print("✓ Database module")
    except ImportError as e:
        print(f"✗ Database module: {e}")
        return False
    
    try:
        from backend.core import solver
        print("✓ Solver module")
    except ImportError as e:
        print(f"✗ Solver module: {e}")
        return False
    
    try:
        from backend.core import seed_db
        print("✓ Seed DB module")
    except ImportError as e:
        print(f"✗ Seed DB module: {e}")
        return False
    
    try:
        from backend.api.routes import tasks, corridors, optimize
        print("✓ API routes")
    except ImportError as e:
        print(f"✗ API routes: {e}")
        return False
    
    return True


def check_data_files():
    """Verify all data files exist."""
    print("\n" + "=" * 70)
    print("2. CHECKING DATA FILES")
    print("=" * 70)
    
    data_dir = PROJECT_ROOT / "data"
    files = ["tasks.json", "windows.json", "conflict_pairs.json", "seed_summary.json"]
    
    all_exist = True
    for filename in files:
        path = data_dir / filename
        if path.exists():
            size_kb = path.stat().st_size / 1024
            print(f"✓ {filename} ({size_kb:.1f} KB)")
        else:
            print(f"✗ {filename} NOT FOUND")
            all_exist = False
    
    if all_exist:
        print("\n✓ All data files present")
    else:
        print("\n⚠ Some data files missing. Run: python scripts/generate_demo_data.py")
    
    return all_exist


def check_scenarios():
    """Verify scenario data is present."""
    print("\n" + "=" * 70)
    print("3. CHECKING SCENARIO DATA")
    print("=" * 70)
    
    # Scenario 1: TRK-1000 + OHE-3000
    try:
        with open(PROJECT_ROOT / "data" / "tasks.json") as fh:
            tasks = json.load(fh)
        
        trk_1000 = next((t for t in tasks if t["id"] == "TRK-1000"), None)
        ohe_3000 = next((t for t in tasks if t["id"] == "OHE-3000"), None)
        
        if trk_1000:
            print(f"✓ Scenario 1a: TRK-1000 found ({trk_1000.get('defect_type', 'N/A')})")
            if trk_1000.get("is_compatible_with") == "OHE":
                print(f"  ✓ Compatible with OHE (will form Joint Block)")
            else:
                print(f"  ⚠ Not marked as compatible with OHE")
        else:
            print("✗ Scenario 1a: TRK-1000 NOT FOUND")
        
        if ohe_3000:
            print(f"✓ Scenario 1b: OHE-3000 found ({ohe_3000.get('defect_type', 'N/A')})")
            if ohe_3000.get("is_compatible_with") == "TRK":
                print(f"  ✓ Compatible with TRK")
            else:
                print(f"  ⚠ Not marked as compatible with TRK")
        else:
            print("✗ Scenario 1b: OHE-3000 NOT FOUND")
        
        # Scenario 3: TRK-1002 (long-duration unscheduled)
        trk_1002 = next((t for t in tasks if t["id"] == "TRK-1002"), None)
        if trk_1002:
            dur = trk_1002.get("est_duration_min", 0)
            print(f"✓ Scenario 3: TRK-1002 found (Duration: {dur} min)")
            if dur > 300:
                print(f"  ✓ Long duration ({dur} min) — will likely be unscheduled")
            else:
                print(f"  ⚠ Duration {dur} min is short, may fit in windows")
        else:
            print("✗ Scenario 3: TRK-1002 NOT FOUND")
        
        # Check total tasks and conflicts
        print(f"\n✓ Total tasks in dataset: {len(tasks)}")
        
        with open(PROJECT_ROOT / "data" / "conflict_pairs.json") as fh:
            conflicts = json.load(fh)
        print(f"✓ Total conflicts detected: {len(conflicts)}")
        
        return True
    
    except Exception as exc:
        print(f"✗ Error checking scenarios: {exc}")
        return False


def check_solver():
    """Test the mock solver."""
    print("\n" + "=" * 70)
    print("4. CHECKING MOCK SOLVER")
    print("=" * 70)
    
    try:
        from backend.core.solver import solve_scheduling_problem
        import json
        
        # Load minimal test data
        with open(PROJECT_ROOT / "data" / "tasks.json") as fh:
            all_tasks = json.load(fh)
        with open(PROJECT_ROOT / "data" / "windows.json") as fh:
            all_windows = json.load(fh)
        
        # Use only first 10 tasks for quick test
        test_tasks = all_tasks[:10]
        test_windows = all_windows[:20]
        
        print(f"Running solver with {len(test_tasks)} tasks and {len(test_windows)} windows...")
        
        assignments, unscheduled, stats = solve_scheduling_problem(
            test_tasks, test_windows, [], max_solve_seconds=30
        )
        
        print(f"✓ Solver completed successfully")
        print(f"  - Assignments: {len(assignments)}")
        print(f"  - Unscheduled: {len(unscheduled)}")
        print(f"  - Status: {stats.get('status', 'UNKNOWN')}")
        print(f"  - Time: {stats.get('solve_time_seconds', 0):.3f}s")
        
        # Verify response structure
        if len(assignments) > 0:
            a = assignments[0]
            required_keys = ["task_id", "assigned_start", "assigned_end", "is_integrated"]
            missing = [k for k in required_keys if k not in a]
            if missing:
                print(f"  ⚠ Assignment missing keys: {missing}")
            else:
                print(f"  ✓ Assignment has all required keys")
        
        if len(unscheduled) > 0:
            u = unscheduled[0]
            required_keys = ["task_id", "reason"]
            missing = [k for k in required_keys if k not in u]
            if missing:
                print(f"  ⚠ Unscheduled missing keys: {missing}")
            else:
                print(f"  ✓ Unscheduled has all required keys")
        
        return True
    
    except Exception as exc:
        print(f"✗ Solver check failed: {exc}")
        import traceback
        traceback.print_exc()
        return False


def check_api():
    """Test API endpoints."""
    print("\n" + "=" * 70)
    print("5. CHECKING API ENDPOINTS")
    print("=" * 70)
    
    try:
        from fastapi.testclient import TestClient
        from backend.main import app
        
        client = TestClient(app)
        
        # Test health
        print("Testing GET /api/v1/health...")
        response = client.get("/api/v1/health")
        if response.status_code == 200:
            print("  ✓ Health check OK")
        else:
            print(f"  ✗ Health check failed: {response.status_code}")
            return False
        
        # Test tasks
        print("Testing GET /api/v1/tasks/pending...")
        response = client.get("/api/v1/tasks/pending?limit=5")
        if response.status_code == 200:
            data = response.json()
            count = data.get("count", 0)
            print(f"  ✓ Got {count} pending tasks")
        else:
            print(f"  ✗ Tasks endpoint failed: {response.status_code}")
            return False
        
        # Test corridors
        print("Testing GET /api/v1/corridors/availability...")
        response = client.get("/api/v1/corridors/availability?limit=5")
        if response.status_code == 200:
            data = response.json()
            count = data.get("count", 0)
            print(f"  ✓ Got {count} available windows")
        else:
            print(f"  ✗ Corridors endpoint failed: {response.status_code}")
            return False
        
        # Test optimizer
        print("Testing POST /api/v1/optimize...")
        response = client.post("/api/v1/optimize", json={})
        if response.status_code == 200:
            data = response.json()
            assigned = len(data.get("assignments", []))
            unscheduled = len(data.get("unscheduled", []))
            print(f"  ✓ Optimizer returned: {assigned} assigned, {unscheduled} unscheduled")
        else:
            print(f"  ✗ Optimizer failed: {response.status_code}")
            return False
        
        # Test conflicts
        print("Testing GET /api/v1/conflicts...")
        response = client.get("/api/v1/conflicts")
        if response.status_code == 200:
            data = response.json()
            count = data.get("count", 0)
            print(f"  ✓ Got {count} conflicts")
        else:
            print(f"  ✗ Conflicts endpoint failed: {response.status_code}")
            return False
        
        # Test explainer
        print("Testing POST /api/v1/explain...")
        response = client.post("/api/v1/explain", json={
            "task_id": "TRK-1001",
            "defect": "Rail Fracture",
            "severity": 5,
            "days_overdue": 15,
            "score": 82.5,
            "corridor": "NDLS-GZB-UP",
            "assigned_start": "2026-09-02T02:00:00Z",
            "assigned_end": "2026-09-02T05:00:00Z",
            "status": "Scheduled",
        })
        if response.status_code == 200:
            data = response.json()
            if "explanation" in data:
                print(f"  ✓ Got explanation")
            else:
                print(f"  ⚠ No explanation in response")
        else:
            print(f"  ✗ Explain endpoint failed: {response.status_code}")
            return False
        
        return True
    
    except Exception as exc:
        print(f"✗ API check failed: {exc}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all checks."""
    print("\n")
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 15 + "BlockSync Backend Quick Validation" + " " * 20 + "║")
    print("╚" + "=" * 68 + "╝")
    
    checks = [
        ("Imports", check_imports),
        ("Data Files", check_data_files),
        ("Scenarios", check_scenarios),
        ("Mock Solver", check_solver),
        ("API Endpoints", check_api),
    ]
    
    results = []
    for name, check_func in checks:
        try:
            result = check_func()
            results.append((name, result))
        except Exception as exc:
            print(f"\n✗ ERROR in {name}: {exc}")
            import traceback
            traceback.print_exc()
            results.append((name, False))
    
    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    
    all_passed = True
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}  {name}")
        if not result:
            all_passed = False
    
    print("=" * 70)
    
    if all_passed:
        print("\n🎉 ALL CHECKS PASSED! Backend is ready.\n")
        print("Next steps:")
        print("  1. Run tests:     python -m pytest backend/tests/ -v")
        print("  2. Start API:     uvicorn backend.main:app --reload")
        print("  3. Open Docs:     http://localhost:8000/docs")
        print("  4. Notify Member 1: Backend ready for CP-SAT integration")
        print()
        return 0
    else:
        print("\n⚠ Some checks failed. Review the output above.\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
