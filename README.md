# 🚗 Vietnam Live Traffic & Cloud-Native AI Forecast System (Lab 5)

Hệ thống thu thập, xử lý ETL phân tán Spark, mô hình hóa AI siêu tốc bằng **Rust GBT Engine** và giám sát lưu lượng giao thông thời gian thực trên bản đồ vector 63 tỉnh thành Việt Nam.

---

## 🏛️ Kiến Trúc Hệ Thống (Cloud-Native & High Availability Architecture)

```text
                                  ┌──────────────────────────┐
                                  │   NGINX Ingress Gateway  │ (Port 80)
                                  └────────────┬─────────────┘
                                               │
             ┌─────────────────────────────────┼────────────────────────────────┐
             │                                 │                                │
             ▼                                 ▼                                ▼
 ┌──────────────────────┐          ┌──────────────────────┐          ┌──────────────────────┐
 │   Web SPA Dashboard  │          │     Go Live API      │          │  Rust AI Inference   │
 │   (Go Embedded SPA)  │          │   (Go REST Engine)   │          │  (Axum + GBT Engine) │
 │     Port 8501        │          │     Port 8084        │          │     Port 8080        │
 └──────────────────────┘          └───────────┬──────────┘          └──────────────────────┘
                                               │
                                               ▼
                                   ┌──────────────────────┐
                                   │  Go Collector Pool   │ (Port 8083)
                                   └───────────┬──────────┘
                                               │
                          ┌────────────────────┴────────────────────┐
                          ▼                                         ▼
              ┌──────────────────────┐                  ┌──────────────────────┐
              │   Apache Kafka Queue │                  │   PostgreSQL / PostGIS   │
              └───────────┬──────────┘                  └──────────────────────┘
                          │
                          ▼
              ┌──────────────────────┐                  ┌──────────────────────┐
              │  Spark ETL Cluster   │ ───────────────► │   HDFS Data Lake     │
              └──────────────────────┘                  └──────────────────────┘
```

---

## ⚡ Các Dịch Vụ Core System

| Service Name | Technology | Port Host / Internal | Chức năng chính |
|---|---|---|---|
| **`nginx-gateway`** | NGINX | `80:80` | Ingress Gateway proxy điều hướng động tới các microservice |
| **`web-dashboard`** | Go + React Vector SPA | `8501:8501` | Bản đồ tương tác Chấm Tròn Leaflet chỉ báo giao thông thời gian thực |
| **`go-live-api`** | Go (Net/HTTP) | `8084:8084` | REST API cung cấp danh mục 200+ tuyến đường chuẩn GPS 63 tỉnh thành |
| **`rust-inference-api`**| Rust (Axum + Rayon) | `8080:8080` | Engine suy luận AI chuỗi thời gian siêu tốc (**<1ms**) Auto-Regressive Fusion |
| **`go-traffic-collector`**| Go Worker Pool | `8083:8083` | Daemon thu thập dữ liệu giao thông liên tục không nghẽn cổ chai |
| **`postgres-postgis`** | PostgreSQL 15 + PostGIS | `5432:5432` | Cơ sở dữ liệu không gian lưu trữ bản ghi giao thông |
| **`kafka` / `zookeeper`** | Apache Kafka | `9092:9092` | Hàng chờ sự kiện phân tán streaming dữ liệu giao thông |
| **`spark-master` / `worker`**| Apache Spark 3.5.0 | `7077`, `8081` | Cụm máy chủ xử lý ETL phân tán & trích xuất đặc trưng AI |
| **`namenode` / `datanode`**| Hadoop HDFS | `9090:9000`, `9870` | Data Lake lưu trữ dữ liệu thô (Raw) & dữ liệu đã làm sạch (Processed) |

---

## 🤖 Mô Hình Dự Báo AI Chuỗi Thời Gian (Rust Auto-Regressive Fusion)

