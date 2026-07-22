Ý tưởng này rất hợp với hệ thống của bạn. Giao diện nên theo kiểu **map-first**: bản đồ chiếm gần toàn màn hình, các chức năng nằm trong panel nổi và bottom sheet, thay vì làm dashboard nhiều biểu đồ như Streamlit.

Với yêu cầu “giống trải nghiệm Google Maps, có đăng nhập, không màu mè”, tôi đề xuất:

```text
Frontend:       Next.js + TypeScript
Map engine:     MapLibre GL JS
Authentication: Keycloak/OIDC
Live API:       Go
Prediction API: Rust
Training/ETL:   Python/PySpark
```

MapLibre GL JS phù hợp với bản đồ vector tương tác trên trình duyệt và có thư viện tích hợp React chính thức/cộng đồng duy trì. Next.js có sẵn mô hình tổ chức cho authentication, authorization và session. Keycloak có thể đóng vai trò Identity Provider theo OpenID Connect để phát token cho frontend và các service kiểm tra. ([MapLibre][1])

# Kiến trúc UI đề xuất

```text
┌───────────────────────────────────────────────────────┐
│                    Web Browser                        │
│                                                       │
│  Next.js + TypeScript + MapLibre                      │
│  ├── Login                                            │
│  ├── Live traffic map                                 │
│  ├── Prediction                                       │
│  ├── Historical traffic                              │
│  └── User preferences                                 │
└──────────────────────┬────────────────────────────────┘
                       │ HTTPS
                       ▼
┌───────────────────────────────────────────────────────┐
│                  Ingress / Nginx                      │
│                                                       │
│ /v1/traffic/*       → Go Live API                     │
│ /v1/predictions/*   → Rust Prediction API             │
│ /auth/*             → Keycloak                        │
│ /*                  → Next.js frontend                │
└───────────────────────────────────────────────────────┘
```

Tree hiện tại có `src/dashboard/app.py`, `dashboard_service.py` và `map_builder.py`, nghĩa là dashboard vẫn đang nằm trong Python. Ta có thể giữ Streamlit làm bản demo cũ, đồng thời xây frontend mới rồi chuyển dần traffic sang đó. 

# Bố cục giao diện

## Màn hình bản đồ chính

```text
┌────────────────────────────────────────────────────────────┐
│ Logo   [ Tìm địa điểm...                    ]   Avatar  ▼  │
├───────────────┬────────────────────────────────────────────┤
│               │                                            │
│  LIVE         │                                            │
│  DỰ ĐOÁN      │                 BẢN ĐỒ                     │
│  LỊCH SỬ      │                                            │
│  ĐÃ LƯU       │       ● xanh   lưu thông tốt               │
│               │       ● vàng   đông                        │
│               │       ● đỏ     ùn tắc                      │
│               │                                            │
│               │                                [+]         │
│               │                                [-]         │
│               │                                [◎]         │
└───────────────┴────────────────────────────────────────────┘
```

Không cần sidebar luôn mở. Có thể thu gọn thành các nút:

```text
[Live] [Dự đoán] [Lịch sử] [Lớp bản đồ]
```

Khi người dùng chọn một địa điểm, mở panel:

```text
Ngã tư Hàng Xanh

Tốc độ hiện tại:        14 km/h
Tốc độ thông thường:    32 km/h
Mức độ:                 Ùn tắc
Độ tin cậy:             98%
Cập nhật:               2 phút trước

[ Xem dự đoán ]    [ Lưu địa điểm ]
```

Trên mobile, panel này nên là **bottom sheet** kéo lên, giống ứng dụng bản đồ.

# Những màn hình nên có

## 1. Đăng nhập

Gọn, không cần tự viết form quản lý mật khẩu phức tạp:

```text
┌──────────────────────────┐
│      TRAFFIC VIEW        │
│                          │
│  Theo dõi và dự đoán     │
│  tình trạng giao thông   │
│                          │
│  [ Đăng nhập với Google ]│
│  [ Đăng nhập tài khoản ] │
└──────────────────────────┘
```

