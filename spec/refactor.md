Đúng hướng tối ưu là **không thay toàn bộ Python bằng Go/Rust**. Hệ thống nên chia thành ba vùng:

```text
Python = Data/ML plane
Go     = I/O, ingestion, live-data và control plane
Rust   = model inference và đường xử lý cần độ trễ thấp
```

Tree hiện tại đã tách khá rõ `ingestion`, `streaming`, `processing`, `training`, `prediction`, `serving`, `api`, `dashboard`, Airflow và MLOps, nên có thể chuyển đổi dần mà không cần viết lại toàn bộ project. 

Điểm tăng tốc lớn nhất không phải vì Rust nhanh hơn Python vài lần, mà là:

```text
Loại SparkSession và JVM khỏi request inference
→ load model một lần
→ chạy GBT trực tiếp trong Rust
→ không khởi động Spark cho mỗi request
```

# 1. Phân chia ngôn ngữ cuối cùng

| Thành phần hiện tại                 |               Ngôn ngữ đích | Quyết định                  |
| ----------------------------------- | --------------------------: | --------------------------- |
| `src/training/`                     |              Python/PySpark | Giữ nguyên                  |
| `src/processing/`                   |              Python/PySpark | Giữ nguyên                  |
| `src/data_quality/`                 |              Python/PySpark | Giữ nguyên                  |
| `src/mlops/`                        |                      Python | Giữ phần training lifecycle |
| `airflow/dags/`                     |                      Python | Giữ nguyên                  |
| `src/prediction/`                   |                        Rust | Thay toàn bộ                |
| `src/serving/model_loader.py`       |                        Rust | Thay                        |
| `src/serving/model_warmup.py`       |                        Rust | Thay                        |
| `src/serving/prediction_service.py` |                        Rust | Thay                        |
| `src/api/routes/predictions.py`     |                        Rust | Thay                        |
| `src/api/routes/model_info.py`      |                        Rust | Thay                        |
| TomTom client và online ingestion   |                          Go | Thay                        |
| Source router, retry, budget        |                          Go | Thay                        |
| Kafka producer                      |                          Go | Thay                        |
| Live traffic API                    |                          Go | Thay                        |
| Spark Streaming consumer/ETL        |              Python/PySpark | Giữ                         |
| Streamlit dashboard                 | Tạm giữ Python, sau đó thay | Go phục vụ static frontend  |
| Nginx/Ingress                       |                         Giữ | Route trực tiếp đến Go/Rust |

Cấu trúc hiện tại cho thấy tầng inference Python nằm trong `src/prediction`, `src/serving`, `src/api`; ingestion nằm trong `src/ingestion`; Kafka producer và Spark stream processor nằm chung trong `src/streaming`. Đây chính là ranh giới nên tách.   

# 2. Kiến trúc đích

```text
                           ┌─────────────────────────┐
                           │     Python/PySpark      │
                           │ ETL / Train / Evaluate  │
                           └────────────┬────────────┘
                                        │
                              export inference model
                                        │
                               ONNX hoặc Tree Model
                                        │
                                        ▼
┌──────────────┐               ┌─────────────────────┐
│ Browser / UI │──────────────▶│ Rust Prediction API │
└──────┬───────┘               │ model in memory     │
       │                       └─────────────────────┘
       │
       │                       ┌─────────────────────┐
       └──────────────────────▶│ Go Live Traffic API │
                               │ latest-state cache  │
                               └──────────┬──────────┘
                                          │
                                       Redis
                                          ▲
                                          │
TomTom API ──▶ Go Collector ──▶ Kafka ────┴────▶ PySpark Streaming
                                │                       │
                                │                       ▼
                                └────────────────────▶ HDFS/Parquet
```

Ingress route trực tiếp:

```text
/v1/predictions/*   → Rust
/v1/model/*         → Rust
/v1/traffic/live/*  → Go
/dashboard/*        → static frontend
```

Không nên đặt Go gateway trước Rust cho mọi prediction, vì sẽ tạo thêm một network hop không cần thiết.

Axum/Tokio là stack phù hợp để triển khai HTTP bất đồng bộ trong Rust; phía Go có thể dùng chuẩn `net/http`, còn Kafka producer/consumer có thể dùng `franz-go`. ([GitHub][1])

---

# Phase H0 — Audit, dọn repository và đo baseline

