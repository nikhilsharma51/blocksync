'use client';

import React, { useState, useEffect } from 'react';
import {
  Train,
  Clock,
  Zap,
  ChevronDown,
  Sparkles,
  ShieldCheck,
  Award,
  AlertTriangle,
} from 'lucide-react';
import { Department, ActivePageView } from '../../types/railway';

interface AppHeaderProps {
  activeView: ActivePageView;
  onViewChange: (view: ActivePageView) => void;
  onRunOptimizer: () => void;
  selectedDepartments: Department[];
  onToggleDepartment: (dept: Department) => void;
  isPlanApproved?: boolean;
  onToggleDemoMode: () => void;
  isDemoModeOpen: boolean;
}

export const AppHeader: React.FC<AppHeaderProps> = ({
  activeView,
  onViewChange,
  onRunOptimizer,
  selectedDepartments,
  onToggleDepartment,
  isPlanApproved = false,
  onToggleDemoMode,
  isDemoModeOpen,
}) => {
  const [currentTime, setCurrentTime] = useState<string>('19:10:00 IST');
  const [selectedDivision, setSelectedDivision] = useState<string>('Delhi - Kanpur Mainline');

  useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      const timeStr = now.toLocaleTimeString('en-IN', {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        hour12: false,
      });
      setCurrentTime(`${timeStr} IST`);
    };
    const interval = setInterval(updateTime, 1000);
    return () => clearInterval(interval);
  }, []);

  return (
    <header className="sticky top-0 z-30 bg-white border-b border-slate-200">
      <div className="flex items-center justify-between px-5 h-14 gap-4">
        {/* Left: Division & Horizon Context */}
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 text-xs">
            <span className="text-slate-400 font-medium">NR /</span>
            <div className="relative inline-flex items-center">
              <select
                value={selectedDivision}
                onChange={(e) => setSelectedDivision(e.target.value)}
                className="appearance-none font-semibold text-slate-900 bg-transparent pr-5 cursor-pointer focus:outline-hidden hover:text-slate-700 text-xs"
              >
                <option value="Delhi - Kanpur Mainline">Delhi - Kanpur Mainline</option>
                <option value="Delhi - Ambala Section">Delhi - Ambala Section</option>
                <option value="Howrah - Asansol Trunk">Howrah - Asansol Trunk</option>
                <option value="Mumbai - Surat Corridor">Mumbai - Surat Corridor</option>
              </select>
              <ChevronDown className="w-3 h-3 text-slate-400 absolute right-0 pointer-events-none" />
            </div>
            <span className="text-slate-300">•</span>
            <span className="text-slate-500 font-medium">Week 36 (Aug 31 – Sep 06)</span>
          </div>

          {isPlanApproved && (
            <span className="hidden lg:inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-medium bg-emerald-50 text-emerald-800 border border-emerald-200">
              <ShieldCheck className="w-3 h-3 text-emerald-600" />
              <span>Bulletin Approved</span>
            </span>
          )}
        </div>

        {/* Center: Department Filters */}
        <div className="hidden md:flex items-center gap-1 p-1 bg-slate-100/80 rounded-md border border-slate-200/60 text-xs">
          <button
            onClick={() => onToggleDepartment('Track')}
            className={`px-2.5 py-1 rounded transition-all flex items-center gap-1.5 cursor-pointer text-xs font-medium ${
              selectedDepartments.includes('Track')
                ? 'bg-white text-slate-900 shadow-2xs'
                : 'text-slate-400 hover:text-slate-600'
            }`}
          >
            <span className="w-1.5 h-1.5 rounded-full bg-orange-600"></span>
            <span>Track</span>
          </button>

          <button
            onClick={() => onToggleDepartment('Signal')}
            className={`px-2.5 py-1 rounded transition-all flex items-center gap-1.5 cursor-pointer text-xs font-medium ${
              selectedDepartments.includes('Signal')
                ? 'bg-white text-slate-900 shadow-2xs'
                : 'text-slate-400 hover:text-slate-600'
            }`}
          >
            <span className="w-1.5 h-1.5 rounded-full bg-blue-600"></span>
            <span>Signal</span>
          </button>

          <button
            onClick={() => onToggleDepartment('OHE')}
            className={`px-2.5 py-1 rounded transition-all flex items-center gap-1.5 cursor-pointer text-xs font-medium ${
              selectedDepartments.includes('OHE')
                ? 'bg-white text-slate-900 shadow-2xs'
                : 'text-slate-400 hover:text-slate-600'
            }`}
          >
            <span className="w-1.5 h-1.5 rounded-full bg-amber-600"></span>
            <span>Traction</span>
          </button>
        </div>

        {/* Right: Actions, Live Clock & Optimizer */}
        <div className="flex items-center gap-2.5">
          {/* Live Shift Clock */}
          <div className="hidden sm:flex items-center gap-1.5 text-xs text-slate-500 font-mono pr-1">
            <Clock className="w-3.5 h-3.5 text-slate-400" />
            <span>{currentTime}</span>
          </div>

          {/* Judge Demo Mode Toggle */}
          <button
            onClick={onToggleDemoMode}
            className={`px-2.5 py-1.5 rounded-md text-xs font-semibold transition-all flex items-center gap-1.5 cursor-pointer border ${
              isDemoModeOpen
                ? 'bg-slate-900 text-white border-slate-900'
                : 'bg-white text-slate-700 border-slate-200 hover:bg-slate-50'
            }`}
            title="Toggle 5-minute Judge Walkthrough presentation bar"
          >
            <Award className="w-3.5 h-3.5 text-amber-400" />
            <span className="hidden sm:inline">Judge Demo</span>
          </button>

          {/* Primary View Quick Toggle */}
          <div className="inline-flex p-0.5 bg-slate-100 rounded-md border border-slate-200 text-xs font-medium">
            <button
              onClick={() => onViewChange('conflicts')}
              className={`px-2.5 py-1 rounded transition-all cursor-pointer ${
                activeView === 'conflicts'
                  ? 'bg-white text-slate-950 font-bold shadow-2xs'
                  : 'text-slate-500 hover:text-slate-800'
              }`}
            >
              Conflicts
            </button>
            <button
              onClick={() => onViewChange('optimized')}
              className={`px-2.5 py-1 rounded transition-all cursor-pointer ${
                activeView === 'optimized'
                  ? 'bg-white text-slate-950 font-bold shadow-2xs'
                  : 'text-slate-500 hover:text-slate-800'
              }`}
            >
              Schedule
            </button>
          </div>

          {/* Run CP-SAT Optimizer */}
          <button
            onClick={onRunOptimizer}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-slate-950 hover:bg-slate-800 text-white text-xs font-semibold transition-all cursor-pointer active:scale-98 shadow-xs"
          >
            <Zap className="w-3 h-3 text-amber-300 fill-amber-300" />
            <span>Solve</span>
          </button>
        </div>
      </div>
    </header>
  );
};
