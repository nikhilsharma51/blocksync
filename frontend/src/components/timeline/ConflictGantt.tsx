'use client';

import React, { useState } from 'react';
import {
  AlertTriangle,
  Search,
  Zap,
  ChevronRight,
  Info,
  SlidersHorizontal,
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

  const hours = [0, 1, 2, 3, 4, 5, 6, 7, 8];

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

  const getDepartmentBadge = (dept: Department) => {
    switch (dept) {
      case 'Track':
        return {
          bg: 'bg-orange-50/90',
          border: 'border-orange-300',
          text: 'text-orange-950',
          chip: 'bg-orange-600 text-white',
        };
      case 'Signal':
        return {
          bg: 'bg-blue-50/90',
          border: 'border-blue-300',
          text: 'text-blue-950',
          chip: 'bg-blue-600 text-white',
        };
      case 'OHE':
        return {
          bg: 'bg-amber-50/90',
          border: 'border-amber-300',
          text: 'text-amber-950',
          chip: 'bg-amber-600 text-white',
        };
    }
  };

  return (
    <div className="space-y-3">
      {/* 1. Sleek Compact Metric Strip (No card clutter) */}
      <div className="bg-white border border-slate-200 rounded-lg p-3 px-4 shadow-2xs">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 divide-y md:divide-y-0 md:divide-x divide-slate-100">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-md bg-red-50 border border-red-200 flex items-center justify-center text-red-600 font-bold text-xs shrink-0">
              !
            </div>
            <div>
              <div className="text-[11px] font-medium text-slate-500">Active Conflicts</div>
              <div className="text-base font-bold text-slate-950 font-mono">14 Clashes</div>
            </div>
          </div>

          <div className="flex items-center gap-3 md:pl-4 pt-2 md:pt-0">
            <div className="w-8 h-8 rounded-md bg-slate-50 border border-slate-200 flex items-center justify-center text-slate-700 font-bold text-xs shrink-0">
              #
            </div>
            <div>
              <div className="text-[11px] font-medium text-slate-500">Pending Requests</div>
              <div className="text-base font-bold text-slate-950 font-mono">42 Tasks</div>
            </div>
          </div>

          <div className="flex items-center gap-3 md:pl-4 pt-2 md:pt-0">
            <div className="w-8 h-8 rounded-md bg-amber-50 border border-amber-200 flex items-center justify-center text-amber-700 font-bold text-xs shrink-0">
              7d
            </div>
            <div>
              <div className="text-[11px] font-medium text-slate-500">Overdue SLA Breaches</div>
              <div className="text-base font-bold text-slate-950 font-mono">9 Tasks</div>
            </div>
          </div>

          <div className="flex items-center gap-3 md:pl-4 pt-2 md:pt-0">
            <div className="w-8 h-8 rounded-md bg-slate-50 border border-slate-200 flex items-center justify-center text-slate-700 font-bold text-xs shrink-0">
              ⏱
            </div>
            <div>
              <div className="text-[11px] font-medium text-slate-500">Duplicate Stoppage Risk</div>
              <div className="text-base font-bold text-slate-950 font-mono">38.5 Hours</div>
            </div>
          </div>
        </div>
      </div>

      {/* 2. Streamlined Conflict Timeline Canvas */}
      <div className="bg-white border border-slate-200 rounded-lg overflow-hidden shadow-2xs">
        {/* Timeline Integrated Action Bar */}
        <div className="p-3 border-b border-slate-200 flex flex-wrap items-center justify-between gap-3 bg-slate-50/50">
          <div className="flex flex-wrap items-center gap-2.5">
            <span className="font-semibold text-xs text-slate-900">
              Raw Intake Timeline
            </span>
            <span className="text-[10px] font-mono font-medium text-red-700 bg-red-50 px-1.5 py-0.2 rounded border border-red-200">
              Uncoordinated State
            </span>

            <span className="text-slate-300 hidden sm:inline">|</span>

            {/* Corridor Select */}
            <select
              value={selectedCorridorId}
              onChange={(e) => setSelectedCorridorId(e.target.value)}
              className="text-xs font-medium py-1 px-2 rounded border border-slate-200 bg-white text-slate-800 focus:outline-hidden"
            >
              <option value="ALL">All Sections (6 Corridors)</option>
              {corridors.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name}
                </option>
              ))}
            </select>

            {/* Search */}
            <div className="relative">
              <Search className="w-3 h-3 text-slate-400 absolute left-2 top-2 pointer-events-none" />
              <input
                type="text"
                placeholder="Search defect..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-6 pr-2 py-0.5 text-xs rounded border border-slate-200 bg-white text-slate-900 w-36 focus:w-48 transition-all"
              />
            </div>
          </div>

          {/* Right Action Controls */}
          <div className="flex items-center gap-2">
            <button
              onClick={onToggleConflictPanel}
              className={`px-2.5 py-1 rounded text-xs font-medium border transition-all cursor-pointer ${
                isConflictPanelOpen
                  ? 'bg-red-50 text-red-900 border-red-300'
                  : 'bg-white text-slate-700 border-slate-200 hover:bg-slate-50'
              }`}
            >
              <span>Inspect {conflicts.length} Clashes</span>
            </button>

            <button
              onClick={onRunOptimizer}
              className="inline-flex items-center gap-1.5 px-3 py-1 rounded bg-slate-950 text-white hover:bg-slate-800 text-xs font-semibold shadow-2xs cursor-pointer active:scale-98"
            >
              <Zap className="w-3 h-3 text-amber-300 fill-amber-300" />
              <span>Solve with CP-SAT</span>
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
                  const corridorTasks = filteredTasks.filter((t) => t.corridorId === corridor.id);
                  const corridorConflicts = conflicts.filter(
                    (conf) =>
                      corridorTasks.some((t) => t.id === conf.taskA.id) &&
                      corridorTasks.some((t) => t.id === conf.taskB.id)
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

                        {/* Red Clash Box Overlay */}
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
                              className="absolute top-1 bottom-1 pattern-clash rounded z-10 pointer-events-none flex items-center justify-center"
                            >
                              <span className="bg-red-600 text-white text-[9px] font-bold px-1.5 py-0.2 rounded shadow-2xs font-mono">
                                CLASH {conf.overlapDurationMins}m
                              </span>
                            </div>
                          );
                        })}

                        {/* Task Blocks */}
                        {corridorTasks.map((task, idx) => {
                          const leftPercent = (task.requestedStartHour / 8) * 100;
                          const widthPercent = (task.durationHours / 8) * 100;
                          const style = getDepartmentBadge(task.department);
                          const topOffset = idx % 2 === 0 ? 'top-1.5' : 'top-10';

                          return (
                            <button
                              key={task.id}
                              onClick={() => onSelectTask(task)}
                              style={{
                                left: `${Math.max(0, Math.min(100, leftPercent))}%`,
                                width: `${Math.max(8, Math.min(100, widthPercent))}%`,
                              }}
                              className={`absolute ${topOffset} h-7 rounded px-2 py-0.5 text-left border ${style.border} ${style.bg} hover:border-slate-400 transition-all flex items-center justify-between gap-1.5 cursor-pointer z-20 shadow-2xs`}
                            >
                              <div className="flex items-center gap-1.5 truncate">
                                <span className="font-semibold text-[10px] text-slate-900 truncate">
                                  #{task.taskNumber} {task.defect.category}
                                </span>
                              </div>

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
    </div>
  );
};