## Mục tiêu

Không rewrite khi chưa biết hệ thống hiện tại nhanh/chậm ở đâu.

## Task cho Gemini

1. Đọc nội dung thật của:

   * `src/api`;
   * `src/serving`;
   * `src/prediction`;
   * `src/ingestion`;
   * `src/streaming`;
   * `src/training`.

2. Vẽ dependency graph:

   * module nào import PySpark;
   * module nào load model;
   * module nào gọi TomTom;
   * module nào ghi HDFS;
   * module nào produce/consume Kafka.

3. Đo baseline:

   * thời gian khởi động API;
   * thời gian khởi tạo Spark;
   * thời gian load model;
   * prediction batch 1, 37, 100, 1.000;
   * p50, p95, p99;
   * RAM và CPU;
   * kích thước Docker image.

4. Dọn repository:

   * xóa `venv/` khỏi Git;
   * xóa toàn bộ `__pycache__/`;
   * thêm vào `.gitignore`;
   * không để `preprocess_*.csv` trong `data/lab_raw`;
   * tách dữ liệu raw và processed rõ ràng.

Tree hiện tại đang chứa cả `venv`, nhiều thư mục `__pycache__`, đồng thời `data/lab_raw` chứa cả raw CSV và `preprocess_*.csv`; cần dọn trước khi tạo build đa ngôn ngữ. 

## Output

```text
artifacts/benchmarks/python_baseline.json
docs/language_migration_dependency_graph.md
docs/python_runtime_baseline.md
```

## Acceptance criteria

* Có số đo thật, không tự tạo số.
* Xác định chính xác request path hiện tại.
* Không thay code nghiệp vụ trong phase này.
* Repository không còn track `venv` và cache Python.

---

# Phase H1 — Tạo shared contracts

## Mục tiêu

Python, Go và Rust hiểu dữ liệu giống nhau.

## Cấu trúc mới

```text
contracts/
├── traffic_event.proto
├── prediction.openapi.yaml
├── feature_contract.json
├── model_manifest.schema.json
├── source_resolution.schema.json
└── examples/
    ├── traffic_event.json
    ├── prediction_request.json
    └── prediction_response.json
```

## Task

Định nghĩa các contract:

### Traffic event

```text
event_id
event_time
ingested_at
location_id
location_name
district
latitude
longitude
current_speed
free_flow_speed
confidence
source
batch_id
schema_version
```

### Prediction feature contract

```text
feature order
feature data type
timezone
day-of-week mapping
weekend mapping
null policy
prediction clamp
output unit
```

### Model manifest

```text
model_version
training_run_id
spark_model_checksum
inference_model_checksum
feature_contract_version
model_format
created_at
metrics
minimum_runtime_version
```

## Quy tắc

* External HTTP dùng JSON.
* Kafka dùng Protobuf hoặc Avro.
* HDFS dùng Parquet.
* Không gửi CSV qua Kafka.
* Rust ban đầu phải dùng `f64`, vì Spark ML dùng giá trị số double; chỉ đổi sang `f32` sau khi parity test đạt.

## Acceptance criteria

* Go, Rust và Python đều đọc được cùng contract.
* Feature order không được hard-code ở ba nơi khác nhau.
* Có schema version.
* Có compatibility tests.

---

# Phase H2 — Python model export pipeline

## Mục tiêu

Training vẫn hoàn toàn bằng Python/PySpark, nhưng tạo model để Rust inference.

## Task

1. Load `PipelineModel` hiện tại.
2. Xác định:

   * `VectorAssembler`;
   * feature order;
   * GBT tree count;
   * tree weights;
   * thresholds;
   * leaf values;
   * Spark version.
3. Sinh golden dataset tối thiểu 1.000 dòng.
4. Mỗi dòng lưu:

   * input business fields;
   * ordered feature vector;
   * Spark prediction;
   * model checksum.
5. Thử hai định dạng:

   * ONNX `TreeEnsembleRegressor`;
   * custom versioned tree model.
6. Chạy prediction bằng Python độc lập với Spark.
7. So sánh với Spark.

## File mới

