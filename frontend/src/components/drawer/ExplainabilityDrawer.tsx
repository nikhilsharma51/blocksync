'use client';

import React, { useState } from 'react';
import {
  X,
  Sparkles,
  Cpu,
  ShieldCheck,
  Clock,
  AlertTriangle,
  Flame,
  CheckCircle2,
  Users,
  Wrench,
  Gauge,
  FileCheck2,
  Share2,
  Info,
} from 'lucide-react';
import { MaintenanceTask, Department } from '../../types/railway';

interface ExplainabilityDrawerProps {
  task: MaintenanceTask | null;
  onClose: () => void;
}

export const ExplainabilityDrawer: React.FC<ExplainabilityDrawerProps> = ({
  task,
  onClose,
}) => {
  const [activeTab, setActiveTab] = useState<'ai' | 'math' | 'defect'>('ai');

  if (!task) return null;

  const getDepartmentColor = (dept: Department) => {
    switch (dept) {
      case 'Track':
        return { badge: 'bg-orange-600 text-white', border: 'border-orange-200', bg: 'bg-orange-50' };
      case 'Signal':
        return { badge: 'bg-blue-600 text-white', border: 'border-blue-200', bg: 'bg-blue-50' };
      case 'OHE':
        return { badge: 'bg-amber-600 text-white', border: 'border-amber-200', bg: 'bg-amber-50' };
    }
  };

  const deptStyle = getDepartmentColor(task.department);

  return (
    <div className="fixed inset-0 z-50 overflow-hidden">
      {/* Backdrop */}
      <div
        onClick={onClose}
        className="absolute inset-0 bg-slate-900/40 backdrop-blur-2xs transition-opacity animate-in fade-in"
      />

      <div className="fixed inset-y-0 right-0 max-w-full flex pl-10">
        <div className="w-screen max-w-xl bg-white shadow-2xl border-l border-slate-200 flex flex-col justify-between animate-in slide-in-from-right duration-300">
          {/* 1. Header */}
          <div className="p-5 border-b border-slate-200 bg-slate-50/70">
            <div className="flex items-start justify-between gap-3">
              <div>
                <div className="flex items-center gap-2 mb-1.5">
                  <span className={`px-2 py-0.5 rounded text-[11px] font-bold ${deptStyle.badge}`}>
                    {task.department.toUpperCase()} DEPARTMENT
                  </span>
                  <span className="px-2 py-0.5 rounded text-[11px] font-bold bg-slate-900 text-amber-300 font-mono">
                    SCORE {task.criticalityScore}/100 • {task.priority}
                  </span>
                  {task.status === 'Merged' && (
                    <span className="px-2 py-0.5 rounded text-[11px] font-bold bg-amber-100 text-amber-900 border border-amber-300">
                      🤝 JOINT BLOCK
                    </span>
                  )}
                </div>
                <h2 className="text-base font-bold text-slate-950 leading-snug">
                  Task #{task.taskNumber}: {task.title}
                </h2>
                <div className="mt-1 flex items-center gap-2 text-xs text-slate-500 font-medium">
                  <span>{task.corridorName}</span>
                  <span>•</span>
                  <span>Duration: {task.durationHours * 60} mins</span>
                </div>
              </div>

              <button
                onClick={onClose}
                className="p-1.5 rounded-lg text-slate-400 hover:text-slate-700 hover:bg-slate-200 transition-all cursor-pointer"
                title="Close Drawer"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Sub-navigation Tabs */}
            <div className="mt-4 flex items-center gap-1 p-1 bg-slate-200/80 rounded-lg text-xs font-semibold text-slate-600">
              <button
                onClick={() => setActiveTab('ai')}
                className={`flex-1 py-1.5 px-3 rounded-md flex items-center justify-center gap-1.5 transition-all ${
                  activeTab === 'ai'
                    ? 'bg-white text-slate-950 shadow-xs font-bold'
                    : 'hover:text-slate-900'
                }`}
              >
                <Sparkles className="w-3.5 h-3.5 text-sky-600" />
                <span>Gemini AI Rationale</span>
              </button>
              <button
                onClick={() => setActiveTab('math')}
                className={`flex-1 py-1.5 px-3 rounded-md flex items-center justify-center gap-1.5 transition-all ${
                  activeTab === 'math'
                    ? 'bg-white text-slate-950 shadow-xs font-bold'
                    : 'hover:text-slate-900'
                }`}
              >
                <Cpu className="w-3.5 h-3.5 text-emerald-600" />
                <span>CP-SAT Formula (Math)</span>
              </button>
              <button
                onClick={() => setActiveTab('defect')}
                className={`flex-1 py-1.5 px-3 rounded-md flex items-center justify-center gap-1.5 transition-all ${
                  activeTab === 'defect'
                    ? 'bg-white text-slate-950 shadow-xs font-bold'
                    : 'hover:text-slate-900'
                }`}
              >
                <Wrench className="w-3.5 h-3.5 text-slate-600" />
                <span>Defect &amp; Crew Specs</span>
              </button>
            </div>
          </div>

          {/* 2. Scrollable Body Content */}
          <div className="flex-1 overflow-y-auto p-5 space-y-5">
            {/* TAB 1: Gemini AI Explanation */}
            {activeTab === 'ai' && (
              <div className="space-y-4 animate-in fade-in">
                {/* AI Executive Summary Card */}
                <div className="p-4 rounded-xl bg-sky-50 border border-sky-200 space-y-2.5">
                  <div className="flex items-center gap-2 text-sky-950 font-bold text-xs uppercase tracking-wider">
                    <span className="p-1 rounded-md bg-sky-600 text-white">
                      <Sparkles className="w-3.5 h-3.5" />
                    </span>
                    <span>AI Reasoning — {task.geminiExplanation.headline}</span>
                  </div>
                  <p className="text-xs text-slate-800 leading-relaxed">
                    {task.geminiExplanation.summary}
                  </p>
                </div>

                {/* Key Operational Drivers */}
                <div className="space-y-2">
                  <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500">
                    Key Prioritization Drivers
                  </h3>
                  <div className="space-y-1.5">
                    {task.geminiExplanation.keyDrivers.map((driver, idx) => (
                      <div
                        key={idx}
                        className="p-2.5 rounded-lg border border-slate-200 bg-slate-50/80 text-xs text-slate-800 flex items-start gap-2"
                      >
                        <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
                        <span>{driver}</span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Trade-offs Evaluated */}
                <div className="p-3.5 rounded-xl border border-slate-200 bg-white space-y-1.5">
                  <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500 flex items-center gap-1.5">
                    <Clock className="w-3.5 h-3.5 text-slate-400" />
                    <span>Optimization Trade-offs Evaluated</span>
                  </h3>
                  <p className="text-xs text-slate-700 leading-relaxed">
                    {task.geminiExplanation.tradeoffsEvaluated}
                  </p>
                </div>

                {/* Joint Block Rationale if any */}
                {task.geminiExplanation.jointBlockRationale && (
                  <div className="p-3.5 rounded-xl border border-amber-200 bg-amber-50/70 space-y-1.5">
                    <h3 className="text-xs font-bold uppercase tracking-wider text-amber-900 flex items-center gap-1.5">
                      <span>🤝 Multi-Department Joint Block Rationale</span>
                    </h3>
                    <p className="text-xs text-amber-950 leading-relaxed">
                      {task.geminiExplanation.jointBlockRationale}
                    </p>
                  </div>
                )}
              </div>
            )}

            {/* TAB 2: Mathematical CP-SAT Breakdown */}
            {activeTab === 'math' && (
              <div className="space-y-5 animate-in fade-in">
                {/* Overall Formula Card */}
                <div className="p-4 rounded-xl bg-slate-900 text-white space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400">
                      Deterministic Criticality Formula (P0 Engine)
                    </span>
                    <span className="text-xs font-mono font-bold text-amber-300">
                      Score: {task.criticalityBreakdown.totalScore}/100
                    </span>
                  </div>
                  <div className="p-2.5 rounded-lg bg-slate-800 font-mono text-[11px] text-emerald-300 overflow-x-auto">
                    Score = W₁·Severity + W₂·Overdue + W₃·Asset + W₄·Traffic
                  </div>
                  <div className="text-[10px] text-slate-400 font-mono">
                    {task.criticalityBreakdown.formula}
                  </div>
                </div>

                {/* Individual Weights Breakdown */}
                <div className="space-y-3">
                  <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500">
                    Weighted Parameter Contribution
                  </h3>

                  {/* W1: Severity */}
                  <div className="p-3 rounded-lg border border-slate-200 bg-slate-50 space-y-1.5">
                    <div className="flex items-center justify-between text-xs">
                      <span className="font-semibold text-slate-800">
                        W₁: Defect Severity ({task.defect.severity}/5)
                      </span>
                      <span className="font-bold text-slate-900 font-mono">
                        {task.criticalityBreakdown.severityScore.toFixed(1)} / 35.0 pts
                      </span>
                    </div>
                    <div className="w-full h-2 rounded-full bg-slate-200 overflow-hidden">
                      <div
                        style={{ width: `${(task.criticalityBreakdown.severityScore / 35) * 100}%` }}
                        className="h-full bg-red-600 rounded-full"
                      />
                    </div>
                  </div>

                  {/* W2: Overdue Penalty */}
                  <div className="p-3 rounded-lg border border-slate-200 bg-slate-50 space-y-1.5">
                    <div className="flex items-center justify-between text-xs">
                      <span className="font-semibold text-slate-800">
                        W₂: Overdue SLA Penalty ({task.defect.overdueDays} Days Overdue)
                      </span>
                      <span className="font-bold text-slate-900 font-mono">
                        {task.criticalityBreakdown.overduePenalty.toFixed(1)} / 35.0 pts
                      </span>
                    </div>
                    <div className="w-full h-2 rounded-full bg-slate-200 overflow-hidden">
                      <div
                        style={{ width: `${(task.criticalityBreakdown.overduePenalty / 35) * 100}%` }}
                        className="h-full bg-amber-500 rounded-full"
                      />
                    </div>
                  </div>

                  {/* W3: Asset Importance */}
                  <div className="p-3 rounded-lg border border-slate-200 bg-slate-50 space-y-1.5">
                    <div className="flex items-center justify-between text-xs">
                      <span className="font-semibold text-slate-800">
                        W₃: Asset Importance (Trunk Mainline)
                      </span>
                      <span className="font-bold text-slate-900 font-mono">
                        {task.criticalityBreakdown.assetWeight.toFixed(1)} / 20.0 pts
                      </span>
                    </div>
                    <div className="w-full h-2 rounded-full bg-slate-200 overflow-hidden">
                      <div
                        style={{ width: `${(task.criticalityBreakdown.assetWeight / 20) * 100}%` }}
                        className="h-full bg-sky-600 rounded-full"
                      />
                    </div>
                  </div>

                  {/* W4: Traffic Disruption */}
                  <div className="p-3 rounded-lg border border-slate-200 bg-slate-50 space-y-1.5">
                    <div className="flex items-center justify-between text-xs">
                      <span className="font-semibold text-slate-800">
                        W₄: Traffic Disruption Minimization
                      </span>
                      <span className="font-bold text-slate-900 font-mono">
                        {task.criticalityBreakdown.trafficFactor.toFixed(1)} / 10.0 pts
                      </span>
                    </div>
                    <div className="w-full h-2 rounded-full bg-slate-200 overflow-hidden">
                      <div
                        style={{ width: `${(task.criticalityBreakdown.trafficFactor / 10) * 100}%` }}
                        className="h-full bg-emerald-600 rounded-full"
                      />
                    </div>
                  </div>
                </div>

                {/* Hard Constraints Audit */}
                <div className="p-3.5 rounded-xl border border-slate-200 bg-white space-y-2">
                  <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500 flex items-center gap-1.5">
                    <ShieldCheck className="w-4 h-4 text-emerald-600" />
                    <span>CP-SAT Hard Constraints Audit</span>
                  </h3>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-[11px]">
                    <div className="flex items-center gap-2 text-slate-700">
                      <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 shrink-0" />
                      <span>Zero Corridor Overlap</span>
                    </div>
                    <div className="flex items-center gap-2 text-slate-700">
                      <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 shrink-0" />
                      <span>Window Duration Fit</span>
                    </div>
                    <div className="flex items-center gap-2 text-slate-700">
                      <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 shrink-0" />
                      <span>Traction Isolated 15m Prior</span>
                    </div>
                    <div className="flex items-center gap-2 text-slate-700">
                      <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 shrink-0" />
                      <span>Crew Shift Compliance (&lt;8h)</span>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* TAB 3: Defect & Crew Specifications */}
            {activeTab === 'defect' && (
              <div className="space-y-4 animate-in fade-in">
                {/* Defect Source Details */}
                <div className="p-4 rounded-xl border border-slate-200 bg-white space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">
                      Defect Record ({task.defect.sourceSystem})
                    </span>
                    <span className="px-2 py-0.5 rounded text-[11px] font-mono font-bold bg-slate-100 text-slate-800">
                      {task.defect.code}
                    </span>
                  </div>

                  <div className="space-y-1.5 text-xs">
                    <div>
                      <span className="text-slate-400">Category: </span>
                      <strong className="text-slate-800">{task.defect.category}</strong>
                    </div>
                    <div>
                      <span className="text-slate-400">Reported Date: </span>
                      <span className="text-slate-700">{task.defect.reportedDate} ({task.defect.overdueDays} days ago)</span>
                    </div>
                    <div className="pt-2 border-t border-slate-100 text-slate-700 leading-relaxed">
                      {task.defect.description}
                    </div>
                  </div>
                </div>

                {/* Recommended Engineering Action */}
                <div className="p-3.5 rounded-xl border border-slate-200 bg-slate-50 space-y-1">
                  <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider">
                    Recommended Engineering Procedure
                  </span>
                  <p className="text-xs text-slate-800 leading-relaxed">
                    {task.defect.recommendedAction}
                  </p>
                </div>

                {/* Work Crew & Logistics */}
                <div className="p-4 rounded-xl border border-slate-200 bg-white space-y-3">
                  <div className="flex items-center gap-1.5 text-xs font-bold text-slate-500 uppercase tracking-wider">
                    <Users className="w-3.5 h-3.5 text-slate-400" />
                    <span>Crew &amp; Machine Mobilization</span>
                  </div>

                  <div className="grid grid-cols-2 gap-3 text-xs">
                    <div>
                      <div className="text-[11px] text-slate-400">Supervisor</div>
                      <div className="font-semibold text-slate-800">{task.crew.supervisor}</div>
                    </div>
                    <div>
                      <div className="text-[11px] text-slate-400">Gang Size</div>
                      <div className="font-semibold text-slate-800">{task.crew.crewSize} Personnel</div>
                    </div>
                    {task.crew.requiredMachine && (
                      <div className="col-span-2">
                        <div className="text-[11px] text-slate-400">Heavy Machine Unit</div>
                        <div className="font-semibold text-slate-800">{task.crew.requiredMachine}</div>
                      </div>
                    )}
                    {task.crew.speedRestrictionAfterwards && (
                      <div className="col-span-2">
                        <div className="text-[11px] text-slate-400">Post-Work Speed Restriction (TSR)</div>
                        <div className="font-semibold text-amber-800">{task.crew.speedRestrictionAfterwards}</div>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* 3. Footer Action */}
          <div className="p-4 border-t border-slate-200 bg-slate-50 flex items-center justify-between">
            <div className="flex items-center gap-1.5 text-xs text-slate-500 font-mono">
              <CheckCircle2 className="w-4 h-4 text-emerald-600" />
              <span>Constraint Validated by CP-SAT</span>
            </div>
            <button
              onClick={onClose}
              className="px-4 py-2 rounded-lg bg-slate-900 text-white hover:bg-slate-800 text-xs font-semibold cursor-pointer"
            >
              Close Panel
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
