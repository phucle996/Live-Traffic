// ==============================================================================
// Prediction API Client Module (web/src/api/predictionClient.ts)
// REST API Client Interfacing with High-Speed Rust Inference Engine (Port 8090)
// Single & Batch Location AI Model Speed Predictions & Model Metadata Inspection
// ==============================================================================

export interface PredictionRequest {
  latitude: number;
  longitude: number;
  free_flow_speed: number;
  confidence: number;
  street_name: string;
}

export interface PredictionResponse {
  street_name: string;
  predicted_speed_kmh: number;
  congestion_level: string;
  model_version: string;
  data_source: string;
  inference_timestamp?: string;
}

export interface BatchPredictionItem {
  latitude: number;
  longitude: number;
  free_flow_speed: number;
  confidence: number;
  street_name: string;
}

export interface BatchPredictionRequest {
  locations: BatchPredictionItem[];
  prediction_time?: string;
}

export interface BatchPredictionResponse {
  predictions: PredictionResponse[];
  total_count: number;
  model_version: string;
}

const RUST_PREDICT_API_BASE = process.env.NEXT_PUBLIC_RUST_PREDICT_API_URL || "http://localhost:8090";

// Gọi Rust Prediction API (/v1/predictions) suy luận tốc độ đơn vị vị trí (Public REST Endpoint)
export async function fetchSinglePrediction(
  payload: PredictionRequest
): Promise<PredictionResponse> {
  // Thiết lập Headers chuẩn JSON cho request gửi sang Rust Engine
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    "Accept": "application/json",
  };

  // Gửi request POST suy luận AI công khai không yêu cầu token xác thực
  const response = await fetch(`${RUST_PREDICT_API_BASE}/v1/predictions`, {
    method: "POST",
    headers,
    body: JSON.stringify(payload),
  });

  // Kiểm tra mã phản hồi HTTP từ server Rust
  if (!response.ok) {
    throw new Error(`HTTP Error ${response.status}: Failed to execute Rust AI prediction`);
  }

  // Trả về kết quả suy luận dự đoán tốc độ
  return response.json();
}

// Gọi Rust Prediction API (/v1/predictions/batch) suy luận tốc độ hàng loạt (Public REST Endpoint)
export async function fetchBatchPredictions(
  payload: BatchPredictionRequest
): Promise<BatchPredictionResponse> {
  // Headers yêu cầu dữ liệu định dạng JSON
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    "Accept": "application/json",
  };

  // Gửi request Batch Inference POST sang Rust Engine
  const response = await fetch(`${RUST_PREDICT_API_BASE}/v1/predictions/batch`, {
    method: "POST",
    headers,
    body: JSON.stringify(payload),
  });

  // Đảm bảo không gặp lỗi suy luận trên backend
  if (!response.ok) {
    throw new Error(`HTTP Error ${response.status}: Failed to execute Rust batch prediction`);
  }

  // Trả về kết quả danh sách dự đoán tốc độ hàng loạt
  return response.json();
}
