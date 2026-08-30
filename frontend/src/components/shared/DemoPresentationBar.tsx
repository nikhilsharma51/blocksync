'use client';

import React from 'react';
import { Award, ChevronRight, X } from 'lucide-react';

interface DemoPresentationBarProps {
  currentStep: number;
  onSelectStep: (step: number) => void;
  isOpen: boolean;
  onToggle: () => void;
}

export const DemoPresentationBar: React.FC<DemoPresentationBarProps> = ({
  currentStep,
  onSelectStep,
  isOpen,
  onToggle,
}) => {
  const steps = [
    { number: 1, label: '1. Clashes' },
    { number: 2, label: '2. Explain IMR' },
    { number: 3, label: '3. Run CP-SAT' },
    { number: 4, label: '4. Joint Block' },
    { number: 5, label: '5. Bulletin' },
  ];

  if (!isOpen) {
    return (
      <div className="fixed bottom-4 right-5 z-40">
        <button
          onClick={onToggle}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-slate-900 text-white font-medium text-xs shadow-lg border border-slate-700 hover:bg-slate-800 cursor-pointer active:scale-98"
        >
          <Award className="w-3.5 h-3.5 text-amber-300" />
          <span>Judge Walkthrough</span>
        </button>
      </div>
    );
  }

  return (
    <div className="fixed bottom-4 left-1/2 -translate-x-1/2 z-40 w-auto max-w-xl px-4 animate-in slide-in-from-bottom duration-200">
      <div className="bg-slate-950 text-white rounded-full shadow-xl border border-slate-800 py-1.5 px-3 flex items-center gap-2">
        <div className="flex items-center gap-1.5 pl-1 pr-2 text-xs font-semibold text-amber-300 border-r border-slate-800">
          <Award className="w-3.5 h-3.5" />
          <span className="hidden sm:inline">Demo Arc</span>
        </div>

        <div className="flex items-center gap-1">
          {steps.map((step) => (
            <button
              key={step.number}
              onClick={() => onSelectStep(step.number)}
              className={`px-2.5 py-1 rounded-full text-xs font-medium transition-all cursor-pointer ${
                currentStep === step.number
                  ? 'bg-white text-slate-950 font-bold shadow-xs'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              {step.label}
            </button>
          ))}
        </div>

        <button
          onClick={onToggle}
          className="p-1 rounded-full text-slate-500 hover:text-white cursor-pointer ml-1"
          title="Close Presentation Bar"
        >
          <X className="w-3.5 h-3.5" />
        </button>
      </div>
    </div>
  );
};
