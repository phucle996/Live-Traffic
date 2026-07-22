Đúng, vậy mình **coi toàn bộ kế hoạch HERE trước đó là chưa thực hiện** và refactor lại từ trạng thái project hiện tại.

Project đang có Go collector phụ thuộc trực tiếp vào:

```text
services/go-traffic/internal/tomtom/client.go
services/go-traffic/internal/source/router.go
services/go-traffic/internal/budget/
services/go-traffic/internal/collector/worker_pool.go
services/go-traffic/internal/kafka/producer.go
```

Đồng thời vẫn còn pipeline TomTom cũ bên Python. 

Mục tiêu lần refactor này:

```text
TomTom point API
        ↓ thay dần

Provider-agnostic Go Collector
├── HERE Traffic Flow — primary
├── TomTom — fallback
└── Offline Lab — development fallback
        ↓
Kafka
        ↓
PySpark ETL
        ↓
Training theo road segment
        ↓
Rust batch inference
        ↓
Google Maps prediction overlay
```

Không làm big-bang. Mỗi phase phải chạy và rollback độc lập.

---

# Tổng thứ tự phase

```text
R0   Audit và baseline
R1   Shared traffic provider contract
R2   Refactor TomTom vào provider interface
R3   HERE API pilot
R4   HERE provider production client
R5   Area scheduler và request budget
R6   Event contract V2 và Kafka
R7   Road catalog TP.HCM
R8   Spatial matching
R9   Spark segment dataset
R10  Model V2
R11  Rust city-wide inference
R12  Google Maps UI
R13  Shadow run và cutover
R14  Mở rộng Việt Nam
```

---

# Phase R0 — Audit và đóng băng baseline

## Mục tiêu

Hiểu chính xác collector hiện tại trước khi thay đổi.

## Tasks

1. Đọc toàn bộ:

```text
services/go-traffic/cmd/collector/main.go
services/go-traffic/internal/tomtom/client.go
services/go-traffic/internal/source/router.go
services/go-traffic/internal/collector/worker_pool.go
services/go-traffic/internal/budget/
services/go-traffic/internal/retry/
services/go-traffic/internal/kafka/producer.go
services/go-traffic/internal/contract/event.go
```

2. Tìm mọi chỗ import hoặc phụ thuộc TomTom:

```bash
grep -R "tomtom\|TomTom" services src tests config
```

3. Ghi lại luồng hiện tại:

```text
location input
→ source router
→ TomTom request
→ normalize
→ Kafka hoặc state store
```

4. Benchmark hiện tại:

   * request latency;
   * số request mỗi vòng;
   * số location;
   * tỷ lệ lỗi;
   * memory;
   * Kafka event count;
   * dữ liệu bị duplicate.

5. Chạy toàn bộ test Go hiện có.

6. Chưa sửa behavior.

## Output

```text
docs/refactor/
├── current_ingestion_flow.md
├── tomtom_dependency_map.md
├── current_event_contract.md
└── baseline_metrics.md

artifacts/benchmarks/
└── collector_baseline.json
```

## Acceptance criteria

* Go tests hiện tại pass.
* Có sơ đồ dependency.
* Có danh sách file sẽ bị ảnh hưởng.
* Có baseline để so sánh sau refactor.
* Không thay đổi output Kafka.

---

# Phase R1 — Traffic provider contract

## Mục tiêu

Tách collector khỏi TomTom nhưng chưa thêm HERE.

## Cấu trúc mới

```text
services/go-traffic/internal/provider/
├── provider.go
├── query.go
├── observation.go
├── errors.go
└── registry.go
```

## Contract

```go
type TrafficProvider interface {
    Name() string

    HealthCheck(ctx context.Context) error

    FetchFlow(
        ctx context.Context,
        query FlowQuery,
    ) ([]FlowObservation, error)
}
```

## Query chung

```go
type FlowQuery struct {
    Area        GeoArea
    RequestedAt time.Time
    RoadClasses []string
}
```

## Observation chung

```go
type FlowObservation struct {
    Provider          string
    ProviderSegmentID string
    ObservedAt        time.Time

    RoadName          string
    CurrentSpeedKPH   *float64
    FreeFlowSpeedKPH  *float64
    JamFactor         *float64
    Confidence        *float64
    RoadClosed        *bool

    Geometry          []Coordinate
}
```

Dùng pointer hoặc optional cho dữ liệu thiếu. Không biến dữ liệu thiếu thành `0`.

## Tasks

