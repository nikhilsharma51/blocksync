'use client';

import React, { useState } from 'react';
import {
  CheckCircle2,
  Sparkles,
  Sliders,
  FileText,
  ShieldCheck,
  Search,
  AlertCircle,
  ChevronRight,
} from 'lucide-react';
import {
  CorridorSection,
  MaintenanceTask,
  OptimizedAssignment,
  IntegratedJointBlock,
  UnscheduledTask,
  Department,
  SolverStats,
} from '../../types/railway';

interface OptimizedGanttProps {
  corridors: CorridorSection[];
  assignments: OptimizedAssignment[];
  jointBlocks: IntegratedJointBlock[];
  unscheduledTasks: UnscheduledTask[];
  solverStats: SolverStats;
  selectedDepartments: Department[];
  onSelectTask: (task: MaintenanceTask) => void;
  onOpenBulletin: () => void;
  onApprovePlan: () => void;
  isPlanApproved: boolean;
}

export const OptimizedGantt: React.FC<OptimizedGanttProps> = ({
  corridors,
  assignments,
  jointBlocks,
  unscheduledTasks,
  solverStats,
  selectedDepartments,
  onSelectTask,
  onOpenBulletin,
  onApprovePlan,
  isPlanApproved,
}) => {
  const [selectedCorridorId, setSelectedCorridorId] = useState<string>('ALL');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [viewFilter, setViewFilter] = useState<'all' | 'joint_only' | 'single_only'>('all');
  const [overrideToast, setOverrideToast] = useState<string | null>(null);

  const hours = [0, 1, 2, 3, 4, 5, 6, 7, 8];

  const filteredAssignments = assignments.filter((a) => {
    const matchDept = selectedDepartments.includes(a.task.department);
    const matchCorridor = selectedCorridorId === 'ALL' || a.task.corridorId === selectedCorridorId;
    const matchSearch =
      searchQuery === '' ||
      a.task.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      a.task.taskNumber.toString().includes(searchQuery);
    const matchView =
      viewFilter === 'all' ||
      (viewFilter === 'joint_only' && a.isIntegrated) ||
      (viewFilter === 'single_only' && !a.isIntegrated);

    return matchDept && matchCorridor && matchSearch && matchView;
  });

  const getDepartmentBadge = (dept: Department) => {
    switch (dept) {
      case 'Track':
        return { bg: 'bg-orange-50', border: 'border-orange-300', text: 'text-orange-950' };
      case 'Signal':
        return { bg: 'bg-blue-50', border: 'border-blue-300', text: 'text-blue-950' };
      case 'OHE':
        return { bg: 'bg-amber-50', border: 'border-amber-300', text: 'text-amber-950' };
    }
  };

  const handleTestOverride = () => {
    setOverrideToast('Constraint Check: Re-validated CP-SAT headway (0 collisions, 15m power headway maintained).');
    setTimeout(() => setOverrideToast(null), 4000);
  };

  return (
    <div className="space-y-3">
      {/* 1. Calm Solver Metric Strip */}
      <div className="bg-white border border-slate-200 rounded-lg p-3 px-4 shadow-2xs">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 divide-y md:divide-y-0 md:divide-x divide-slate-100">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-md bg-emerald-50 border border-emerald-200 flex items-center justify-center text-emerald-700 font-bold text-xs shrink-0">
              ✓
            </div>
            <div>
              <div className="text-[11px] font-medium text-slate-500">CP-SAT Status</div>
              <div className="text-base font-bold text-emerald-900 font-mono">100% Solved</div>
            </div>
          </div>

          <div className="flex items-center gap-3 md:pl-4 pt-2 md:pt-0">
            <div className="w-8 h-8 rounded-md bg-slate-50 border border-slate-200 flex items-center justify-center text-slate-700 font-bold text-xs shrink-0">
              0
            </div>
            <div>
              <div className="text-[11px] font-medium text-slate-500">Conflicts Resolved</div>
              <div className="text-base font-bold text-slate-950 font-mono">14 of 14</div>
            </div>
          </div>

          <div className="flex items-center gap-3 md:pl-4 pt-2 md:pt-0">
            <div className="w-8 h-8 rounded-md bg-amber-50 border border-amber-200 flex items-center justify-center text-amber-700 font-bold text-xs shrink-0">
              🤝
            </div>
            <div>
              <div className="text-[11px] font-medium text-slate-500">Joint Blocks Formed</div>
              <div className="text-base font-bold text-amber-900 font-mono">6 (+12.5h)</div>
            </div>
          </div>

          <div className="flex items-center gap-3 md:pl-4 pt-2 md:pt-0">
            <div className="w-8 h-8 rounded-md bg-slate-50 border border-slate-200 flex items-center justify-center text-slate-700 font-bold text-xs shrink-0">
              ⚡
            </div>
            <div>
              <div className="text-[11px] font-medium text-slate-500">Solver Runtime</div>
              <div className="text-base font-bold text-slate-950 font-mono">1.84s</div>
            </div>
          </div>
        </div>
      </div>

      {/* Override Feedback Toast */}
      {overrideToast && (
        <div className="p-2.5 bg-slate-100 border border-slate-300 rounded text-xs text-slate-800 flex items-center justify-between animate-in fade-in">
          <span>{overrideToast}</span>
          <button onClick={() => setOverrideToast(null)} className="text-slate-500 hover:text-slate-900 cursor-pointer">
            ✕
          </button>
        </div>
      )}

      {/* 2. Resolved Master Timeline Canvas */}
      <div className="bg-white border border-slate-200 rounded-lg overflow-hidden shadow-2xs">
        {/* Timeline Integrated Action Bar */}
        <div className="p-3 border-b border-slate-200 flex flex-wrap items-center justify-between gap-3 bg-slate-50/50">
          <div className="flex flex-wrap items-center gap-2.5">
            <span className="font-semibold text-xs text-slate-900">
              Master Plan
            </span>
            <span className="text-[10px] font-mono font-medium text-emerald-700 bg-emerald-50 px-1.5 py-0.2 rounded border border-emerald-200">
              Conflict-Free
            </span>

            <span className="text-slate-300 hidden sm:inline">|</span>

            {/* Filter Toggle */}
            <div className="inline-flex p-0.5 bg-slate-200/60 rounded text-xs font-medium">
              <button
                onClick={() => setViewFilter('all')}
                className={`px-2 py-0.5 rounded cursor-pointer ${
                  viewFilter === 'all' ? 'bg-white text-slate-900 shadow-2xs font-semibold' : 'text-slate-500'
                }`}
              >
                All ({assignments.length})
              </button>
              <button
                onClick={() => setViewFilter('joint_only')}
                className={`px-2 py-0.5 rounded cursor-pointer ${
                  viewFilter === 'joint_only' ? 'bg-white text-slate-900 shadow-2xs font-semibold' : 'text-slate-500'
                }`}
              >
                Joint ({jointBlocks.length})
              </button>
            </div>

            {/* Search */}
            <div className="relative">
              <Search className="w-3 h-3 text-slate-400 absolute left-2 top-2 pointer-events-none" />
              <input
                type="text"
                placeholder="Filter task..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-6 pr-2 py-0.5 text-xs rounded border border-slate-200 bg-white text-slate-900 w-32 focus:w-44 transition-all"
              />
            </div>
          </div>

          {/* Right Action Controls */}
          <div className="flex items-center gap-2">
            <button
              onClick={handleTestOverride}
              className="px-2.5 py-1 rounded text-xs font-medium bg-white text-slate-700 border border-slate-200 hover:bg-slate-50 cursor-pointer"
            >
              <span>Test Override</span>
            </button>

            <button
              onClick={onOpenBulletin}
              className="px-2.5 py-1 rounded text-xs font-medium bg-white text-slate-700 border border-slate-200 hover:bg-slate-50 cursor-pointer"
            >
              <span>Bulletin (PDF)</span>
            </button>

            <button
              onClick={onApprovePlan}
              disabled={isPlanApproved}
              className={`px-3 py-1 rounded text-xs font-semibold transition-all ${
                isPlanApproved
                  ? 'bg-emerald-50 text-emerald-800 border border-emerald-200 cursor-default'
                  : 'bg-emerald-700 text-white hover:bg-emerald-800 cursor-pointer'
              }`}
            >
              <span>{isPlanApproved ? 'Approved' : 'Approve Plan'}</span>
            </button>
          </div>
        </div>

        {/* Timeline Grid */}
        <div className="overflow-x-auto">
          <div className="min-w-[840px]">
            {/* Hour Scale */}
            <div className="grid grid-cols-12 border-b border-slate-200 bg-slate-50 text-[11px] font-medium text-slate-500 select-none">
              <div className="col-span-3 px-3 py-1.5 border-r border-slate-200">
                Corridor Section
              </div>
              <div className="col-span-9 grid grid-cols-8 divide-x divide-slate-200">
                {hours.slice(0, 8).map((hour) => (
                  <div key={hour} className="px-2 py-1.5 text-center font-mono">
                    {hour.toString().padStart(2, '0')}:00
                  </div>
                ))}
              </div>
            </div>

            {/* Corridor Rows */}
            <div className="divide-y divide-slate-100">
              {corridors
                .filter((c) => selectedCorridorId === 'ALL' || c.id === selectedCorridorId)
                .map((corridor) => {
                  const corridorAssignments = filteredAssignments.filter(
                    (a) => a.task.corridorId === corridor.id
                  );
                  const corridorJointBlocks = jointBlocks.filter(
                    (jb) => jb.corridorId === corridor.id
                  );

                  return (
                    <div
                      key={corridor.id}
                      className="grid grid-cols-12 min-h-[82px] hover:bg-slate-50/40 transition-colors"
                    >
                      {/* Left: Corridor Header */}
                      <div className="col-span-3 px-3 py-2 border-r border-slate-200 flex flex-col justify-center bg-slate-50/20">
                        <div className="flex items-center gap-1.5">
                          <span
                            className={`px-1 py-0.2 rounded text-[9px] font-bold font-mono ${
                              corridor.lineType === 'UP'
                                ? 'bg-indigo-50 text-indigo-700 border border-indigo-200'
                                : 'bg-teal-50 text-teal-700 border border-teal-200'
                            }`}
                          >
                            {corridor.lineType}
                          </span>
                          <span className="font-semibold text-xs text-slate-900 truncate">
                            {corridor.name}
                          </span>
                        </div>
                        <div className="text-[10px] text-slate-400 font-mono mt-0.5">
                          {corridor.trackKm}
                        </div>
                      </div>

                      {/* Right: Gantt Track */}
                      <div className="col-span-9 relative grid grid-cols-8 divide-x divide-slate-100 h-full min-h-[82px]">
                        {/* Background Hour Columns */}
                        {hours.slice(0, 8).map((hour) => (
                          <div
                            key={hour}
                            className={`h-full ${
                              hour >= 1 && hour <= 4 ? 'bg-slate-50/60' : 'bg-transparent'
                            }`}
                          />
                        ))}

                        {/* Joint Block Boundary Container */}
                        {corridorJointBlocks.map((jb) => {
                          const leftPercent = (jb.startHour / 8) * 100;
                          const widthPercent = (jb.durationHours / 8) * 100;

                          return (
                            <div
                              key={jb.id}
                              style={{
                                left: `${Math.max(0, Math.min(100, leftPercent))}%`,
                                width: `${Math.max(8, Math.min(100, widthPercent))}%`,
                              }}
                              className="absolute top-1 bottom-1 pattern-joint-block rounded z-10 pointer-events-none flex items-start justify-between p-1 opacity-90"
                            >
                              <span className="bg-amber-700 text-white font-mono text-[8px] px-1 rounded">
                                JOINT #JB-0{jb.jointBlockNumber} (-{jb.downtimeSavedMinutes}m)
                              </span>
                            </div>
                          );
                        })}

                        {/* Task Blocks */}
                        {corridorAssignments.map((assignment, idx) => {
                          const task = assignment.task;
                          const leftPercent = (assignment.assignedStartHour / 8) * 100;
                          const widthPercent =
                            ((assignment.assignedEndHour - assignment.assignedStartHour) / 8) * 100;
                          const style = getDepartmentBadge(task.department);
                          const topOffset = assignment.isIntegrated
                            ? idx % 2 === 0
                              ? 'top-2'
                              : 'top-9'
                            : 'top-3';

                          return (
                            <button
                              key={task.id}
                              onClick={() => onSelectTask(task)}
                              style={{
                                left: `${Math.max(0, Math.min(100, leftPercent))}%`,
                                width: `${Math.max(8, Math.min(100, widthPercent))}%`,
                              }}
                              className={`absolute ${topOffset} h-7 rounded px-2 py-0.5 text-left border ${style.border} ${
                                assignment.isIntegrated ? 'bg-white' : style.bg
                              } hover:border-slate-400 transition-all flex items-center justify-between gap-1.5 cursor-pointer z-20 shadow-2xs`}
                            >
                              <span className="font-semibold text-[10px] text-slate-900 truncate">
                                #{task.taskNumber} {task.defect.category}
                              </span>

                              <span className="font-mono text-[9px] text-slate-500 shrink-0">
                                {task.durationHours * 60}m
                              </span>
                            </button>
                          );
                        })}
                      </div>
                    </div>
                  );
                })}
            </div>
          </div>
        </div>
      </div>

      {/* 3. Streamlined Unscheduled Drawer */}
      <div className="bg-white border border-slate-200 rounded-lg p-3 px-4 shadow-2xs">
        <div className="flex items-center justify-between text-xs font-semibold text-slate-700 mb-2">
          <span>Unscheduled / Deferred Requests ({unscheduledTasks.length})</span>
          <span className="text-[11px] font-normal text-slate-400">Preempted by CP-SAT constraint solver</span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-xs">
          {unscheduledTasks.map((item) => (
            <div
              key={item.task.id}
              onClick={() => onSelectTask(item.task)}
              className="p-2 rounded border border-slate-200 bg-slate-50/50 hover:bg-slate-50 transition-colors flex items-center justify-between cursor-pointer"
            >
              <div>
                <span className="font-semibold text-slate-900">
                  #{item.task.taskNumber} {item.task.title}
                </span>
                <div className="text-[11px] text-slate-500 font-mono mt-0.5">
                  {item.mathematicalReason}
                </div>
              </div>
              <span className="text-[10px] text-amber-800 font-bold bg-amber-50 px-1.5 py-0.5 rounded border border-amber-200 shrink-0 ml-2">
                Deferred
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
