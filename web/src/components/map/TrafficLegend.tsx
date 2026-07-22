"use client";

// ==============================================================================
// Map Traffic Legend Component (web/src/components/map/TrafficLegend.tsx)
// Map Traffic Status Color Indicators & Speed Thresholds Reference
// ==============================================================================

import React from "react";

export const TrafficLegend: React.FC = () => {
  return (
    <div className="bg-slate-900/90 backdrop-blur-md border border-slate-700/60 p-3 rounded-2xl shadow-xl text-xs space-y-2 max-w-[200px]">
      <span className="font-bold text-slate-200 block border-b border-slate-800 pb-1">
        🚦 Mức Độ Giao Thông
      </span>

      <div className="space-y-1.5">
        <div className="flex items-center space-x-2">
          <span className="w-3 h-3 rounded-full bg-emerald-500 shadow-sm shadow-emerald-500/50"></span>
          <span className="text-slate-300 text-[11px]">Thông thoáng (&ge; 35 km/h)</span>
        </div>

        <div className="flex items-center space-x-2">
          <span className="w-3 h-3 rounded-full bg-amber-500 shadow-sm shadow-amber-500/50"></span>
          <span className="text-slate-300 text-[11px]">Đông xe (20 - 35 km/h)</span>
        </div>

        <div className="flex items-center space-x-2">
          <span className="w-3 h-3 rounded-full bg-red-500 shadow-sm shadow-red-500/50"></span>
          <span className="text-slate-300 text-[11px]">Ùn tắc (&lt; 20 km/h)</span>
        </div>

        <div className="flex items-center space-x-2">
          <span className="w-3 h-3 rounded-full bg-slate-500"></span>
          <span className="text-slate-400 text-[11px]">Chưa có dữ liệu</span>
        </div>
      </div>
    </div>
  );
};
