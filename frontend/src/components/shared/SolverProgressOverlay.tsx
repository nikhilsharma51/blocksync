'use client';

import React, { useEffect, useState } from 'react';
import { Cpu, CheckCircle2, Zap, Sparkles, ShieldCheck } from 'lucide-react';

interface SolverProgressOverlayProps {
  isOpen: boolean;
  onComplete: () => void;
}

export const SolverProgressOverlay: React.FC<SolverProgressOverlayProps> = ({
  isOpen,
  onComplete,
}) => {
  const [currentStep, setCurrentStep] = useState<number>(0);

  const steps = [
    { label: 'Ingesting 42 defect orders from TMS, SMMS & TDMS feeds', detail: 'Normalizing schemas & calculating criticality scores (W1..W4)' },
    { label: 'Formulating CP-SAT Integer Programming Model', detail: '128 linear constraints • No-overlap corridor interval variables' },
    { label: 'Running Google OR-Tools CP-SAT Solver v9.8', detail: 'Branch-and-bound search • Timetable headway preservation' },
    { label: 'Composing Integrated Joint Blocks (Track + OHE)', detail: 'Merging shared traction power shutdowns • Saved 12.5h downtime' },
    { label: 'Optimal Conflict-Free Schedule Verified (100% Feasible)', detail: 'Total runtime: 1.84s • 0 collisions remaining' },
  ];

  useEffect(() => {
    if (!isOpen) {
      setCurrentStep(0);
      return;
    }

    const interval = setInterval(() => {
      setCurrentStep((prev) => {
        if (prev < steps.length - 1) {
          return prev + 1;
        } else {
          clearInterval(interval);
          setTimeout(onComplete, 500);
          return prev;
        }
      });
    }, 450);

    return () => clearInterval(interval);
  }, [isOpen, onComplete, steps.length]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-2xs animate-in fade-in">
      <div className="w-full max-w-md bg-white rounded-2xl shadow-2xl border border-slate-200 p-6 space-y-5 animate-in zoom-in-95 duration-200">
        {/* Header */}
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-slate-950 text-amber-300 flex items-center justify-center shadow-xs">
            <Zap className="w-5 h-5 fill-amber-300 animate-pulse" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-slate-950">
              OR-Tools CP-SAT Block Optimizer
            </h3>
            <p className="text-xs text-slate-500">
              Northern Railway • Delhi Division Scheduling
            </p>
          </div>
        </div>

        {/* Progress Bar */}
        <div className="space-y-1.5">
          <div className="flex items-center justify-between text-xs font-semibold text-slate-700">
            <span>Constraint Programming Solve</span>
            <span className="font-mono text-sky-700 font-bold">
              {Math.round(((currentStep + 1) / steps.length) * 100)}%
            </span>
          </div>
          <div className="w-full h-2 rounded-full bg-slate-100 overflow-hidden border border-slate-200">
            <div
              style={{ width: `${((currentStep + 1) / steps.length) * 100}%` }}
              className="h-full bg-slate-900 transition-all duration-300 ease-out"
            />
          </div>
        </div>

        {/* Step Items List */}
        <div className="space-y-2.5 pt-1">
          {steps.map((step, idx) => {
            const isCompleted = idx < currentStep;
            const isCurrent = idx === currentStep;

            return (
              <div
                key={idx}
                className={`p-2.5 rounded-lg border text-xs transition-all flex items-start gap-2.5 ${
                  isCurrent
                    ? 'bg-sky-50 border-sky-300 text-sky-950 font-semibold shadow-2xs'
                    : isCompleted
                    ? 'bg-slate-50 border-slate-200 text-slate-700 opacity-85'
                    : 'bg-white border-slate-100 text-slate-400 opacity-40'
                }`}
              >
                <div className="mt-0.5 shrink-0">
                  {isCompleted ? (
                    <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                  ) : isCurrent ? (
                    <Cpu className="w-4 h-4 text-sky-600 animate-spin" />
                  ) : (
                    <div className="w-4 h-4 rounded-full border border-slate-300" />
                  )}
                </div>
                <div>
                  <div className="leading-snug">{step.label}</div>
                  {isCurrent && (
                    <div className="text-[10px] font-mono text-sky-700 font-normal mt-0.5">
                      {step.detail}
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};
