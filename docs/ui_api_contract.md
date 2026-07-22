# Phase UI-0 — UI API Contract Specification

Tài liệu kiểm kê chi tiết các REST API Endpoints hiện có, cấu trúc Request/Response Payload, các HTTP Status Codes, và danh sách các Endpoints còn thiếu cần bổ sung để phục vụ cho **Next.js Map-First Frontend**.

---

## 1. Danh Sách Endpoint Hiện Có (Active Backend Microservices)

### A. Go Live Traffic API (`http://localhost:8084` / `/v1/traffic/*`)

#### 1. `GET /v1/traffic/live`
- **Mô tả**: Lấy danh sách trạng thái vận tốc giao thông thời gian thực cho toàn bộ vị trí.
- **Header bắt buộc**: `Authorization: Bearer <TOKEN>` (Scope: `traffic:read`)
- **Response `HTTP 200 OK`**:
  ```json
  {
    "cache_control": "15_seconds",
    "count": 8,
    "served_from": "latest_state_store",
    "traffic_data": [
      {
        "location_id": "loc-01",
        "location_name": "Nam Kỳ Khởi Nghĩa",
        "district": "Quận 3",
        "latitude": 10.7781,
        "longitude": 106.6952,
        "current_speed": 22.5,
        "free_flow_speed": 45.0,
        "confidence": 0.95,
        "source": "tomtom_live",
        "observed_at": "2026-07-21T15:31:40Z",
        "data_age_seconds": 12
      }
    ]
  }
  ```

#### 2. `GET /v1/source/status`
- **Mô tả**: Kiểm tra trạng thái nguồn nạp dữ liệu giao thông (`tomtom_live` vs `offline_seed`).
- **Header bắt buộc**: `Authorization: Bearer <TOKEN>` (Scope: `traffic:read`)
- **Response `HTTP 200 OK`**:
  ```json
  {
    "active_source_mode": "tomtom_live",
    "daily_budget_limit": 2500,
    "daily_budget_used": 0,
    "total_locations": 37
  }
  ```

#### 3. `GET /health/live` & `GET /health/ready`
- **Mô tả**: Liveness và Readiness probes dành cho Kubernetes & Gateway.
- **Response `HTTP 200 OK`**: `{"status": "UP"}` / `{"status": "READY"}`

---

### B. Rust Traffic Inference Engine (`http://localhost:8090` / `/v1/predictions/*`)

#### 1. `POST /v1/predictions`
- **Mô tả**: Thực thi suy luận tốc độ giao thông đơn lẻ qua mô hình AI in-memory.
- **Header bắt buộc**: `Authorization: Bearer <TOKEN>` (Scope: `prediction:execute`)
- **Request Payload**:
  ```json
  {
    "latitude": 10.7727,
    "longitude": 106.6980,
    "free_flow_speed": 45.0,
    "confidence": 0.95,
    "street_name": "Chợ Bến Thành"
  }
  ```
- **Response `HTTP 200 OK`**:
  ```json
  {
    "street_name": "Chợ Bến Thành",
    "predicted_speed_kmh": 14.5,
    "congestion_level": "HEAVY_CONGESTION",
    "model_version": "traffic-gbt-20260721-001",
    "data_source": "Rust native GBT in-memory engine",
    "inference_timestamp": "2026-07-21T16:30:00Z"
  }
  ```

#### 2. `POST /v1/predictions/batch`
- **Mô tả**: Thực thi suy luận tốc độ hàng loạt cho danh sách các tuyến đường.
- **Header bắt buộc**: `Authorization: Bearer <TOKEN>` (Scope: `prediction:execute`)

#### 3. `GET /v1/model`
- **Mô tả**: Lấy thông tin Metadata của mô hình AI hiện tại (RMSE, MAE, R², Feature Contract).
- **Header bắt buộc**: `Authorization: Bearer <TOKEN>` (Scope: `model:read`)

#### 4. `POST /v1/model/reload`
- **Mô tả**: Kích hoạt Hot Reload nạp mô hình mới bất biến vào RAM (Zero-Downtime Swap).
- **Header bắt buộc**: `Authorization: Bearer <TOKEN>` (Scope: `model:reload`, Role: `admin`)

---

## 2. Các Endpoints Còn Thiếu Cần Bổ Sung (Giai đoạn Triển khai Sau)

Để hỗ trợ đầy đủ các màn hình trong bản spec UI, cần bổ sung các API Endpoints sau ở Backend:

| Endpoint | Method | Service | Mục đích sử dụng trên Frontend Next.js |
| :--- | :---: | :---: | :--- |
| `/v1/history/traffic` | `GET` | Go API | Lấy dữ liệu tốc độ lịch sử theo khoảng thời gian cho thanh Playback Timeline Slider (`07:00 - 23:00`). |
| `/v1/user/saved-places` | `GET/POST/DELETE` | Go API | Quản lý danh sách địa điểm yêu thích của người dùng (lưu trữ PostgreSQL). |
| `/v1/admin/pipeline-status` | `GET` | Go API | Giám sát trạng thái HDFS, Kafka Consumer Lag và Spark Training Pipeline cho Admin. |
| `/auth/login` & `/auth/refresh` | `POST` | Keycloak | Quản lý OIDC authentication token exchange và refresh session. |