```text
src/export/
├── inspect_spark_pipeline.py
├── export_feature_contract.py
├── export_gbt_onnx.py
├── export_gbt_tree_model.py
├── validate_exported_model.py
└── generate_golden_dataset.py

artifacts/inference/
├── candidate-onnx/
│   ├── model.onnx
│   └── manifest.json
├── candidate-tree/
│   ├── model.json
│   └── manifest.json
└── golden/
    └── golden_predictions.jsonl
```

## Quyết định định dạng

Không được mặc định ONNX chắc chắn tốt nhất. ONNX Runtime có API Rust ở mức community, nên phải kiểm tra build, deployment, parity và latency trước khi chọn. ([ONNX Runtime][2])

## Acceptance criteria

* Spark model vẫn được giữ nguyên.
* Export không thay đổi training.
* `max_absolute_error` đạt ngưỡng đã đặt.
* Model có checksum.
* Golden dataset chứa đủ precision.
* Export lỗi phải làm pipeline fail.

---

# Phase H3 — Rust inference engine bake-off

## Mục tiêu

So sánh hai engine và giữ engine mạnh nhất.

## Cấu trúc

```text
services/rust-inference/
├── Cargo.toml
├── Cargo.lock
└── crates/
    ├── traffic-contract/
    ├── traffic-onnx-engine/
    ├── traffic-tree-engine/
    ├── traffic-inference/
    └── traffic-api/
```

## Task

### Engine A — ONNX

* Load session một lần.
* Reuse input/output buffers.
* Hỗ trợ batch tensor.
* Không tạo session cho mỗi request.

### Engine B — Native Rust tree

* Parse tree model một lần.
* Chuyển nodes sang flat arrays.
* Tránh object allocation trong vòng traversal.
* Mỗi node dùng integer index.
* Batch prediction.
* Không dùng recursion sâu; dùng iterative traversal.

### Benchmark

Đo:

```text
batch=1
batch=37
batch=100
batch=1000
single-thread
multi-thread
cold start
warm prediction
RAM
binary/image size
```

## Quy tắc chọn

```text
1. Parity phải đạt trước.
2. Sau đó chọn p95 thấp nhất.
3. Nếu gần bằng nhau, chọn model dễ vận hành và rollback hơn.
```

## Acceptance criteria

* Cả hai engine được test trên cùng golden dataset.
* Không có prediction khác Spark ngoài tolerance.
* Có benchmark thật.
* Chỉ một engine được đánh dấu `production`.
* Engine còn lại có thể giữ làm fallback, không nằm trong hot path.

---

# Phase H4 — Rust Prediction API

## Mục tiêu

Thay hoàn toàn Python inference service.

## Thay thế các file

```text
src/prediction/batch_predict.py
src/prediction/feature_builder.py
src/prediction/predictor.py

src/serving/model_loader.py
src/serving/model_warmup.py
src/serving/prediction_service.py

src/api/routes/predictions.py
src/api/routes/model_info.py
```

## Endpoint

```text
GET  /health/live
GET  /health/ready
GET  /v1/model
POST /v1/predictions
POST /v1/predictions/batch
```

## Task

* Axum + Tokio.
* Load model lúc startup.
* Readiness chỉ OK sau khi model warmup.
* Input validation.
* Batch-size limit.
* Request timeout.
* Graceful shutdown.
* Prometheus metrics.
* Structured logs.
* Request ID.
* Model hot reload an toàn.
* Atomic model swap.
* Giữ model cũ nếu model mới load lỗi.

## Quy tắc hiệu năng

* Không clone toàn bộ model.
* Không load contract cho mỗi request.
* Không tạo thread mới thủ công cho từng request.
* Không gọi Python subprocess.
* Không gọi Spark.
* Không cần Java runtime.
* Feature builder phải nằm trong Rust, không nằm ở dashboard.

## Acceptance criteria

* Runtime container không có Python, Java hoặc Spark.
* Prediction parity đạt.
* Batch prediction hoạt động.
* Mọi response chứa `model_version`.
* Model lỗi trả 503, không tạo prediction giả.
* p95 tốt hơn baseline Spark-serving một cách đo được.

---

# Phase H5 — Go TomTom Collector

## Mục tiêu

Thay online ingestion Python bằng một service Go nhẹ và bền.

## Thay thế

```text
src/ingestion/api_healthcheck.py
src/ingestion/crawl_traffic.py
src/ingestion/online_tomtom_source.py
src/ingestion/request_budget.py
src/ingestion/source_mode.py
src/ingestion/source_router.py
src/ingestion/tomtom_client.py
src/ingestion/fallback_report.py
src/streaming/kafka_producer.py
```