1. Tạo interface và internal types.
2. Không chứa field đặc thù HERE hoặc TomTom trong contract chung.
3. Tạo fake provider cho unit test.
4. Tạo provider registry.
5. Chưa đổi collector sang contract mới.
6. Viết compatibility tests.

## Acceptance criteria

* Package `provider` không import TomTom.
* Fake provider dùng được trong worker-pool test.
* Không có network call trong unit test.
* Contract có thể biểu diễn dữ liệu thiếu.

---

# Phase R2 — Đưa TomTom vào provider interface

## Mục tiêu

Giữ nguyên hành vi hiện tại nhưng TomTom chỉ còn là một implementation.

## Cấu trúc

```text
services/go-traffic/internal/provider/tomtom/
├── client.go
├── request.go
├── response.go
├── mapper.go
├── errors.go
└── client_test.go
```

## Tasks

1. Di chuyển logic từ:

```text
internal/tomtom/client.go
```

sang:

```text
internal/provider/tomtom/
```

2. Mapper TomTom response → `FlowObservation`.
3. Collector chỉ gọi `TrafficProvider`.
4. Không để worker pool biết TomTom.
5. Giữ nguyên retry, budget và metrics.
6. Giữ alias tạm thời nếu các test cũ còn import package cũ.
7. Xóa package TomTom cũ chỉ khi không còn dependency.

## Cấu hình

```yaml
traffic:
  provider:
    primary: tomtom
    fallback: offline
```

## Acceptance criteria

* Output Kafka trước và sau refactor tương đương.
* TomTom vẫn là provider mặc định.
* Collector không import package TomTom trực tiếp.
* Tất cả test cũ pass.
* Có rollback bằng một commit.

---

# Phase R3 — HERE API pilot

## Mục tiêu

Kiểm tra HERE bằng dữ liệu thật trước khi tích hợp production.

Phase này **không nối vào collector chính**.

## Khu vực pilot

```text
hcm_central
hcm_binh_thanh
hcm_thu_duc
hcm_tan_son_nhat
```

## Tasks

1. Tạo một command riêng:

```text
services/go-traffic/cmd/here-pilot/main.go
```

2. Gọi HERE Traffic Flow theo bounding box.
3. Lưu raw JSON đã loại API key.
4. Normalize thử sang `FlowObservation`.
5. Đo:

   * latency;
   * response size;
   * số flow item;
   * số item có geometry;
   * số item có speed;
   * số item có free-flow;
   * confidence distribution;
   * lỗi và rate limit.
6. Chạy ở nhiều khung giờ.
7. Không produce vào Kafka production.
8. Không train model.
9. Xác minh quyền:

   * lưu raw data;
   * lưu lịch sử;
   * dùng train ML;
   * tạo derived prediction.

## Output

```text
artifacts/here-pilot/
├── raw/
├── normalized/
└── report.json

docs/providers/
├── here_pilot_report.md
├── here_coverage_report.md
└── here_licensing_checklist.md
```

## Acceptance criteria

* Có response thật ở TP.HCM.
* Có geometry và tốc độ cho phần đáng kể các đường lớn.
* Không có API key trong artifact.
* Có quyết định `go`, `conditional-go` hoặc `no-go`.
* Không thay đổi production collector.

---

# Phase R4 — HERE provider production client

Chỉ thực hiện khi R3 được duyệt.

## Cấu trúc

```text
services/go-traffic/internal/provider/here/
├── client.go
├── request.go
├── response.go
├── decoder.go
├── mapper.go
├── errors.go
├── client_test.go
└── testdata/
```

## Tasks

1. Reuse một `http.Client`.
2. Có timeout bằng context.
3. Retry với exponential backoff và jitter.
4. Không retry vô hạn.
5. Không retry 401/403.
6. Xử lý 429 và `Retry-After`.
7. Circuit breaker riêng cho HERE.
8. Parse bbox response.
9. Normalize m/s → km/h.
10. Redact secret.
11. Thêm fixture tests.
12. Integration test chỉ chạy khi có key.

## Metrics

```text
traffic_provider_requests_total{provider="here"}
traffic_provider_errors_total{provider="here"}
traffic_provider_request_duration_seconds{provider="here"}
traffic_provider_items_total{provider="here"}
traffic_provider_rate_limited_total{provider="here"}
```

## Acceptance criteria

* Unit tests không gọi mạng.
* Không log API key.
* Client không tạo connection mới cho từng item.
* Response rỗng không bị xem là crash.
* Rate-limit được báo rõ qua metrics.

---

# Phase R5 — Area scheduler và request budget

## Mục tiêu

Thay việc gọi từng tọa độ bằng việc crawl từng vùng.

## Cấu trúc

