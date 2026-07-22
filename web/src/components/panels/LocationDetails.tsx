"use client";

// ==============================================================================
// Location Details Panel Component (web/src/components/panels/LocationDetails.tsx)
// Renders Selected Location Details, Traffic Status, Freshness & Action Controls
// ==============================================================================

import React from "react";
import { LiveTrafficRecord } from "@/api/liveTrafficClient";

interface LocationDetailsProps {
  location: LiveTrafficRecord | null;
  onPredictClick?: (location: LiveTrafficRecord) => void;
  onSaveClick?: (location: LiveTrafficRecord) => void;
}

export const LocationDetails: React.FC<LocationDetailsProps> = ({
  location,
  onPredictClick,
  onSaveClick,
}) => {
  if (!location) {
    return (
      <div className="p-6 text-center text-slate-400 space-y-2">
        <span className="text-3xl block">📍</span>
        <p className="text-xs">Nhấp vào một điểm trên bản đồ để xem thông tin chi tiết giao thông thời gian thực.</p>
      </div>
    );
  }

  // Xác định màu sắc theo vận tốc
  let speedColor = "text-emerald-400";
  let statusBadge = "🟢 Thông thoáng";
  let statusBg = "bg-emerald-500/10 border-emerald-500/30 text-emerald-400";

  if (location.current_speed < 20) {
    speedColor = "text-red-500";
    statusBadge = "🔴 Ùn tắc nghiêm trọng";
    statusBg = "bg-red-500/10 border-red-500/30 text-red-400";
  } else if (location.current_speed < 35) {
    speedColor = "text-amber-400";
    statusBadge = "🟡 Đông xe";
    statusBg = "bg-amber-500/10 border-amber-500/30 text-amber-400";
  }

  // Xác định độ tươi dữ liệu (Data Freshness)
  let freshnessBadge = "🟢 LIVE";
  let freshnessText = `${location.data_age_seconds || 0}s trước`;
  if ((location.data_age_seconds || 0) > 1800) {
    freshnessBadge = "🔴 OFFLINE";
  } else if ((location.data_age_seconds || 0) > 180) {
    freshnessBadge = "🟡 STALE";
  }

  return (
    <div className="space-y-4">
      {/* Title Header */}
      <div className="p-3.5 bg-slate-800/70 rounded-2xl border border-slate-700/50 space-y-1">
        <div className="flex items-center justify-between">
          <span className="text-[10px] font-bold tracking-wider uppercase text-slate-400">Tuyến đường</span>
          <span className="text-[10px] px-2 py-0.5 rounded font-mono bg-slate-900 text-slate-300 border border-slate-700">
            {freshnessBadge} • {freshnessText}
          </span>
        </div>
        <h3 className="text-base font-bold text-white">{location.location_name}</h3>
        <p className="text-xs text-slate-400">{location.district}, TP. Hồ Chí Minh</p>
      </div>

      {/* Speed Metrics Grid */}
      <div className="grid grid-cols-2 gap-2">
        <div className="p-3 bg-slate-800/40 rounded-2xl border border-slate-700/30">
          <span className="text-[11px] text-slate-400 block mb-1">Vận tốc hiện tại</span>
          <span className={`text-xl font-extrabold ${speedColor}`}>
            {location.current_speed.toFixed(1)} km/h
          </span>
        </div>
        <div className="p-3 bg-slate-800/40 rounded-2xl border border-slate-700/30">
          <span className="text-[11px] text-slate-400 block mb-1">Vận tốc tự do</span>
          <span className="text-xl font-bold text-slate-200">
            {location.free_flow_speed.toFixed(1)} km/h
          </span>
        </div>
      </div>

      {/* Traffic Status Badge */}
      <div className={`p-3 border rounded-2xl ${statusBg} flex items-center justify-between`}>
        <span className="text-xs font-semibold">{statusBadge}</span>
        <span className="text-[11px] font-mono opacity-80">
          Tỷ lệ: {((location.current_speed / (location.free_flow_speed || 45)) * 100).toFixed(0)}%
        </span>
      </div>

      {/* Metadata Info */}
      <div className="text-[11px] text-slate-400 space-y-1 px-1">
        <div className="flex justify-between">
          <span>Nguồn dữ liệu:</span>
          <code className="text-slate-300">{location.source || "tomtom_live"}</code>
        </div>
        <div className="flex justify-between">
          <span>Độ tin cậy cảm biến:</span>
          <span className="text-slate-300">{((location.confidence || 0.95) * 100).toFixed(0)}%</span>
        </div>
      </div>

      {/* Action Buttons */}
      <div className="pt-2 flex space-x-2">
        <button
          onClick={() => onPredictClick && onPredictClick(location)}
          className="flex-1 py-2.5 bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold rounded-xl transition shadow-lg flex items-center justify-center space-x-1"
        >
          <span>🤖</span>
          <span>Xem AI Dự Đoán</span>
        </button>
        <button
          onClick={() => onSaveClick && onSaveClick(location)}
          className="px-3.5 py-2.5 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium rounded-xl transition border border-slate-700"
        >
          ⭐️ Lưu
        </button>
      </div>
    </div>
  );
};