`offline_lab_source.py` có thể tạm giữ Python vì đây là batch import, không phải hot path.

## Cấu trúc

```text
services/go-traffic/
├── go.mod
├── go.sum
├── cmd/
│   ├── collector/
│   └── live-api/
└── internal/
    ├── config/
    ├── contract/
    ├── tomtom/
    ├── collector/
    ├── budget/
    ├── source/
    ├── kafka/
    ├── retry/
    ├── metrics/
    └── health/
```

## Task

* HTTP connection pooling.
* Context timeout.
* Bounded worker pool.
* Retry với exponential backoff và jitter.
* Không retry 401/403 liên tục.
* Circuit breaker khi TomTom lỗi diện rộng.
* Global daily request budget.
* Per-batch request budget.
* Xử lý HTTP 429.
* Event ID deterministic.
* Kafka producer có delivery acknowledgement.
* Dead-letter event.
* Không log API key.
* Auto mode và offline fallback report.

## Acceptance criteria

* Không tạo duplicate event khi retry.
* Không vượt request budget.
* Collector restart không làm mất trạng thái quan trọng.
* API key không xuất hiện trong log.
* Kafka unavailable không làm dữ liệu bị báo thành công giả.
* Có health và metrics endpoint.

---

# Phase H6 — Go Live Traffic API

## Mục tiêu

Không gọi TomTom mỗi khi người dùng mở dashboard.

```text
Go Collector
→ Kafka
→ latest-state store
→ Go Live API
```

## Thay thế

```text
src/api/routes/live_traffic.py
src/serving/live_traffic_service.py
```

Phần cache live trong `result_cache.py` cũng chuyển sang Go hoặc Redis.

## Task

* Consumer đọc topic `traffic.validated`.
* Ghi latest state theo `location_id`.
* Dùng Redis cho nhiều replica.
* Live API chỉ đọc Redis.
* Response chứa:

  * `observed_at`;
  * `source`;
  * `data_age_seconds`;
  * `current_speed`;
  * `free_flow_speed`;
  * `confidence`.
* Không trả nhãn Live nếu dữ liệu fallback offline.
* ETag hoặc conditional response.
* Cache-Control phù hợp.
* Rate limit.
* Authentication middleware.

## Endpoint

```text
GET /health/live
GET /health/ready
GET /v1/traffic/live
GET /v1/traffic/live/{location_id}
GET /v1/source/status
```

## Acceptance criteria

* Một nghìn người dùng không tạo một nghìn request TomTom.
* Go API vẫn phục vụ dữ liệu cache khi TomTom tạm lỗi.
* Hiển thị data freshness.
* Dữ liệu quá cũ phải có trạng thái `stale`.
* Không proxy prediction qua Go.

---

# Phase H7 — Tối ưu streaming boundary

## Mục tiêu

Go đảm nhận producer; Spark vẫn đảm nhận distributed processing.

## Giữ Python

```text
src/streaming/traffic_stream_processor.py
src/streaming/checkpoint_manager.py
src/processing/process_spark.py
src/processing/validate_raw_data.py
```

## Thay bằng Go

```text
src/streaming/kafka_producer.py
```

## Luồng

```text
Go collector
→ traffic.raw
→ PySpark Structured Streaming
→ traffic.validated
→ HDFS Parquet
→ Redis latest state
```

## Task

* Dùng contract có version.
* Kafka key là `location_id`.
* `event_id` dùng cho deduplication.
* Consumer checkpoint.
* Watermark cho event đến muộn.
* Quarantine topic.
* Dead-letter topic.
* Compaction job để tránh nhiều file Parquet nhỏ.
* Không ghi từng TomTom response thành một file HDFS riêng.

## Acceptance criteria

* Restart Spark không tạo duplicate output không kiểm soát.
* Event sai schema đi vào quarantine.
* Có lag metrics.
* HDFS không phát sinh hàng triệu file rất nhỏ.
* Python Spark code không phụ thuộc implementation nội bộ của Go.

---

# Phase H8 — Dashboard migration

## Giai đoạn 1

Giữ Streamlit nhưng đổi thành HTTP client:

```text
Streamlit
├── gọi Go Live API
└── gọi Rust Prediction API
```

