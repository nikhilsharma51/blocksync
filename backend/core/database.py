"""
BlockSync Supabase Connection & Data Layer
=========================================
Handles all DB reads and writes for tasks, windows, conflicts, and assignments.

Branch: hriday-dataset | Author: Hriday (Backend Architect - Member 2)

Usage:
    from backend.core.database import db
    tasks = db.get_pending_tasks(department="TRK")
"""

from __future__ import annotations

import os
import logging
from typing import Optional
from datetime import datetime

logger = logging.getLogger(__name__)

# Check if supabase is installed; allow graceful fallback to JSON
try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    logger.warning("supabase package not installed. Database operations will use JSON fallback.")


class SupabaseDB:
    """Singleton connection to the BlockSync Supabase database."""
    
    _instance: Optional['SupabaseDB'] = None
    _client: Optional[Client] = None
    _initialized: bool = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize Supabase connection (singleton pattern ensures once-only)."""
        if self._initialized:
            return
        
        if not SUPABASE_AVAILABLE:
            logger.warning("Supabase not available. Using JSON fallback mode.")
            self._initialized = True
            return
        
        url = os.environ.get("SUPABASE_URL", "").strip()
        key = os.environ.get("SUPABASE_KEY", "").strip()
        
        if not url or not key:
            logger.warning(
                "SUPABASE_URL or SUPABASE_KEY not set in .env. Using JSON fallback mode. "
                "To enable database, set these environment variables."
            )
            self._initialized = True
            return
        
        try:
            self._client = create_client(url, key)
            logger.info("✓ Connected to Supabase")
            self._initialized = True
        except Exception as exc:
            logger.error(f"Failed to connect to Supabase: {exc}. Using JSON fallback.")
            self._initialized = True
    
    @property
    def client(self) -> Optional[Client]:
        """Get the Supabase client (may be None if not initialized)."""
        return self._client
    
    def is_available(self) -> bool:
        """Check if Supabase connection is active."""
        return self._client is not None
    
    # ========================================================================
    # TASKS
    # ========================================================================
    
    def get_pending_tasks(
        self,
        department: Optional[str] = None,
        corridor_code: Optional[str] = None,
        min_score: Optional[float] = None,
        priority: Optional[str] = None,
        limit: int = 200,
    ) -> list[dict]:
        """
        Fetch pending/clashed maintenance tasks from the DB.
        
        Returns:
            List of task dicts with all required fields for PendingTaskResponse.
        """
        if not self.is_available():
            return []
        
        try:
            query = self.client.table("maintenance_tasks").select("*")
            
            # Filter by status
            query = query.in_("status", ["Pending", "Clashed"])
            
            if department:
                dept_id = self._dept_code_to_id(department)
                query = query.eq("department_id", dept_id)
            
            if corridor_code:
                query = query.eq("corridor_code", corridor_code)
            
            if priority:
                query = query.eq("priority_level", priority)
            
            if min_score is not None:
                query = query.gte("criticality_score", min_score)
            
            # Sort by criticality_score DESC (highest first)
            query = query.order("criticality_score", desc=True)
            query = query.limit(limit)
            
            result = query.execute()
            return result.data or []
        
        except Exception as exc:
            logger.error(f"Error fetching pending tasks: {exc}")
            return []
    
    def get_task_by_id(self, task_id: str) -> Optional[dict]:
        """Fetch a single task by ID."""
        if not self.is_available():
            return None
        
        try:
            result = (
                self.client.table("maintenance_tasks")
                .select("*")
                .eq("id", task_id)
                .single()
                .execute()
            )
            return result.data if result.data else None
        
        except Exception as exc:
            logger.error(f"Error fetching task {task_id}: {exc}")
            return None
    
    def get_all_tasks(
        self,
        limit: int = 200,
    ) -> list[dict]:
        """Fetch all tasks (any status)."""
        if not self.is_available():
            return []
        
        try:
            result = (
                self.client.table("maintenance_tasks")
                .select("*")
                .order("criticality_score", desc=True)
                .limit(limit)
                .execute()
            )
            return result.data or []
        
        except Exception as exc:
            logger.error(f"Error fetching all tasks: {exc}")
            return []
    
    # ========================================================================
    # CORRIDORS & WINDOWS
    # ========================================================================
    
    def get_corridor_by_id(self, corridor_id: int) -> Optional[dict]:
        """Fetch corridor metadata by ID."""
        if not self.is_available():
            return None
        
        try:
            result = (
                self.client.table("corridors")
                .select("*")
                .eq("id", corridor_id)
                .single()
                .execute()
            )
            return result.data if result.data else None
        
        except Exception as exc:
            logger.error(f"Error fetching corridor {corridor_id}: {exc}")
            return None
    
    def get_available_windows(
        self,
        corridor_id: Optional[int] = None,
        corridor_code: Optional[str] = None,
        date: Optional[str] = None,  # YYYY-MM-DD
        window_label: Optional[str] = None,
        min_duration: Optional[int] = None,
        limit: int = 200,
    ) -> list[dict]:
        """
        Fetch available COA windows that the optimizer can use.
        
        Returns:
            List of window dicts with start_time, end_time, duration_min, etc.
        """
        if not self.is_available():
            return []
        
        try:
            query = (
                self.client.table("block_windows")
                .select("*")
                .eq("is_available", True)
            )
            
            if corridor_id:
                query = query.eq("corridor_id", corridor_id)
            
            if corridor_code:
                query = query.eq("corridor_code", corridor_code)
            
            if window_label:
                query = query.eq("window_label", window_label)
            
            if min_duration:
                query = query.gte("duration_min", min_duration)
            
            if date:
                # Filter to windows that START on this date (YYYY-MM-DD)
                query = query.ilike("start_time", f"{date}%")
            
            query = query.order("start_time", desc=False)
            query = query.limit(limit)
            
            result = query.execute()
            return result.data or []
        
        except Exception as exc:
            logger.error(f"Error fetching windows: {exc}")
            return []
    
    # ========================================================================
    # CONFLICTS
    # ========================================================================
    
    def get_conflicts(
        self,
        corridor_id: Optional[int] = None,
        severity: Optional[str] = None,  # 'Critical' | 'High' | 'Moderate'
        limit: int = 200,
    ) -> list[dict]:
        """Fetch pre-detected conflict pairs."""
        if not self.is_available():
            return []
        
        try:
            query = self.client.table("conflict_pairs").select("*")
            
            if corridor_id:
                query = query.eq("corridor_id", corridor_id)
            
            if severity:
                query = query.eq("conflict_severity", severity)
            
            query = query.limit(limit)
            result = query.execute()
            return result.data or []
        
        except Exception as exc:
            logger.error(f"Error fetching conflicts: {exc}")
            return []
    
    # ========================================================================
    # OPTIMIZATION PLANS & ASSIGNMENTS
    # ========================================================================
    
    def create_optimization_plan(
        self,
        plan_id: str,
        solver_status: str = "RUNNING",
    ) -> dict:
        """Create a new optimization plan record."""
        if not self.is_available():
            return {"id": plan_id, "solver_status": solver_status}
        
        try:
            result = (
                self.client.table("optimization_plans")
                .insert({
                    "id": plan_id,
                    "solver_status": solver_status,
                    "created_at": datetime.utcnow().isoformat(),
                })
                .execute()
            )
            return result.data[0] if result.data else {"id": plan_id}
        
        except Exception as exc:
            logger.error(f"Error creating plan {plan_id}: {exc}")
            return {"id": plan_id}
    
    def save_plan_result(
        self,
        plan_id: str,
        solver_status: str,
        solve_time_sec: float,
        objective_value: float,
        conflicts_resolved: int,
        total_conflicts: int,
        joint_blocks_formed: int,
        downtime_saved_hours: float,
        total_tasks_scheduled: int,
        total_tasks_unscheduled: int,
        constraints_evaluated: int,
    ) -> dict:
        """Update an optimization plan with solver results."""
        if not self.is_available():
            return {"id": plan_id, "solver_status": solver_status}
        
        try:
            result = (
                self.client.table("optimization_plans")
                .update({
                    "solver_status": solver_status,
                    "solve_time_sec": solve_time_sec,
                    "objective_value": objective_value,
                    "conflicts_resolved": conflicts_resolved,
                    "total_conflicts": total_conflicts,
                    "joint_blocks_formed": joint_blocks_formed,
                    "downtime_saved_hours": downtime_saved_hours,
                    "total_tasks_scheduled": total_tasks_scheduled,
                    "total_tasks_unscheduled": total_tasks_unscheduled,
                    "constraints_evaluated": constraints_evaluated,
                })
                .eq("id", plan_id)
                .execute()
            )
            return result.data[0] if result.data else {"id": plan_id}
        
        except Exception as exc:
            logger.error(f"Error updating plan {plan_id}: {exc}")
            return {"id": plan_id}
    
    def save_block_assignment(
        self,
        plan_id: str,
        task_id: str,
        window_id: int,
        assigned_start: str,  # ISO-8601
        assigned_end: str,    # ISO-8601
        is_integrated: bool = False,
        joint_block_id: Optional[str] = None,
        merged_with_task_id: Optional[str] = None,
        window_type: str = "Night Gold Window",
        ai_explanation: Optional[str] = None,
    ) -> dict:
        """Save a single block assignment."""
        if not self.is_available():
            return {"task_id": task_id, "plan_id": plan_id}
        
        try:
            result = (
                self.client.table("block_assignments")
                .insert({
                    "plan_id": plan_id,
                    "task_id": task_id,
                    "window_id": window_id,
                    "assigned_start": assigned_start,
                    "assigned_end": assigned_end,
                    "is_integrated": is_integrated,
                    "joint_block_id": joint_block_id,
                    "merged_with_task_id": merged_with_task_id,
                    "window_type": window_type,
                    "ai_explanation": ai_explanation,
                    "created_at": datetime.utcnow().isoformat(),
                })
                .execute()
            )
            return result.data[0] if result.data else {"task_id": task_id}
        
        except Exception as exc:
            logger.error(f"Error saving assignment {task_id}: {exc}")
            return {"task_id": task_id}
    
    def save_unscheduled_task(
        self,
        plan_id: str,
        task_id: str,
        mathematical_reason: str,
        deferred_to: Optional[str] = None,
        next_recommended_window: Optional[str] = None,
    ) -> dict:
        """Save a task that couldn't be scheduled."""
        if not self.is_available():
            return {"task_id": task_id, "plan_id": plan_id}
        
        try:
            result = (
                self.client.table("unscheduled_tasks")
                .insert({
                    "plan_id": plan_id,
                    "task_id": task_id,
                    "mathematical_reason": mathematical_reason,
                    "deferred_to": deferred_to,
                    "next_recommended_window": next_recommended_window,
                    "created_at": datetime.utcnow().isoformat(),
                })
                .execute()
            )
            return result.data[0] if result.data else {"task_id": task_id}
        
        except Exception as exc:
            logger.error(f"Error saving unscheduled task {task_id}: {exc}")
            return {"task_id": task_id}
    
    # ========================================================================
    # HELPERS
    # ========================================================================
    
    def _dept_code_to_id(self, code: str) -> int:
        """Convert department code (TRK, SNT, OHE) to ID."""
        mapping = {"TRK": 1, "SNT": 2, "OHE": 3}
        if code not in mapping:
            raise ValueError(f"Unknown department code: {code}")
        return mapping[code]


# Singleton access
db = SupabaseDB()