Keycloak có thể hỗ trợ tài khoản riêng và liên kết các nhà cung cấp đăng nhập OIDC. ([Keycloak][2])

Role ban đầu chỉ cần:

```text
viewer
admin
```

Quyền:

| Chức năng               | Viewer | Admin |
| ----------------------- | :----: | :---: |
| Xem live traffic        |    ✓   |   ✓   |
| Chạy prediction         |    ✓   |   ✓   |
| Lưu địa điểm            |    ✓   |   ✓   |
| Xem model version       |        |   ✓   |
| Reload model            |        |   ✓   |
| Xem trạng thái pipeline |        |   ✓   |

Frontend chỉ ẩn/hiện nút. Go và Rust vẫn phải kiểm tra quyền thật ở backend.

## 2. Live Traffic

Hiển thị:

* Điểm hoặc đoạn đường theo màu giao thông.
* Nguồn dữ liệu.
* Thời gian cập nhật.
* Trạng thái `live`, `stale` hoặc `offline`.
* Bộ lọc quận.
* Bộ lọc mức độ ùn tắc.
* Nút định vị hiện tại.
* Danh sách địa điểm đang ùn tắc nặng.

Không nên gọi TomTom mỗi lần người dùng kéo bản đồ. UI chỉ gọi Go Live API, dữ liệu mới nhất được đọc từ Redis.

## 3. Prediction

Người dùng chọn:

```text
Ngày:        25/07/2026
Thời gian:   17:30
Khu vực:     Tất cả / Quận 1 / Quận Bình Thạnh
```

Sau đó frontend gọi:

```http
POST /v1/predictions
```

Kết quả hiển thị trên map:

```text
MODEL PREDICTION

Dự đoán lúc:       17:30, 25/07/2026
Model version:     traffic-gbt-20260721-001
Nguồn:             Rust inference
```

Phải có sự phân biệt trực quan:

```text
● Live observation
◆ Model prediction
```

Tránh làm người dùng nhầm dữ liệu dự đoán là giao thông thực tế.

## 4. Historical Traffic

Cho phép kéo thanh thời gian:

```text
07:00 ─────●──────────── 23:00
```

Các chức năng:

* Chọn ngày.
* Chọn giờ.
* Xem tốc độ theo thời gian.
* So sánh ngày thường/cuối tuần.
* Xem các điểm thường xuyên ùn tắc.
* Playback từng mốc thời gian trên bản đồ.

## 5. Saved Places

Người dùng có thể lưu:

```text
Nhà
Công ty
Ngã tư Hàng Xanh
Chợ Bến Thành
```

Hiển thị nhanh:

```text
Hàng Xanh
Hiện tại: 16 km/h — Đông
Dự đoán 18:00: 12 km/h — Ùn tắc
```

Đây là tính năng nhỏ nhưng tạo cảm giác sản phẩm thật hơn rất nhiều.

## 6. Admin

Không đưa vào giao diện người dùng thông thường.

Admin có thể xem:

```text
TomTom collector       Healthy
Kafka consumer lag     12
Latest live data       45 seconds ago
Rust inference         Healthy
Active model           traffic-gbt-20260721-001
Model RMSE             ...
Last training          ...
```

Các thao tác nhạy cảm như reload model cần xác nhận lại và ghi audit log.

# Phong cách thiết kế

Không cần nhiều màu. Chỉ dùng màu có ý nghĩa:

```text
Nền UI:              trắng / xám rất nhạt
Text:                xám đậm
Primary action:      xanh dương đậm
Lưu thông tốt:       xanh lá
Đông:                vàng/cam
Ùn tắc:              đỏ
Không có dữ liệu:    xám
```

Các nguyên tắc:

* Map luôn là nội dung chính.
* Panel có nền sáng, bo góc nhẹ.
* Không dùng gradient.
* Ít shadow.
* Icon đơn giản.
* Không hiển thị quá nhiều biểu đồ cùng lúc.
* Thời gian cập nhật luôn nhìn thấy.
* Desktop dùng side panel; mobile dùng bottom sheet.
* Dark mode có thể làm sau.

