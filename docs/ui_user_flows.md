# Phase UI-0 — UI User Flows Specification

Tài liệu định nghĩa các luồng tương tác người dùng (User Flows), chuyển đổi trạng thái (State Transitions), và cơ chế xử lý lỗi/fallback cho giao diện Web Frontend Map-First.

---

## 1. Màn hình & Quyền Hạn (RBAC Matrix)

| Role | Chức năng cho phép |
| :--- | :--- |
| **Viewer** | - Đăng nhập / Đăng xuất qua Keycloak OIDC.<br/>- Xem bản đồ giao thông thời gian thực (Live Traffic Map).<br/>- Thực thi suy luận tốc độ giao thông (Model Prediction).<br/>- Kéo thanh lịch sử giao thông (Historical Traffic Playback).<br/>- Lưu & quản lý danh sách địa điểm yêu thích (Saved Places). |
| **Admin** | - Tất cả các quyền của **Viewer**.<br/>- Xem trạng thái Health & Pipeline Status của các Microservices.<br/>- Xem thông tin chi tiết Mô hình AI (Active Model, RMSE, MAE, R²).<br/>- Thực thi kích hoạt **Model Hot Reload** (`POST /v1/model/reload`) kèm Audit Log. |

---

## 2. Các Luồng Tương Tác Cốt Lõi (User Flows)

### Flow 1: Đăng Nhập & Phân Quyền (Authentication & Session Flow)
1. Người dùng mở trang web ➔ Hệ thống kiểm tra OIDC Session/Token.
2. Nếu chưa đăng nhập ➔ Chuyển hướng sang giao diện Keycloak / Provider Login (`/login`).
3. Đăng nhập thành công ➔ Keycloak trả về ID Token & Access Token (chứa Roles: `viewer` hoặc `admin`).
4. Session được lưu trong bộ nhớ an toàn (Secure HTTP-only Cookies / OIDC Session).
5. Khi Access Token hết hạn ➔ Tự động làm mới bằng Refresh Token qua OIDC Client background loop.
6. Nếu Refresh Token hết hạn ➔ Chuyển hướng người dùng về màn hình `/login` kèm thông báo `Phiên đăng nhập đã hết hạn`.

---

### Flow 2: Trực Quan Hóa Giao Thông Thời Gian Thực (Live Traffic Flow)
1. Người dùng vào trang Map chính (`/map`).
2. Component `TrafficMap` tải bản đồ nền vector MapLibre GL JS TP.HCM (`[10.7769, 106.7009]`).
3. Next.js Frontend gửi HTTP Request `GET /v1/traffic/live` tới **Go Live Traffic API** kèm `Authorization: Bearer <TOKEN>`.
4. Render các điểm đường (GeoJSON Location Markers) theo màu sắc HSL:
   - 🟢 **Xanh lá**: Tốc độ mượt mà (`>= 35 km/h` hoặc `Ratio >= 0.75`)
   - 🟡 **Vàng**: Đông xe (`20 km/h <= Speed < 35 km/h`)
   - 🔴 **Đỏ**: Ùn tắc nghiêm trọng (`< 20 km/h` hoặc `Ratio < 0.35`)
5. **Trạng thái Dữ liệu**:
   - `live`: Độ tươi dữ liệu `< 180s`.
   - `stale`: Độ tươi dữ liệu từ `180s` đến `1800s`.
   - `offline`: Không có dữ liệu hoặc Go Service ngắt kết nối.
6. Khi chọn vị trí ➔ Mở Side Panel (Desktop) hoặc Bottom Sheet (Mobile) hiển thị vận tốc hiện tại, vận tốc tự do, và nút `[ Xem dự đoán ]`.

---

### Flow 3: Suy Luận Mô Hình AI (Prediction Flow)
1. Người dùng mở tab `Dự đoán` hoặc chọn địa điểm trên Map ➔ Chọn Ngày & Giờ dự đoán (ví dụ: `2026-07-25 17:30:00`).
2. Frontend gửi HTTP Request `POST /v1/predictions` tới **Rust Prediction Engine** kèm Payload chứa vị trí, giờ dự đoán và Bearer Token.
3. Trong lúc chờ ➔ Hiển thị Skeleton Loading trên Side Panel / Bottom Sheet.
4. Nhận phản hồi thành công ➔ Render lớp dữ liệu **Model Prediction Layer** trên bản đồ với biểu tượng hình thoi `◆` phân biệt với hình tròn `●` của Live Observation.
5. Hiển thị thông số `Model Version` (ví dụ: `traffic-gbt-20260721-001`) và chỉ số `Congestion Level`.

---

### Flow 4: Lịch Sử & Playback (Historical Traffic Flow)
1. Người dùng mở tab `Lịch sử`.
2. Chọn Ngày và kéo thanh Timeline Slider (`07:00 ────●──────── 23:00`).
3. Frontend truy vấn dữ liệu lịch sử từ Go API và cập nhật các Marker trên MapLibre GL JS.
4. Bấm nút `▶ Playback` ➔ Tự động di chuyển mốc thời gian tăng dần và cập nhật trạng thái ô màu giao thông.

---

### Flow 5: Quản Lý Hệ Thống dành cho Admin (Admin Status Flow)
1. Admin truy cập trang `/admin`.
2. Frontend kiểm tra Scope/Role `admin`. Nếu là Viewer ➔ Hiển thị màn hình `403 Forbidden`.
3. Nếu là Admin ➔ Hiển thị bảng Dashboard giám sát Health các dịch vụ (Go Collector, Kafka Lag, Rust Engine, Active Model).
4. Bấm nút `[ Hot Reload Model ]` ➔ Mở Confirmation Dialog ➔ Gửi `POST /v1/model/reload` và ghi nhận Audit Log.

---

## 3. Trạng Thái Ứng Dụng (Loading, Error & Stale State Specs)

| Trạng thái | Điều kiện kích hoạt | Phản hồi UI tương ứng |
| :--- | :--- | :--- |
| **Loading** | Đang gọi Go/Rust API | Hiển thị Skeleton Loader ở Panel, Spinner nhẹ ở góc bản đồ. |
| **Empty** | Không có địa điểm được chọn / Tìm kiếm không thấy | Hiển thị ô trống thông báo "Không tìm thấy tuyến đường tương ứng". |
| **Stale Data** | `data_age_seconds > 180` | Hiển thị Banner màu vàng: `⚠️ Dữ liệu giao thông chưa cập nhật (3 phút trước)`. |
| **Offline / Error** | API trả về 50x / Connection Refused | Hiển thị Banner đỏ: `🚫 Không thể kết nối API Server. Đang thử kết nối lại...`. |
| **Auth Expiry** | Token trả về HTTP 401 | Tự động gọi Refresh Token OIDC; nếu thất bại chuyển về `/login`. |
