'use client';

import React, { useState } from 'react';
import {
  FileCheck,
  CheckCircle2,
  Clock,
  AlertTriangle,
  Play,
  Check,
  ShieldCheck,
  RotateCcw,
  Sparkles,
  History,
  Lock,
} from 'lucide-react';
import {
  ExecutionBlockItem,
  AuditTrailLog,
  ExecutionStatus,
  Department,
} from '../../types/railway';

interface ExecutionTrackingPageProps {
  initialItems: ExecutionBlockItem[];
  auditLogs: AuditTrailLog[];
}

export const ExecutionTrackingPage: React.FC<ExecutionTrackingPageProps> = ({
  initialItems,
  auditLogs,
}) => {
  const [items, setItems] = useState<ExecutionBlockItem[]>(initialItems);
  const [logs, setLogs] = useState<AuditTrailLog[]>(auditLogs);
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  const handleAdvanceStatus = (id: string, currentStatus: ExecutionStatus) => {
    let nextStatus: ExecutionStatus = currentStatus;
    let actionLog = '';

    if (currentStatus === 'SCHEDULED') {
      nextStatus = 'GRANTED';
      actionLog = 'Block Granted (Traffic Halted by Controller)';
    } else if (currentStatus === 'GRANTED') {
      nextStatus = 'IN_PROGRESS';
      actionLog = 'Work Started by Engineering Gang';
    } else if (currentStatus === 'IN_PROGRESS') {
      nextStatus = 'RESTORED';
      actionLog = 'Track Restored & Fit (Speed Restored)';
    }

    setItems((prev) =>
      prev.map((item) =>
        item.id === id
          ? {
              ...item,
              status: nextStatus,
              lastUpdated: new Date().toLocaleTimeString('en-IN', {
                hour: '2-digit',
                minute: '2-digit',
              }) + ' IST',
            }
          : item
      )
    );

    const changedItem = items.find((i) => i.id === id);
    if (changedItem) {
      const newLog: AuditTrailLog = {
        id: `log-${Date.now()}`,
        timestamp: '30-AUG-2026 ' + new Date().toLocaleTimeString('en-IN') + ' IST',
        userRole: 'Section Controller (COA)',
        action: actionLog,
        targetTask: changedItem.taskTitle,
        previousValue: `Status: ${currentStatus}`,
        newValue: `Status: ${nextStatus}`,
        validationStatus: 'Constraint Passed',
      };
      setLogs((prev) => [newLog, ...prev]);

      if (nextStatus === 'RESTORED') {
        setToastMessage(`✅ Closed Loop: ${changedItem.taskTitle} marked Track Fit. Defect cleared from active backlog!`);
        setTimeout(() => setToastMessage(null), 5000);
      }
    }
  };

  const getDepartmentBadge = (dept: Department) => {
    switch (dept) {
      case 'Track':
        return 'bg-orange-100 text-orange-950 border-orange-200';
      case 'Signal':
        return 'bg-blue-100 text-blue-950 border-blue-200';
      case 'OHE':
        return 'bg-amber-100 text-amber-950 border-amber-200';
    }
  };

  return (
    <div className="space-y-4 animate-in fade-in">
      {/* 1. Top Header Bar */}
      <div className="p-4 bg-white border border-slate-200 rounded-xl shadow-2xs flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="p-1 rounded-md bg-slate-900 text-white">
              <FileCheck className="w-4 h-4" />
            </span>
            <h2 className="text-base font-bold text-slate-950">
              Shift Execution Tracking &amp; Immutable Audit Trail
            </h2>
            <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-indigo-100 text-indigo-900 border border-indigo-200">
              CLOSED-LOOP OPERATIONAL LOG
            </span>
          </div>
          <p className="mt-1 text-xs text-slate-500">
            Real-time track block grant authority, field progress, and safety compliance sign-offs.
          </p>
        </div>

        <div className="flex items-center gap-2 font-mono text-xs text-slate-600 bg-slate-50 px-3 py-1.5 rounded-lg border border-slate-200">
          <ShieldCheck className="w-4 h-4 text-emerald-600" />
          <span>Audit Log: Append-Only Immutable Store</span>
        </div>
      </div>

      {/* Toast Feedback */}
      {toastMessage && (
        <div className="p-3 bg-emerald-50 border border-emerald-300 rounded-xl text-xs text-emerald-950 font-medium flex items-center justify-between shadow-xs animate-in fade-in">
          <span>{toastMessage}</span>
          <button
            onClick={() => setToastMessage(null)}
            className="text-xs font-bold text-emerald-800 hover:text-emerald-950 cursor-pointer"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* 2. Live Block Execution Kanban Board */}
      <div className="space-y-2">
        <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500">
          Live Block Execution Board (4 Shift Stages)
        </h3>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3.5">
          {/* Column 1: Scheduled */}
          <div className="p-3 bg-slate-50 border border-slate-200 rounded-xl space-y-3">
            <div className="flex items-center justify-between text-xs font-bold text-slate-800">
              <span>1. Scheduled for Shift</span>
              <span className="px-1.5 py-0.2 rounded bg-slate-200 text-slate-700 font-mono text-[10px]">
                {items.filter((i) => i.status === 'SCHEDULED').length}
              </span>
            </div>

            <div className="space-y-2.5">
              {items
                .filter((i) => i.status === 'SCHEDULED')
                .map((item) => (
                  <div
                    key={item.id}
                    className="p-3 bg-white border border-slate-200 rounded-lg shadow-2xs space-y-2 text-xs"
                  >
                    <div className="flex items-center justify-between">
                      <span className={`px-1.5 py-0.2 rounded text-[9px] font-bold border ${getDepartmentBadge(item.department)}`}>
                        {item.department}
                      </span>
                      <span className="font-mono text-[10px] text-slate-400">{item.blockNumber}</span>
                    </div>

                    <div className="font-semibold text-slate-900">{item.taskTitle}</div>
                    <div className="text-[11px] text-slate-500">{item.corridorName}</div>
                    <div className="font-mono text-[10px] text-slate-600 bg-slate-50 p-1 rounded">
                      🕒 {item.timeWindow}
                    </div>

                    <button
                      onClick={() => handleAdvanceStatus(item.id, item.status)}
                      className="w-full py-1.5 px-2 rounded-md bg-slate-900 hover:bg-slate-800 text-white font-bold text-[11px] flex items-center justify-center gap-1 cursor-pointer transition-all active:scale-98"
                    >
                      <Play className="w-3 h-3 text-amber-300" />
                      <span>Grant Block (Stop Traffic)</span>
                    </button>
                  </div>
                ))}
            </div>
          </div>

          {/* Column 2: Granted */}
          <div className="p-3 bg-amber-50/60 border border-amber-200 rounded-xl space-y-3">
            <div className="flex items-center justify-between text-xs font-bold text-amber-950">
              <span>2. Block Granted</span>
              <span className="px-1.5 py-0.2 rounded bg-amber-200 text-amber-900 font-mono text-[10px]">
                {items.filter((i) => i.status === 'GRANTED').length}
              </span>
            </div>

            <div className="space-y-2.5">
              {items
                .filter((i) => i.status === 'GRANTED')
                .map((item) => (
                  <div
                    key={item.id}
                    className="p-3 bg-white border border-amber-200 rounded-lg shadow-2xs space-y-2 text-xs"
                  >
                    <div className="flex items-center justify-between">
                      <span className={`px-1.5 py-0.2 rounded text-[9px] font-bold border ${getDepartmentBadge(item.department)}`}>
                        {item.department}
                      </span>
                      <span className="px-1.5 py-0.2 rounded bg-amber-100 text-amber-900 font-bold text-[9px]">
                        TRAFFIC HALTED
                      </span>
                    </div>

                    <div className="font-semibold text-slate-900">{item.taskTitle}</div>
                    <div className="text-[11px] text-slate-500">{item.corridorName}</div>
                    <div className="text-[10px] text-slate-600">Supervisor: {item.supervisor}</div>

                    <button
                      onClick={() => handleAdvanceStatus(item.id, item.status)}
                      className="w-full py-1.5 px-2 rounded-md bg-amber-600 hover:bg-amber-700 text-white font-bold text-[11px] flex items-center justify-center gap-1 cursor-pointer transition-all active:scale-98"
                    >
                      <Clock className="w-3 h-3" />
                      <span>Start Gang Work</span>
                    </button>
                  </div>
                ))}
            </div>
          </div>

          {/* Column 3: In Progress */}
          <div className="p-3 bg-sky-50/60 border border-sky-200 rounded-xl space-y-3">
            <div className="flex items-center justify-between text-xs font-bold text-sky-950">
              <span>3. Work in Progress</span>
              <span className="px-1.5 py-0.2 rounded bg-sky-200 text-sky-900 font-mono text-[10px]">
                {items.filter((i) => i.status === 'IN_PROGRESS').length}
              </span>
            </div>

            <div className="space-y-2.5">
              {items
                .filter((i) => i.status === 'IN_PROGRESS')
                .map((item) => (
                  <div
                    key={item.id}
                    className="p-3 bg-white border border-sky-200 rounded-lg shadow-2xs space-y-2 text-xs"
                  >
                    <div className="flex items-center justify-between">
                      <span className={`px-1.5 py-0.2 rounded text-[9px] font-bold border ${getDepartmentBadge(item.department)}`}>
                        {item.department}
                      </span>
                      <span className="px-1.5 py-0.2 rounded bg-sky-100 text-sky-900 font-bold text-[9px] animate-pulse">
                        GANG ON TRACK
                      </span>
                    </div>

                    <div className="font-semibold text-slate-900">{item.taskTitle}</div>
                    <div className="text-[11px] text-slate-500">{item.corridorName}</div>

                    <button
                      onClick={() => handleAdvanceStatus(item.id, item.status)}
                      className="w-full py-1.5 px-2 rounded-md bg-emerald-700 hover:bg-emerald-800 text-white font-bold text-[11px] flex items-center justify-center gap-1 cursor-pointer transition-all active:scale-98"
                    >
                      <Check className="w-3 h-3" />
                      <span>Mark Track Restored &amp; Fit</span>
                    </button>
                  </div>
                ))}
            </div>
          </div>

          {/* Column 4: Restored */}
          <div className="p-3 bg-emerald-50/60 border border-emerald-200 rounded-xl space-y-3">
            <div className="flex items-center justify-between text-xs font-bold text-emerald-950">
              <span>4. Track Restored &amp; Fit</span>
              <span className="px-1.5 py-0.2 rounded bg-emerald-200 text-emerald-900 font-mono text-[10px]">
                {items.filter((i) => i.status === 'RESTORED').length}
              </span>
            </div>

            <div className="space-y-2.5">
              {items
                .filter((i) => i.status === 'RESTORED')
                .map((item) => (
                  <div
                    key={item.id}
                    className="p-3 bg-white border border-emerald-200 rounded-lg shadow-2xs space-y-1.5 text-xs"
                  >
                    <div className="flex items-center justify-between">
                      <span className="px-1.5 py-0.2 rounded bg-emerald-100 text-emerald-800 font-bold text-[9px] flex items-center gap-1">
                        <CheckCircle2 className="w-3 h-3" />
                        <span>CLOSED &amp; FIT</span>
                      </span>
                      <span className="font-mono text-[10px] text-slate-400">{item.lastUpdated}</span>
                    </div>

                    <div className="font-semibold text-slate-900">{item.taskTitle}</div>
                    <div className="text-[10px] text-emerald-800 font-medium">
                      {item.speedRestriction}
                    </div>
                  </div>
                ))}
            </div>
          </div>
        </div>
      </div>

      {/* 3. Immutable Audit Trail Table */}
      <div className="p-4 bg-white border border-slate-200 rounded-xl shadow-2xs space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <History className="w-4 h-4 text-slate-600" />
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-900">
              Safety Compliance Audit Trail (Immutable Shift Log)
            </h3>
          </div>
          <span className="text-xs text-slate-400 font-mono">
            {logs.length} Total Audit Records
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse text-xs">
            <thead className="bg-slate-50 border-b border-slate-200 text-slate-600 font-semibold text-[11px] uppercase tracking-wider">
              <tr>
                <th className="py-2.5 px-3">Timestamp</th>
                <th className="py-2.5 px-3">User / System Role</th>
                <th className="py-2.5 px-3">Action Executed</th>
                <th className="py-2.5 px-3">Target Work Order</th>
                <th className="py-2.5 px-3">Previous State</th>
                <th className="py-2.5 px-3">New State</th>
                <th className="py-2.5 px-3">Safety Verification</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-slate-800 font-mono text-[11px]">
              {logs.map((log) => (
                <tr key={log.id} className="hover:bg-slate-50/70 transition-colors">
                  <td className="py-2.5 px-3 text-slate-500 whitespace-nowrap">{log.timestamp}</td>
                  <td className="py-2.5 px-3 font-semibold text-slate-900">{log.userRole}</td>
                  <td className="py-2.5 px-3 font-sans text-xs text-slate-800">{log.action}</td>
                  <td className="py-2.5 px-3 font-sans text-xs text-slate-700">{log.targetTask}</td>
                  <td className="py-2.5 px-3 text-slate-500">{log.previousValue}</td>
                  <td className="py-2.5 px-3 font-bold text-slate-900">{log.newValue}</td>
                  <td className="py-2.5 px-3">
                    <span className="px-1.5 py-0.2 rounded text-[10px] font-bold bg-emerald-100 text-emerald-800 font-sans">
                      ✅ {log.validationStatus}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