Xóa khỏi dashboard:

```text
SparkSession
PipelineModel.load
model.transform
TomTom API key
feature engineering
```

## Giai đoạn 2 — Bản production

Thay Streamlit bằng:

```text
Go static web server
+ HTML/CSS/JavaScript frontend
+ Leaflet hoặc MapLibre
```

Go chỉ serve static files và cấu hình frontend. Browser gọi trực tiếp:

```text
/v1/traffic/live → Go
/v1/predictions  → Rust
```

## Acceptance criteria

* Dashboard không cần Python runtime.
* Dashboard không chạy Spark.
* Reload trang không trigger prediction không cần thiết.
* Map rendering thực hiện phía browser.
* API lỗi được hiển thị rõ.
* Dữ liệu live và prediction có nhãn riêng.

---

# Phase H9 — Airflow, training và model lifecycle

## Giữ nguyên Python

```text
airflow/dags/
src/training/
src/data_quality/
src/mlops/
src/processing/
```

## Pipeline mới

```text
Spark ETL
→ quality gate
→ Python/PySpark training
→ evaluation
→ export model
→ generate golden dataset
→ Rust parity test
→ publish candidate
→ canary
→ production manifest update
→ Rust hot reload
```

## Task

* Sửa `model_training_dag.py`.
* Thêm export task.
* Thêm Rust parity task.
* Không promote nếu parity fail.
* Không promote nếu metric model fail.
* Model publish phải atomic.
* Rust service phải giữ previous version.
* Airflow không build Rust trong mỗi request; chỉ trong CI/model pipeline.

## Acceptance criteria

* Training vẫn chạy bằng Python.
* Model mới không tự ghi đè model production.
* Rust response ghi đúng model version.
* Rollback không cần retrain.
* Export/parity fail thì production model không đổi.

---

# Phase H10 — Docker và Kubernetes

## Image tách riêng

```text
traffic-training-python
traffic-spark-processing
traffic-airflow
traffic-go-collector
traffic-go-live-api
traffic-rust-inference
traffic-dashboard-static
```

## Task

* Multi-stage build.
* Binary release.
* Container non-root.
* Read-only root filesystem.
* Model mount read-only.
* Config và secret mount riêng.
* Go collector chỉ một replica active hoặc có distributed lock.
* Go live API nhiều replica.
* Rust inference nhiều replica.
* HPA riêng cho Go và Rust.
* Pod disruption budget.
* Rolling update.
* Canary model/deployment.

## Ingress

```text
/v1/predictions → rust-inference
/v1/model       → rust-inference
/v1/traffic     → go-live-api
/               → dashboard
```

## Acceptance criteria

* Rust image không chứa Python/Java.
* Go image không chứa Python.
* Kill một inference pod không làm API mất hoàn toàn.
* Model volume read-only.
* Collector không bị chạy trùng polling ngoài ý muốn.

---

# Phase H11 — Observability đa ngôn ngữ

## Metrics Go

```text
tomtom_requests_total
tomtom_errors_total
tomtom_rate_limit_total
collector_batches_total
collector_events_total
kafka_produce_errors_total
live_cache_age_seconds
```

## Metrics Rust

```text
inference_requests_total
inference_duration_seconds
inference_batch_size
inference_errors_total
model_load_duration_seconds
active_model_version
model_reload_total
```

## Metrics Python

```text
training_duration_seconds
model_rmse
model_mae
model_r2
data_quality_failures_total
spark_job_duration_seconds
```

## Task

* Cùng một `trace_id`/`request_id`.
* JSON structured logging.
* Không log secrets hoặc raw API key.
* Grafana dashboard theo service.
* Alert khi model quá cũ.
* Alert khi live data stale.
* Alert khi prediction parity gate fail.

---

# Phase H12 — Shadow traffic, cutover và xóa Python serving

## Mục tiêu

Không chuyển đổi kiểu big bang.

## Shadow mode

```text
Prediction request
├── Python/Spark inference cũ
└── Rust inference mới
```

Chỉ response Rust hoặc Python cho người dùng theo cấu hình, nhưng ghi cả hai kết quả để so sánh.

## Task

1. Chạy shadow prediction.
2. So sánh:

   * absolute error;
   * p95 latency;
   * error rate;
   * memory;
   * CPU.
