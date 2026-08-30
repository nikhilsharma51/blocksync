'use client';

import React from 'react';
import {
  AlertTriangle,
  Sparkles,
  ClipboardList,
  BarChart3,
  MapPin,
  FileCheck,
  ChevronLeft,
  ChevronRight,
  Shield,
  Cpu,
} from 'lucide-react';
import { ActivePageView } from '../../types/railway';

interface AppSidebarProps {
  activeView: ActivePageView;
  onViewChange: (view: ActivePageView) => void;
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
      className={`relative flex flex-col justify-between bg-white border-r border-slate-200 transition-all duration-200 z-20 shrink-0 ${
        isCollapsed ? 'w-16' : 'w-60'
      }`}
    >
      {/* Brand Header */}
      <div>
        <div className="flex items-center justify-between px-4 h-14 border-b border-slate-200">
          {!isCollapsed ? (
            <div className="flex items-center gap-2">
              <span className="w-6 h-6 rounded-md bg-slate-950 flex items-center justify-center text-white font-black text-xs">
                B
              </span>
              <div>
                <span className="font-bold text-slate-950 tracking-tight text-sm">BlockSync</span>
                <span className="ml-1 text-[10px] font-mono text-slate-400">IR-AI</span>
              </div>
            </div>
          ) : (
            <span className="w-6 h-6 mx-auto rounded-md bg-slate-950 flex items-center justify-center text-white font-black text-xs">
              B
            </span>
          )}

          <button
            onClick={onToggleCollapse}
            className="p-1 rounded text-slate-400 hover:text-slate-700 hover:bg-slate-100 cursor-pointer"
            title={isCollapsed ? 'Expand Sidebar' : 'Collapse Sidebar'}
          >
            {isCollapsed ? <ChevronRight className="w-3.5 h-3.5" /> : <ChevronLeft className="w-3.5 h-3.5" />}
          </button>
        </div>

        {/* Navigation Sections */}
        <div className="p-2.5 space-y-5">
          {/* Main Scheduling Engine */}
          <div className="space-y-1">
            {!isCollapsed && (
              <div className="px-2 mb-1.5 text-[10px] font-bold uppercase tracking-wider text-slate-400">
                Core Engine
              </div>
            )}

            {/* Page 1: Conflict Matrix */}
            <button
              onClick={() => onViewChange('conflicts')}
              className={`w-full flex items-center justify-between px-2.5 py-1.5 rounded-md text-xs font-medium transition-all cursor-pointer ${
                activeView === 'conflicts'
                  ? 'bg-slate-100 text-slate-950 font-semibold'
                  : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'
              }`}
            >
              <div className="flex items-center gap-2">
                <AlertTriangle
                  className={`w-3.5 h-3.5 ${activeView === 'conflicts' ? 'text-red-600' : 'text-slate-400'}`}
                />
                {!isCollapsed && <span>Conflict Matrix</span>}
              </div>
              {!isCollapsed && (
                <span className="text-[10px] font-mono font-semibold text-red-600 bg-red-50 px-1.5 py-0.2 rounded border border-red-200">
                  {conflictCount}
                </span>
              )}
            </button>

            {/* Page 2: AI Master Schedule */}
            <button
              onClick={() => onViewChange('optimized')}
              className={`w-full flex items-center justify-between px-2.5 py-1.5 rounded-md text-xs font-medium transition-all cursor-pointer ${
                activeView === 'optimized'
                  ? 'bg-slate-100 text-slate-950 font-semibold'
                  : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'
              }`}
            >
              <div className="flex items-center gap-2">
                <Sparkles
                  className={`w-3.5 h-3.5 ${activeView === 'optimized' ? 'text-emerald-600' : 'text-slate-400'}`}
                />
                {!isCollapsed && <span>Master Schedule</span>}
              </div>
              {!isCollapsed && (
                <span className="text-[10px] font-mono font-semibold text-emerald-700 bg-emerald-50 px-1.5 py-0.2 rounded border border-emerald-200">
                  {resolvedCount} OK
                </span>
              )}
            </button>
          </div>

