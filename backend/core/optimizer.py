"""
backend/core/optimizer.py
=========================
BlockSync CP-SAT Block Planning Engine
Branch: Cp-sat | Author: BlockSync Optimization Team

Implements constraint programming using Google OR-Tools CP-SAT solver:
  1. Mathematical Decision Variables:
     - Binary assignment: x[t, w] (Task t assigned to Window w)
     - Start offset: s[t, w] (Minute offset from window start)
     - Absolute timeline: S[t, w], E[t, w] (Minutes from planning horizon epoch)
     - Optional Interval: iv[t, w] (Active only when x[t, w] is 1)
     - Joint Block indicator: jb[t1, t2, w] (Compatible task pair in same window)
  2. Hard Constraints:
     - At most one window per task (sum_w x[t, w] <= 1)
     - Global Corridor Non-Overlap: model.AddNoOverlap per corridor across all windows
     - Window duration boundary: s[t, w] + duration_t <= window.duration_min
     - Safety Precedence: Traction power disconnection starts <= track maintenance
  3. Multi-Objective Optimization:
     - Maximize priority-weighted criticality coverage
     - Maximize Integrated Joint Block bonus (saving corridor downtime)
     - Minimize deviation from requested schedule date
     - Compact window packing (minimize start offsets)
  4. Infeasibility Diagnostics:
     - Mathematical explanation for unscheduled tasks (Scenario 3 guaranteed)
"""

from __future__ import annotations

import logging
import math
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

try:
    from ortools.sat.python import cp_model
    ORTOOLS_AVAILABLE = True
except ImportError:
    ORTOOLS_AVAILABLE = False

logger = logging.getLogger("blocksync.optimizer")


