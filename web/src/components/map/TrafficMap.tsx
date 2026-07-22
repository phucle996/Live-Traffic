"use client";

// ==============================================================================
// MapLibre GL JS Container Component (web/src/components/map/TrafficMap.tsx)
// Interactive Vector Map Engine for TP.HCM Urban Traffic System
// Navigation, Geolocation, Fullscreen Controls & Responsive Resizing
// ==============================================================================

import React, { useEffect, useRef } from "react";
import maplibregl from "maplibre-gl";

interface TrafficMapProps {
  onMapLoad?: (map: maplibregl.Map) => void;
  onLocationSelect?: (lat: number, lon: number, name: string) => void;
}

export const TrafficMap: React.FC<TrafficMapProps> = ({ onMapLoad, onLocationSelect }) => {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<maplibregl.Map | null>(null);

  useEffect(() => {
    if (!mapContainerRef.current || mapInstanceRef.current) return;

    // 1. Khởi tạo MapLibre GL JS Map Instance tại Trung tâm TP.HCM (Longitude 106.7009, Latitude 10.7769)
    const map = new maplibregl.Map({
      container: mapContainerRef.current,
      style: {
        version: 8,
        sources: {
          "carto-dark": {
            type: "raster",
            tiles: [
              "https://a.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}.png",
              "https://b.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}.png",
              "https://c.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}.png",
            ],
            tileSize: 256,
            attribution: "&copy; OpenStreetMap & CartoDB",
          },
        },
        layers: [
          {
            id: "carto-dark-layer",
            type: "raster",
            source: "carto-dark",
            minzoom: 0,
            maxzoom: 20,
          },
        ],
      },
      center: [106.7009, 10.7769], // TP.HCM Center
      zoom: 13,
      pitch: 0,
      bearing: 0,
    });

    // 2. Thêm Navigation Controls (Zoom In +, Zoom Out -, Dải la bàn)
    map.addControl(new maplibregl.NavigationControl({ showCompass: true }), "bottom-right");

    // 3. Thêm Geolocation Control (Tự động định vị trí GPS người dùng)
    map.addControl(
      new maplibregl.GeolocateControl({
        positionOptions: { enableHighAccuracy: true },
        trackUserLocation: true,
      }),
      "bottom-right"
    );

    // 4. Thêm Fullscreen Control
    map.addControl(new maplibregl.FullscreenControl(), "bottom-right");

    // 5. Khi Map tải xong ➔ Gọi callback trigger
    map.on("load", () => {
      mapInstanceRef.current = map;
      if (onMapLoad) {
        onMapLoad(map);
      }
    });

    // Clean up khi component unmount
    return () => {
      map.remove();
      mapInstanceRef.current = null;
    };
  }, [onMapLoad]);

  return (
    <div className="relative w-full h-full">
      {/* Container nơi MapLibre GL JS render bản đồ Canvas */}
      <div ref={mapContainerRef} className="w-full h-full" />
    </div>
  );
};
