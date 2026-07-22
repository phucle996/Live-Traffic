# Phase UI-0 — UI Wireframes Specification

Tài liệu thiết kế cấu trúc bố cục (Wireframes) dạng Markdown cho cả hai định dạng **Desktop (Side Panel)** và **Mobile (Bottom Sheet)** theo phong cách thiết kế **Map-First Tối Giản**.

---

## 1. Màn Hình Bản Đồ Chính (Main Live Map Screen)

### Desktop Wireframe (Top Search Bar + Floating Floating Side Panel)

```text
┌────────────────────────────────────────────────────────────────────────────┐
│ 🚗 TRAFFIC VIEW  │  [🔍 Tìm địa điểm, ngã tư...      ]   │ (🟢 Live) 👤 User ▼│
├──────────────────┴───────────────────────────────────────┴─────────────────┤
│ ┌──────────────────────┐                                                   │
│ │ 📍 Ngã tư Hàng Xanh  │                                                   │
│ │ Quận Bình Thạnh      │                                                   │
│ ├──────────────────────┤                     BẢN ĐỒ VECTOR                 │
│ │ Tốc độ hiện tại:     │                      MAPLIBRE GL                  │
│ │  14 km/h  (🔴 Ùn tắc)│                                                   │
│ │                      │           ● (Xanh: >35km/h)                       │
│ │ Tốc độ thông thường: │           ● (Vàng: 20-35km/h)                     │
│ │  32 km/h             │           ● (Đỏ: <20km/h)                         │
│ │                      │                                                   │
│ │ Độ tin cậy:  98%     │                                                   │
│ │ Cập nhật:    2m trước│                                              [ + ]│
│ ├──────────────────────┤                                              [ - ]│
│ │ [ 🤖 Xem dự đoán ]   │                                              [ 🎯]│
│ │ [ ⭐️ Lưu địa điểm ]  │                                                   │
│ └──────────────────────┘                                                   │
└────────────────────────────────────────────────────────────────────────────┘
```

---

### Mobile Wireframe (Compact Top Bar + Bottom Sheet)

```text
┌───────────────────────────┐
│ 🚗 TRAFFIC VIEW  (🔴 Live)│
├───────────────────────────┤
│                           │
│       MAPLIBRE GL         │
│          BẢN ĐỒ           │
│       ● xanh  ● đỏ        │
│                           │
│                     [ 🎯 ]│
├───────────────────────────┤
│ ═════════ (Kéo lên) ═════ │
│ 📍 Ngã tư Hàng Xanh       │
│ Vận tốc: 14 km/h (🔴 Ùn tắc)│
│ [ 🤖 Xem dự đoán ]        │
└───────────────────────────┘
```

---

## 2. Màn Hình Đăng Nhập (Login Screen Wireframe)

```text
┌──────────────────────────────────────────┐
│              TRAFFIC VIEW                │
│                                          │
│   Hệ Thống Phân Tích & Dự Đoán Giao Thông│
│               TP. Hồ Chí Minh            │
│                                          │
│  ┌────────────────────────────────────┐  │
│  │  🌐  Đăng nhập bằng Keycloak OIDC  │  │
│  └────────────────────────────────────┘  │
│  ┌────────────────────────────────────┐  │
│  │  🔑  Đăng nhập tài khoản Google    │  │
│  └────────────────────────────────────┘  │
│                                          │
│   Phiên bản Cloud-Native High Availability│
└──────────────────────────────────────────┘
```

---

## 3. Màn Hình Dự Đoán Mô Hình AI (Prediction Screen Wireframe)

```text
┌────────────────────────────────────────────────────────────────────────────┐
│ 🚗 TRAFFIC VIEW  │  [ Tab: 🔴 Live | 🤖 Dự Đoán | 📜 Lịch Sử ]             │
├──────────────────┬─────────────────────────────────────────────────────────┤
│ 🤖 CẤU HÌNH DỰ ĐOÁN│                                                         │
│ ─────────────────│                                                         │
│ Ngày dự đoán:    │                       BẢN ĐỒ PREDICTION                 │
│ [ 25/07/2026  📅]│                         LAYER                       │
│                  │                                                         │
│ Giờ dự đoán:     │            ◆ Dự đoán lúc 17:30 (◆ Hình thoi)            │
│ [ 17:30       ⏰]│            ● Live quan sát thực tế (● Hình tròn)        │
│                  │                                                         │
│ Khu vực:         │                                                         │
│ [ Tất cả Quận  ▼]│                                                         │
│ ─────────────────│                                                         │
│ MODEL INFO:      │                                                         │
│ Model: GBT-v2026 │                                                         │
│ Engine: Rust RAM │                                                         │
│                  │                                                         │
│ [ 🚀 Chạy Dự Đoán]│                                                         │
└──────────────────┴─────────────────────────────────────────────────────────┘
```

---

## 4. Màn Hình Lịch Sử & Playback (Historical Traffic Wireframe)

```text
┌────────────────────────────────────────────────────────────────────────────┐
│ 📜 LỊCH SỬ GIAO THÔNG  [ Chọn ngày: 21/07/2026 📅 ]                       │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│                          BẢN ĐỒ HISTORICAL PLAYBACK                        │
│                                                                            │
├────────────────────────────────────────────────────────────────────────────┤
│  [ ▶ Play ]  07:00 ───────────●─────────────────────── 23:00   (Đang chiếu 17:30)│
└────────────────────────────────────────────────────────────────────────────┘
```

---

## 5. Màn Hình Quản Trị Hệ Thống dành cho Admin (Admin Status Panel Wireframe)

```text
┌────────────────────────────────────────────────────────────────────────────┐
│ 👑 ADMIN DASHBOARD — HEALTH & PIPELINE STATUS                             │
├────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────┐  ┌─────────────────────────┐                  │
│  │ Go Live Collector       │  │ Rust Inference Engine   │                  │
│  │ Status: 🟢 HEALTHY      │  │ Status: 🟢 HEALTHY      │                  │
│  │ Latency: <1ms           │  │ Memory RAM: 7.2 KB      │                  │
│  └─────────────────────────┘  └─────────────────────────┘                  │
│  ┌─────────────────────────┐  ┌─────────────────────────┐                  │
│  │ Kafka Consumer Lag      │  │ Active Model Metadata   │                  │
│  │ Lag: 0 messages         │  │ ID: gbt-20260721-latest │                  │
│  └─────────────────────────┘  └─────────────────────────┘                  │
│                                                                            │
│  [ 🔄 Kích Hoạt Hot Reload Model ]    [ 📜 Xem Audit Log ]                  │
└────────────────────────────────────────────────────────────────────────────┘
```