# Cấu trúc frontend

```text
web/
├── package.json
├── next.config.ts
├── tsconfig.json
├── public/
│   └── icons/
├── src/
│   ├── app/
│   │   ├── login/
│   │   │   └── page.tsx
│   │   ├── map/
│   │   │   └── page.tsx
│   │   ├── history/
│   │   │   └── page.tsx
│   │   ├── saved/
│   │   │   └── page.tsx
│   │   ├── admin/
│   │   │   └── page.tsx
│   │   ├── layout.tsx
│   │   └── page.tsx
│   ├── components/
│   │   ├── map/
│   │   │   ├── TrafficMap.tsx
│   │   │   ├── TrafficLayer.tsx
│   │   │   ├── PredictionLayer.tsx
│   │   │   ├── LocationMarker.tsx
│   │   │   ├── MapControls.tsx
│   │   │   └── TrafficLegend.tsx
│   │   ├── panels/
│   │   │   ├── LocationDetails.tsx
│   │   │   ├── PredictionPanel.tsx
│   │   │   ├── HistoryPanel.tsx
│   │   │   └── MobileBottomSheet.tsx
│   │   ├── auth/
│   │   │   ├── LoginButton.tsx
│   │   │   ├── UserMenu.tsx
│   │   │   └── ProtectedRoute.tsx
│   │   └── common/
│   ├── api/
│   │   ├── liveTrafficClient.ts
│   │   ├── predictionClient.ts
│   │   └── locationsClient.ts
│   ├── auth/
│   │   ├── config.ts
│   │   └── permissions.ts
│   ├── hooks/
│   ├── stores/
│   ├── types/
│   └── styles/
└── tests/
```

# Các phase giao cho Gemini

## Phase UI-0 — UX và API audit

Gemini phải đọc API hiện có trước khi làm giao diện.

```text
Tasks:

1. Kiểm kê endpoint hiện tại của:
   - Go Live Traffic API;
   - Rust Prediction API;
   - Python API cũ;
   - authentication service.

2. Xác định dữ liệu cần cho:
   - map marker;
   - live layer;
   - prediction layer;
   - location details;
   - user profile.

3. Viết:
   - docs/ui_user_flows.md;
   - docs/ui_api_contract.md;
   - docs/ui_wireframes.md.

4. Chưa viết giao diện trong phase này.
```

Acceptance criteria:

* Có user flow đăng nhập.
* Có flow xem live.
* Có flow prediction.
* Có flow token hết hạn.
* Có trạng thái loading, empty, stale và error.

## Phase UI-1 — Frontend foundation

```text
Tasks:

1. Tạo project Next.js TypeScript trong web/.
2. Thiết lập lint, formatter và test.
3. Tạo application shell.
4. Tạo responsive layout.
5. Tạo design tokens:
   - spacing;
   - typography;
   - border radius;
   - semantic colors.
6. Không kết nối map hoặc API thật trong phase này.
```

## Phase UI-2 — Authentication

```text
Tasks:

1. Kết nối Keycloak qua OpenID Connect.
2. Tạo login/logout.
3. Tạo protected routes.
4. Tạo user menu.
5. Xử lý token hết hạn.
6. Định nghĩa viewer/admin.
7. Không lưu access token lâu dài trong localStorage.
8. Backend vẫn phải enforce authorization.
```

Next.js có tài liệu riêng về authentication, session và authorization patterns; phần frontend không nên được coi là lớp bảo vệ duy nhất. ([Next.js][3])

## Phase UI-3 — Map shell

```text
Tasks:

1. Tích hợp MapLibre GL JS.
2. Hiển thị bản đồ TP.HCM.
3. Thêm zoom, geolocation và fullscreen.
4. Thêm location search UI.
5. Thêm traffic legend.
6. Thêm desktop side panel.
7. Thêm mobile bottom sheet.
8. Không gọi TomTom trực tiếp từ browser.
```

## Phase UI-4 — Live traffic

