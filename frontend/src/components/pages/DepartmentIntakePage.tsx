'use client';

import React, { useState } from 'react';
import {
  ClipboardList,
  PlusCircle,
  RefreshCw,
  Search,
  Zap,
} from 'lucide-react';
import {
  DepartmentDefectFeedItem,
  Department,
  CorridorSection,
} from '../../types/railway';
import { RaiseRequestModal } from '../modals/RaiseRequestModal';

interface DepartmentIntakePageProps {
  feeds: DepartmentDefectFeedItem[];
  corridors: CorridorSection[];
  onAddFeedItem: (item: DepartmentDefectFeedItem) => void;
  onInjectConflicts: () => void;
  onResetSeedData: () => void;
}

export const DepartmentIntakePage: React.FC<DepartmentIntakePageProps> = ({
  feeds,
  corridors,
  onAddFeedItem,
  onInjectConflicts,
  onResetSeedData,
}) => {
  const [activeTab, setActiveTab] = useState<'ALL' | 'Track' | 'Signal' | 'OHE'>('ALL');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [severityFilter, setSeverityFilter] = useState<string>('ALL');
  const [overdueOnly, setOverdueOnly] = useState<boolean>(false);
  const [isModalOpen, setIsModalOpen] = useState<boolean>(false);
  const [syncToast, setSyncToast] = useState<string | null>(null);

  const filteredFeeds = feeds.filter((item) => {
    const matchTab = activeTab === 'ALL' || item.department === activeTab;
    const matchSearch =
      searchQuery === '' ||
      item.defectCategory.toLowerCase().includes(searchQuery.toLowerCase()) ||
      item.defectCode.toLowerCase().includes(searchQuery.toLowerCase()) ||
      item.corridorName.toLowerCase().includes(searchQuery.toLowerCase()) ||
      item.taskNumber.toString().includes(searchQuery);
    const matchSeverity =
      severityFilter === 'ALL' || item.severity.toString() === severityFilter;
    const matchOverdue = !overdueOnly || item.overdueDays >= 7;

    return matchTab && matchSearch && matchSeverity && matchOverdue;
  });

  const handleSyncFeeds = () => {
    setSyncToast('Connected: 52 defect orders synchronized from TMS, SMMS & TDMS gateways.');
    setTimeout(() => setSyncToast(null), 3000);
  };

  return (
    <div className="space-y-3 animate-in fade-in">
      {/* 1. Page Action Header */}
      <div className="bg-white border border-slate-200 rounded-lg p-3 px-4 shadow-2xs flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-sm font-bold text-slate-950">Department Feeds &amp; Intake Queue</h2>
          <p className="text-[11px] text-slate-500">
            Raw incoming maintenance defect orders from TMS, SMMS, and TDMS.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => setIsModalOpen(true)}
            className="inline-flex items-center gap-1 px-3 py-1.5 rounded bg-slate-950 text-white hover:bg-slate-800 text-xs font-semibold shadow-2xs cursor-pointer active:scale-98"
          >
            <PlusCircle className="w-3 h-3 text-amber-300" />
            <span>Raise Request</span>
          </button>

          <button
            onClick={handleSyncFeeds}
            className="px-2.5 py-1.5 rounded bg-white border border-slate-200 text-slate-700 hover:bg-slate-50 text-xs font-medium cursor-pointer"
          >
            <span>Sync Feeds</span>
          </button>

          <button
            onClick={onInjectConflicts}
            className="px-2.5 py-1.5 rounded bg-red-50 border border-red-200 text-red-800 hover:bg-red-100 text-xs font-semibold cursor-pointer"
          >
            <span>Inject Clashes</span>
          </button>
        </div>
      </div>

      {/* Sync Toast */}
      {syncToast && (
        <div className="p-2.5 bg-slate-100 border border-slate-300 rounded text-xs text-slate-800 flex items-center justify-between">
          <span>{syncToast}</span>
          <button onClick={() => setSyncToast(null)} className="text-slate-500 hover:text-slate-900 cursor-pointer">
            ✕
          </button>
        </div>
      )}

      {/* 2. Structured Feeds Table */}
      <div className="bg-white border border-slate-200 rounded-lg shadow-2xs overflow-hidden">
        {/* Table Filters Header */}
        <div className="p-3 border-b border-slate-200 flex flex-wrap items-center justify-between gap-2.5 bg-slate-50/50">
          <div className="flex items-center gap-1">
            <button
              onClick={() => setActiveTab('ALL')}
              className={`px-2.5 py-1 text-xs rounded font-medium cursor-pointer ${
                activeTab === 'ALL' ? 'bg-white text-slate-950 font-bold shadow-2xs' : 'text-slate-500'
              }`}
            >
              All ({feeds.length})
            </button>
            <button
              onClick={() => setActiveTab('Track')}
              className={`px-2.5 py-1 text-xs rounded font-medium cursor-pointer ${
                activeTab === 'Track' ? 'bg-white text-slate-950 font-bold shadow-2xs' : 'text-slate-500'
              }`}
            >
              Track ({feeds.filter((f) => f.department === 'Track').length})
            </button>
            <button
              onClick={() => setActiveTab('Signal')}
              className={`px-2.5 py-1 text-xs rounded font-medium cursor-pointer ${
                activeTab === 'Signal' ? 'bg-white text-slate-950 font-bold shadow-2xs' : 'text-slate-500'
              }`}
            >
              Signal ({feeds.filter((f) => f.department === 'Signal').length})
            </button>
            <button
              onClick={() => setActiveTab('OHE')}
              className={`px-2.5 py-1 text-xs rounded font-medium cursor-pointer ${
                activeTab === 'OHE' ? 'bg-white text-slate-950 font-bold shadow-2xs' : 'text-slate-500'
              }`}
            >
              Traction ({feeds.filter((f) => f.department === 'OHE').length})
            </button>
          </div>

          <div className="flex items-center gap-2">
            <select
              value={severityFilter}
              onChange={(e) => setSeverityFilter(e.target.value)}
              className="text-xs py-1 px-2 rounded border border-slate-200 bg-white text-slate-700"
            >
              <option value="ALL">All Severities</option>
              <option value="5">Severity 5</option>
              <option value="4">Severity 4</option>
              <option value="3">Severity 3</option>
            </select>

            <div className="relative">
              <Search className="w-3 h-3 text-slate-400 absolute left-2 top-2 pointer-events-none" />
              <input
                type="text"
                placeholder="Search..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-6 pr-2 py-1 text-xs rounded border border-slate-200 bg-white text-slate-900 w-32"
              />
            </div>
          </div>
        </div>

        {/* Table Content */}
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse text-xs">
            <thead className="bg-slate-50 border-b border-slate-200 text-slate-500 font-medium text-[11px]">
              <tr>
                <th className="py-2 px-3">ID</th>
                <th className="py-2 px-3">Dept</th>
                <th className="py-2 px-3">Defect</th>
                <th className="py-2 px-3">Corridor Track</th>
                <th className="py-2 px-3">Location</th>
                <th className="py-2 px-3">Severity</th>
                <th className="py-2 px-3">Overdue</th>
                <th className="py-2 px-3">Duration</th>
                <th className="py-2 px-3">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-slate-800">
              {filteredFeeds.map((item) => (
                <tr key={item.id} className="hover:bg-slate-50/50">
                  <td className="py-2 px-3 font-mono font-semibold text-slate-950">#{item.taskNumber}</td>
                  <td className="py-2 px-3">
                    <span className="font-semibold text-slate-700">{item.department}</span>
                  </td>
                  <td className="py-2 px-3 font-medium text-slate-900">{item.defectCategory}</td>
                  <td className="py-2 px-3 text-slate-600 truncate max-w-[180px]">{item.corridorName}</td>
                  <td className="py-2 px-3 font-mono text-[11px] text-slate-500">{item.trackKm}</td>
                  <td className="py-2 px-3 font-mono font-bold">{item.severity}/5</td>
                  <td className="py-2 px-3 font-mono">
                    {item.overdueDays >= 7 ? (
                      <span className="text-red-700 font-bold">{item.overdueDays}d overdue</span>
                    ) : (
                      <span className="text-slate-500">{item.overdueDays}d</span>
                    )}
                  </td>
                  <td className="py-2 px-3 font-mono text-slate-600">{item.estimatedMinutes}m</td>
                  <td className="py-2 px-3">
                    <span
                      className={`px-1.5 py-0.2 rounded text-[10px] font-medium ${
                        item.status === 'Merged'
                          ? 'bg-amber-50 text-amber-900 border border-amber-200'
                          : item.status === 'Scheduled'
                          ? 'bg-emerald-50 text-emerald-800 border border-emerald-200'
                          : 'bg-slate-100 text-slate-600'
                      }`}
                    >
                      {item.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <RaiseRequestModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        corridors={corridors}
        onAddRequest={onAddFeedItem}
      />
    </div>
  );
};
