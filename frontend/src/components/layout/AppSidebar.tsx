'use client';

import React from 'react';
import {
  AlertTriangle,
  Sparkles,
  ClipboardList,
  BarChart3,
  MapPin,
  FileCheck,
  Radio,
  Cpu,
  Layers,
  ChevronLeft,
  ChevronRight,
  Shield,
  Activity,
} from 'lucide-react';

interface AppSidebarProps {
  activeView: 'conflicts' | 'optimized';
  onViewChange: (view: 'conflicts' | 'optimized') => void;
  isCollapsed: boolean;
  onToggleCollapse: () => void;
  conflictCount: number;
  resolvedCount: number;
}

export const AppSidebar: React.FC<AppSidebarProps> = ({
  activeView,
  onViewChange,
  isCollapsed,
  onToggleCollapse,
  conflictCount,
  resolvedCount,
}) => {
  return (
    <aside
      className={`relative flex flex-col justify-between bg-white border-r border-slate-200 transition-all duration-300 z-20 shrink-0 ${
        isCollapsed ? 'w-18' : 'w-64'
      }`}
    >
      {/* Brand Header */}
      <div>
        <div className="flex items-center justify-between px-4 py-4 border-b border-slate-100">
          {!isCollapsed ? (
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-lg bg-slate-900 flex items-center justify-center text-white font-bold text-base shadow-xs">
                🚆
              </div>
              <div>
                <div className="flex items-center gap-1.5">
                  <span className="font-bold text-slate-950 tracking-tight text-base">BLOCKSYNC</span>
                  <span className="text-[10px] font-bold px-1.5 py-0.2 rounded bg-sky-100 text-sky-800 border border-sky-200">
                    IR-AI
                  </span>
                </div>
                <div className="text-[10px] font-medium text-slate-400">
                  Northern Railway • PS 26027
                </div>
              </div>
            </div>
          ) : (
            <div className="w-8 h-8 mx-auto rounded-lg bg-slate-900 flex items-center justify-center text-white font-bold text-base">
              🚆
            </div>
          )}

          <button
            onClick={onToggleCollapse}
            className="p-1 rounded-md text-slate-400 hover:text-slate-600 hover:bg-slate-100"
            title={isCollapsed ? 'Expand Sidebar' : 'Collapse Sidebar'}
          >
            {isCollapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
          </button>
        </div>

        {/* Navigation Categories */}
        <div className="p-3 space-y-6">
          {/* Core P0 Demo Section */}
          <div>
            {!isCollapsed && (
              <div className="px-2 mb-2 text-[11px] font-bold uppercase tracking-wider text-slate-400">
                P0 Block Engine
              </div>
            )}

            <nav className="space-y-1">
              {/* Page 1: Conflict Matrix */}
              <button
                onClick={() => onViewChange('conflicts')}
                className={`w-full flex items-center justify-between px-3 py-2.5 rounded-lg text-xs font-semibold transition-all ${
                  activeView === 'conflicts'
                    ? 'bg-red-50 text-red-950 border border-red-200 shadow-2xs'
                    : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'
                }`}
                title="Conflict Matrix (The Broken Schedule)"
              >
                <div className="flex items-center gap-2.5">
                  <AlertTriangle
                    className={`w-4 h-4 ${activeView === 'conflicts' ? 'text-red-600' : 'text-slate-400'}`}
                  />
                  {!isCollapsed && <span>1. Conflict Matrix</span>}
                </div>
                {!isCollapsed && (
                  <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-red-600 text-white">
                    {conflictCount}
                  </span>
                )}
              </button>

              {/* Page 2: AI Master Schedule */}
              <button
                onClick={() => onViewChange('optimized')}
                className={`w-full flex items-center justify-between px-3 py-2.5 rounded-lg text-xs font-semibold transition-all ${
                  activeView === 'optimized'
                    ? 'bg-emerald-50 text-emerald-950 border border-emerald-200 shadow-2xs'
                    : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'
                }`}
                title="Master Optimized Gantt & Integrated Blocks"
              >
                <div className="flex items-center gap-2.5">
                  <Sparkles
                    className={`w-4 h-4 ${activeView === 'optimized' ? 'text-emerald-600' : 'text-slate-400'}`}
                  />
                  {!isCollapsed && <span>2. AI Master Schedule</span>}
                </div>
                {!isCollapsed && (
                  <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-emerald-600 text-white">
                    {resolvedCount} OK
                  </span>
                )}
              </button>
            </nav>
          </div>

          {/* Phase 2 / Integration Scope (Clearly marked as future phases) */}
          <div>
            {!isCollapsed && (
              <div className="px-2 mb-2 text-[11px] font-bold uppercase tracking-wider text-slate-400 flex items-center justify-between">
                <span>Enterprise Modules</span>
                <span className="text-[9px] text-slate-400 font-normal">Phase 2</span>
              </div>
            )}

            <nav className="space-y-1 text-slate-400">
              <div
                className="flex items-center justify-between px-3 py-2 rounded-lg text-xs font-medium text-slate-400 opacity-60 cursor-not-allowed"
                title="Phase 2 Scope: Department Feeds (TMS, SMMS, TDMS)"
              >
                <div className="flex items-center gap-2.5">
                  <ClipboardList className="w-4 h-4 text-slate-400" />
                  {!isCollapsed && <span>Department Feeds</span>}
                </div>
                {!isCollapsed && (
                  <span className="text-[10px] bg-slate-100 text-slate-500 px-1 rounded">Intake</span>
                )}
              </div>

              <div
                className="flex items-center justify-between px-3 py-2 rounded-lg text-xs font-medium text-slate-400 opacity-60 cursor-not-allowed"
                title="Phase 2 Scope: Safety & SLA Backlog Dashboard"
              >
                <div className="flex items-center gap-2.5">
                  <BarChart3 className="w-4 h-4 text-slate-400" />
                  {!isCollapsed && <span>SLA & Safety Backlog</span>}
                </div>
                {!isCollapsed && (
                  <span className="text-[10px] bg-slate-100 text-slate-500 px-1 rounded">DRM</span>
                )}
              </div>

              <div
                className="flex items-center justify-between px-3 py-2 rounded-lg text-xs font-medium text-slate-400 opacity-60 cursor-not-allowed"
                title="Phase 2 Scope: Corridor Timetable Availability (COA)"
              >
                <div className="flex items-center gap-2.5">
                  <MapPin className="w-4 h-4 text-slate-400" />
                  {!isCollapsed && <span>COA Free Windows</span>}
                </div>
                {!isCollapsed && (
                  <span className="text-[10px] bg-slate-100 text-slate-500 px-1 rounded">COA</span>
                )}
              </div>

              <div
                className="flex items-center justify-between px-3 py-2 rounded-lg text-xs font-medium text-slate-400 opacity-60 cursor-not-allowed"
                title="Phase 2 Scope: Shift Execution & Audit Trail"
              >
                <div className="flex items-center gap-2.5">
                  <FileCheck className="w-4 h-4 text-slate-400" />
                  {!isCollapsed && <span>Shift Audit Trail</span>}
                </div>
                {!isCollapsed && (
                  <span className="text-[10px] bg-slate-100 text-slate-500 px-1 rounded">Logs</span>
                )}
              </div>
            </nav>
          </div>
        </div>
      </div>

      {/* Bottom Status & Engine Health */}
      <div className="p-3 border-t border-slate-200 bg-slate-50">
        {!isCollapsed ? (
          <div className="space-y-2">
            <div className="p-2.5 rounded-lg bg-white border border-slate-200 text-[11px] space-y-1.5 shadow-2xs">
              <div className="flex items-center justify-between font-semibold text-slate-800">
                <div className="flex items-center gap-1.5">
                  <Cpu className="w-3.5 h-3.5 text-sky-600" />
                  <span>OR-Tools CP-SAT</span>
                </div>
                <span className="inline-flex items-center gap-1 text-[10px] text-emerald-600 font-bold">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-500"></span> READY
                </span>
              </div>
              <div className="text-[10px] text-slate-500">
                128 Constraints • Single-Division Exact Integer Solver
              </div>
            </div>

            <div className="flex items-center justify-between px-1 text-[10px] text-slate-500">
              <div className="flex items-center gap-1">
                <Shield className="w-3 h-3 text-slate-400" />
                <span>Role: Section Controller</span>
              </div>
              <span className="font-mono text-slate-600">DEL-CTRL-04</span>
            </div>
          </div>
        ) : (
          <div className="flex flex-col items-center gap-2 py-1 text-slate-400">
            <span title="CP-SAT Solver Active">
              <Cpu className="w-4 h-4 text-sky-600" />
            </span>
            <span title="Section Controller">
              <Shield className="w-4 h-4 text-slate-400" />
            </span>
          </div>
        )}
      </div>
    </aside>
  );
};