3. Chạy Go collector song song Python collector nhưng chỉ một bên publish production.
4. So sánh row count và field values.
5. Canary 5%.
6. Canary 25%.
7. Canary 50%.
8. Chuyển 100%.
9. Soak test ít nhất một chu kỳ vận hành đủ dài.
10. Sau khi ổn định mới xóa Python serving.

## Python được xóa sau cutover

```text
src/prediction/
src/serving/model_loader.py
src/serving/model_warmup.py
src/serving/prediction_service.py
src/serving/live_traffic_service.py
src/api/routes/predictions.py
src/api/routes/model_info.py
src/api/routes/live_traffic.py
```

## Python tuyệt đối không xóa

```text
src/training/
src/processing/
src/data_quality/
src/mlops/
airflow/
```

---

# Thứ tự ưu tiên

```text
1. H0  Baseline
2. H1  Contracts
3. H2  Python model exporter
4. H3  Rust engine bake-off
5. H4  Rust prediction API
6. H5  Go collector
7. H6  Go live API
8. H7  Kafka/Spark boundary
9. H9  Model lifecycle
10. H10 Deployment
11. H11 Observability
12. H12 Cutover
13. H8  Thay dashboard cuối cùng
```

Rust inference đem lại cải thiện lớn nhất vì loại JVM và Spark khỏi serving path. Go collector/live API là bước tiếp theo. Dashboard nên làm cuối vì việc thay Streamlit không cải thiện chất lượng model hay ingestion.

# Prompt tổng cho Gemini

```text
Project hiện tại đã hoàn thành bằng Python/PySpark.

Mục tiêu:
- Giữ Python/PySpark cho Spark ETL, data quality, training,
  model evaluation, Airflow và MLOps training lifecycle.
- Thay online ingestion, TomTom client, Kafka producer và live traffic API bằng Go.
- Thay feature building, model loading, model inference,
  prediction API và model hot reload bằng Rust.
- Cuối cùng loại Python khỏi runtime serving path.
- Không thay đổi thuật toán hoặc training output nếu chưa có parity test.

Quy tắc bắt buộc:

1. Không thực hiện big-bang rewrite.
2. Thực hiện lần lượt Phase H0 đến H12.
3. Không làm phase tiếp theo khi acceptance criteria chưa đạt.
4. Đọc code hiện tại trước khi quyết định file nào bị thay.
5. Không suy đoán feature order.
6. Training luôn bằng Python/PySpark.
7. Tạo golden dataset từ Spark model thật.
8. Benchmark ONNX và native Rust tree engine.
9. Chỉ chọn engine sau khi đạt parity và có benchmark thật.
10. Không tạo số liệu benchmark giả.
11. Rust inference không được gọi Python subprocess hoặc Spark.
12. Go collector không ghi từng event thành file HDFS nhỏ.
13. Online event đi qua Kafka; Spark ghi HDFS/Parquet.
14. Không gọi TomTom theo từng dashboard request.
15. Không log API key.
16. External API dùng JSON; Kafka dùng versioned binary contract;
    storage dùng Parquet.
17. Mỗi model và contract phải có version và checksum.
18. Mỗi phase phải trả về:
    - dependency analysis;
    - tree file thay đổi;
    - nội dung đầy đủ file mới;
    - diff file cũ;
    - lệnh build;
    - lệnh test;
    - benchmark;
    - acceptance criteria đạt/chưa đạt;
    - rollback plan.

Hãy bắt đầu chỉ với Phase H0:
- audit code thật;
- dựng dependency graph;
- dọn venv và __pycache__;
- tách raw/preprocessed data;
- đo baseline Python/Spark serving;
- chưa viết Go;
- chưa viết Rust;
- chưa thay đổi nghiệp vụ.
```

Kiến trúc cuối cùng đạt mục tiêu: **Python chỉ xuất hiện trong data pipeline và training; Go xử lý mạng, ingestion và live state; Rust chạy model với độ trễ thấp nhất; Spark/JVM hoàn toàn biến mất khỏi request-serving path.**

[1]: https://github.com/tokio-rs/axum?utm_source=chatgpt.com "GitHub - tokio-rs/axum: HTTP routing and request-handling library for Rust that focuses on ergonomics and modularity · GitHub"
[2]: https://onnxruntime.ai/docs/api/?utm_source=chatgpt.com "API Docs | onnxruntime"
