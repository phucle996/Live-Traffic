"use client";

// ==============================================================================
// Application Shell Component (web/src/components/layout/AppShell.tsx)
// Map-First Responsive Layout Shell (Desktop Side Panel + Mobile Bottom Sheet)
// MapLibre GL JS Engine Integration, Live Traffic API & Rust Prediction Integration
// History Timeline Playback, Saved Locations & Google Maps-style Road Layer Integration
// ==============================================================================

import React, { useState, useRef, useEffect, useCallback } from "react";
// Đã gỡ bỏ import UserMenu (màn hình hoàn toàn công khai)
import { TrafficMap } from "@/components/map/TrafficMap";
import { TrafficLegend } from "@/components/map/TrafficLegend";
import { LocationSearch } from "@/components/map/LocationSearch";
import { TrafficRoadsLayer } from "@/components/map/TrafficRoadsLayer";
import { PredictionLayer, PredictionMarkerData } from "@/components/map/PredictionLayer";
import { LocationDetails } from "@/components/panels/LocationDetails";
import { PredictionPanel } from "@/components/panels/PredictionPanel";
import { HistoryPanel } from "@/components/panels/HistoryPanel";
import { SavedLocationsPanel } from "@/components/panels/SavedLocationsPanel";
import { RoadListPanel } from "@/components/panels/RoadListPanel";
import {
  fetchLiveTrafficData,
  fetchSourceStatusData,
  LiveTrafficRecord,
} from "@/api/liveTrafficClient";
import {
  fetchSinglePrediction,
  fetchBatchPredictions,
  PredictionResponse,
} from "@/api/predictionClient";
// Đã gỡ bỏ useAuth context hook
import maplibregl from "maplibre-gl";

interface AppShellProps {
  children?: React.ReactNode;
}

