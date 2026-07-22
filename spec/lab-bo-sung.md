Đúng. Nên sửa 11 phase thành kiến trúc **hybrid data source**:

```text
OFFLINE → dùng chính dữ liệu CSV của Lab 5
ONLINE  → gọi TomTom Traffic API lấy giao thông hiện tại
AUTO    → ưu tiên API; lỗi/mất mạng thì fallback sang dữ liệu Lab
```

TomTom Flow Segment Data API nhận một tọa độ và trả về các trường như `currentSpeed`, `freeFlowSpeed`, `confidence`, thời gian di chuyển và trạng thái đóng đường. Endpoint phiên bản 4 vẫn tương thích với code của bài lab. ([TomTom Developer][1]) Dữ liệu online là dữ liệu giao thông quan sát theo thời gian thực, trong khi dữ liệu CSV của bài dùng làm dữ liệu lịch sử để ETL và huấn luyện model. ([TomTom Developer][2])

Trong bộ Lab 5:

```text
Data & process_data/data/*.csv
```

là dữ liệu thô lịch sử;

```text
Data & process_data/data_converted.csv
```

là danh sách địa điểm và tọa độ để gọi API;

```text
Data & process_data/process_data_spark.csv
```

là dữ liệu đã xử lý, chỉ nên dùng để đối chiếu kết quả ETL, không dùng làm nguồn raw chính. Pipeline của tài liệu cũng bắt đầu từ TomTom API, ghi CSV, đưa lên HDFS rồi xử lý bằng Spark. 

Dưới đây là nội dung có thể gửi thẳng cho Gemini.

---

# Prompt cập nhật dành cho Gemini

```text
Bạn đang phát triển project:

LAB 05 – Hệ thống phân tích và dự đoán lưu lượng giao thông đô thị.

Project phải sử dụng đúng dữ liệu và code được cung cấp trong hai file:

1. Data & process_data-20260709T105216Z-3-001(1).zip
2. Code & Model-20260709T105215Z-2-001(1).zip

Không tạo dữ liệu giao thông giả nếu dữ liệu Lab hoặc TomTom API có thể được sử dụng.

Hệ thống phải hỗ trợ ba chế độ nguồn dữ liệu:

- offline:
  Chỉ sử dụng dữ liệu lịch sử có sẵn trong bộ Lab.

- online:
  Gọi TomTom Traffic Flow Segment Data API để lấy dữ liệu giao thông thực tế hiện tại.

- auto:
  Ưu tiên TomTom API nếu có API key và kết nối thành công.
  Nếu API không sử dụng được thì fallback sang dữ liệu Lab.
  Việc fallback phải được ghi log và hiển thị rõ trên dashboard.
  Không được fallback âm thầm khiến người dùng tưởng dữ liệu offline là dữ liệu live.

Không sử dụng API key đang hard-code trong source code cũ.
API key phải được lấy từ biến môi trường TOMTOM_API_KEY.
```

---

# Phase 0 — Nhập và kiểm kê tài nguyên Lab

## Mục tiêu

Giải nén, phát hiện và chuẩn hóa toàn bộ dữ liệu, code và model có trong bộ Lab 5.

## Task

1. Phát hiện hai file ZIP đầu vào.
2. Giải nén vào thư mục tạm.
3. Không sửa trực tiếp nội dung file ZIP gốc.
4. Copy dữ liệu cần thiết sang cấu trúc project mới.
5. Kiểm tra schema và số lượng file.
6. Sinh manifest ghi lại:

   * tên file;
   * kích thước;
   * checksum;
   * số dòng CSV;
   * header;
   * thời gian nhỏ nhất và lớn nhất nếu có.
7. Không sử dụng model hoặc processed data trước khi xác minh tương thích.

## Dữ liệu phải tìm trong ZIP

```text
Data & process_data/
├── data/
│   └── *_traffic_data_from_traffic.csv
├── preprocess data/
│   └── preprocess_*.csv
├── data_converted.csv
└── process_data_spark.csv
```

## Code tham khảo phải tìm trong ZIP