Hệ thống áp dụng mô hình suy luận lai **Auto-Regressive Feature Fusion** trên Rust Engine:
1. **Anchor Point:** Sử dụng vận tốc thực tế hiện tại ($V_{\text{curr}}$) làm điểm tựa ban đầu.
2. **Native Decision Tree Traversal:** Duyệt qua 100 cây GBT trong `model.json` để tính toán xu hướng dự báo biến thiên $V_{\text{tree}}$.
3. **Multi-Horizon Forecast:**
   - **Sau 15 phút:** $60\% \times V_{\text{curr}} + 40\% \times V_{\text{tree}}^{+15m}$
   - **Sau 30 phút:** $30\% \times V_{\text{curr}} + 70\% \times V_{\text{tree}}^{+30m}$
   - **Sau 60 phút:** $10\% \times V_{\text{curr}} + 90\% \times V_{\text{tree}}^{+60m}$

---

## 🗺️ Danh Mục 200+ Tuyến Đường Tọa Độ Thực Tế 63 Tỉnh Thành

Dữ liệu địa lý được tạo chuẩn xác thông qua công cụ `src/road_catalog/generate_vietnam_catalog.py`:
- Tất cả 63 tỉnh thành phố Việt Nam (Hà Nội, TP.HCM, Đà Nẵng, Cần Thơ, Hải Phòng, Cà Mau, Vũng Tàu...).
- Tọa độ GPS tâm chính xác 100% nằm trong lòng đất liền Việt Nam.
- Phân loại rõ rệt các dải tốc độ: Cao Tốc, Quốc Lộ, Đại Lộ, Phố Đô Thị.

---

## 🚀 Hướng Dẫn Khởi Chạy (Quick Start)

### 1. Khởi động toàn bộ Hệ thống Microservices bằng Docker Compose
```bash
sudo docker compose up --build -d
```

### 2. Truy cập Giao diện & APIs
- **Web Dashboard:** [http://localhost](http://localhost) (hoặc [http://localhost:8501](http://localhost:8501))
- **Go Live API:** [http://localhost/v1/traffic/live](http://localhost/v1/traffic/live)
- **Rust AI Inference API:** [http://localhost/v1/predictions](http://localhost/v1/predictions)
- **Prometheus Metrics:** [http://localhost/metrics](http://localhost/metrics)

---

## 📂 Cấu Trúc Thư Mục Dự Án (Directory Layout)

```text
lab5/
├── docker-compose.yml              # Cấu hình container HA cho 11 microservices
├── nginx.conf                      # Cấu hình Ingress Gateway proxy với DNS động
├── .gitignore                      # Quy tắc loại bỏ file rác, binary & secrets
├── README.md                       # Tài liệu hướng dẫn hệ thống
│
├── services/
│   ├── go-traffic/                 # Go Collector, Live API & Web Dashboard
│   │   ├── cmd/                    # Entrypoints: collector, live-api, web-dashboard
│   │   ├── internal/               # REST API, Collector Worker Pool, CORS middleware
│   │   ├── web/                    # Static Web SPA Assets (app.js, styles.css)
│   │   ├── Dockerfile
│   │   ├── Dockerfile.live-api
│   │   └── Dockerfile.web
│   │
│   └── rust-inference/             # Rust Native GBT AI Inference Engine
│       ├── crates/
│       │   ├── traffic-api/        # Axum REST API Server & Handlers
│       │   ├── traffic-tree-engine/# Native Flat-Array Decision Tree Engine
│       │   └── traffic-contract/   # Structs & Schema Contracts
│       └── Dockerfile
│
├── src/                            # Python Spark ETL & Catalog Generator
│   ├── road_catalog/               # Script sinh danh mục 200+ đường 63 tỉnh thành
│   ├── processing/                 # Spark ETL Data Pipeline
│   └── training/                   # Model Training & Export Scripts
│
├── artifacts/                      # Model Artifacts (model.json, manifest.json)
└── god_view/                       # Single Source of Truth (SOT) Phase Docs
```

---

## 🔒 An Toàn Bảo Mật & Tối Ưu Hóa Dữ Liệu
- Tất cả các container ứng dụng đều chạy bằng **Non-Root User (UID 10001)** nâng cao an ninh bảo mật.
- NGINX Ingress kết hợp `resolver 127.0.0.11 valid=5s` phòng chống lỗi 502 Bad Gateway khi container restart.
- Rust Native Tree Traversal dùng mảng phẳng (Flat Array) đạt hiệu năng **Zero Heap Allocation** khi suy luận.
