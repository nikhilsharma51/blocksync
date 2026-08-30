'use client';

import React, { useState, useEffect } from 'react';
import {
  Train,
  Clock,
  Zap,
  CheckCircle2,
  AlertTriangle,
  SlidersHorizontal,
  ChevronDown,
  Sparkles,
  ShieldCheck,
} from 'lucide-react';
import { Department } from '../../types/railway';

interface AppHeaderProps {
  activeView: 'conflicts' | 'optimized';
  onViewChange: (view: 'conflicts' | 'optimized') => void;
  onRunOptimizer: () => void;
  selectedDepartments: Department[];
  onToggleDepartment: (dept: Department) => void;
  isPlanApproved?: boolean;
}

export const AppHeader: React.FC<AppHeaderProps> = ({
  activeView,
  onViewChange,
  onRunOptimizer,
  selectedDepartments,
  onToggleDepartment,
  isPlanApproved = false,
}) => {
  const [currentTime, setCurrentTime] = useState<string>('30 Aug 2026, 19:10:00 IST');
  const [selectedDivision, setSelectedDivision] = useState<string>('Delhi - Kanpur Mainline (Northern Railway)');

  useEffect(() => {
    // Realistic live clock simulation
    const updateTime = () => {
      const now = new Date();
      const timeStr = now.toLocaleTimeString('en-IN', {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        hour12: false,
      });
      setCurrentTime(`30 Aug 2026, ${timeStr} IST`);
    };
    const interval = setInterval(updateTime, 1000);
    return () => clearInterval(interval);
  }, []);

  return (
    <header className="sticky top-0 z-30 bg-white border-b border-slate-200 shadow-xs">
      {/* Top Banner with System Status and Division Context */}
      <div className="flex flex-wrap items-center justify-between px-6 py-2.5 bg-slate-50 border-b border-slate-100 text-xs text-slate-600 gap-3">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-1.5 font-medium text-slate-900">
            <span className="inline-block w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
            <span className="text-slate-500 font-normal">System:</span> CRiS Timetable & TMS Synced
          </div>
          <div className="hidden sm:flex items-center gap-1.5 text-slate-500">
            <Clock className="w-3.5 h-3.5 text-slate-400" />
            <span className="font-mono text-slate-700">{currentTime}</span>
            <span className="px-1.5 py-0.5 rounded bg-slate-200 text-slate-700 font-semibold text-[10px]">SHIFT-B</span>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1 text-slate-500">
            <span className="font-normal text-slate-500">Engine:</span>
            <span className="font-medium text-slate-800 bg-white px-2 py-0.5 rounded border border-slate-200">
              Google OR-Tools CP-SAT v9.8
            </span>
          </div>
          {isPlanApproved ? (
            <div className="flex items-center gap-1.5 px-2.5 py-0.5 rounded bg-emerald-100 text-emerald-800 border border-emerald-300 font-medium">
              <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
              <span>Block Bulletin #BB-2026-36-A Approved</span>
            </div>
          ) : (
            <div className="flex items-center gap-1.5 px-2.5 py-0.5 rounded bg-amber-50 text-amber-800 border border-amber-200 font-medium">
              <AlertTriangle className="w-3.5 h-3.5 text-amber-600" />
              <span>Pending Review & Controller Sign-off</span>
            </div>
          )}
        </div>
      </div>

      {/* Main Action Bar */}
      <div className="flex flex-col md:flex-row md:items-center justify-between px-6 py-3 gap-4">
        {/* Left: Division & Horizon Selectors */}
        <div className="flex flex-wrap items-center gap-3">
          <div className="flex items-center gap-2">
            <div className="p-1.5 rounded-lg bg-slate-100 text-slate-700 border border-slate-200">
              <Train className="w-4 h-4" />
            </div>
            <div>
              <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">Division & Route</div>
              <div className="relative inline-block">
                <select
                  value={selectedDivision}
                  onChange={(e) => setSelectedDivision(e.target.value)}
                  className="appearance-none font-semibold text-slate-900 bg-transparent pr-6 cursor-pointer focus:outline-hidden hover:text-sky-700 text-sm"
                >
                  <option value="Delhi - Kanpur Mainline (Northern Railway)">Delhi - Kanpur Mainline (Northern Railway)</option>
                  <option value="Delhi - Ambala Cantt Section (NR)">Delhi - Ambala Cantt Section (NR)</option>
                  <option value="Howrah - Asansol Trunk Section (ER)">Howrah - Asansol Trunk Section (ER)</option>
                  <option value="Mumbai Central - Surat Corridor (WR)">Mumbai Central - Surat Corridor (WR)</option>
                </select>
                <ChevronDown className="w-3.5 h-3.5 text-slate-400 absolute right-0 top-1 pointer-events-none" />
              </div>
            </div>
          </div>

          <div className="h-6 w-px bg-slate-200 hidden md:block" />

          <div>
            <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">Planning Horizon</div>
            <div className="font-medium text-slate-800 text-sm">
              Week 36 (Aug 31 – Sep 06, 2026)
            </div>
          </div>
        </div>

        {/* Center: Department Filters */}
        <div className="flex items-center gap-2">
          <span className="text-xs text-slate-400 font-medium mr-1 hidden lg:inline">Depts:</span>
          
          <button
            onClick={() => onToggleDepartment('Track')}
            className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium border transition-colors ${
              selectedDepartments.includes('Track')
                ? 'bg-orange-50 text-orange-900 border-orange-300'
                : 'bg-white text-slate-400 border-slate-200 opacity-60 hover:opacity-100'
            }`}
            title="Engineering / Track Department (TMS)"
          >
            <span className="w-2 h-2 rounded-full bg-orange-600"></span>
            Track (TMS)
          </button>

          <button
            onClick={() => onToggleDepartment('Signal')}
            className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium border transition-colors ${
              selectedDepartments.includes('Signal')
                ? 'bg-blue-50 text-blue-900 border-blue-300'
                : 'bg-white text-slate-400 border-slate-200 opacity-60 hover:opacity-100'
            }`}
            title="Signal & Telecom Department (SMMS)"
          >
            <span className="w-2 h-2 rounded-full bg-blue-600"></span>
            Signal (SMMS)
          </button>

          <button
            onClick={() => onToggleDepartment('OHE')}
            className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium border transition-colors ${
              selectedDepartments.includes('OHE')
                ? 'bg-amber-50 text-amber-900 border-amber-300'
                : 'bg-white text-slate-400 border-slate-200 opacity-60 hover:opacity-100'
            }`}
            title="Traction / OHE Power Department (TDMS)"
          >
            <span className="w-2 h-2 rounded-full bg-amber-600"></span>
            Traction (TDMS)
          </button>
        </div>

        {/* Right: View Switcher and AI Optimizer Trigger */}
        <div className="flex items-center gap-3">
          {/* Segmented View Switcher */}
          <div className="inline-flex p-1 bg-slate-100 rounded-lg border border-slate-200 text-xs font-medium">
            <button
              onClick={() => onViewChange('conflicts')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md transition-all ${
                activeView === 'conflicts'
                  ? 'bg-white text-red-700 shadow-xs font-semibold'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              <AlertTriangle className="w-3.5 h-3.5 text-red-600" />
              <span>1. Conflict Matrix</span>
            </button>
            <button
              onClick={() => onViewChange('optimized')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md transition-all ${
                activeView === 'optimized'
                  ? 'bg-white text-emerald-700 shadow-xs font-semibold'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              <Sparkles className="w-3.5 h-3.5 text-emerald-600" />
              <span>2. AI Master Gantt</span>
            </button>
          </div>

          {/* Core Optimizer Button */}
          <button
            onClick={onRunOptimizer}
            className="inline-flex items-center justify-center gap-2 px-4 py-2 rounded-lg bg-slate-900 text-white hover:bg-slate-800 text-xs font-semibold shadow-sm transition-all focus:outline-hidden focus:ring-2 focus:ring-slate-950 focus:ring-offset-2 active:scale-98"
          >
            <Zap className="w-3.5 h-3.5 text-amber-300 fill-amber-300" />
            <span>Run CP-SAT Optimizer</span>
          </button>
        </div>
      </div>
    </header>
  );
};
