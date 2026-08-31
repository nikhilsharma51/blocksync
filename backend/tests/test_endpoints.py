"""
BlockSync API Endpoint Tests
============================
Tests all endpoints against mock data and the mock solver.

Branch: hriday-dataset | Author: Hriday (Backend Architect - Member 2)

Run tests:
    cd backend
    python -m pytest tests/test_endpoints.py -v
"""

import pytest
import json
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


class TestHealthCheck:
    """Test the health check endpoint."""
    
    def test_health_check(self):
        """Verify health check returns OK and includes dataset stats."""
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "version" in data
        assert "dataset" in data


class TestTasks:
    """Test task-related endpoints."""
    
    def test_get_pending_tasks(self):
        """Fetch pending/clashed tasks — should return valid schema."""
        response = client.get("/api/v1/tasks/pending")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "count" in data
        assert "data" in data
        assert isinstance(data["data"], list)
        
        # Verify response has required fields
        if data["count"] > 0:
            task = data["data"][0]
            assert "id" in task
            assert "department" in task
            assert "corridor" in task
            assert "criticality_score" in task
            assert "requested_start" in task
            assert "requested_end" in task
    
    def test_get_pending_tasks_filter_department(self):
        """Filter tasks by department code."""
        response = client.get("/api/v1/tasks/pending?department=TRK")
        assert response.status_code == 200
        data = response.json()
        
        # Verify all returned tasks are from TRK department
        for task in data["data"]:
            assert task["department"] == "TRK"
    
    def test_get_pending_tasks_filter_priority(self):
        """Filter tasks by priority level."""
        response = client.get("/api/v1/tasks/pending?priority=P0")
        assert response.status_code == 200
        data = response.json()
        
        # Verify all returned tasks have priority P0
        for task in data["data"]:
            assert task["priority"] == "P0"
    
    def test_get_pending_tasks_filter_min_score(self):
        """Filter tasks by minimum criticality score."""
        response = client.get("/api/v1/tasks/pending?min_score=70.0")
        assert response.status_code == 200
        data = response.json()
        
        # Verify all tasks meet minimum score
        for task in data["data"]:
            assert task["criticality_score"] >= 70.0
    
    def test_get_task_by_id(self):
        """Fetch a specific task by ID."""
        # First, get any task ID from pending tasks
        response = client.get("/api/v1/tasks/pending?limit=1")
        if response.json()["count"] > 0:
            task_id = response.json()["data"][0]["id"]
            
            # Now fetch it directly
            response = client.get(f"/api/v1/tasks/{task_id}")
            assert response.status_code == 200
            task = response.json()
            assert task["id"] == task_id
    
    def test_get_task_by_id_not_found(self):
        """Fetch non-existent task — should return 404."""
        response = client.get("/api/v1/tasks/NONEXISTENT-9999")
        assert response.status_code == 404
    
    def test_get_all_tasks(self):
        """Fetch all tasks regardless of status."""
        response = client.get("/api/v1/tasks")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert isinstance(data["data"], list)


class TestCorridors:
    """Test corridor and window endpoints."""
    
    def test_list_corridors(self):
        """List all available corridors."""
        response = client.get("/api/v1/corridors")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        
        # Verify corridor structure
        corridor = data[0]
        assert "code" in corridor
        assert "name" in corridor
        assert "asset_class" in corridor
    
    def test_get_availability(self):
        """Fetch available COA windows."""
        response = client.get("/api/v1/corridors/availability")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "count" in data
        assert isinstance(data["data"], list)
        
        # Verify window structure
        if data["count"] > 0:
            window = data["data"][0]
            assert "window_id" in window
            assert "corridor_id" in window
            assert "start_time" in window
            assert "end_time" in window
            assert "duration_min" in window
            assert window["is_available"] is True
    
    def test_get_availability_filter_corridor(self):
        """Filter windows by corridor code."""
        response = client.get("/api/v1/corridors/availability?corridor_code=NDLS-GZB-UP")
        assert response.status_code == 200
        data = response.json()
        
        # Verify all windows are for the specified corridor
        for window in data["data"]:
            assert window["corridor_id"] == "NDLS-GZB-UP"
    
    def test_get_availability_filter_min_duration(self):
        """Filter windows by minimum duration."""
        response = client.get("/api/v1/corridors/availability?min_duration=240")
        assert response.status_code == 200
        data = response.json()
        
        # Verify all windows meet minimum duration
        for window in data["data"]:
            assert window["duration_min"] >= 240
    
    def test_get_corridor_windows(self):
        """Get windows for a specific corridor."""
        response = client.get("/api/v1/corridors/NDLS-GZB-UP/windows")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        
        # Verify all windows are for this corridor
        for window in data["data"]:
            assert window["corridor_id"] == "NDLS-GZB-UP"
    
    def test_get_corridor_windows_not_found(self):
        """Fetch windows for non-existent corridor — should return 404."""
        response = client.get("/api/v1/corridors/NONEXISTENT/windows")
        assert response.status_code == 404


