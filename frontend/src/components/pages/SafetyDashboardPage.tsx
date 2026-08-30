'use client';

import React from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  AreaChart,
  Area,
} from 'recharts';
import {
  DefectAgingBucket,
  MonthlySavedHours,
  BottleneckCorridor,
} from '../../types/railway';

interface SafetyDashboardPageProps {
  agingData: DefectAgingBucket[];
  monthlySavedData: MonthlySavedHours[];
  bottlenecks: BottleneckCorridor[];
}

export const SafetyDashboardPage: React.FC<SafetyDashboardPageProps> = ({
  agingData,
  monthlySavedData,
  bottlenecks,
}) => {
  return (
    <div className="space-y-3 animate-in fade-in">
      {/* 1. Metric Strip */}
      <div className="bg-white border border-slate-200 rounded-lg p-3 px-4 shadow-2xs">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 divide-y md:divide-y-0 md:divide-x divide-slate-100">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-md bg-emerald-50 border border-emerald-200 flex items-center justify-center text-emerald-700 font-bold text-xs shrink-0">
              98%
            </div>
            <div>
              <div className="text-[11px] font-medium text-slate-500">Safety Compliance</div>
              <div className="text-base font-bold text-slate-950 font-mono">98.2% Low Risk</div>
            </div>
          </div>

          <div className="flex items-center gap-3 md:pl-4 pt-2 md:pt-0">
            <div className="w-8 h-8 rounded-md bg-slate-50 border border-slate-200 flex items-center justify-center text-slate-700 font-bold text-xs shrink-0">
              SLA
            </div>
            <div>
              <div className="text-[11px] font-medium text-slate-500">Breach Backlog (&gt;14d)</div>
              <div className="text-base font-bold text-slate-950 font-mono">7 Tasks</div>
            </div>
          </div>

          <div className="flex items-center gap-3 md:pl-4 pt-2 md:pt-0">
            <div className="w-8 h-8 rounded-md bg-sky-50 border border-sky-200 flex items-center justify-center text-sky-700 font-bold text-xs shrink-0">
              +h
            </div>
            <div>
              <div className="text-[11px] font-medium text-slate-500">Monthly Downtime Saved</div>
              <div className="text-base font-bold text-slate-950 font-mono">+52.0 Hours</div>
            </div>
          </div>

          <div className="flex items-center gap-3 md:pl-4 pt-2 md:pt-0">
            <div className="w-8 h-8 rounded-md bg-slate-50 border border-slate-200 flex items-center justify-center text-slate-700 font-bold text-xs shrink-0">
              1.8x
            </div>
            <div>
              <div className="text-[11px] font-medium text-slate-500">Productivity Multiplier</div>
              <div className="text-base font-bold text-slate-950 font-mono">1.84x Output</div>
            </div>
          </div>
        </div>
      </div>

      {/* 2. Recharts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
        {/* Aging Distribution */}
        <div className="p-3.5 bg-white border border-slate-200 rounded-lg shadow-2xs space-y-2">
          <div className="flex items-center justify-between">
            <h3 className="text-xs font-semibold text-slate-900">
              Defect Aging Distribution by Department
            </h3>
            <span className="text-[11px] font-mono text-slate-400">52 Active</span>
          </div>

          <div className="h-56 w-full pt-1">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={agingData} margin={{ top: 10, right: 10, left: -25, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                <XAxis dataKey="bucket" tick={{ fontSize: 10, fill: '#64748b' }} />
                <YAxis tick={{ fontSize: 10, fill: '#64748b' }} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#0f172a',
                    color: '#fff',
                    borderRadius: '6px',
                    fontSize: '11px',
                    border: 'none',
                  }}
                />
                <Legend wrapperStyle={{ fontSize: '10px', paddingTop: '4px' }} />
                <Bar dataKey="Track" name="Track" fill="#ea580c" radius={[2, 2, 0, 0]} />
                <Bar dataKey="Signal" name="Signal" fill="#2563eb" radius={[2, 2, 0, 0]} />
                <Bar dataKey="OHE" name="Traction" fill="#d97706" radius={[2, 2, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Hours Saved */}
        <div className="p-3.5 bg-white border border-slate-200 rounded-lg shadow-2xs space-y-2">
          <div className="flex items-center justify-between">
            <h3 className="text-xs font-semibold text-slate-900">
              Monthly Corridor Hours Recovered (AI Joint Blocks)
            </h3>
            <span className="text-[11px] font-mono text-emerald-700 font-semibold">+52h Aug</span>
          </div>

          <div className="h-56 w-full pt-1">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart
                data={monthlySavedData}
                margin={{ top: 10, right: 10, left: -25, bottom: 0 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                <XAxis dataKey="month" tick={{ fontSize: 10, fill: '#64748b' }} />
                <YAxis tick={{ fontSize: 10, fill: '#64748b' }} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#0f172a',
                    color: '#fff',
                    borderRadius: '6px',
                    fontSize: '11px',
                    border: 'none',
                  }}
                />
                <Legend wrapperStyle={{ fontSize: '10px', paddingTop: '4px' }} />
                <Area
                  type="monotone"
                  dataKey="standaloneBlockHours"
                  name="Uncoordinated Hours"
                  stroke="#cbd5e1"
                  fill="#f8fafc"
                />
                <Area
                  type="monotone"
                  dataKey="integratedBlockHours"
                  name="Optimized Hours"
                  stroke="#0284c7"
                  fill="#e0f2fe"
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* 3. Bottleneck Table */}
      <div className="bg-white border border-slate-200 rounded-lg shadow-2xs overflow-hidden">
        <div className="p-3 border-b border-slate-200 text-xs font-semibold text-slate-900 bg-slate-50/50">
          Corridor Bottleneck Analysis &amp; Speed Restrictions
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse text-xs">
            <thead className="bg-slate-50 border-b border-slate-200 text-slate-500 font-medium text-[11px]">
              <tr>
                <th className="py-2 px-3">Corridor</th>
                <th className="py-2 px-3">Daily Trains</th>
                <th className="py-2 px-3">Avg Free Window</th>
                <th className="py-2 px-3">Pending Defects</th>
                <th className="py-2 px-3">Congestion</th>
                <th className="py-2 px-3">Caution Orders (TSR)</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-slate-800">
              {bottlenecks.map((item, idx) => (
                <tr key={idx} className="hover:bg-slate-50/50">
                  <td className="py-2 px-3 font-semibold text-slate-900">{item.corridor}</td>
                  <td className="py-2 px-3 font-mono">{item.trainPathsPerDay}</td>
                  <td className="py-2 px-3 font-mono text-slate-600">{item.avgFreeWindowMins}m</td>
                  <td className="py-2 px-3 font-mono">{item.pendingDefects}</td>
                  <td className="py-2 px-3">
                    <span
                      className={`px-1.5 py-0.2 rounded text-[10px] font-medium ${
                        item.congestionIndex === 'Severe'
                          ? 'text-red-700 bg-red-50'
                          : 'text-amber-700 bg-amber-50'
                      }`}
                    >
                      {item.congestionIndex}
                    </span>
                  </td>
                  <td className="py-2 px-3 font-mono text-[11px] text-slate-500">{item.speedRestrictionKm}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
