"use client";

// ==============================================================================
// Saved Locations Panel Component (web/src/components/panels/SavedLocationsPanel.tsx)
// User Favorite Saved Locations & Quick Real-Time Status Monitoring Panel
// ==============================================================================

import React, { useState } from "react";
import { LiveTrafficRecord } from "@/api/liveTrafficClient";

interface SavedLocationsPanelProps {
  onSelectLocation?: (record: LiveTrafficRecord) => void;
}

export const SavedLocationsPanel: React.FC<SavedLocationsPanelProps> = ({ onSelectLocation }) => {
  // Mẫu danh sách địa điểm yêu thích đã lưu
  const [savedItems, setSavedItems] = useState([
    {
      id: "saved-01",
      tag: "🏠 Nhà",
      location_id: "loc-03",
      location_name: "Ngã tư Hàng Xanh",
      district: "Bình Thạnh",
      current_speed: 14.0,
      free_flow_speed: 32.0,
      latitude: 10.8014,
      longitude: 106.7115,
      source: "tomtom_live",
      observed_at: "2026-07-21T17:30:00Z",
      data_age_seconds: 45,
      confidence: 0.98
    },
    {
      id: "saved-02",
      tag: "🏢 Công ty",
      location_id: "loc-01",
      location_name: "Chợ Bến Thành",
      district: "Quận 1",
      current_speed: 10.0,
      free_flow_speed: 45.0,
      latitude: 10.7727,
      longitude: 106.6980,
      source: "tomtom_live",
      observed_at: "2026-07-21T17:30:00Z",
      data_age_seconds: 45,
      confidence: 0.95
    }
  ]);

  const handleRemoveSaved = (id: string, name: string) => {
    setSavedItems((prev) => prev.filter((item) => item.id !== id));
    alert(`Đã xóa ${name} khỏi danh sách địa điểm yêu thích!`);
  };

  return (
    <div className="space-y-4">
      {/* Header Info */}
      <div className="p-3 bg-blue-600/10 border border-blue-500/30 rounded-2xl">
        <h3 className="text-sm font-bold text-blue-400 flex items-center gap-1.5">
          <span>⭐️</span> Địa Điểm Yêu Thích Đã Lưu
        </h3>
        <p className="text-[11px] text-slate-400 mt-0.5">
          Theo dõi nhanh tình trạng giao thông tại các địa điểm quan trọng của bạn.
        </p>
      </div>

      {/* Saved Locations List */}
      <div className="space-y-2">
        {savedItems.length === 0 ? (
          <div className="p-6 text-center text-slate-500 text-xs">
            Chưa có địa điểm nào được lưu. Hãy bấm nút ⭐️ Lưu trên bản đồ!
          </div>
        ) : (
          savedItems.map((item) => {
            let color = "text-emerald-400";
            let badgeText = "Thông thoáng";
            if (item.current_speed < 20) {
              color = "text-red-500";
              badgeText = "Ùn tắc";
            } else if (item.current_speed < 35) {
              color = "text-amber-400";
              badgeText = "Đông xe";
            }

            return (
              <div
                key={item.id}
                className="p-3.5 bg-slate-800/80 hover:bg-slate-800 rounded-2xl border border-slate-700/60 transition shadow-sm space-y-2"
              >
                <div className="flex items-center justify-between">
                  <span className="text-[10px] font-bold px-2 py-0.5 bg-slate-900 text-blue-400 rounded-lg border border-slate-700">
                    {item.tag}
                  </span>
                  <button
                    onClick={() => handleRemoveSaved(item.id, item.location_name)}
                    className="text-[11px] text-slate-500 hover:text-red-400 transition"
                  >
                    ✕ Xóa
                  </button>
                </div>

                <div className="flex items-center justify-between">
                  <div>
                    <h4 className="text-sm font-bold text-white">{item.location_name}</h4>
                    <span className="text-[11px] text-slate-400">{item.district}</span>
                  </div>
                  <div className="text-right">
                    <span className={`text-base font-extrabold block ${color}`}>
                      {item.current_speed.toFixed(1)} km/h
                    </span>
                    <span className="text-[10px] text-slate-400 block">{badgeText}</span>
                  </div>
                </div>

                <div className="pt-1 flex justify-end">
                  <button
                    onClick={() => onSelectLocation && onSelectLocation(item)}
                    className="px-3 py-1 bg-blue-600/20 hover:bg-blue-600/30 text-blue-400 text-[11px] font-semibold rounded-lg border border-blue-500/30 transition"
                  >
                    Xem trên Bản đồ ✈️
                  </button>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};