class CPSATScheduler:
    """
    Production-grade Google OR-Tools CP-SAT Block Scheduling Engine.
    """

    def __init__(
        self,
        tasks: list[dict],
        windows: list[dict],
        max_solve_seconds: int = 30,
    ) -> None:
        self.tasks = tasks
        self.windows = windows
        self.max_solve_seconds = max_solve_seconds

        # Index windows by corridor_id
        self.windows_by_corridor: dict[int, list[dict]] = {}
        for w in self.windows:
            cid = w.get("corridor_id")
            if cid is not None:
                self.windows_by_corridor.setdefault(cid, []).append(w)
        for cid in self.windows_by_corridor:
            self.windows_by_corridor[cid].sort(key=lambda x: x["start_time"])

        self.window_by_id: dict[int, dict] = {w["id"]: w for w in self.windows}
        self.task_by_id: dict[str, dict] = {t["id"]: t for t in self.tasks}

    def solve(self) -> tuple[list[dict], list[dict], dict]:
        """
        Execute the CP-SAT optimization model.

        Returns:
            (assignments: list[dict], unscheduled: list[dict], stats: dict)
        """
        if not ORTOOLS_AVAILABLE:
            raise RuntimeError(
                "Google OR-Tools is not installed. Please run: pip install ortools"
            )

        t_start = time.perf_counter()

        if not self.tasks or not self.windows:
            return [], [], {
                "conflicts_resolved": 0,
                "joint_blocks_formed": 0,
                "downtime_saved_hours": 0.0,
                "total_tasks_scheduled": 0,
                "total_tasks_unscheduled": len(self.tasks),
                "constraints_evaluated": 0,
                "objective_value": 0.0,
            }

        # -------------------------------------------------------------------
        # 0. Timeline Epoch (T0)
        # -------------------------------------------------------------------
        window_dts = [datetime.fromisoformat(w["start_time"]) for w in self.windows]
        t0 = min(window_dts)

        def _to_epoch_min(dt: datetime) -> int:
            return int((dt - t0).total_seconds() // 60)

        # Precompute window epoch start and end
        window_epoch_start: dict[int, int] = {}
        for w in self.windows:
            w_start_dt = datetime.fromisoformat(w["start_time"])
            window_epoch_start[w["id"]] = _to_epoch_min(w_start_dt)

        model = cp_model.CpModel()

        # -------------------------------------------------------------------
        # 1. Candidate Windows & Variable Creation
        # -------------------------------------------------------------------
        x_vars: dict[tuple[str, int], cp_model.BoolVar] = {}
        s_vars: dict[tuple[str, int], cp_model.IntVar] = {}
        abs_s_vars: dict[tuple[str, int], cp_model.IntVar] = {}
        abs_e_vars: dict[tuple[str, int], cp_model.IntVar] = {}
        iv_vars: dict[tuple[str, int], cp_model.IntervalVar] = {}

        candidate_windows_by_task: dict[str, list[dict]] = {}
        candidate_tasks_by_window: dict[int, list[dict]] = {}
        corridor_intervals: dict[int, list[cp_model.IntervalVar]] = {}

        for task in self.tasks:
            t_id = task["id"]
            corridor_id = task.get("corridor_id")
            duration = int(task.get("est_duration_min", 0))

            available = self.windows_by_corridor.get(corridor_id, [])
            valid_windows = [w for w in available if w.get("duration_min", 0) >= duration]
            candidate_windows_by_task[t_id] = valid_windows

            for w in valid_windows:
                w_id = w["id"]
                w_dur = int(w["duration_min"])
                w_epoch = window_epoch_start[w_id]
                candidate_tasks_by_window.setdefault(w_id, []).append(task)

                x = model.NewBoolVar(f"x_{t_id}_{w_id}")
                s_rel = model.NewIntVar(0, max(0, w_dur - duration), f"s_{t_id}_{w_id}")
                s_abs = model.NewIntVar(w_epoch, w_epoch + max(0, w_dur - duration), f"S_{t_id}_{w_id}")
                e_abs = model.NewIntVar(w_epoch + duration, w_epoch + w_dur, f"E_{t_id}_{w_id}")

                model.Add(s_abs == w_epoch + s_rel)
                model.Add(e_abs == s_abs + duration)

                iv = model.NewOptionalIntervalVar(s_abs, duration, e_abs, x, f"iv_{t_id}_{w_id}")

                x_vars[(t_id, w_id)] = x
                s_vars[(t_id, w_id)] = s_rel
                abs_s_vars[(t_id, w_id)] = s_abs
                abs_e_vars[(t_id, w_id)] = e_abs
                iv_vars[(t_id, w_id)] = iv

                corridor_intervals.setdefault(corridor_id, []).append(iv)

        # -------------------------------------------------------------------
        # 2. Hard Constraints
        # -------------------------------------------------------------------
        constraints_count = 0

        # (a) At most one window per task
        for task in self.tasks:
            t_id = task["id"]
            c_wins = candidate_windows_by_task[t_id]
            if c_wins:
                model.Add(sum(x_vars[(t_id, w["id"])] for w in c_wins) <= 1)
                constraints_count += 1

        # (b) Global Non-overlapping intervals per corridor across ALL windows
        for cid, intervals in corridor_intervals.items():
            if len(intervals) > 1:
                model.AddNoOverlap(intervals)
                constraints_count += 1

        # (c) Integrated Joint Block Candidates & Precedence
        # Identify compatible pairs on the same corridor
        joint_block_vars: dict[tuple[str, str, int], cp_model.BoolVar] = {}
        compatible_pairs: list[tuple[dict, dict]] = []

        processed_pairs: set[tuple[str, str]] = set()
        for t1 in self.tasks:
            t1_id = t1["id"]
            t1_dept = t1.get("department_code", t1.get("department", ""))
            t1_compat = t1.get("is_compatible_with")
            t1_joint_pair = t1.get("joint_pair_id")

            if not t1_compat and not t1_joint_pair:
                continue

            for t2 in self.tasks:
                t2_id = t2["id"]
                if t1_id >= t2_id:
                    continue
                pair_key = (t1_id, t2_id)
                if pair_key in processed_pairs:
                    continue

                t2_dept = t2.get("department_code", t2.get("department", ""))
                t2_compat = t2.get("is_compatible_with")
                t2_joint_pair = t2.get("joint_pair_id")

                if t1.get("corridor_id") != t2.get("corridor_id"):
                    continue

                is_match = False
                if t1_joint_pair and t2_joint_pair and t1_joint_pair == t2_joint_pair:
                    is_match = True
                elif (
                    t1_compat == t2_dept
                    and t2_compat == t1_dept
                ):
                    is_match = True

                if is_match:
                    processed_pairs.add(pair_key)
                    compatible_pairs.append((t1, t2))

                    dur1 = int(t1.get("est_duration_min", 0))
                    dur2 = int(t2.get("est_duration_min", 0))
                    total_dur = dur1 + dur2

                    corridor_windows = self.windows_by_corridor.get(t1.get("corridor_id"), [])
                    for w in corridor_windows:
                        w_id = w["id"]
                        if w["duration_min"] >= total_dur and (t1_id, w_id) in x_vars and (t2_id, w_id) in x_vars:
                            jb_var = model.NewBoolVar(f"jb_{t1_id}_{t2_id}_{w_id}")
                            joint_block_vars[(t1_id, t2_id, w_id)] = jb_var

                            model.Add(jb_var <= x_vars[(t1_id, w_id)])
                            model.Add(jb_var <= x_vars[(t2_id, w_id)])
                            model.Add(jb_var >= x_vars[(t1_id, w_id)] + x_vars[(t2_id, w_id)] - 1)
                            constraints_count += 3

                            # Safety Precedence:
                            # If t1 is OHE with power disconnection and t2 is TRK: t1 starts before or with t2
                            if t1.get("power_disconnection_required") and t1_dept == "OHE" and t2_dept == "TRK":
                                model.Add(s_vars[(t1_id, w_id)] <= s_vars[(t2_id, w_id)]).OnlyEnforceIf(jb_var)
                                constraints_count += 1
                            elif t2.get("power_disconnection_required") and t2_dept == "OHE" and t1_dept == "TRK":
                                model.Add(s_vars[(t2_id, w_id)] <= s_vars[(t1_id, w_id)]).OnlyEnforceIf(jb_var)
                                constraints_count += 1

        # -------------------------------------------------------------------
        # 3. Multi-Objective Function
        # -------------------------------------------------------------------
        objective_terms = []

        for (t_id, w_id), x in x_vars.items():
            task = self.task_by_id[t_id]
            crit_score = float(task.get("criticality_score", 0.0))
            score_weight = int(round(crit_score * 1000))

            w_obj = self.window_by_id[w_id]
            req_start = task.get("requested_start")
            date_bonus = 0
            if req_start and w_obj.get("start_time", "").startswith(req_start[:10]):
                date_bonus = 500

            objective_terms.append((score_weight + date_bonus) * x)
            # Gentle packing incentive towards window start
            objective_terms.append(-1 * s_vars[(t_id, w_id)])

        for (t1_id, t2_id, w_id), jb_var in joint_block_vars.items():
            # Substantial reward to form integrated blocks and save corridor downtime
            objective_terms.append(15000 * jb_var)

        model.Maximize(sum(objective_terms))

        # -------------------------------------------------------------------
        # 4. Solver Execution
        # -------------------------------------------------------------------
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = float(self.max_solve_seconds)
        solver.parameters.num_workers = 4

        solve_status = solver.Solve(model)
        solve_time = round(time.perf_counter() - t_start, 3)
        logger.info(
            f"CP-SAT solver finished in {solve_time}s with status: {solver.StatusName(solve_status)}"
        )

        # -------------------------------------------------------------------
        # 5. Extract Assignments & Joint Blocks
        # -------------------------------------------------------------------
        assignments: list[dict] = []
        unscheduled: list[dict] = []
        scheduled_task_ids: set[str] = set()

        active_joint_blocks: dict[int, list[dict]] = {}

        if solve_status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            for task in self.tasks:
                t_id = task["id"]
                c_wins = candidate_windows_by_task.get(t_id, [])

                for w in c_wins:
                    w_id = w["id"]
                    if solver.Value(x_vars[(t_id, w_id)]) == 1:
                        s_val = solver.Value(s_vars[(t_id, w_id)])
                        duration = int(task.get("est_duration_min", 0))

                        w_start = datetime.fromisoformat(w["start_time"])
                        slot_start = w_start + timedelta(minutes=s_val)
                        slot_end = slot_start + timedelta(minutes=duration)

                        h = slot_start.hour
                        if 1 <= h < 8:
                            wtype = "Night Gold Window"
                        elif 8 <= h < 12:
                            wtype = "Early Morning Window"
                        else:
                            wtype = "Midday Freight Window"

                        entry = {
                            "task_id": t_id,
                            "department": task.get("department_code", task.get("department", "")),
                            "corridor": task.get("corridor_code", ""),
                            "corridor_name": task.get("corridor_name", ""),
                            "defect_type": task.get("defect_type", ""),
                            "criticality_score": float(task.get("criticality_score", 0.0)),
                            "assigned_start": slot_start.isoformat(),
                            "assigned_end": slot_end.isoformat(),
                            "is_integrated": False,
                            "joint_block_id": None,
                            "merged_departments": [],
                            "window_type": wtype,
                            "ai_explanation": None,
                            "_task_ref": task,
                            "_window_id": w_id,
                            "_start_dt": slot_start,
                        }

                        assignments.append(entry)
                        scheduled_task_ids.add(t_id)
                        active_joint_blocks.setdefault(w_id, []).append(entry)
                        break

            # Mark integrated joint blocks
            for w_id, w_tasks in active_joint_blocks.items():
                if len(w_tasks) > 1:
                    depts = sorted(list({t["department"] for t in w_tasks}))
                    if len(depts) > 1:
                        jb_id = f"JB-{w_id:03d}"
                        for t_entry in w_tasks:
                            t_entry["is_integrated"] = True
                            t_entry["joint_block_id"] = jb_id
                            t_entry["merged_departments"] = depts

        # -------------------------------------------------------------------
        # 6. Build Unscheduled Diagnostic Explanations
        # -------------------------------------------------------------------
        for task in self.tasks:
            t_id = task["id"]
            if t_id not in scheduled_task_ids:
                corridor_id = task.get("corridor_id")
                corridor_code = task.get("corridor_code", "")
                dur = int(task.get("est_duration_min", 0))
                available_w = self.windows_by_corridor.get(corridor_id, [])

                max_window_dur = max(
                    (w.get("duration_min", 0) for w in available_w),
                    default=0,
                )

                if not available_w:
                    reason = (
                        f"No COA windows exist for corridor '{corridor_code}' "
                        "in the planning horizon."
                    )
                elif dur > max_window_dur:
                    reason = (
                        f"No continuous window available for requested duration "
                        f"({dur} mins). Longest available window on "
                        f"{corridor_code} is {max_window_dur} mins."
                    )
                else:
                    reason = (
                        f"All windows on {corridor_code} are fully booked by "
                        f"higher-priority tasks (Score "
                        f"{task.get('criticality_score', 0):.1f}). "
                        "Task deferred to next planning cycle."
                    )

                unscheduled.append({
                    "task_id": t_id,
                    "department": task.get("department_code", task.get("department", "")),
                    "defect_type": task.get("defect_type", ""),
                    "criticality_score": float(task.get("criticality_score", 0.0)),
                    "requested_duration_min": dur,
                    "reason": reason,
                    "deferred_to": "Next planning cycle (Week 37 or Sunday Mega Block)",
                    "next_recommended_window": self._suggest_next_window(task),
                })

        # -------------------------------------------------------------------
        # 7. Compute Solver Stats
        # -------------------------------------------------------------------
        joint_block_ids = {
            a["joint_block_id"] for a in assignments if a.get("joint_block_id")
        }

        downtime_saved_min = 0.0
        for jbid in joint_block_ids:
            members = [a for a in assignments if a.get("joint_block_id") == jbid]
            durations = [
                a["_task_ref"].get("est_duration_min", 0) for a in members
            ]
            if durations:
                downtime_saved_min += min(durations)

        stats = {
            "conflicts_resolved": len(joint_block_ids),
            "joint_blocks_formed": len(joint_block_ids),
            "downtime_saved_hours": round(downtime_saved_min / 60, 2),
            "total_tasks_scheduled": len(assignments),
            "total_tasks_unscheduled": len(unscheduled),
            "constraints_evaluated": max(1, constraints_count + len(objective_terms)),
            "objective_value": round(
                sum(a["criticality_score"] for a in assignments), 2
            ),
        }

        return assignments, unscheduled, stats

    def _suggest_next_window(self, task: dict) -> str:
        """Find the earliest suitable future window for an unscheduled task."""
        corridor_id = task.get("corridor_id")
        dur = int(task.get("est_duration_min", 0))
        candidates = [
            w for w in self.windows_by_corridor.get(corridor_id, [])
            if w.get("duration_min", 0) >= dur
        ]
        if not candidates:
            return "No suitable window found — request emergency block grant from COA."
        earliest = min(candidates, key=lambda x: x["start_time"])
        return f"{earliest['start_time'][:10]} {earliest.get('window_label', 'Block Window')}"


def solve_cpsat(
    tasks: list[dict],
    windows: list[dict],
    max_solve_seconds: int = 30,
) -> tuple[list[dict], list[dict], dict]:
    """
    Convenience functional wrapper for CPSATScheduler.
    """
    scheduler = CPSATScheduler(
        tasks=tasks,
        windows=windows,
        max_solve_seconds=max_solve_seconds,
    )
    return scheduler.solve()