          {/* Operational Workflows */}
          <div className="space-y-1">
            {!isCollapsed && (
              <div className="px-2 mb-1.5 text-[10px] font-bold uppercase tracking-wider text-slate-400">
                Workflows
              </div>
            )}

            {/* Page 3: Department Feeds */}
            <button
              onClick={() => onViewChange('intake')}
              className={`w-full flex items-center justify-between px-2.5 py-1.5 rounded-md text-xs font-medium transition-all cursor-pointer ${
                activeView === 'intake'
                  ? 'bg-slate-100 text-slate-950 font-semibold'
                  : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'
              }`}
            >
              <div className="flex items-center gap-2">
                <ClipboardList className={`w-3.5 h-3.5 ${activeView === 'intake' ? 'text-slate-900' : 'text-slate-400'}`} />
                {!isCollapsed && <span>Intake Feeds</span>}
              </div>
              {!isCollapsed && (
                <span className="text-[10px] font-mono text-slate-400">52</span>
              )}
            </button>

            {/* Page 4: Safety Dashboard */}
            <button
              onClick={() => onViewChange('safety')}
              className={`w-full flex items-center justify-between px-2.5 py-1.5 rounded-md text-xs font-medium transition-all cursor-pointer ${
                activeView === 'safety'
                  ? 'bg-slate-100 text-slate-950 font-semibold'
                  : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'
              }`}
            >
              <div className="flex items-center gap-2">
                <BarChart3 className={`w-3.5 h-3.5 ${activeView === 'safety' ? 'text-slate-900' : 'text-slate-400'}`} />
                {!isCollapsed && <span>Safety &amp; SLA</span>}
              </div>
              {!isCollapsed && (
                <span className="text-[10px] font-mono text-slate-400">DRM</span>
              )}
            </button>

            {/* Page 5: Corridor Timetable */}
            <button
              onClick={() => onViewChange('corridormap')}
              className={`w-full flex items-center justify-between px-2.5 py-1.5 rounded-md text-xs font-medium transition-all cursor-pointer ${
                activeView === 'corridormap'
                  ? 'bg-slate-100 text-slate-950 font-semibold'
                  : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'
              }`}
            >
              <div className="flex items-center gap-2">
                <MapPin className={`w-3.5 h-3.5 ${activeView === 'corridormap' ? 'text-slate-900' : 'text-slate-400'}`} />
                {!isCollapsed && <span>COA Windows</span>}
              </div>
              {!isCollapsed && (
                <span className="text-[10px] font-mono text-slate-400">Map</span>
              )}
            </button>

            {/* Page 6: Shift Execution */}
            <button
              onClick={() => onViewChange('execution')}
              className={`w-full flex items-center justify-between px-2.5 py-1.5 rounded-md text-xs font-medium transition-all cursor-pointer ${
                activeView === 'execution'
                  ? 'bg-slate-100 text-slate-950 font-semibold'
                  : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'
              }`}
            >
              <div className="flex items-center gap-2">
                <FileCheck className={`w-3.5 h-3.5 ${activeView === 'execution' ? 'text-slate-900' : 'text-slate-400'}`} />
                {!isCollapsed && <span>Shift Execution</span>}
              </div>
              {!isCollapsed && (
                <span className="text-[10px] font-mono text-slate-400">Log</span>
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Minimal Footer */}
      <div className="p-3 border-t border-slate-200 text-xs text-slate-500">
        {!isCollapsed ? (
          <div className="flex items-center justify-between text-[11px]">
            <div className="flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
              <span className="font-mono text-slate-700">CP-SAT v9.8</span>
            </div>
            <span className="text-slate-400">DEL-04</span>
          </div>
        ) : (
          <div className="flex justify-center">
            <span className="w-2 h-2 rounded-full bg-emerald-500" title="CP-SAT Ready"></span>
          </div>
        )}
      </div>
    </aside>
  );
};
