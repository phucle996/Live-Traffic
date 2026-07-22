"use client";

// ==============================================================================
// Traffic Layer Component (web/src/components/map/TrafficLayer.tsx)
// MapLibre GL JS Real-Time Location Markers & Traffic Status Rendering
// Dynamic GeoJSON Markers, Color Coding & Click Selection Handler
// ==============================================================================

import React, { useEffect, useRef } from "react";
import maplibregl from "maplibre-gl";
import { LiveTrafficRecord } from "@/api/liveTrafficClient";

interface TrafficLayerProps {
  map: maplibregl.Map | null;
  records: LiveTrafficRecord[];
  onSelectLocation: (record: LiveTrafficRecord) => void;
}

export const TrafficLayer: React.FC<TrafficLayerProps> = ({
  map,
  records,
  onSelectLocation,
}) => {
  const markersRef = useRef<maplibregl.Marker[]>([]);

  useEffect(() => {
    if (!map) return;

    // 1. Dọn dẹp các Marker cũ trên bản đồ
    markersRef.current.forEach((marker) => marker.remove());
    markersRef.current = [];

    // 2. Render các HTML Markers mới tương ứng với danh sách vị trí giao thông
    records.forEach((rec) => {
      // Xác định màu sắc chỉ báo
      let markerColor = "#22c55e"; // 🟢 Xanh
      if (rec.current_speed < 20) markerColor = "#ef4444"; // 🔴 Đỏ
      else if (rec.current_speed < 35) markerColor = "#eab308"; // 🟡 Vàng

      // Tạo Custom Element cho Marker với hiệu ứng Glow
      const el = document.createElement("div");
      el.className = "traffic-marker-dot";
      el.style.width = "18px";
      el.style.height = "18px";
      el.style.borderRadius = "50%";
      el.style.backgroundColor = markerColor;
      el.style.border = "2px solid #ffffff";
      el.style.boxShadow = `0 0 10px ${markerColor}`;
      el.style.cursor = "pointer";
      el.style.transition = "transform 0.2s ease";

      el.addEventListener("mouseenter", () => {
        el.style.transform = "scale(1.3)";
      });
      el.addEventListener("mouseleave", () => {
        el.style.transform = "scale(1.0)";
      });

      // Tạo Popup thông tin nhanh khi hover
      const popup = new maplibregl.Popup({ offset: 12, closeButton: false }).setHTML(`
        <div style="font-family:Inter,sans-serif;padding:2px">
          <b style="color:#0f172a">${rec.location_name}</b><br/>
          Vận tốc: <b style="color:${markerColor}">${rec.current_speed.toFixed(1)} km/h</b>
        </div>
      `);

      // Gắn sự kiện click mở Detail Panel
      el.addEventListener("click", () => {
        onSelectLocation(rec);
      });

      // Thêm Marker vào bản đồ
      const marker = new maplibregl.Marker({ element: el })
        .setLngLat([rec.longitude, rec.latitude])
        .setPopup(popup)
        .addTo(map);

      markersRef.current.push(marker);
    });

    return () => {
      markersRef.current.forEach((marker) => marker.remove());
      markersRef.current = [];
    };
  }, [map, records, onSelectLocation]);

  return null;
};