```text
services/go-traffic/internal/coverage/
├── area.go
├── grid.go
├── planner.go
├── scheduler.go
├── priority.go
└── lease.go

config/coverage/
├── hcm_boundary.geojson
├── hcm_cells.yaml
└── polling_policy.yaml
```

## Tasks

1. Chia TP.HCM thành các cell bounding box.
2. Mỗi cell có ID ổn định.
3. Hỗ trợ priority.
4. Polling interval là config.
5. Có distributed lease để tránh hai replica crawl trùng.
6. Budget tính theo:

   * provider;
   * ngày;
   * giờ;
   * cell.
7. Khi gần hết quota:

   * giảm frequency;
   * bỏ cell ưu tiên thấp;
   * không crash.
8. Không mở rộng cả Việt Nam trong phase này.

## Acceptance criteria

* Một cell không được crawl đồng thời bởi hai worker.
* Hết quota thì dừng có kiểm soát.
* Có metrics cell overdue.
* Có thể thêm cell mà không rebuild Go binary.
* Một HERE request trả nhiều flow item.

---

# Phase R6 — Event contract V2 và Kafka

## Mục tiêu

Chuẩn hóa event cho nhiều provider và road segment.

## Cập nhật

```text
contracts/traffic_event.proto
contracts/examples/traffic_event.json
services/go-traffic/internal/contract/event.go
src/streaming/stream_schema.py
```

## Event V2

```text
event_id
schema_version

provider
provider_request_id
provider_segment_id
provider_observed_at

cell_id
batch_id

road_name
current_speed_kph
free_flow_speed_kph
jam_factor
confidence
road_closed

geometry
ingested_at
source_mode
fallback_used
fallback_reason
```

Chưa cần `segment_id` nội bộ nếu road matching chưa hoàn thành.

## Topics

```text
traffic.provider.raw
traffic.provider.normalized
traffic.provider.invalid
traffic.dead-letter
```

## Tasks

1. Tạo schema version 2.
2. Giữ reader tương thích V1 trong thời gian migration.
3. Event ID phải deterministic.
4. Không gửi raw secret.
5. Invalid event đi topic riêng.
6. Contract test Go ↔ Python.
7. Không thay field meaning trong cùng version.

## Acceptance criteria

* Python đọc được event Go.
* Replay không tạo duplicate logic.
* V1 vẫn được đọc trong migration.
* Missing field không biến thành tốc độ bằng 0.

---

# Phase R7 — Road catalog TP.HCM

## Mục tiêu

Tạo mạng lưới segment nội bộ để train và dự đoán.

## Dữ liệu

Bắt đầu từ OpenStreetMap hoặc nguồn GIS được phép dùng.

## Road class

```text
motorway
trunk
primary
secondary
tertiary
```

Bổ sung `residential` hoặc `unclassified` sau, không lấy hẻm ngay.

## Cấu trúc

```text
src/road_catalog/
├── import_network.py
├── filter_roads.py
├── split_segments.py
├── enrich_segments.py
├── validate_catalog.py
└── export_catalog.py

db/migrations/
├── 001_enable_postgis.sql
└── 002_create_road_segments.sql
```

## Fields

```text
segment_id
catalog_version
road_name
road_class
direction
length_m
bearing
lanes
speed_limit_kph
geometry
centroid
active
```

## Tasks

1. Import đường TP.HCM.
2. Lọc đường lớn và trung bình.
3. Split tại giao lộ.
4. Tách hai chiều.
5. Chia segment quá dài.
6. Sinh stable segment ID.
7. Lưu PostGIS.
8. Export Parquet.
9. Tạo spatial index.
10. Sinh checksum và catalog version.

## Acceptance criteria

* Không có geometry rỗng.
* Không trộn hai chiều.
* Segment ID ổn định khi import lại cùng dữ liệu.
* Viewport query dùng spatial index.
* Có coverage report theo quận và road class.

---

# Phase R8 — Spatial matching HERE → road segment

## Mục tiêu

Ghép geometry từ HERE vào `segment_id` nội bộ.

## Matching signal

```text
distance
overlap
bearing
direction
road class
road name
length
```

## Tasks

1. Candidate search bằng PostGIS.
2. Tính matching score.
3. Phân loại:

   * matched;
   * ambiguous;
   * unmatched.
4. Cache mapping theo:

```text
provider
provider_segment_id
catalog_version
matching_algorithm_version
```

5. Không tính lại mapping ổn định ở mỗi poll.
6. Match score thấp không vào training.
7. Tạo report kiểm tra bằng bản đồ.
8. Review thủ công ít nhất 200 segment.

