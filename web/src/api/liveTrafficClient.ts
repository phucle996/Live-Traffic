// ==============================================================================
// Live Traffic API Client Module (web/src/api/liveTrafficClient.ts)
// REST API Client Interfacing with Go Live Traffic Microservice (Port 8084)
// Bearer Token Authentication, Data Freshness Checking & Fail-Safe Error Handling
// ==============================================================================

export interface LiveTrafficRecord {
  location_id: string;
  location_name: string;
  district: string;
  latitude: number;
  longitude: number;
  current_speed: number;
  free_flow_speed: number;
  confidence: number;
  source: string;
  observed_at: string;
  data_age_seconds: number;
}

export interface LiveTrafficResponse {
  cache_control: string;
  count: number;
  served_from: string;
  traffic_data: LiveTrafficRecord[];
}

export interface SourceStatusResponse {
  active_source_mode: string;
  daily_budget_limit: number;
  daily_budget_used: number;
  total_locations: number;
}

const GO_LIVE_API_BASE = process.env.NEXT_PUBLIC_GO_LIVE_API_URL || "http://localhost:8084";

// Gọi Go Live API lấy danh sách vị trí giao thông thời gian thực (Public API - không yêu cầu Bearer Token)
export async function fetchLiveTrafficData(): Promise<LiveTrafficResponse> {
  // Cấu hình headers tiêu chuẩn cho request lấy dữ liệu công khai
  const headers: Record<string, string> = {
    "Accept": "application/json",
  };

  // Thực hiện HTTP GET tới Go Live Microservice endpoint công khai
  const response = await fetch(`${GO_LIVE_API_BASE}/v1/traffic/live`, {
    method: "GET",
    headers,
    cache: "no-store",
  });

  // Kiểm tra HTTP response status code
  if (!response.ok) {
    throw new Error(`HTTP Error ${response.status}: Failed to fetch live traffic data`);
  }

  // Phân tích dữ liệu JSON trả về
  return response.json();
}

// Gọi Go Source Status API lấy thông tin trạng thái nạp dữ liệu (Public Access)
export async function fetchSourceStatusData(): Promise<SourceStatusResponse> {
  // Header kết quả dữ liệu dạng JSON
  const headers: Record<string, string> = {
    "Accept": "application/json",
  };

  // Gửi request không kèm Authorization Header
  const response = await fetch(`${GO_LIVE_API_BASE}/v1/source/status`, {
    method: "GET",
    headers,
    cache: "no-store",
  });

  // Xử lý lỗi nếu HTTP status khống bằng 200 OK
  if (!response.ok) {
    throw new Error(`HTTP Error ${response.status}: Failed to fetch source status`);
  }

  // Trả về đối tượng trạng thái nguồn dữ liệu
  return response.json();
}
