'use client';

import React from 'react';
import {
  AlertTriangle,
  X,
  Zap,
  ArrowRight,
  ShieldAlert,
  Clock,
  Layers,
  ChevronRight,
} from 'lucide-react';
import { ConflictPair, MaintenanceTask } from '../../types/railway';

interface ConflictListPanelProps {
  conflicts: ConflictPair[];
  isOpen: boolean;
  onClose: () => void;
  onSelectTask: (task: MaintenanceTask) => void;
  onRunOptimizer: () => void;
}

export const ConflictListPanel: React.FC<ConflictListPanelProps> = ({
  conflicts,
  isOpen,
  onClose,
  onSelectTask,
  onRunOptimizer,
}) => {
  if (!isOpen) return null;

  return (
    <div className="p-4 bg-red-50/70 border border-red-200 rounded-xl space-y-3 animate-in fade-in">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="p-1 rounded-md bg-red-600 text-white">
            <AlertTriangle className="w-4 h-4" />
          </span>
          <div>
            <h3 className="text-xs font-bold uppercase tracking-wider text-red-950">
              Active Corridor Clashes &amp; Double-Bookings ({conflicts.length} Pairs)
            </h3>
            <p className="text-[11px] text-red-800">
              Conflicting work requests competing for the same track segment during overlapping windows.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={onRunOptimizer}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-red-700 hover:bg-red-800 text-white text-xs font-bold shadow-xs cursor-pointer active:scale-98"
          >
            <Zap className="w-3.5 h-3.5 text-amber-300 fill-amber-300" />
            <span>Resolve All with CP-SAT</span>
          </button>
          <button
            onClick={onClose}
            className="p-1 rounded-lg text-slate-400 hover:text-slate-700 hover:bg-red-100 cursor-pointer"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3 pt-2">
        {conflicts.map((conf) => (
          <div
            key={conf.id}
            className="p-3 bg-white border border-red-200 rounded-lg shadow-2xs space-y-2.5 hover:border-red-300 transition-all"
          >
            <div className="flex items-center justify-between text-[11px]">
              <span className="font-bold text-red-900">{conf.corridorName}</span>
              <span className="px-1.5 py-0.2 rounded bg-red-100 text-red-800 font-bold">
                {conf.overlapDurationMins}m Overlap
              </span>
            </div>

            {/* Conflicting Task Pair Box */}
            <div className="space-y-1.5 text-xs">
              {/* Task A */}
              <div
                onClick={() => onSelectTask(conf.taskA)}
                className="p-2 rounded bg-orange-50/80 border border-orange-200 flex items-center justify-between cursor-pointer hover:bg-orange-100 transition-colors"
                title="Inspect Task A"
              >
                <div className="flex items-center gap-1.5 truncate">
                  <span className="px-1 py-0.2 rounded bg-orange-600 text-white font-bold text-[9px]">
                    {conf.taskA.department}
                  </span>
                  <span className="font-semibold text-slate-900 truncate">
                    #{conf.taskA.taskNumber} {conf.taskA.title}
                  </span>
                </div>
                <ChevronRight className="w-3.5 h-3.5 text-slate-400 shrink-0" />
              </div>

              {/* Task B */}
              <div
                onClick={() => onSelectTask(conf.taskB)}
                className="p-2 rounded bg-amber-50/80 border border-amber-200 flex items-center justify-between cursor-pointer hover:bg-amber-100 transition-colors"
                title="Inspect Task B"
              >
                <div className="flex items-center gap-1.5 truncate">
                  <span className="px-1 py-0.2 rounded bg-amber-600 text-white font-bold text-[9px]">
                    {conf.taskB.department}
                  </span>
                  <span className="font-semibold text-slate-900 truncate">
                    #{conf.taskB.taskNumber} {conf.taskB.title}
                  </span>
                </div>
                <ChevronRight className="w-3.5 h-3.5 text-slate-400 shrink-0" />
              </div>
            </div>

            {/* Resolution Strategy Preview */}
            <div className="text-[11px] text-slate-600 pt-1.5 border-t border-slate-100 leading-relaxed font-mono text-[10px]">
              <strong className="text-slate-800">CP-SAT Strategy:</strong> {conf.resolutionStrategy}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