```text
Tasks:

1. Gọi Go Live API.
2. Vẽ marker/layer theo traffic status.
3. Hiển thị data freshness.
4. Xử lý live, stale và offline.
5. Click location mở detail panel.
6. Tự refresh theo interval hợp lý.
7. Không refresh khi tab không active nếu không cần.
8. Không gọi API lại chỉ vì người dùng pan map nhẹ.
```

## Phase UI-5 — Prediction

```text
Tasks:

1. Tạo date/time selector.
2. Gọi Rust Prediction API.
3. Hiển thị prediction layer.
4. Cho phép so sánh Live và Prediction.
5. Hiển thị model version.
6. Hiển thị inference timestamp.
7. Không duplicate feature engineering ở frontend.
8. Không gọi prediction trên mỗi lần người dùng gõ.
```

## Phase UI-6 — History và saved locations

```text
Tasks:

1. Tạo history time slider.
2. Thêm playback.
3. Cho phép lưu địa điểm.
4. Tạo danh sách địa điểm yêu thích.
5. Lưu user preferences vào PostgreSQL.
6. Không lưu dữ liệu người dùng quan trọng chỉ ở browser.
```

## Phase UI-7 — Admin

```text
Tasks:

1. Chỉ cho role admin truy cập.
2. Hiển thị health các service.
3. Hiển thị active model.
4. Hiển thị data freshness.
5. Hiển thị pipeline status.
6. Mọi action thay đổi hệ thống phải có confirmation.
7. Ghi audit log.
```

## Phase UI-8 — Performance và production

```text
Tasks:

1. Lazy load map.
2. Không rerender toàn bộ map khi panel thay đổi.
3. Dùng GeoJSON source update thay vì tạo lại map.
4. Cluster marker nếu số điểm tăng.
5. Code splitting.
6. Error boundary.
7. Accessibility keyboard.
8. Responsive test.
9. E2E test login/live/prediction.
10. Build container production.
11. CSP và security headers.
12. Không để API key bản đồ hoặc secret nhạy cảm trong bundle.
```

# Prompt mở đầu cho Gemini

```text
Project hiện có Python/PySpark training pipeline, Go Live Traffic API,
Rust Prediction API và dashboard Streamlit cũ.

Hãy xây frontend web mới theo kiểu map-first, trải nghiệm gần với
Google Maps nhưng thiết kế tối giản.

Stack bắt buộc:

- Next.js;
- React;
- TypeScript;
- MapLibre GL JS;
- OpenID Connect với Keycloak;
- Go Live Traffic API;
- Rust Prediction API.

Không dùng Streamlit cho frontend mới.
Không gọi TomTom trực tiếp từ browser.
Không load model hoặc thực hiện feature engineering trong frontend.
Không lưu secret trong client bundle.

Chỉ thực hiện Phase UI-0:
- audit API;
- định nghĩa user flow;
- định nghĩa API contract;
- tạo wireframe bằng Markdown;
- chưa tạo project Next.js;
- chưa viết component.

Các màn hình bắt buộc:
1. Login.
2. Live traffic map.
3. Prediction.
4. Historical traffic.
5. Saved locations.
6. User profile.
7. Admin service status.

Sau phase, trả về:
- tài liệu được tạo;
- endpoint còn thiếu;
- wireframe desktop/mobile;
- trạng thái loading/error/stale;
- acceptance criteria đạt/chưa đạt.
```

Với project này, tôi sẽ không dùng Go để viết giao diện HTML thủ công. **Next.js/TypeScript xử lý trải nghiệm bản đồ; Go và Rust tập trung vào backend hiệu năng cao.** Đây là ranh giới hợp lý giữa UI dễ phát triển và hệ thống phía sau mạnh.

[1]: https://maplibre.org/maplibre-gl-js/docs?utm_source=chatgpt.com "MapLibre GL JS"
[2]: https://www.keycloak.org/securing-apps/oidc-layers?utm_source=chatgpt.com "Securing applications and services with OpenID Connect - Keycloak"
[3]: https://nextjs.org/docs/app/guides/authentication?utm_source=chatgpt.com "Guides: Authentication | Next.js"