## Acceptance criteria

* Có precision report.
* Hai chiều không bị ghép nhầm.
* Mapping invalidated khi catalog đổi.
* Unmatched rate được theo dõi.
* Không im lặng gán nearest road khi confidence thấp.

---

# Phase R9 — Spark dataset theo segment

## Mục tiêu

Tạo dữ liệu train:

```text
segment_id + time_bucket + traffic features
```

## Tasks

1. Spark đọc normalized event.
2. Join provider mapping.
3. Deduplicate.
4. Watermark.
5. Chuẩn hóa time bucket 5 phút.
6. Tạo:

   * lag 5 phút;
   * lag 15 phút;
   * lag 30 phút;
   * rolling mean;
   * rolling standard deviation;
   * historical same-slot profile.
7. Không forward-fill qua khoảng mất dữ liệu dài.
8. Partition theo ngày/giờ/provider.
9. Compact small files.
10. Quality report theo road class và district.

## Acceptance criteria

* Không temporal leakage.
* Replay không tạo duplicate.
* Segment match thấp bị loại.
* Có missing-interval report.
* Dataset có lineage về provider batch.

---

# Phase R10 — Model V2

## Mục tiêu

Train model toàn bộ các segment đường chính TP.HCM.

## Features

```text
road_class
latitude
longitude
length_m
bearing
direction
lanes
speed_limit
free_flow_speed

hour
minute_bucket
day_of_week
weekend
holiday

speed_lag_5m
speed_lag_15m
speed_lag_30m
rolling_mean_30m
historical_mean_same_slot
```

## Tasks

1. Train baseline GBT.
2. Split dữ liệu theo thời gian.
3. Có holdout segment.
4. Đánh giá theo:

   * road class;
   * quận;
   * giờ;
   * ngày thường/cuối tuần;
   * seen/unseen segment.
5. So sánh model có và không có lag features.
6. Export model tree và ONNX.
7. Sinh feature contract V2.
8. Sinh golden dataset.
9. Rust parity test.
10. Không replace model V1 ngay.

## Acceptance criteria

* Không temporal leakage.
* Metric theo vùng được công bố.
* Unseen-segment metric không quá kém.
* Rust parity đạt tolerance.
* Có rollback về model V1.

---

# Phase R11 — Rust city-wide inference

## Mục tiêu

Dự đoán hàng nghìn segment theo batch, không theo từng request browser.

## Tasks

1. Load model vào RAM.
2. Load static road features vào RAM.
3. Predict toàn bộ active segment theo time bucket.
4. Cache kết quả theo:

```text
model_version
catalog_version
feature_snapshot_version
prediction_time
```

5. Precompute:

   * +15 phút;
   * +30 phút;
   * +60 phút.
6. Query API theo viewport.
7. Không trả toàn TP.HCM mỗi request.
8. Segment thiếu dữ liệu trả `unavailable`.
9. Hot reload bằng atomic swap.
10. Benchmark batch 1.000, 10.000 và toàn catalog.

## Endpoint

```text
POST /v2/predictions/precompute

GET /v2/predictions/segments
    ?bbox=...
    &time=...

GET /v2/predictions/segments/{segment_id}
```

## Acceptance criteria

* Không file I/O trên hot path.
* Không inference lại cho từng user.
* Response chứa model và catalog version.
* Reload lỗi không làm mất model cũ.
* RAM ổn định sau nhiều batch.

---

# Phase R12 — Google Maps UI

## Mục tiêu

```text
Live       → Google TrafficLayer
Prediction → layer của model
```

## Tasks

1. Thay map hiện tại bằng Google Maps JavaScript API.
2. Thêm các chế độ:

```text
Live
Prediction
Compare
```

3. Prediction query theo viewport.
4. Debounce khi pan/zoom.
5. Click road mở panel.
6. Hiển thị:

   * road name;
   * predicted speed;
   * free-flow speed;
   * congestion ratio;
   * model version;
   * prediction time;
   * data freshness.
7. Login giữ OIDC hiện có.
8. Không gọi HERE từ browser.
9. Không để HERE key trong Next.js bundle.
10. Google Maps key phải giới hạn domain và API.

## Acceptance criteria

* Live không bị ghi nhãn thành prediction.
* Prediction vẽ thành polyline, không phải marker.
* Pan/zoom không tải toàn thành phố.
* Mobile dùng được.
* Token hết hạn được xử lý đúng.

---

# Phase R13 — Shadow run và cutover

## Luồng

```text
TomTom production
HERE shadow
        ↓
HERE 10%
HERE 25%
HERE 50%
HERE 100%
TomTom fallback
```

