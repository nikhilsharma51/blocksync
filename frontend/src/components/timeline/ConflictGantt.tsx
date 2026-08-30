'use client';

import React, { useState } from 'react';
import {
  AlertTriangle,
  Flame,
  Clock,
  Zap,
  Info,
  ShieldAlert,
  Search,
  CheckCircle2,
  ChevronRight,
  Filter,
  Eye,
} from 'lucide-react';
import {
  CorridorSection,
  MaintenanceTask,
  ConflictPair,
  Department,
} from '../../types/railway';

interface ConflictGanttProps {
  corridors: CorridorSection[];
  tasks: MaintenanceTask[];
  conflicts: ConflictPair[];
  selectedDepartments: Department[];
  onSelectTask: (task: MaintenanceTask) => void;
  onRunOptimizer: () => void;
  onToggleConflictPanel: () => void;
  isConflictPanelOpen: boolean;
}

export const ConflictGantt: React.FC<ConflictGanttProps> = ({
  corridors,
  tasks,
  conflicts,
  selectedDepartments,
  onSelectTask,
  onRunOptimizer,
  onToggleConflictPanel,
  isConflictPanelOpen,
}) => {
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [selectedCorridorId, setSelectedCorridorId] = useState<string>('ALL');

  // Timeline hours from 00:00 to 08:00 (The Critical Shift Maintenance Window) or 00:00 to 12:00
  // Display 00:00 to 08:00 prominently since 95% of IR night blocks occur between 00:30 and 06:00
  const hours = [0, 1, 2, 3, 4, 5, 6, 7, 8];

  // Filtering tasks based on active controls
  const filteredTasks = tasks.filter((task) => {
    const matchDept = selectedDepartments.includes(task.department);
    const matchCorridor = selectedCorridorId === 'ALL' || task.corridorId === selectedCorridorId;
    const matchSearch =
      searchQuery === '' ||
      task.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      task.taskNumber.toString().includes(searchQuery) ||
      task.defect.code.toLowerCase().includes(searchQuery.toLowerCase());
    return matchDept && matchCorridor && matchSearch;
  });

  const getDepartmentColor = (dept: Department) => {
    switch (dept) {
      case 'Track':
        return {
          bg: 'bg-orange-100',
          text: 'text-orange-950',
          border: 'border-orange-400',
          badge: 'bg-orange-600 text-white',
        };
      case 'Signal':
        return {
          bg: 'bg-blue-100',
          text: 'text-blue-950',
          border: 'border-blue-400',
          badge: 'bg-blue-600 text-white',
        };
      case 'OHE':
        return {
          bg: 'bg-amber-100',
          text: 'text-amber-950',
          border: 'border-amber-400',
          badge: 'bg-amber-600 text-white',
        };
    }
  };

  return (
    <div className="space-y-4">
      {/* 1. Top KPI Summary Banner (The Problem) */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3.5">
        <div className="p-4 bg-red-50 border border-red-200 rounded-xl shadow-2xs">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-red-900 uppercase tracking-wider">Active Clashes</span>
            <span className="p-1 rounded-md bg-red-600 text-white">
              <AlertTriangle className="w-4 h-4" />
            </span>
          </div>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="text-2xl font-black text-red-950 tracking-tight">14 Conflicts</span>
            <span className="text-xs font-semibold text-red-700">Raw Overlaps</span>
          </div>
          <p className="mt-1 text-[11px] text-red-800">
            Simultaneous requests competing for identical track slots without coordination.
          </p>
        </div>

        <div className="p-4 bg-white border border-slate-200 rounded-xl shadow-2xs">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">Pending Block Requests</span>
            <span className="p-1 rounded-md bg-slate-100 text-slate-700">
              <Clock className="w-4 h-4" />
            </span>
          </div>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="text-2xl font-black text-slate-900 tracking-tight">42 Tasks</span>
            <span className="text-xs font-medium text-slate-500">Across 3 Depts</span>
          </div>
          <p className="mt-1 text-[11px] text-slate-500">
            TMS (18) • SMMS (14) • TDMS (10) independent intake feeds.
          </p>
        </div>

        <div className="p-4 bg-amber-50 border border-amber-200 rounded-xl shadow-2xs">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-amber-900 uppercase tracking-wider">Overdue Defect Risk</span>
            <span className="p-1 rounded-md bg-amber-600 text-white">
              <Flame className="w-4 h-4" />
            </span>
          </div>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="text-2xl font-black text-amber-950 tracking-tight">9 Tasks &gt;7 Days</span>
            <span className="text-xs font-semibold text-amber-700">Safety SLA Breach</span>
          </div>
          <p className="mt-1 text-[11px] text-amber-800">
            Includes 14-day overdue IMR rail fracture (#101) & 17-day bridge flaw (#112).
          </p>
        </div>

        <div className="p-4 bg-white border border-slate-200 rounded-xl shadow-2xs">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">Wasted Capacity Risk</span>
            <span className="p-1 rounded-md bg-slate-100 text-slate-700">
              <ShieldAlert className="w-4 h-4 text-rose-600" />
            </span>
          </div>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="text-2xl font-black text-slate-900 tracking-tight">38.5 Hours</span>
            <span className="text-xs font-medium text-slate-500">Duplicate Stoppages</span>
          </div>
          <p className="mt-1 text-[11px] text-slate-500">
            Corridor time lost if requests are granted as separate single-department blocks.
          </p>
        </div>
      </div>

      {/* 2. Operational Control & Filter Bar */}
      <div className="flex flex-col md:flex-row items-stretch md:items-center justify-between p-3 bg-white border border-slate-200 rounded-xl gap-3 shadow-2xs">
        <div className="flex flex-wrap items-center gap-3">
          {/* Corridor Section Select */}
          <div className="flex items-center gap-2">
            <span className="text-xs font-semibold text-slate-500">Corridor:</span>
            <select
              value={selectedCorridorId}
              onChange={(e) => setSelectedCorridorId(e.target.value)}
              className="text-xs font-medium px-2.5 py-1.5 rounded-lg border border-slate-200 bg-slate-50 text-slate-800 focus:outline-hidden focus:ring-1 focus:ring-slate-400"
            >
              <option value="ALL">All Sections (6 Corridors)</option>
              {corridors.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name}
                </option>
              ))}
            </select>
          </div>

          {/* Quick Search */}
          <div className="relative">
            <Search className="w-3.5 h-3.5 text-slate-400 absolute left-2.5 top-2.5 pointer-events-none" />
            <input
              type="text"
              placeholder="Search task #, defect code, keyword..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-8 pr-3 py-1.5 text-xs rounded-lg border border-slate-200 bg-slate-50 text-slate-900 placeholder:text-slate-400 focus:outline-hidden focus:ring-1 focus:ring-slate-400 w-56 sm:w-64"
            />
          </div>
        </div>

        {/* Action Controls */}
        <div className="flex items-center gap-2 justify-end">
          <button
            onClick={onToggleConflictPanel}
            className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold border transition-all ${
              isConflictPanelOpen
                ? 'bg-red-100 text-red-900 border-red-300'
                : 'bg-white text-slate-700 border-slate-200 hover:bg-slate-50'
            }`}
          >
            <AlertTriangle className="w-3.5 h-3.5 text-red-600" />
            <span>Conflict Pairs Breakdown ({conflicts.length})</span>
          </button>

          <button
            onClick={onRunOptimizer}
            className="inline-flex items-center gap-2 px-4 py-1.5 rounded-lg bg-slate-950 text-white hover:bg-slate-800 text-xs font-bold shadow-xs transition-all active:scale-98"
          >
            <Zap className="w-3.5 h-3.5 text-amber-300 fill-amber-300" />
            <span>Run CP-SAT Optimizer</span>
          </button>
        </div>
      </div>

      {/* 3. The Conflict Gantt Timeline Canvas */}
      <div className="bg-white border border-slate-200 rounded-xl overflow-hidden shadow-xs">
        {/* Timeline Header Bar */}
        <div className="p-3.5 bg-slate-50 border-b border-slate-200 flex flex-wrap items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-red-600 animate-pulse"></span>
            <h2 className="text-sm font-bold text-slate-900">
              Raw Intake Timeline — Conflicting Uncoordinated Requests
            </h2>
            <span className="px-2 py-0.5 rounded-md bg-red-100 text-red-800 font-bold text-[10px] border border-red-200">
              BEFORE OPTIMIZATION
            </span>
          </div>

          {/* Timeline Visual Legend */}
          <div className="flex flex-wrap items-center gap-3 text-[11px]">
            <div className="flex items-center gap-1.5">
              <span className="w-3 h-3 rounded-xs bg-orange-200 border border-orange-500"></span>
              <span className="text-slate-600 font-medium">Track Gang</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="w-3 h-3 rounded-xs bg-blue-200 border border-blue-500"></span>
              <span className="text-slate-600 font-medium">Signal (S&amp;T)</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="w-3 h-3 rounded-xs bg-amber-200 border border-amber-500"></span>
              <span className="text-slate-600 font-medium">Traction (OHE)</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="w-3 h-3 rounded-xs pattern-clash"></span>
              <span className="text-red-700 font-bold">🚨 Clashing Overlap</span>
            </div>
          </div>
        </div>

        {/* Interactive Gantt Rows */}
        <div className="overflow-x-auto">
          <div className="min-w-[840px]">
            {/* Hour Scale Header */}
            <div className="grid grid-cols-12 border-b border-slate-200 bg-slate-100/70 text-[11px] font-semibold text-slate-600 select-none">
              <div className="col-span-3 px-4 py-2 border-r border-slate-200">
                CORRIDOR TRACK SECTION
              </div>
              <div className="col-span-9 grid grid-cols-8 divide-x divide-slate-200">
                {hours.slice(0, 8).map((hour) => (
                  <div key={hour} className="px-2 py-2 text-center">
                    <span className="font-mono text-slate-700">
                      {hour.toString().padStart(2, '0')}:00
                    </span>
                    {hour >= 1 && hour <= 4 && (
                      <span className="block text-[9px] font-normal text-emerald-700">
                        Night Window
                      </span>
                    )}
                  </div>
                ))}
              </div>
            </div>

            {/* Corridor Timeline Rows */}
            <div className="divide-y divide-slate-200">
              {corridors
                .filter((c) => selectedCorridorId === 'ALL' || c.id === selectedCorridorId)
                .map((corridor) => {
                  const corridorTasks = filteredTasks.filter(
                    (t) => t.corridorId === corridor.id
                  );
                  const corridorConflicts = conflicts.filter(
                    (conf) =>
                      corridorTasks.some((t) => t.id === conf.taskA.id) &&
                      corridorTasks.some((t) => t.id === conf.taskB.id)
                  );

                  return (
                    <div
                      key={corridor.id}
                      className="grid grid-cols-12 min-h-[96px] hover:bg-slate-50/50 transition-colors"
                    >
                      {/* Left: Corridor Details */}
                      <div className="col-span-3 px-4 py-3 border-r border-slate-200 flex flex-col justify-center bg-slate-50/30">
                        <div className="flex items-center gap-1.5">
                          <span
                            className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${
                              corridor.lineType === 'UP'
                                ? 'bg-indigo-100 text-indigo-800'
                                : corridor.lineType === 'DOWN'
                                ? 'bg-teal-100 text-teal-800'
                                : 'bg-slate-200 text-slate-800'
                            }`}
                          >
                            {corridor.lineType} LINE
                          </span>
                          <span className="font-bold text-xs text-slate-900">{corridor.name}</span>
                        </div>
                        <div className="mt-1 text-[11px] text-slate-500 font-mono">
                          {corridor.trackKm} • {corridor.speedLimit}
                        </div>
                        {corridorConflicts.length > 0 && (
                          <div className="mt-1.5 flex items-center gap-1 text-[10px] font-bold text-red-600 bg-red-50 px-2 py-0.5 rounded border border-red-200 w-fit">
                            <AlertTriangle className="w-3 h-3" />
                            <span>{corridorConflicts.length} Active Collision</span>
                          </div>
                        )}
                      </div>

                      {/* Right: 8-Hour Gantt Track */}
                      <div className="col-span-9 relative grid grid-cols-8 divide-x divide-slate-100 h-full min-h-[96px] bg-white">
                        {/* Hour Grid Background Lines */}
                        {hours.slice(0, 8).map((hour) => (
                          <div
                            key={hour}
                            className={`h-full ${
                              hour >= 1 && hour <= 4 ? 'bg-emerald-50/20' : 'bg-transparent'
                            }`}
                          />
                        ))}

                        {/* Red Conflict Collision Box Overlay */}
                        {corridorConflicts.map((conf) => {
                          const leftPercent = (conf.overlapStartHour / 8) * 100;
                          const widthPercent =
                            ((conf.overlapEndHour - conf.overlapStartHour) / 8) * 100;

                          return (
                            <div
                              key={conf.id}
                              style={{
                                left: `${Math.max(0, Math.min(100, leftPercent))}%`,
                                width: `${Math.max(4, Math.min(100, widthPercent))}%`,
                              }}
                              className="absolute top-1.5 bottom-1.5 pattern-clash rounded-lg z-10 pointer-events-none flex items-center justify-center shadow-xs"
                            >
                              <div className="bg-red-600 text-white text-[10px] font-black px-2 py-0.5 rounded shadow-sm flex items-center gap-1 uppercase tracking-tight animate-bounce">
                                <AlertTriangle className="w-3 h-3" />
                                <span>🚨 CLASH ({conf.overlapDurationMins}m Overlap)</span>
                              </div>
                            </div>
                          );
                        })}

                        {/* Task Blocks */}
                        {corridorTasks.map((task, idx) => {
                          const leftPercent = (task.requestedStartHour / 8) * 100;
                          const widthPercent = (task.durationHours / 8) * 100;
                          const deptStyle = getDepartmentColor(task.department);
                          const isClashed = !!task.clashingTaskId;

                          // Alternate vertical stacking if multiple tasks are on same row
                          const topOffset = idx % 2 === 0 ? 'top-2' : 'top-11';

                          return (
                            <button
                              key={task.id}
                              onClick={() => onSelectTask(task)}
                              style={{
                                left: `${Math.max(0, Math.min(100, leftPercent))}%`,
                                width: `${Math.max(8, Math.min(100, widthPercent))}%`,
                              }}
                              className={`absolute ${topOffset} h-8 rounded-md px-2 py-1 text-left border ${deptStyle.border} ${deptStyle.bg} shadow-2xs hover:shadow-md transition-all flex items-center justify-between gap-1.5 group cursor-pointer z-20 hover:scale-[1.02]`}
                              title={`Click to inspect task #${task.taskNumber}: ${task.title}`}
                            >
                              <div className="flex items-center gap-1.5 truncate">
                                <span
                                  className={`px-1 rounded text-[9px] font-bold ${deptStyle.badge}`}
                                >
                                  {task.department.toUpperCase()}
                                </span>
                                <span className="font-bold text-[11px] text-slate-900 truncate">
                                  #{task.taskNumber} {task.defect.category}
                                </span>
                              </div>

                              <div className="flex items-center gap-1 shrink-0">
                                {task.defect.overdueDays >= 7 && (
                                  <span className="px-1 py-0.2 rounded bg-red-600 text-white font-bold text-[9px]">
                                    {task.defect.overdueDays}d Overdue
                                  </span>
                                )}
                                <span className="font-mono text-[10px] font-semibold text-slate-700 bg-white/80 px-1 rounded">
                                  {task.durationHours * 60}m
                                </span>
                              </div>
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

        {/* Timeline Footer with Explanatory Callout */}
        <div className="p-3 bg-slate-50 border-t border-slate-200 flex flex-wrap items-center justify-between gap-3 text-xs">
          <div className="flex items-center gap-2 text-slate-600">
            <Info className="w-4 h-4 text-sky-600 shrink-0" />
            <span>
              Click any maintenance block to view defect details, scoring matrix ($W_1 \dots W_4$), and conflict diagnostic.
            </span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-slate-400 font-medium">Ready to eliminate clashes?</span>
            <button
              onClick={onRunOptimizer}
              className="font-bold text-sky-700 hover:text-sky-900 flex items-center gap-1 hover:underline cursor-pointer"
            >
              <span>Solve with CP-SAT</span>
              <ChevronRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