export const AppShell: React.FC<AppShellProps> = ({ children }) => {
  // Ứng dụng công khai - Không sử dụng accessToken xác thực

  // State quản lý tab đang chọn (Live+List | Prediction | History | Saved)
  const [activeTab, setActiveTab] = useState<"live" | "predict" | "history" | "saved">("live");
  // State thu gọn Side Panel trên Desktop
  const [isPanelOpen, setIsPanelOpen] = useState(true);
  // State nâng Bottom Sheet trên Mobile
  const [isMobileSheetExpanded, setIsMobileSheetExpanded] = useState(false);

  // State Dữ liệu Live Traffic từ Go API Microservice
  const [trafficRecords, setTrafficRecords] = useState<LiveTrafficRecord[]>([]);
  const [selectedLocation, setSelectedLocation] = useState<LiveTrafficRecord | null>(null);
  const [sourceModeText, setSourceModeText] = useState<string>("Nạp dữ liệu...");
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // State Dữ liệu Dự đoán Model AI từ Rust Engine Microservice
  const [predictionMarkers, setPredictionMarkers] = useState<PredictionMarkerData[]>([]);
  const [singlePredictionResult, setSinglePredictionResult] = useState<PredictionResponse | null>(null);
  const [isPredicting, setIsPredicting] = useState<boolean>(false);

  // Reference điều khiển MapLibre Camera FlyTo
  const mapRef = useRef<maplibregl.Map | null>(null);

  // Hàm nạp dữ liệu Live Traffic công khai từ Go API (:8084)
  const loadLiveTraffic = useCallback(async () => {
    setIsLoading(true);
    setErrorMessage(null);
    try {
      // Gọi fetchLiveTrafficData không cần token
      const data = await fetchLiveTrafficData();
      const records = data.traffic_data || [];
      setTrafficRecords(records);

      if (records.length > 0 && !selectedLocation) {
        setSelectedLocation(records[0]);
      }
    } catch (err) {
      console.warn("Lỗi fetch Live Traffic Data:", err);
      setErrorMessage("⚠️ Không thể kết nối Go Live API Server");
    } finally {
      setIsLoading(false);
    }
  }, [selectedLocation]);

  // Hàm nạp thông tin trạng thái nguồn dữ liệu công khai từ Go Source Status API
  const loadSourceStatus = useCallback(async () => {
    try {
      // Gọi fetchSourceStatusData không cần token
      const status = await fetchSourceStatusData();
      setSourceModeText(`Nguồn: ${status.active_source_mode.toUpperCase()}`);
    } catch (err) {
      console.warn("Lỗi fetch Source Status:", err);
    }
  }, []);

  // Tự động nạp dữ liệu khi nạp trang và thiết lập Auto-Refresh Loop (15 giây/lần)
  useEffect(() => {
    loadLiveTraffic();
    loadSourceStatus();

    const intervalId = setInterval(() => {
      if (!document.hidden) {
        loadLiveTraffic();
        loadSourceStatus();
      }
    }, 15000);

    return () => clearInterval(intervalId);
  }, [loadLiveTraffic, loadSourceStatus]);

  // Thực thi suy luận AI cho vị trí đang được chọn từ Rust Inference Engine (:8090)
  const handleRunSinglePrediction = async (location: LiveTrafficRecord) => {
    setIsPredicting(true);
    try {
      // Thực hiện suy luận điểm đơn không cần truyền token
      const result = await fetchSinglePrediction({
        latitude: location.latitude,
        longitude: location.longitude,
        free_flow_speed: location.free_flow_speed,
        confidence: location.confidence || 0.95,
        street_name: location.location_name,
      });

      setSinglePredictionResult(result);
      setPredictionMarkers([
        {
          ...result,
          latitude: location.latitude,
          longitude: location.longitude,
        },
      ]);
      setActiveTab("predict");
      setIsPanelOpen(true);
    } catch (err: any) {
      alert("Lỗi suy luận AI từ Rust Engine: " + err.message);
    } finally {
      setIsPredicting(false);
    }
  };

  // Thực thi suy luận AI hàng loạt cho danh sách các vị trí
  const handleRunBatchPrediction = async (datetimeStr: string, districtFilter: string) => {
    setIsPredicting(true);
    try {
      const targetList = trafficRecords.filter(
        (r) => districtFilter === "ALL" || r.district === districtFilter
      );

      if (targetList.length === 0) {
        alert("Không có tuyến đường nào thuộc khu vực đã chọn!");
        return;
      }

      const batchReq = {
        locations: targetList.map((r) => ({
          latitude: r.latitude,
          longitude: r.longitude,
          free_flow_speed: r.free_flow_speed,
          confidence: r.confidence || 0.95,
          street_name: r.location_name,
        })),
        prediction_time: datetimeStr,
      };

      // Thực hiện suy luận batch AI không cần truyền token
      const res = await fetchBatchPredictions(batchReq);
      const newMarkers: PredictionMarkerData[] = res.predictions.map((p, idx) => ({
        ...p,
        latitude: targetList[idx]?.latitude || 10.7727,
        longitude: targetList[idx]?.longitude || 106.6980,
      }));

      setPredictionMarkers(newMarkers);
      if (newMarkers.length > 0) {
        setSinglePredictionResult(newMarkers[0]);
      }
    } catch (err: any) {
      alert("Lỗi suy luận Batch AI từ Rust Engine: " + err.message);
    } finally {
      setIsPredicting(false);
    }
  };

  // Xử lý thay đổi mốc thời gian Playback trên HistoryPanel
  const handleHistoryTimeChange = (hour: number) => {
    // Giả lập biến thiên vận tốc theo giờ phát playback
    setTrafficRecords((prev) =>
      prev.map((rec) => {
        let simulatedSpeed = rec.free_flow_speed * 0.8;
        if (hour === 7 || hour === 8 || hour === 17 || hour === 18) {
          simulatedSpeed = rec.free_flow_speed * 0.3; // Giờ cao điểm tắc nghẽn
        } else if (hour >= 22 || hour <= 5) {
          simulatedSpeed = rec.free_flow_speed * 0.95; // Đêm vắng thông thoáng
        }
        return {
          ...rec,
          current_speed: simulatedSpeed,
        };
      })
    );
  };

  // Xử lý di chuyển Camera MapLibre đến tọa độ địa điểm được chọn
  const handleSelectLocationFromSearch = (lat: number, lon: number, name: string) => {
    if (mapRef.current) {
      mapRef.current.flyTo({
        center: [lon, lat],
        zoom: 15,
        speed: 1.2,
        curve: 1.4,
      });
    }

    const matched = trafficRecords.find(
      (r) => r.location_name.toLowerCase().includes(name.toLowerCase()) || r.latitude === lat
    );
    if (matched) {
      setSelectedLocation(matched);
      setIsPanelOpen(true);
    }
  };

  const handleSelectLocationMarker = (record: LiveTrafficRecord) => {
    setSelectedLocation(record);
    setIsPanelOpen(true);
    setIsMobileSheetExpanded(true);
  };

  return (
    <div className="relative flex flex-col w-screen h-screen overflow-hidden bg-slate-900 text-slate-100 font-sans">
      {/* 1. Top Navigation Bar (Header Tối Giản Map-First) */}
      <header className="absolute top-0 left-0 right-0 z-30 flex items-center justify-between px-4 py-3 bg-slate-900/80 backdrop-blur-md border-b border-slate-700/50 shadow-md">
        {/* Logo & Application Title */}
        <div className="flex items-center space-x-3">
          <span className="text-2xl">🚗</span>
          <div>
            <h1 className="text-lg font-bold tracking-tight text-white font-heading">
              TRAFFIC VIEW
            </h1>
            <p className="text-xs text-slate-400 hidden sm:block">
              Hệ thống Giám sát & Dự đoán Giao thông TP.HCM
            </p>
          </div>
        </div>

        {/* Universal Search Input Box */}
        <div className="flex-1 max-w-md mx-4 hidden md:block">
          <LocationSearch onSelectLocation={handleSelectLocationFromSearch} />
        </div>

        {/* Status Badge & User Controls */}
        <div className="flex items-center space-x-3">
          <div className="flex items-center space-x-2 px-3 py-1 bg-emerald-500/10 border border-emerald-500/30 rounded-full">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
            <span className="text-xs font-semibold text-emerald-400">{sourceModeText}</span>
          </div>

          <button
            onClick={loadLiveTraffic}
            disabled={isLoading}
            className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold rounded-xl border border-slate-700 transition"
          >
            {isLoading ? "🔄..." : "🔄 Làm Mới"}
          </button>

          {/* Đã gỡ bỏ UserMenu Profile Dropdown */}
        </div>
      </header>

      {/* 2. Main Map-First Canvas Area */}
      <main className="relative flex-1 w-full h-full pt-14">
        {/* MapLibre GL JS Vector Map Container */}
        <div className="absolute inset-0 w-full h-full">
          <TrafficMap
            onMapLoad={(map) => {
              mapRef.current = map;
            }}
          />
          {/* Google Maps-style Road Polyline Layer (click đường → hiện chi tiết) */}
          <TrafficRoadsLayer
            map={mapRef.current}
            records={trafficRecords}
            onSelectRoad={handleSelectLocationMarker}
          />
          {/* AI Model Prediction Layer (Hình thoi ◆) */}
          <PredictionLayer
            map={mapRef.current}
            predictions={predictionMarkers}
          />
        </div>

        {/* Map Traffic Legend */}
        <div className="absolute bottom-6 left-6 z-20 hidden md:block">
          <TrafficLegend />
        </div>

        {/* 3. Floating Navigation Floating Pills */}
        <div className="absolute top-16 left-4 z-20 hidden sm:flex items-center space-x-1 p-1 bg-slate-900/80 backdrop-blur border border-slate-700/60 rounded-xl shadow-lg">
          <button
            onClick={() => setActiveTab("live")}
            className={`px-3 py-1.5 text-xs font-medium rounded-lg transition-all ${
              activeTab === "live"
                ? "bg-blue-600 text-white shadow"
                : "text-slate-300 hover:bg-slate-800"
            }`}
          >
            🔴 Live Traffic
          </button>
          <button
            onClick={() => setActiveTab("predict")}
            className={`px-3 py-1.5 text-xs font-medium rounded-lg transition-all ${
              activeTab === "predict"
                ? "bg-blue-600 text-white shadow"
                : "text-slate-300 hover:bg-slate-800"
            }`}
          >
            🤖 AI Dự Đoán
          </button>
          <button
            onClick={() => setActiveTab("history")}
            className={`px-3 py-1.5 text-xs font-medium rounded-lg transition-all ${
              activeTab === "history"
                ? "bg-blue-600 text-white shadow"
                : "text-slate-300 hover:bg-slate-800"
            }`}
          >
            📜 Lịch Sử
          </button>
          <button
            onClick={() => setActiveTab("saved")}
            className={`px-3 py-1.5 text-xs font-medium rounded-lg transition-all ${
              activeTab === "saved"
                ? "bg-blue-600 text-white shadow"
                : "text-slate-300 hover:bg-slate-800"
            }`}
          >
            ⭐️ Đã Lưu
          </button>
        </div>

        {/* 4. Desktop Floating Side Panel */}
        <aside
          className={`absolute top-28 left-4 bottom-6 z-20 w-80 bg-slate-900/90 backdrop-blur-xl border border-slate-700/60 rounded-2xl shadow-2xl transition-all duration-300 hidden sm:flex flex-col ${
            isPanelOpen ? "translate-x-0 opacity-100" : "-translate-x-96 opacity-0 pointer-events-none"
          }`}
        >
          {/* Side Panel Header */}
          <div className="flex items-center justify-between px-4 py-3 border-b border-slate-700/50">
            <h2 className="text-sm font-bold text-slate-100 flex items-center gap-2">
              <span>
                {activeTab === "predict"
                  ? "🤖"
                  : activeTab === "history"
                  ? "📜"
                  : activeTab === "saved"
                  ? "⭐️"
                  : selectedLocation
                  ? "📍"
                  : "🛣️"}
              </span>
              <span>
                {activeTab === "predict"
                  ? "Dự Đoán AI Engine"
                  : activeTab === "history"
                  ? "Lịch Sử Playback"
                  : activeTab === "saved"
                  ? "Địa Điểm Đã Lưu"
                  : selectedLocation
                  ? selectedLocation.location_name
                  : "Danh Sách Tuyến Đường"}
              </span>
            </h2>
            <button
              onClick={() => setIsPanelOpen(false)}
              className="text-slate-400 hover:text-white text-xs px-2 py-1 rounded bg-slate-800"
            >
              Thu gọn ◄
            </button>
          </div>

          {/* Side Panel Content Switcher */}
          <div className="flex-1 p-4 overflow-y-auto flex flex-col">
            {activeTab === "predict" ? (
              <PredictionPanel
                onRunBatchPrediction={handleRunBatchPrediction}
                isLoading={isPredicting}
                modelPredictionResult={singlePredictionResult}
                liveSpeed={selectedLocation?.current_speed}
              />
            ) : activeTab === "history" ? (
              <HistoryPanel onTimeChange={handleHistoryTimeChange} />
            ) : activeTab === "saved" ? (
              <SavedLocationsPanel
                onSelectLocation={(rec) => {
                  setSelectedLocation(rec);
                  handleSelectLocationFromSearch(rec.latitude, rec.longitude, rec.location_name);
                }}
              />
            ) : errorMessage ? (
              <div className="p-4 bg-red-500/10 border border-red-500/30 rounded-2xl text-red-400 text-xs text-center font-bold">
                {errorMessage}
              </div>
            ) : selectedLocation ? (
              // Khi đã chọn tuyến đường → hiện chi tiết + nút Quay lại danh sách
              <div className="flex flex-col h-full">
                <button
                  onClick={() => setSelectedLocation(null)}
                  className="mb-3 flex items-center space-x-1.5 text-xs text-blue-400 hover:text-blue-300 transition"
                >
                  <span>◄</span>
                  <span>Danh sách tuyến đường</span>
                </button>
                <LocationDetails
                  location={selectedLocation}
                  onPredictClick={handleRunSinglePrediction}
                  onSaveClick={(loc) => alert(`Đã lưu ${loc.location_name} vào danh sách yêu thích!`)}
                />
              </div>
            ) : (
              // Mặc định: hiện danh sách tất cả tuyến đường kèm tốc độ realtime
              <RoadListPanel
                records={trafficRecords}
                selectedId={selectedLocation ?? undefined}
                onSelectRoad={(rec) => {
                  setSelectedLocation(rec);
                  if (mapRef.current) {
                    mapRef.current.flyTo({ center: [rec.longitude, rec.latitude], zoom: 15, speed: 1.3 });
                  }
                }}
              />
            )}
          </div>
        </aside>

        {/* Desktop Panel Re-open Button */}
        {!isPanelOpen && (
          <button
            onClick={() => setIsPanelOpen(true)}
            className="absolute top-28 left-4 z-20 hidden sm:flex items-center space-x-2 px-3 py-2 bg-slate-900/90 backdrop-blur border border-slate-700 rounded-xl shadow-lg text-xs font-medium text-slate-200 hover:bg-slate-800"
          >
            <span>▶</span> <span>Hiện Side Panel</span>
          </button>
        )}

        {/* 5. Mobile Bottom Sheet Container */}
        <div
          className={`absolute bottom-0 left-0 right-0 z-20 sm:hidden bg-slate-900/95 backdrop-blur-2xl border-t border-slate-700/80 rounded-t-3xl shadow-2xl transition-all duration-300 ${
            isMobileSheetExpanded ? "h-3/4" : "h-40"
          }`}
        >
          {/* Handle Drag Bar */}
          <div
            onClick={() => setIsMobileSheetExpanded(!isMobileSheetExpanded)}
            className="w-full py-2 flex flex-col items-center justify-center cursor-pointer"
          >
            <div className="w-12 h-1.5 bg-slate-600 rounded-full mb-1"></div>
            <span className="text-[10px] text-slate-400">
              {isMobileSheetExpanded ? "Kéo xuống để thu gọn 🔻" : "Kéo lên để xem chi tiết 🔺"}
            </span>
          </div>

          {/* Bottom Sheet Content */}
          <div className="px-4 pb-4 overflow-y-auto h-full">
            {activeTab === "predict" ? (
              <PredictionPanel
                onRunBatchPrediction={handleRunBatchPrediction}
                isLoading={isPredicting}
                modelPredictionResult={singlePredictionResult}
                liveSpeed={selectedLocation?.current_speed}
              />
            ) : activeTab === "history" ? (
              <HistoryPanel onTimeChange={handleHistoryTimeChange} />
            ) : activeTab === "saved" ? (
              <SavedLocationsPanel
                onSelectLocation={(rec) => {
                  setSelectedLocation(rec);
                  handleSelectLocationFromSearch(rec.latitude, rec.longitude, rec.location_name);
                }}
              />
            ) : (
              <LocationDetails
                location={selectedLocation}
                onPredictClick={handleRunSinglePrediction}
                onSaveClick={(loc) => alert(`Đã lưu ${loc.location_name} vào danh sách yêu thích!`)}
              />
            )}
          </div>
        </div>
      </main>
    </div>
  );
};