## Tasks

1. Chạy cùng một nhóm khu vực.
2. So sánh:

   * coverage;
   * latency;
   * rate limit;
   * matching rate;
   * speed difference;
   * chi phí.
3. Chỉ một provider publish production event cho một cell tại một thời điểm.
4. Ghi rõ fallback reason.
5. Không average dữ liệu hai provider tự động.
6. Có rollback config.
7. Sau soak mới tắt TomTom primary.
8. Chưa xóa TomTom provider.

## Acceptance criteria

* Không duplicate traffic event.
* HERE lỗi thì TomTom fallback hoạt động.
* Dashboard hiển thị đúng source.
* Có rollback dưới một lần deploy/config change.
* Không mất dữ liệu trong cutover.

---

# Phase R14 — Mở rộng toàn Việt Nam

Chỉ làm sau khi TP.HCM ổn định.

## Thứ tự

```text
1. Hà Nội
2. Đà Nẵng
3. Bình Dương và Đồng Nai
4. Hải Phòng và Cần Thơ
5. Cao tốc và quốc lộ
6. Các đô thị còn lại
```

## Thay đổi kiến trúc

```text
country_code
province_code
region_id
cell_id
segment_id
timezone
```

## Tasks

1. Import road catalog toàn Việt Nam.
2. Partition PostGIS/Parquet theo vùng.
3. Scheduler theo priority region.
4. Không crawl toàn quốc cùng tần suất.
5. Model registry theo vùng:

```text
vn-global
hcm
hanoi
major-cities
highway
```

6. Rust route model theo region.
7. Chỉ load model cần thiết trong deployment tương ứng.

---

# Các nguyên tắc bắt buộc

```text
Không xóa TomTom trước cutover.
Không gọi HERE từ frontend.
Không request một lần cho từng segment.
Không train từ Google TrafficLayer.
Không lấy traffic tile hình ảnh để suy ngược tốc độ.
Không đưa event match thấp vào training.
Không inference lại cho từng browser.
Không mở rộng toàn Việt Nam trước khi TP.HCM chạy ổn.
Không sửa nhiều phase trong cùng một PR.
```

# Prompt đầu tiên gửi Gemini

```text
Project hiện tại đã có Go collector phụ thuộc TomTom, Kafka producer,
Python/PySpark pipeline, Rust inference và Next.js frontend.

Các kế hoạch HERE trước đây chưa được thực hiện. Hãy coi repository hiện tại
là trạng thái ban đầu và không giả định bất kỳ HERE code nào đã tồn tại.

Chỉ thực hiện Phase R0 — Audit và baseline.

Tasks:

1. Đọc:
   - services/go-traffic/cmd/collector/main.go
   - services/go-traffic/internal/tomtom/client.go
   - services/go-traffic/internal/source/router.go
   - services/go-traffic/internal/collector/worker_pool.go
   - services/go-traffic/internal/budget/
   - services/go-traffic/internal/retry/
   - services/go-traffic/internal/kafka/producer.go
   - services/go-traffic/internal/contract/event.go

2. Tìm toàn bộ dependency TomTom trong:
   - services/
   - src/
   - tests/
   - config/
   - scripts/
   - airflow/

3. Vẽ luồng ingestion hiện tại.

4. Ghi lại:
   - request model;
   - retry behavior;
   - budget behavior;
   - fallback behavior;
   - Kafka event schema;
   - state store behavior;
   - metrics hiện tại.

5. Chạy test hiện có và lưu kết quả.

6. Benchmark collector hiện tại nếu chạy được:
   - latency;
   - request count;
   - event count;
   - error count;
   - memory;
   - CPU.

7. Tạo:
   - docs/refactor/current_ingestion_flow.md
   - docs/refactor/tomtom_dependency_map.md
   - docs/refactor/current_event_contract.md
   - docs/refactor/baseline_metrics.md
   - artifacts/benchmarks/collector_baseline.json

Không được:
- thêm HERE client;
- thay provider;
- sửa Kafka schema;
- xóa TomTom;
- sửa production behavior;
- train lại model;
- thay frontend.

Cuối phase, báo cáo:
1. File đã đọc.
2. Dependency graph.
3. Test pass/fail.
4. Baseline.
5. Rủi ro refactor.
6. Acceptance criteria đạt/chưa đạt.
7. Đề xuất phạm vi chính xác của Phase R1.
```

Bắt đầu từ **R0**, sau đó chỉ chuyển sang R1 khi đã biết rõ TomTom hiện đang nối vào những đâu.
