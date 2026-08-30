'use client';

import React, { useState } from 'react';
import {
  X,
  PlusCircle,
  Clock,
  Train,
  Zap,
  ShieldAlert,
  CheckCircle2,
  AlertTriangle,
  Flame,
} from 'lucide-react';
import { Department, CorridorSection, DepartmentDefectFeedItem } from '../../types/railway';

interface RaiseRequestModalProps {
  isOpen: boolean;
  onClose: () => void;
  corridors: CorridorSection[];
  onAddRequest: (newItem: DepartmentDefectFeedItem) => void;
}

export const RaiseRequestModal: React.FC<RaiseRequestModalProps> = ({
  isOpen,
  onClose,
  corridors,
  onAddRequest,
}) => {
  const [department, setDepartment] = useState<Department>('Track');
  const [corridorId, setCorridorId] = useState<string>(corridors[0]?.id || 'sec-delhi-gzb-up');
  const [defectCategory, setDefectCategory] = useState<string>('Ultrasonic Rail Flaw (USFD)');
  const [trackKm, setTrackKm] = useState<string>('Km 18/24');
  const [severity, setSeverity] = useState<number>(4);
  const [overdueDays, setOverdueDays] = useState<number>(8);
  const [durationMins, setDurationMins] = useState<number>(120);
  const [powerDisconnection, setPowerDisconnection] = useState<boolean>(true);
  const [speedRestriction, setSpeedRestriction] = useState<boolean>(true);

  if (!isOpen) return null;

  const selectedCorridor = corridors.find((c) => c.id === corridorId) || corridors[0];

  // Real-time calculated corridor availability status
  const isNightSlot = durationMins <= 180;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const sourceSystem = department === 'Track' ? 'TMS' : department === 'Signal' ? 'SMMS' : 'TDMS';
    const randomTaskNumber = Math.floor(Math.random() * 800) + 200;

    const newItem: DepartmentDefectFeedItem = {
      id: `feed-custom-${Date.now()}`,
      taskNumber: randomTaskNumber,
      department,
      sourceSystem,
      defectCode: `${sourceSystem}-MAN-${randomTaskNumber}`,
      defectCategory,
      corridorName: selectedCorridor.name,
      trackKm,
      severity: severity as 1 | 2 | 3 | 4 | 5,
      overdueDays,
      estimatedMinutes: durationMins,
      requestedDateTime: '01-Sep 02:00',
      status: 'Pending',
      powerBlockRequired: powerDisconnection,
    };

    onAddRequest(newItem);
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-2xs animate-in fade-in overflow-y-auto">
      <div className="w-full max-w-lg bg-white rounded-2xl shadow-2xl border border-slate-200 overflow-hidden animate-in zoom-in-95 duration-200">
        {/* Header */}
        <div className="p-4 border-b border-slate-200 bg-slate-50 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="p-1.5 rounded-lg bg-slate-900 text-white">
              <PlusCircle className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-slate-950">
                Raise New Maintenance Block Request
              </h3>
              <p className="text-xs text-slate-500">
                Direct Indian Railways Ingestion Portal (TMS / SMMS / TDMS)
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-slate-700 hover:bg-slate-200 cursor-pointer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-5 space-y-4 text-xs">
          {/* Department Selection */}
          <div className="space-y-1.5">
            <label className="font-semibold text-slate-700">Requesting Engineering Department</label>
            <div className="grid grid-cols-3 gap-2">
              <button
                type="button"
                onClick={() => setDepartment('Track')}
                className={`py-2 px-3 rounded-lg border font-semibold text-center transition-all ${
                  department === 'Track'
                    ? 'bg-orange-50 text-orange-950 border-orange-400 shadow-2xs'
                    : 'bg-white text-slate-600 border-slate-200 hover:bg-slate-50'
                }`}
              >
                Track (TMS)
              </button>
              <button
                type="button"
                onClick={() => setDepartment('Signal')}
                className={`py-2 px-3 rounded-lg border font-semibold text-center transition-all ${
                  department === 'Signal'
                    ? 'bg-blue-50 text-blue-950 border-blue-400 shadow-2xs'
                    : 'bg-white text-slate-600 border-slate-200 hover:bg-slate-50'
                }`}
              >
                Signal (SMMS)
              </button>
              <button
                type="button"
                onClick={() => setDepartment('OHE')}
                className={`py-2 px-3 rounded-lg border font-semibold text-center transition-all ${
                  department === 'OHE'
                    ? 'bg-amber-50 text-amber-950 border-amber-400 shadow-2xs'
                    : 'bg-white text-slate-600 border-slate-200 hover:bg-slate-50'
                }`}
              >
                Traction (TDMS)
              </button>
            </div>
          </div>

          {/* Corridor Selection & Track KM */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div className="space-y-1">
              <label className="font-semibold text-slate-700">Corridor Track Section</label>
              <select
                value={corridorId}
                onChange={(e) => setCorridorId(e.target.value)}
                className="w-full py-1.5 px-2.5 rounded-lg border border-slate-200 bg-slate-50 text-slate-900 font-medium focus:outline-hidden focus:ring-1 focus:ring-slate-400"
              >
                {corridors.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.name}
                  </option>
                ))}
              </select>
            </div>

            <div className="space-y-1">
              <label className="font-semibold text-slate-700">Physical Location / Track Km</label>
              <input
                type="text"
                value={trackKm}
                onChange={(e) => setTrackKm(e.target.value)}
                className="w-full py-1.5 px-2.5 rounded-lg border border-slate-200 bg-slate-50 text-slate-900 font-mono focus:outline-hidden focus:ring-1 focus:ring-slate-400"
                placeholder="e.g. Km 18/24 near Sahibabad"
                required
              />
            </div>
          </div>

          {/* Defect Category */}
          <div className="space-y-1">
            <label className="font-semibold text-slate-700">Defect Description / Category</label>
            <input
              type="text"
              value={defectCategory}
              onChange={(e) => setDefectCategory(e.target.value)}
              className="w-full py-1.5 px-2.5 rounded-lg border border-slate-200 bg-slate-50 text-slate-900 font-medium focus:outline-hidden focus:ring-1 focus:ring-slate-400"
              placeholder="e.g. Broken rail joint, Point motor jam..."
              required
            />
          </div>

          {/* Severity & Overdue Days */}
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1">
              <div className="flex items-center justify-between">
                <label className="font-semibold text-slate-700">Defect Severity</label>
                <span className="font-bold text-red-600 font-mono">{severity} / 5</span>
              </div>
              <input
                type="range"
                min="1"
                max="5"
                value={severity}
                onChange={(e) => setSeverity(Number(e.target.value))}
                className="w-full accent-red-600 cursor-pointer"
              />
              <div className="flex justify-between text-[10px] text-slate-400 font-mono">
                <span>1 (Routine)</span>
                <span>3 (Caution)</span>
                <span>5 (Immediate)</span>
              </div>
            </div>

            <div className="space-y-1">
              <label className="font-semibold text-slate-700">Defect Overdue Days</label>
              <input
                type="number"
                min="0"
                max="60"
                value={overdueDays}
                onChange={(e) => setOverdueDays(Number(e.target.value))}
                className="w-full py-1.5 px-2.5 rounded-lg border border-slate-200 bg-slate-50 text-slate-900 font-mono focus:outline-hidden focus:ring-1 focus:ring-slate-400"
                required
              />
            </div>
          </div>

          {/* Duration & Prerequisites */}
          <div className="p-3 bg-slate-50 border border-slate-200 rounded-xl space-y-2.5">
            <div className="flex items-center justify-between">
              <label className="font-semibold text-slate-800">Required Window Duration</label>
              <select
                value={durationMins}
                onChange={(e) => setDurationMins(Number(e.target.value))}
                className="py-1 px-2 rounded-md border border-slate-300 bg-white font-mono text-xs font-semibold"
              >
                <option value="60">60 mins (1.0 hr)</option>
                <option value="90">90 mins (1.5 hrs)</option>
                <option value="120">120 mins (2.0 hrs)</option>
                <option value="150">150 mins (2.5 hrs)</option>
                <option value="180">180 mins (3.0 hrs)</option>
                <option value="240">240 mins (4.0 hrs)</option>
              </select>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-[11px] pt-1">
              <label className="flex items-center gap-2 text-slate-700 cursor-pointer">
                <input
                  type="checkbox"
                  checked={powerDisconnection}
                  onChange={(e) => setPowerDisconnection(e.target.checked)}
                  className="rounded border-slate-300 accent-amber-600"
                />
                <span>Requires 25kV OHE Power Cut</span>
              </label>

              <label className="flex items-center gap-2 text-slate-700 cursor-pointer">
                <input
                  type="checkbox"
                  checked={speedRestriction}
                  onChange={(e) => setSpeedRestriction(e.target.checked)}
                  className="rounded border-slate-300 accent-sky-600"
                />
                <span>Imposes Speed Restriction (TSR)</span>
              </label>
            </div>
          </div>

          {/* Live Corridor Timetable Availability Checker */}
          <div
            className={`p-3 rounded-xl border flex items-start gap-2.5 ${
              isNightSlot
                ? 'bg-emerald-50 border-emerald-200 text-emerald-950'
                : 'bg-amber-50 border-amber-200 text-amber-950'
            }`}
          >
            <div className="mt-0.5 shrink-0">
              {isNightSlot ? (
                <CheckCircle2 className="w-4 h-4 text-emerald-600" />
              ) : (
                <AlertTriangle className="w-4 h-4 text-amber-600" />
              )}
            </div>
            <div className="space-y-0.5 text-xs">
              <div className="font-bold">
                {isNightSlot ? 'COA Live Slot Available (Gold Window)' : 'Corridor Congestion Advisory'}
              </div>
              <div className="text-[11px] text-slate-700">
                {isNightSlot
                  ? `Night window 01:30 - 04:30 AM has zero passenger traffic on ${selectedCorridor.name}. High chance of CP-SAT auto-approval.`
                  : `A continuous ${durationMins}m window may conflict with morning peak passenger trains. Solver will consider weekend mega-block.`}
              </div>
            </div>
          </div>

          {/* Footer Actions */}
          <div className="flex items-center justify-end gap-2 pt-2 border-t border-slate-100">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 rounded-lg bg-white border border-slate-200 text-slate-700 hover:bg-slate-50 font-semibold cursor-pointer"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-4 py-2 rounded-lg bg-slate-900 text-white hover:bg-slate-800 font-bold shadow-xs cursor-pointer active:scale-98"
            >
              Submit Block Request
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
