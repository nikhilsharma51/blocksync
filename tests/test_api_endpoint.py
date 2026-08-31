"""
tests/test_api_endpoint.py
==========================
Tests the FastAPI /api/v1/optimize and /api/v1/health endpoints with CP-SAT solver.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient
from backend.main import app


def test_api_optimize():
    client = TestClient(app)

    # 1. Health check
    health_resp = client.get("/api/v1/health")
    assert health_resp.status_code == 200, f"Health check failed: {health_resp.text}"
    print(f"[PASS] Health check: {health_resp.json()}")

    # 2. Run optimizer endpoint
    payload = {"max_solve_seconds": 15}
    opt_resp = client.post("/api/v1/optimize", json=payload)
    assert opt_resp.status_code == 200, f"Optimize endpoint failed: {opt_resp.text}"

    data = opt_resp.json()
    assert data["status"] == "success"
    assert "plan_id" in data
    assert len(data["assignments"]) > 0
    assert len(data["unscheduled"]) > 0
    assert data["solver_stats"]["status"] in ("OPTIMAL", "FEASIBLE")

    print(f"[PASS] Plan ID: {data['plan_id']}")
    print(f"[PASS] Total assignments: {len(data['assignments'])}")
    print(f"[PASS] Total unscheduled: {len(data['unscheduled'])}")
    print(f"[PASS] Joint blocks formed: {data['solver_stats']['joint_blocks_formed']}")
    print(f"[PASS] Downtime saved (hours): {data['solver_stats']['downtime_saved_hours']}")
    print(f"[PASS] Conflicts resolved: {data['solver_stats']['conflicts_resolved']}")

    print("\n[SUCCESS] FastAPI endpoint tests passed completely!")


if __name__ == "__main__":
    test_api_optimize()
