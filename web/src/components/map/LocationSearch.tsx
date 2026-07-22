"use client";

// ==============================================================================
// Location Search & Auto-complete Component (web/src/components/map/LocationSearch.tsx)
// Quick Target Location Lookup & FlyTo Camera Navigation Control
// ==============================================================================

import React, { useState } from "react";

export interface TargetLocation {
  id: string;
  name: string;
  district: string;
  lat: number;
  lon: number;
}

// Danh sách 37 vị trí địa lý trọng điểm tại TP.HCM
export const TARGET_LOCATIONS: TargetLocation[] = [
  { id: "loc-01", name: "Chợ Bến Thành", district: "Quận 1", lat: 10.7727, lon: 106.6980 },
  { id: "loc-02", name: "Đường Nguyễn Huệ", district: "Quận 1", lat: 10.7740, lon: 106.7036 },
  { id: "loc-03", name: "Ngã tư Hàng Xanh", district: "Bình Thạnh", lat: 10.8014, lon: 106.7115 },
  { id: "loc-04", name: "Đường Điện Biên Phủ", district: "Quận 1", lat: 10.7887, lon: 106.6955 },
  { id: "loc-05", name: "Võ Văn Kiệt", district: "Quận 5", lat: 10.7458, lon: 106.6533 },
  { id: "loc-06", name: "Xa lộ Hà Nội", district: "QL1A", lat: 10.9493, lon: 106.8720 },
  { id: "loc-07", name: "Ngã tư An Sương", district: "Hóc Môn", lat: 10.8432, lon: 106.6151 },
  { id: "loc-08", name: "Cầu Sài Gòn", district: "Quận 2", lat: 10.7990, lon: 106.7270 },
  { id: "loc-09", name: "Cách Mạng Tháng 8", district: "Quận 3", lat: 10.7790, lon: 106.6768 },
  { id: "loc-10", name: "Phạm Văn Đồng", district: "Gò Vấp", lat: 10.8353, lon: 106.7294 },
  { id: "loc-11", name: "Nguyễn Văn Linh", district: "Quận 7", lat: 10.7526, lon: 106.7251 },
  { id: "loc-12", name: "Phú Mỹ Hưng", district: "Quận 7", lat: 10.7228, lon: 106.7281 },
];

interface LocationSearchProps {
  onSelectLocation: (lat: number, lon: number, name: string) => void;
}

export const LocationSearch: React.FC<LocationSearchProps> = ({ onSelectLocation }) => {
  const [query, setQuery] = useState("");
  const [isOpen, setIsOpen] = useState(false);

  const filtered = TARGET_LOCATIONS.filter(
    (loc) =>
      loc.name.toLowerCase().includes(query.toLowerCase()) ||
      loc.district.toLowerCase().includes(query.toLowerCase())
  );

  return (
    <div className="relative w-full">
      <input
        type="text"
        value={query}
        onChange={(e) => {
          setQuery(e.target.value);
          setIsOpen(true);
        }}
        onFocus={() => setIsOpen(true)}
        placeholder="🔍 Tìm đường, quận, ngã tư (vd: Hàng Xanh, Bến Thành)..."
        className="w-full py-2 pl-9 pr-4 text-xs bg-slate-800/90 border border-slate-700 rounded-full text-slate-200 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all shadow-inner"
      />

      {isOpen && filtered.length > 0 && (
        <div className="absolute top-full left-0 right-0 mt-2 bg-slate-900/95 backdrop-blur-xl border border-slate-700/80 rounded-2xl shadow-2xl z-50 max-h-60 overflow-y-auto p-1">
          {filtered.map((loc) => (
            <button
              key={loc.id}
              onClick={() => {
                onSelectLocation(loc.lat, loc.lon, loc.name);
                setQuery(loc.name);
                setIsOpen(false);
              }}
              className="w-full text-left px-3 py-2 hover:bg-slate-800 rounded-xl transition flex items-center justify-between text-xs"
            >
              <div>
                <span className="font-bold text-slate-100 block">{loc.name}</span>
                <span className="text-[10px] text-slate-400">{loc.district}</span>
              </div>
              <span className="text-blue-400 text-xs">Bay tới ✈️</span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
};
