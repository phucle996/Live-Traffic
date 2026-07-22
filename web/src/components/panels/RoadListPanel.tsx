"use client";

// ==============================================================================
// Road List Sidebar Panel (web/src/components/panels/RoadListPanel.tsx)
// Scrollable List of All Monitored Roads with Real-Time Speed Indicators
// Search/Filter by Name & District, Click-to-Select on Map
// ==============================================================================

import React, { useState, useMemo } from "react";
import { LiveTrafficRecord } from "@/api/liveTrafficClient";

interface RoadListPanelProps {
  records: LiveTrafficRecord[];
  selectedId?: string;
  onSelectRoad: (record: LiveTrafficRecord) => void;
}

export const RoadListPanel: React.FC<RoadListPanelProps> = ({
  records,
  selectedId,
  onSelectRoad,
}) => {
  const [query, setQuery] = useState("");
  const [sortBy, setSortBy] = useState<"name" | "speed" | "congestion">("congestion");

  // Lọc danh sách theo từ khóa tìm kiếm
  const filtered = useMemo(() => {
    const q = query.toLowerCase();
    return records.filter(
      (r) =>
        r.location_name.toLowerCase().includes(q) ||
        r.district.toLowerCase().includes(q)
    );
  }, [records, query]);

  // Sắp xếp danh sách theo tiêu chí
  const sorted = useMemo(() => {
    return [...filtered].sort((a, b) => {
      if (sortBy === "speed")     return a.current_speed - b.current_speed;
      if (sortBy === "name")      return a.location_name.localeCompare(b.location_name);
      // Mặc định: congestion (vận tốc / tự do) — tắc nhất lên đầu
      const ra = a.current_speed / (a.free_flow_speed || 45);
      const rb = b.current_speed / (b.free_flow_speed || 45);
      return ra - rb;
    });
  }, [filtered, sortBy]);

  const getSpeedInfo = (rec: LiveTrafficRecord) => {
    const ratio = rec.current_speed / (rec.free_flow_speed || 45);
    if (ratio >= 0.75) return { color: "text-emerald-400", bg: "border-emerald-500/30", badge: "🟢 Thông thoáng" };
    if (ratio >= 0.45) return { color: "text-amber-400",   bg: "border-amber-500/30",   badge: "🟡 Đông xe" };
    return              { color: "text-red-500",            bg: "border-red-500/30",     badge: "🔴 Ùn tắc" };
  };

  return (
    <div className="flex flex-col h-full space-y-3">
      {/* Header thống kê nhanh */}
      <div className="grid grid-cols-3 gap-1.5 shrink-0">
        <div className="p-2 bg-red-500/10 border border-red-500/30 rounded-xl text-center">
          <span className="text-lg font-extrabold text-red-500 block">
            {records.filter(r => r.current_speed < 20).length}
          </span>
          <span className="text-[9px] text-red-400 leading-tight block">🔴 Ùn tắc</span>
        </div>
        <div className="p-2 bg-amber-500/10 border border-amber-500/30 rounded-xl text-center">
          <span className="text-lg font-extrabold text-amber-400 block">
            {records.filter(r => r.current_speed >= 20 && r.current_speed < 35).length}
          </span>
          <span className="text-[9px] text-amber-400 leading-tight block">🟡 Đông xe</span>
        </div>
        <div className="p-2 bg-emerald-500/10 border border-emerald-500/30 rounded-xl text-center">
          <span className="text-lg font-extrabold text-emerald-400 block">
            {records.filter(r => r.current_speed >= 35).length}
          </span>
          <span className="text-[9px] text-emerald-400 leading-tight block">🟢 Thông</span>
        </div>
      </div>

      {/* Search Box */}
      <div className="shrink-0">
        <input
          type="text"
          value={query}
          onChange={e => setQuery(e.target.value)}
          placeholder="🔍 Tìm tuyến đường hoặc quận..."
          className="w-full py-2 px-3 bg-slate-800 border border-slate-700 rounded-xl text-xs text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>

      {/* Sort Controls */}
      <div className="flex items-center space-x-1.5 shrink-0">
        <span className="text-[10px] text-slate-400">Sắp xếp:</span>
        {(["congestion", "speed", "name"] as const).map((s) => (
          <button
            key={s}
            onClick={() => setSortBy(s)}
            className={`px-2 py-0.5 rounded-lg text-[10px] font-semibold transition ${
              sortBy === s
                ? "bg-blue-600 text-white"
                : "bg-slate-800 text-slate-400 hover:bg-slate-700"
            }`}
          >
            {s === "congestion" ? "Ùn tắc nhất" : s === "speed" ? "Tốc độ" : "Tên A-Z"}
          </button>
        ))}
      </div>

      {/* Scrollable Road List */}
      <div className="flex-1 overflow-y-auto space-y-1.5 pr-0.5">
        {sorted.length === 0 ? (
          <div className="p-6 text-center text-slate-500 text-xs">
            Không tìm thấy tuyến đường nào phù hợp.
          </div>
        ) : (
          sorted.map((rec) => {
            const info = getSpeedInfo(rec);
            const isSelected = rec.location_id === selectedId;
            return (
              <button
                key={rec.location_id}
                onClick={() => onSelectRoad(rec)}
                className={`w-full text-left p-3 rounded-xl border transition-all ${
                  isSelected
                    ? "bg-blue-600/20 border-blue-500/60 ring-1 ring-blue-500/40"
                    : `bg-slate-800/60 hover:bg-slate-800 ${info.bg}`
                }`}
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="flex-1 min-w-0">
                    <span className="text-xs font-bold text-white block truncate">
                      {rec.location_name}
                    </span>
                    <span className="text-[10px] text-slate-400 block">{rec.district}</span>
                  </div>
                  <div className="text-right shrink-0">
                    <span className={`text-sm font-extrabold block leading-tight ${info.color}`}>
                      {rec.current_speed.toFixed(1)}
                    </span>
                    <span className="text-[9px] text-slate-400">km/h</span>
                  </div>
                </div>
                <div className="flex items-center justify-between mt-1.5">
                  <span className={`text-[9px] font-semibold ${info.color}`}>{info.badge}</span>
                  <div className="flex-1 mx-2 h-1 bg-slate-700 rounded-full overflow-hidden">
                    <div
                      className="h-full rounded-full transition-all"
                      style={{
                        width: `${Math.min((rec.current_speed / (rec.free_flow_speed || 45)) * 100, 100)}%`,
                        backgroundColor: info.color.includes("emerald") ? "#22c55e" : info.color.includes("amber") ? "#eab308" : "#ef4444",
                      }}
                    />
                  </div>
                  <span className="text-[9px] text-slate-500">
                    {((rec.current_speed / (rec.free_flow_speed || 45)) * 100).toFixed(0)}%
                  </span>
                </div>
              </button>
            );
          })
        )}
      </div>
    </div>
  );
};