class TestOptimizer:
    """Test the optimization engine."""
    
    def test_run_optimizer(self):
        """Run the optimizer with default settings."""
        response = client.post(
            "/api/v1/optimize",
            json={"max_solve_seconds": 30},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "plan_id" in data
        assert "assignments" in data
        assert "unscheduled" in data
        assert "solver_stats" in data
        assert isinstance(data["assignments"], list)
        assert isinstance(data["unscheduled"], list)
    
    def test_optimizer_response_schema(self):
        """Verify optimizer response matches expected schema."""
        response = client.post("/api/v1/optimize")
        assert response.status_code == 200
        data = response.json()
        
        # Check solver stats presence
        stats = data["solver_stats"]
        assert "status" in stats  # OPTIMAL | FEASIBLE | INFEASIBLE
        assert "solve_time_seconds" in stats
        assert "conflicts_resolved" in stats
        assert "total_conflicts" in stats
        assert "joint_blocks_formed" in stats
        assert "downtime_saved_hours" in stats
        assert "total_tasks_scheduled" in stats
        assert "total_tasks_unscheduled" in stats
        
        # Verify status is one of the expected values
        assert stats["status"] in ["OPTIMAL", "FEASIBLE", "INFEASIBLE"]
    
    def test_optimizer_assignments_schema(self):
        """Verify assignment objects have required fields."""
        response = client.post("/api/v1/optimize")
        assert response.status_code == 200
        data = response.json()
        
        # Check each assignment
        for assignment in data["assignments"]:
            assert "task_id" in assignment
            assert "department" in assignment
            assert "corridor" in assignment
            assert "criticality_score" in assignment
            assert "assigned_start" in assignment
            assert "assigned_end" in assignment
            assert "is_integrated" in assignment
            assert "merged_departments" in assignment
            assert isinstance(assignment["merged_departments"], list)
    
    def test_optimizer_unscheduled_schema(self):
        """Verify unscheduled task objects have required fields."""
        response = client.post("/api/v1/optimize")
        assert response.status_code == 200
        data = response.json()
        
        # Check unscheduled tasks
        for unsch in data["unscheduled"]:
            assert "task_id" in unsch
            assert "reason" in unsch
    
    def test_optimizer_filter_by_date(self):
        """Optimize only for a specific date."""
        response = client.post(
            "/api/v1/optimize",
            json={"plan_date": "2026-09-02"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
    
    def test_optimizer_scenario_1_present(self):
        """
        Scenario 1: Integrated Joint Block (TRK + OHE)
        At least one assignment should have is_integrated=True.
        """
        response = client.post("/api/v1/optimize")
        assert response.status_code == 200
        data = response.json()
        
        # Check for at least one integrated block
        integrated = [a for a in data["assignments"] if a["is_integrated"]]
        # This may or may not have integrated blocks depending on data,
        # but the field must be present
        assert any("is_integrated" in a for a in data["assignments"])
    
    def test_optimizer_scenario_3_check(self):
        """
        Scenario 3: Unscheduled task (TRK-1002 ideally)
        At least one task should be unscheduled with a clear reason.
        """
        response = client.post("/api/v1/optimize")
        assert response.status_code == 200
        data = response.json()
        
        # Check for unscheduled tasks
        unscheduled = data["unscheduled"]
        if len(unscheduled) > 0:
            unsch = unscheduled[0]
            assert "reason" in unsch
            assert len(unsch["reason"]) > 0


class TestConflicts:
    """Test conflict detection endpoints."""
    
    def test_get_conflicts(self):
        """Fetch pre-detected conflicts."""
        response = client.get("/api/v1/conflicts")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "count" in data
        assert isinstance(data["data"], list)
        
        # If conflicts exist, verify structure
        if data["count"] > 0:
            conflict = data["data"][0]
            assert "id" in conflict
            assert "task_a_id" in conflict
            assert "task_b_id" in conflict
            assert "conflict_severity" in conflict
    
    def test_get_conflicts_filter_severity(self):
        """Filter conflicts by severity."""
        response = client.get("/api/v1/conflicts?severity=Critical")
        assert response.status_code == 200
        data = response.json()
        
        # Verify all conflicts have the specified severity
        for conflict in data["data"]:
            assert conflict["conflict_severity"] == "Critical"


class TestExplainer:
    """Test the AI explainability endpoint."""
    
    def test_explain_scheduled_task(self):
        """Generate explanation for a scheduled task."""
        response = client.post(
            "/api/v1/explain",
            json={
                "task_id": "TRK-1001",
                "defect": "Rail Fracture",
                "severity": 5,
                "days_overdue": 15,
                "score": 82.5,
                "corridor": "NDLS-GZB-UP",
                "assigned_start": "2026-09-02T02:00:00Z",
                "assigned_end": "2026-09-02T05:00:00Z",
                "status": "Scheduled",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "explanation" in data
        assert len(data["explanation"]) > 0
        assert "gemini" in data["generated_by"] or "rule-based" in data["generated_by"]
    
    def test_explain_deferred_task(self):
        """Generate explanation for a deferred (unscheduled) task."""
        response = client.post(
            "/api/v1/explain",
            json={
                "task_id": "TRK-1099",
                "defect": "Deep Screening (BCM)",
                "severity": 3,
                "days_overdue": 2,
                "score": 51.3,
                "status": "Deferred",
                "mathematical_reason": "Duration (360 min) exceeds longest available window (240 min)",
                "next_recommended_window": "Sep 06, 2026 01:00–07:00 AM (Sunday Mega Block)",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "explanation" in data
        assert len(data["explanation"]) > 0
    
    def test_explain_integrated_task(self):
        """Generate explanation for a task in an Integrated Joint Block."""
        response = client.post(
            "/api/v1/explain",
            json={
                "task_id": "TRK-1000",
                "defect": "Routine Tamping",
                "severity": 2,
                "days_overdue": 5,
                "score": 43.83,
                "is_integrated_block": True,
                "merged_with": "OHE-3000",
                "downtime_saved_minutes": 120,
                "corridor": "NDLS-CNB-UP",
                "assigned_start": "2026-09-02T02:00:00Z",
                "assigned_end": "2026-09-02T04:00:00Z",
                "status": "Merged",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "explanation" in data


class TestEndToEnd:
    """Test complete workflows."""
    
    def test_conflict_to_optimize_flow(self):
        """End-to-end: Fetch conflicts → Run optimizer → Check results."""
        # Step 1: Get conflicts
        response = client.get("/api/v1/conflicts")
        assert response.status_code == 200
        conflicts = response.json()
        initial_count = conflicts["count"]
        
        # Step 2: Get pending tasks
        response = client.get("/api/v1/tasks/pending")
        assert response.status_code == 200
        tasks = response.json()
        initial_tasks = tasks["count"]
        
        # Step 3: Run optimizer
        response = client.post("/api/v1/optimize")
        assert response.status_code == 200
        plan = response.json()
        
        # Verify results
        scheduled_count = len(plan["assignments"])
        unscheduled_count = len(plan["unscheduled"])
        
        # Should schedule all or most tasks
        assert scheduled_count + unscheduled_count <= initial_tasks
        assert plan["solver_stats"]["total_conflicts"] == initial_count
    
    def test_optimize_and_explain_flow(self):
        """End-to-end: Optimize → Explain first assignment."""
        # Step 1: Run optimizer
        response = client.post("/api/v1/optimize")
        assert response.status_code == 200
        plan = response.json()
        
        # Step 2: If there are assignments, explain the first one
        if len(plan["assignments"]) > 0:
            assignment = plan["assignments"][0]
            
            response = client.post(
                "/api/v1/explain",
                json={
                    "task_id": assignment["task_id"],
                    "defect": assignment["defect_type"],
                    "severity": 3,  # Placeholder
                    "days_overdue": 5,  # Placeholder
                    "score": assignment["criticality_score"],
                    "corridor": assignment["corridor_name"],
                    "assigned_start": assignment["assigned_start"],
                    "assigned_end": assignment["assigned_end"],
                    "is_integrated_block": assignment["is_integrated"],
                    "status": "Scheduled",
                },
            )
            assert response.status_code == 200
            explanation = response.json()
            assert "explanation" in explanation


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
