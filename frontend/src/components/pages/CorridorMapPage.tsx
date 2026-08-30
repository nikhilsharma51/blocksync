'use client';

import React, { useState } from 'react';
import {
  MapPin,
  Train,
  Clock,
  Zap,
  CheckCircle2,
  AlertTriangle,
  Layers,
  Sparkles,
  Info,
  Shield,
  Sliders,
} from 'lucide-react';
import {
  StationNode,
  TimetableFreeWindow,
  CorridorSection,
} from '../../types/railway';

interface CorridorMapPageProps {
  stations: StationNode[];
  windows: TimetableFreeWindow[];
  corridors: CorridorSection[];
}

export const CorridorMapPage: React.FC<CorridorMapPageProps> = ({
  stations,
  windows,
  corridors,
}) => {
  const [showGoodsOverlay, setShowGoodsOverlay] = useState<boolean>(true);
  const [selectedStation, setSelectedStation] = useState<StationNode | null>(stations[0]);

  return (
    <div className="space-y-4 animate-in fade-in">
      {/* 1. Top Header Bar */}
      <div className="p-4 bg-white border border-slate-200 rounded-xl shadow-2xs flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="p-1 rounded-md bg-slate-900 text-white">
              <MapPin className="w-4 h-4" />
            </span>
            <h2 className="text-base font-bold text-slate-950">
              Corridor Capacity &amp; Timetable Availability Map
            </h2>
            <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-teal-100 text-teal-800 border border-teal-200">
              COA LIVE TIMETABLE ENGINE
            </span>
          </div>
          <p className="mt-1 text-xs text-slate-500">
            Delhi–Kanpur Trunk Quad-Track Schematic • Dynamic Maintenance Window Detection
          </p>
        </div>

        {/* Goods Train Overlay Toggle */}
        <div className="flex items-center gap-3">
          <label className="flex items-center gap-2 text-xs font-semibold text-slate-800 bg-slate-50 px-3 py-2 rounded-lg border border-slate-200 cursor-pointer hover:bg-slate-100 transition-colors">
            <input
              type="checkbox"
              checked={showGoodsOverlay}
              onChange={(e) => setShowGoodsOverlay(e.target.checked)}
              className="rounded border-slate-300 accent-sky-600"
            />
            <span>Overlay Goods Train Forecast (COA/FOIS)</span>
          </label>
        </div>
      </div>

      {/* 2. Linear Corridor Schematic Diagram */}
      <div className="p-5 bg-white border border-slate-200 rounded-xl shadow-2xs space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-900 flex items-center gap-2">
            <Train className="w-4 h-4 text-slate-600" />
            <span>Delhi – Kanpur Quad-Track Route Schematic (Km 0 to Km 440)</span>
          </h3>
          <span className="text-xs text-slate-400 font-mono">10 Major Interlocking Stations</span>
        </div>

        {/* Station Track Map Visualization */}
        <div className="overflow-x-auto pb-4 pt-2">
          <div className="min-w-[900px] relative px-4">
            {/* UP Line Track Line */}
            <div className="absolute top-[38px] left-8 right-8 h-1 bg-indigo-500 rounded-full z-0" />
            {/* DOWN Line Track Line */}
            <div className="absolute top-[82px] left-8 right-8 h-1 bg-teal-500 rounded-full z-0" />

            {/* Stations Track Nodes */}
            <div className="relative z-10 flex items-center justify-between">
              {stations.map((stn, idx) => (
                <div
                  key={stn.code}
                  onClick={() => setSelectedStation(stn)}
                  className="flex flex-col items-center group cursor-pointer"
                >
                  {/* Station Code & Name */}
                  <div className="text-[11px] font-bold text-slate-900 group-hover:text-sky-700 transition-colors">
                    {stn.code}
                  </div>
                  <div className="text-[9px] font-medium text-slate-400">{stn.name}</div>

                  {/* UP Track Node */}
                  <div className="mt-1.5 w-4 h-4 rounded-full bg-white border-2 border-indigo-600 flex items-center justify-center group-hover:scale-125 transition-transform shadow-2xs">
                    <span className="w-1.5 h-1.5 rounded-full bg-indigo-600" />
                  </div>

                  {/* Distance Km */}
                  <div className="my-1.5 text-[9px] font-mono text-slate-500 bg-slate-100 px-1 rounded">
                    Km {stn.km}
                  </div>

                  {/* DOWN Track Node */}
                  <div className="w-4 h-4 rounded-full bg-white border-2 border-teal-600 flex items-center justify-center group-hover:scale-125 transition-transform shadow-2xs">
                    <span className="w-1.5 h-1.5 rounded-full bg-teal-600" />
                  </div>

                  {stn.isJunction && (
                    <span className="mt-1.5 px-1 py-0.2 rounded text-[8px] font-black bg-slate-900 text-amber-300">
                      JN
                    </span>
                  )}
                </div>
              ))}
            </div>

            {/* Line Identifiers */}
            <div className="mt-4 flex items-center justify-between text-[11px] font-bold pt-2 border-t border-slate-100">
              <div className="flex items-center gap-2 text-indigo-900">
                <span className="w-3 h-1 bg-indigo-500 rounded" />
                <span>UP MAIN LINE (Towards New Delhi • 160 km/h)</span>
              </div>
              <div className="flex items-center gap-2 text-teal-900">
                <span className="w-3 h-1 bg-teal-500 rounded" />
                <span>DOWN MAIN LINE (Towards Kanpur Central • 160 km/h)</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* 3. Timetable Availability & Gold Windows Band */}
      <div className="p-4 bg-white border border-slate-200 rounded-xl shadow-2xs space-y-3">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-900 flex items-center gap-1.5">
              <Clock className="w-4 h-4 text-emerald-600" />
              <span>COA Free Maintenance Windows (Night Traffic Lulls)</span>
            </h3>
            <p className="text-[11px] text-slate-500">
              Derived from passenger timetable headway + goods train DFC paths
            </p>
          </div>
          <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-100 text-emerald-900 border border-emerald-200">
            6 Gold Windows Identified
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          {windows.map((win) => (
            <div
              key={win.id}
              className="p-3 rounded-lg border border-emerald-200 bg-emerald-50/50 space-y-2 hover:border-emerald-300 transition-all shadow-2xs"
            >
              <div className="flex items-center justify-between text-xs">
                <span className="font-bold text-slate-950">
                  {win.corridorId.replace('sec-', '').toUpperCase()}
                </span>
                <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-emerald-700 text-white font-mono">
                  {win.durationMins} Mins Free
                </span>
              </div>

              <div className="space-y-1 text-[11px] text-slate-700">
                <div className="flex items-center justify-between">
                  <span className="text-slate-500">Window Slot:</span>
                  <span className="font-mono font-bold text-emerald-900">
                    0{Math.floor(win.startHour)}:30 – 0{Math.floor(win.endHour)}:30 IST
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-slate-500">Passenger Trains:</span>
                  <span className="font-semibold text-emerald-800">0 Collisions</span>
                </div>
                {showGoodsOverlay && (
                  <div className="pt-1.5 border-t border-emerald-200 text-[10px] text-slate-600 font-mono">
                    🚂 <strong>Freight Status:</strong> {win.goodsTrainBuffer}
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