```text
Code & Model/
├── traffic_data_crawl.py
├── process_spark.py
├── train_model_GBT.py
├── train_model_xgboost.py
├── app.py
├── app_spark.py
├── train_model_spark/
└── xgboost_model.pkl
```

## Quy tắc sử dụng

* `data/*.csv` là nguồn raw offline chính.
* `data_converted.csv` là danh mục địa điểm để gọi API online.
* `process_data_spark.csv` là kết quả tham chiếu để kiểm tra ETL.
* `preprocess data/*.csv` là dữ liệu tham chiếu bổ sung.
* Code cũ chỉ dùng để hiểu nghiệp vụ.
* Không copy API key, đường dẫn tuyệt đối hoặc logic lỗi từ code cũ.
* Model cũ có thể dùng để kiểm tra nhanh nhưng pipeline phải train lại được model mới.

## File cần viết

```text
scripts/import_lab_assets.py
src/common/file_manifest.py
src/common/csv_inspector.py
tests/unit/test_lab_asset_import.py
docs/lab_asset_inventory.md
artifacts/manifests/lab_assets.json
```

## Cấu trúc output

```text
data/
├── lab_raw/
│   └── *.csv
├── lab_reference/
│   ├── process_data_spark.csv
│   └── preprocess/
├── locations/
│   └── data_converted.csv
└── samples/
```

## Kết quả cần đạt

Lệnh:

```bash
python -m scripts.import_lab_assets \
  --data-zip "/input/Data & process_data-20260709T105216Z-3-001(1).zip" \
  --code-zip "/input/Code & Model-20260709T105215Z-2-001(1).zip"
```

phải:

* giải nén thành công;
* copy đúng raw data;
* copy đúng location file;
* tạo manifest;
* báo lỗi rõ ràng nếu thiếu file bắt buộc.

## Acceptance criteria

* Không tạo dữ liệu mẫu thay thế khi dữ liệu Lab tồn tại.
* Không train trực tiếp từ `process_data_spark.csv`.
* Không làm thay đổi file ZIP gốc.
* Chạy lại không tạo dữ liệu trùng.
* Manifest ghi được số file và số dòng.

````

---

# Phase 1 — Cấu hình nguồn dữ liệu Hybrid

## Mục tiêu

Cho phép thay đổi nguồn dữ liệu mà không sửa code.

## File `.env.example`

```env
DATA_SOURCE_MODE=offline

LAB_DATA_ZIP=/input/Data & process_data-20260709T105216Z-3-001(1).zip
LAB_CODE_ZIP=/input/Code & Model-20260709T105215Z-2-001(1).zip

OFFLINE_RAW_GLOB=/app/data/lab_raw/*.csv
LOCATIONS_FILE=/app/data/locations/data_converted.csv
REFERENCE_PROCESSED_FILE=/app/data/lab_reference/process_data_spark.csv

TOMTOM_API_KEY=
TOMTOM_API_BASE_URL=https://api.tomtom.com
TOMTOM_FLOW_VERSION=4
TOMTOM_FLOW_STYLE=relative
TOMTOM_FLOW_ZOOM=10
TOMTOM_SPEED_UNIT=kmph

ONLINE_REQUEST_TIMEOUT_SECONDS=15
ONLINE_MAX_RETRIES=3
ONLINE_RETRY_DELAY_SECONDS=5
ONLINE_POLL_INTERVAL_SECONDS=1800
ONLINE_REQUEST_BUDGET_PER_DAY=2000

TIMEZONE=Asia/Ho_Chi_Minh

HDFS_URI=hdfs://namenode:9000
HDFS_RAW_PATH=/traffic_project/raw
HDFS_PROCESSED_PATH=/traffic_project/processed
HDFS_MODEL_PATH=/traffic_project/models
HDFS_PREDICTION_PATH=/traffic_project/predictions
````

## Quy tắc từng mode

### `DATA_SOURCE_MODE=offline`

```text
Lab CSV
→ validate
→ normalize
→ HDFS raw
```

Không được gọi Internet.

### `DATA_SOURCE_MODE=online`

```text
data_converted.csv
→ TomTom API
→ normalize
→ HDFS raw
```

Nếu thiếu API key hoặc API lỗi hoàn toàn thì pipeline phải fail rõ ràng.

### `DATA_SOURCE_MODE=auto`

```text
Có API key và API health check thành công
        ↓
      online
```

Nếu không:

```text
Ghi warning + fallback_reason
        ↓
      offline
```

## File cần viết

```text
src/common/config.py
src/ingestion/source_mode.py
src/ingestion/source_router.py
tests/unit/test_source_router.py
```

## Interface bắt buộc

```python
from enum import Enum


class DataSourceMode(str, Enum):
    OFFLINE = "offline"
    ONLINE = "online"
    AUTO = "auto"
```

```python
class SourceRouter:
    def resolve_source(self) -> str:
        """
        Trả về 'offline' hoặc 'online'.

        Trong auto mode:
        - kiểm tra API key;
        - kiểm tra kết nối API;
        - ghi lại lý do fallback;
        - không fallback âm thầm.
        """
```

## Kết quả cần đạt

```bash
DATA_SOURCE_MODE=offline python -m src.ingestion.ingest
DATA_SOURCE_MODE=online python -m src.ingestion.ingest
DATA_SOURCE_MODE=auto python -m src.ingestion.ingest
```

cả ba mode có hành vi đúng.

---

# Phase 2 — Chuẩn hóa Data Contract

## Mục tiêu

Dữ liệu offline và online phải tạo ra cùng một schema để Spark không cần biết dữ liệu đến từ đâu.

## Raw schema chuẩn

```text
Timestamp              timestamp
Location/Street        string
District               string
Latitude               double
Longitude              double
CurrentSpeed           double
FreeFlowSpeed          double
Confidence              double

CurrentTravelTime      nullable integer
FreeFlowTravelTime     nullable integer
RoadClosure            nullable boolean

DataSource             string
IngestedAtUtc          timestamp
IngestionBatchId       string
```

## Mapping offline

Dữ liệu Lab hiện có:

```text
Timestamp
Location/Street
District
Latitude
Longitude
CurrentSpeed
FreeFlowSpeed
Confidence
```

Bổ sung:

```text
DataSource = "lab_offline"
IngestedAtUtc = thời gian import
IngestionBatchId = UUID của batch
```

Các trường không có trong Lab:

```text
CurrentTravelTime = null
FreeFlowTravelTime = null
RoadClosure = null
```

## Mapping online

Response TomTom:

```text
currentSpeed
freeFlowSpeed
confidence
currentTravelTime
freeFlowTravelTime
roadClosure
```

Mapping:

```text
currentSpeed         → CurrentSpeed
freeFlowSpeed        → FreeFlowSpeed
confidence           → Confidence
currentTravelTime    → CurrentTravelTime
freeFlowTravelTime   → FreeFlowTravelTime
roadClosure          → RoadClosure
```

Thông tin:

```text
Location/Street
District
Latitude
Longitude
```

lấy từ `data_converted.csv`.

## Xử lý `data_converted.csv`

File Lab có cột:

```text
"Latitude,Longitude"
```

Phải tách thành:

```text
Latitude
Longitude
```

Quy tắc:

* trim khoảng trắng;
* cast sang double;
* kiểm tra latitude từ -90 đến 90;
* kiểm tra longitude từ -180 đến 180;
* reject dòng sai định dạng;
* không tự thay bằng tọa độ mặc định.

## File cần viết

```text
src/common/schemas.py
src/ingestion/data_normalizer.py
src/ingestion/location_loader.py
src/processing/validate_raw_data.py
tests/unit/test_location_loader.py
tests/unit/test_data_normalizer.py
```

## Acceptance criteria

* Offline và online trả về cùng danh sách cột.
* Không dùng `inferSchema` làm schema chính.
* Không silently cast dữ liệu sai thành null.
* Dữ liệu lỗi được ghi vào quarantine.

````

---

# Phase 3 — Offline Lab Data Source

## Mục tiêu

Dùng chính các file CSV raw của bài Lab để chạy toàn bộ pipeline khi không có Internet hoặc API key.

## Task

1. Đọc toàn bộ:

```text
data/lab_raw/*_traffic_data_from_traffic.csv
````

2. Validate header.
3. Parse `Timestamp`.
4. Cast các trường số.
5. Thêm metadata nguồn.
6. Loại bỏ file rỗng.
7. Không đưa `process_data_spark.csv` vào raw ingestion.
8. Upload dữ liệu lên HDFS.
9. Partition theo ngày sự kiện.
10. Tạo manifest để bảo đảm idempotent.

## HDFS output

```text
/traffic_project/raw/
└── source=lab_offline/
    ├── event_date=2025-11-07/
    ├── event_date=2025-11-08/
    └── ...
```

## File cần viết

```text
src/ingestion/base_source.py
src/ingestion/offline_lab_source.py
src/ingestion/ingestion_manifest.py
src/ingestion/hdfs_writer.py
scripts/run_offline_ingestion.sh
tests/integration/test_offline_lab_ingestion.py
```

## Interface

```python
class TrafficDataSource:
    def read(self):
        raise NotImplementedError
```

```python
class OfflineLabSource(TrafficDataSource):
    def read(self):
        """
        Đọc toàn bộ raw CSV thật được cung cấp trong Lab.
        Không tạo dữ liệu synthetic.
        """
```

## Idempotency

Mỗi file phải được nhận dạng bằng:

```text
relative_path
file_size
sha256
```

Nếu file đã ingest và checksum không đổi thì bỏ qua.

## Kết quả cần đạt

```bash
DATA_SOURCE_MODE=offline \
python -m src.ingestion.ingest
```

Sau đó:

```bash
hdfs dfs -ls -R /traffic_project/raw/source=lab_offline
```

phải nhìn thấy dữ liệu được partition theo ngày.

## Acceptance criteria

* Chạy offline hoàn toàn không cần Internet.
* Không cần TomTom API key.
* Chạy lại không duplicate dữ liệu.
* Số dòng output được báo cáo rõ ràng.
* Có báo cáo valid/invalid rows.

````

---

# Phase 4 — Online TomTom Real Traffic Source

## Mục tiêu

Gọi nguồn API thật để lấy tốc độ giao thông hiện tại tại các địa điểm của bài Lab.

## API sử dụng

Sử dụng TomTom Traffic Flow Segment Data API.

Request mặc định:

```text
GET https://api.tomtom.com/traffic/services/4/
    flowSegmentData/relative/10/json
````

Query parameters:

```text
key=<TOMTOM_API_KEY>
point=<latitude>,<longitude>
unit=kmph
```

Không ghi trực tiếp API key vào URL log.

## Task

1. Đọc danh sách địa điểm từ:

```text
data/locations/data_converted.csv
```

2. Tách latitude và longitude.
3. Với mỗi địa điểm, gọi TomTom API.
4. Dùng HTTP timeout.
5. Retry có giới hạn.
6. Xử lý riêng:

   * HTTP 400;
   * HTTP 401/403;
   * HTTP 429;
   * HTTP 5xx;
   * timeout;
   * JSON không đúng schema.
7. Không retry nhiều lần với API key không hợp lệ.
8. Không ghi file rỗng nếu toàn bộ request thất bại.
9. Ghi một batch output cho mỗi lần crawl.
10. Append batch vào HDFS.
11. Ghi metrics:

    * tổng địa điểm;
    * request thành công;
    * request thất bại;
    * request bị rate limit;
    * thời gian chạy;
    * request budget còn lại theo cấu hình nội bộ.

## File cần viết

```text
src/ingestion/tomtom_client.py
src/ingestion/online_tomtom_source.py
src/ingestion/request_budget.py
src/ingestion/api_healthcheck.py
src/ingestion/ingest.py
scripts/run_online_ingestion.sh
tests/unit/test_tomtom_client.py
tests/unit/test_request_budget.py
tests/integration/test_online_ingestion_mocked.py
```

## TomTom client

```python
class TomTomTrafficClient:
    def get_flow_segment(
        self,
        latitude: float,
        longitude: float,
    ) -> dict:
        """
        Gọi API thật khi chạy production.
        Trong unit test phải mock HTTP.
        """
```

## Quy tắc API key

```python
api_key = os.getenv("TOMTOM_API_KEY")

if not api_key:
    raise RuntimeError(
        "DATA_SOURCE_MODE=online nhưng thiếu TOMTOM_API_KEY"
    )
```

Không được:

```python
API_KEY = "hard-coded-key"
```

## HDFS output

```text
/traffic_project/raw/
└── source=tomtom_live/
    └── event_date=YYYY-MM-DD/
        └── hour=HH/
            └── batch_<uuid>.parquet
```

## Kết quả cần đạt

```bash
DATA_SOURCE_MODE=online \
TOMTOM_API_KEY=<user-key> \
python -m src.ingestion.ingest --once
```

phải lấy dữ liệu thật và ghi vào HDFS.

Chế độ polling:

```bash
python -m src.ingestion.ingest --daemon
```

phải chạy theo:

```text
ONLINE_POLL_INTERVAL_SECONDS
```

## Acceptance criteria

* Dữ liệu lấy từ API thật, không mock khi chạy production.
* Unit test không gọi API thật.
* Không lộ API key trong log.
* Mỗi batch có timestamp và UUID.
* Có request budget guard.
* Khi HTTP 429 phải backoff hoặc dừng batch.
* Khi key sai phải báo lỗi rõ ràng.
* Không sinh prediction ngẫu nhiên để thay dữ liệu API lỗi.

````

---

# Phase 5 — Auto Mode và cơ chế fallback

## Mục tiêu

Hệ thống có thể chạy an toàn khi Internet hoặc TomTom API không khả dụng.

## Luồng quyết định

```text
DATA_SOURCE_MODE=auto
        ↓
Có TOMTOM_API_KEY?
        │
        ├── Không → offline
        │
        └── Có
             ↓
       API health check
             │
             ├── Thành công → online
             └── Thất bại → offline + warning
````

## Fallback metadata

Khi fallback phải ghi:

```json
{
  "requested_mode": "auto",
  "resolved_mode": "offline",
  "fallback": true,
  "fallback_reason": "TOMTOM_API_UNAVAILABLE",
  "checked_at": "...",
  "api_error_type": "timeout"
}
```

## File cần viết

```text
src/ingestion/source_router.py
src/ingestion/fallback_report.py
artifacts/reports/source_resolution.json
tests/unit/test_auto_fallback.py
```

## Acceptance criteria

* Không có API key → offline.
* API timeout → offline.
* API key invalid → offline nhưng hiển thị cảnh báo authentication.
* API hoạt động → online.
* Dashboard hiển thị đúng nguồn dữ liệu đang dùng.
* Không gắn nhãn “Live” cho dữ liệu fallback offline.

````

---

# Thay đổi Phase Spark ETL

Bổ sung yêu cầu sau vào phase xử lý Spark:

```text
Spark phải đọc được dữ liệu từ cả:

/traffic_project/raw/source=lab_offline
/traffic_project/raw/source=tomtom_live

Dữ liệu từ hai nguồn phải dùng cùng schema.

ETL phải giữ lại cột DataSource để:
- phân tích chất lượng theo nguồn;
- tránh nhầm dữ liệu live và lịch sử;
- hỗ trợ lọc nguồn khi train;
- kiểm tra drift giữa Lab data và dữ liệu mới.
````

## Quy tắc training

```text
Mặc định:
- train bằng toàn bộ dữ liệu lịch sử hợp lệ;
- bao gồm lab_offline;
- có thể bao gồm tomtom_live sau khi đã tích lũy đủ dữ liệu.

Không train model chỉ từ một snapshot live duy nhất.
```

Thêm cấu hình:

```env
TRAIN_ALLOWED_SOURCES=lab_offline,tomtom_live
MIN_TRAIN_ROWS=1000
MIN_TOMTOM_LIVE_ROWS_FOR_TRAINING=1000
```

---

# Thay đổi Phase Prediction và Dashboard

Dashboard phải có hai chức năng khác nhau.

## 1. Live Traffic

```text
Nguồn:
TomTom API

Mục đích:
Hiển thị tốc độ quan sát hiện tại.
```

Hiển thị rõ:

```text
LIVE OBSERVATION
Source: TomTom Traffic API
Fetched at: ...
```

Nếu offline:

```text
OFFLINE SNAPSHOT
Source: Lab historical dataset
Event time: ...
```

Không được ghi chữ `Live`.

## 2. Traffic Prediction

```text
Nguồn:
Spark GBT model

Mục đích:
Dự đoán tốc độ cho ngày và giờ người dùng chọn.
```

Hiển thị rõ:

```text
MODEL PREDICTION
Model version: ...
Prediction time: ...
```

## Routing trong dashboard

```text
Người dùng chọn "Live Traffic"
        ↓
online/auto mode
        ↓
TomTom API
```

```text
Người dùng chọn "Prediction"
        ↓
GBT model
```

Không dùng model prediction để giả làm dữ liệu live.

## File cần cập nhật

```text
src/dashboard/app.py
src/dashboard/dashboard_service.py
src/dashboard/source_badge.py
src/prediction/predictor.py
```

## Acceptance criteria

* Live data và predicted data có nhãn khác nhau.
* Dashboard hiển thị thời điểm lấy dữ liệu.
* Dashboard hiển thị nguồn.
* Offline fallback không được hiển thị là live.
* Dữ liệu API mới được append vào HDFS.
* Prediction vẫn chạy được khi API mất.

````

---

# Lệnh end-to-end mong muốn

## Chạy hoàn toàn offline

```bash
cp .env.example .env

sed -i 's/DATA_SOURCE_MODE=offline/DATA_SOURCE_MODE=offline/' .env

make up
make import-lab
make ingest
make process
make train
make dashboard
````

Luồng:

```text
Lab CSV
→ HDFS
→ Spark ETL
→ GBT training
→ Prediction dashboard
```

## Chạy online lấy dữ liệu thật

```bash
DATA_SOURCE_MODE=online
TOMTOM_API_KEY=<new-api-key>

make up
make import-lab
make ingest-online-once
make process
make train
make dashboard
```

Luồng:

```text
data_converted.csv
→ TomTom Traffic API
→ HDFS
→ Spark ETL
→ tích lũy dữ liệu
→ retrain model khi đủ dữ liệu
```

## Chạy auto

```bash
DATA_SOURCE_MODE=auto
TOMTOM_API_KEY=<optional-key>

make pipeline
```

Luồng:

```text
API dùng được → dữ liệu TomTom thật
API không dùng được → Lab CSV + cảnh báo fallback
```

---

# Yêu cầu cuối dành cho Gemini

```text
Không hoàn thành phase tiếp theo trước khi phase hiện tại chạy được.

Sau mỗi phase, hãy trả về:

1. Cây thư mục được tạo hoặc thay đổi.
2. Nội dung đầy đủ của từng file mới.
3. Diff cho những file đã tồn tại.
4. Các lệnh chạy.
5. Các lệnh kiểm tra.
6. Kết quả mong đợi.
7. Các lỗi phổ biến và cách xử lý.
8. Danh sách acceptance criteria đã đạt/chưa đạt.

Không tạo mock data để thay thế dữ liệu Lab.

Mock TomTom API chỉ được dùng trong unit test.
Khi chạy online mode, phải gọi API thật.

Không sử dụng API key cũ tìm thấy trong source code.
Người dùng sẽ cung cấp TOMTOM_API_KEY mới qua environment.

Dữ liệu offline và online phải được normalize về cùng một schema.

Dashboard phải phân biệt rõ:
- dữ liệu quan sát live;
- dữ liệu lịch sử offline;
- dữ liệu dự đoán bởi model.
```

Thiết kế này giúp project vừa **chạy chắc chắn bằng dữ liệu có sẵn khi offline**, vừa **có khả năng lấy giao thông thực tế từ TomTom khi online**, mà không trộn lẫn dữ liệu thật hiện tại với kết quả dự đoán của model.

[1]: https://developer.tomtom.com/traffic-api/documentation/tomtom-maps/v1/traffic-flow/flow-segment-data "Flow Segment Data | Traffic API | TomTom Developer Portal"
[2]: https://developer.tomtom.com/traffic-api/documentation/tomtom-maps/v1/product-information/introduction "Introduction | Traffic API | TomTom Developer Portal"
