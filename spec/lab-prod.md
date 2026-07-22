Đúng, sau 11 phase hiện tại hệ thống mới đạt mức **MVP/Lab end-to-end**. Để gọi là production thực sự, cần bổ sung các phase vận hành, bảo mật, giám sát, triển khai và khôi phục sự cố.

Một điểm quan trọng: production không nên để Streamlit trực tiếp chịu trách nhiệm khởi tạo Spark, load model và xử lý toàn bộ request. Nên tách thành **API serving riêng**, còn Streamlit chỉ là giao diện.

# Phase 12 — Production configuration và secrets

## Mục tiêu

Tách riêng môi trường:

```text
development
staging
production
```

Bảo vệ TomTom API key, mật khẩu, certificate và thông tin kết nối.

## Task

* Tạo cấu hình riêng cho dev, staging và prod.
* Không dùng `.env` lưu secret trên server production.
* Dùng Docker Secrets, Kubernetes Secrets hoặc Vault.
* Bật HTTPS.
* Phân quyền truy cập HDFS, Spark, Airflow và dashboard.
* Không public NameNode, DataNode hoặc Spark UI ra Internet.
* Thêm authentication và authorization.
* Rotate TomTom API key.
* Chặn log in API key.
* Cấu hình rate limit.

Hadoop cũng khuyến nghị đọc và áp dụng chế độ bảo mật trước khi triển khai cluster production. ([Apache Hadoop][1])

## File cần viết

```text
config/
├── development.yaml
├── staging.yaml
└── production.yaml

deploy/
├── secrets/
│   └── README.md
└── nginx/
    ├── nginx.conf
    └── security_headers.conf

src/security/
├── authentication.py
├── authorization.py
├── secret_provider.py
└── rate_limiter.py

docs/
├── security_policy.md
└── secrets_rotation.md
```

## Kết quả cần đạt

* Không có secret trong Git.
* Production bắt buộc dùng HTTPS.
* Dashboard yêu cầu đăng nhập.
* HDFS và Spark UI không truy cập được từ Internet.
* API key có thể rotate mà không rebuild image.

---

# Phase 13 — Workflow orchestration và scheduling

## Mục tiêu

Pipeline tự chạy đúng lịch thay vì phải gọi `make pipeline` bằng tay.

## Pipeline dự kiến

```text
TomTom ingestion: mỗi 5–30 phút
Spark ETL: mỗi giờ
Data quality: sau ETL
Model training: mỗi tuần
Model evaluation: sau training
Model promotion: nếu đạt điều kiện
```

Airflow phù hợp để quản lý dependency, retry, backfill và trạng thái các job. Tài liệu Airflow cũng nhấn mạnh DAG production cần được kiểm thử như code production; với triển khai lớn, tài liệu chính thức hướng tới Kubernetes và Helm thay vì coi Docker Compose là nền tảng production cuối cùng. ([Apache Airflow][2])

## File cần viết

```text
airflow/
├── Dockerfile
├── requirements.txt
└── dags/
    ├── traffic_ingestion_dag.py
    ├── traffic_etl_dag.py
    ├── model_training_dag.py
    └── model_monitoring_dag.py

src/orchestration/
├── pipeline_state.py
├── job_lock.py
└── notifications.py

tests/airflow/
├── test_ingestion_dag.py
├── test_training_dag.py
└── test_dag_imports.py
```

## Acceptance criteria

* ETL không chạy nếu ingestion thất bại.
* Training không chạy nếu data quality fail.
* Job có retry hữu hạn.
* Có timeout.
* Có backfill.
* Chạy lại không duplicate dữ liệu.
* Không có hai training job ghi đè cùng một model.

---

# Phase 14 — Online ingestion bền vững và streaming

## Mục tiêu

Không để crawler gọi API rồi ghi trực tiếp vào HDFS theo cách dễ mất dữ liệu.

Luồng production nên là:

```text
TomTom API
    ↓
Ingestion service
    ↓
Kafka
    ↓
Spark Structured Streaming
    ↓
HDFS/Data Lake
```

Kafka đóng vai trò bộ đệm. Khi Spark hoặc HDFS tạm thời dừng, dữ liệu vẫn có thể chờ trong broker. Spark cung cấp Structured Streaming và tích hợp Kafka cho xử lý dữ liệu tăng dần theo luồng. ([Apache Spark][3])

Phase này chỉ bắt buộc khi yêu cầu near-real-time. Nếu hệ thống chỉ crawl mỗi 30 phút và chấp nhận batch, có thể triển khai sau.

## File cần viết

```text
src/streaming/
├── kafka_producer.py
├── traffic_stream_processor.py
├── stream_schema.py
├── checkpoint_manager.py
└── dead_letter_handler.py

config/kafka/
├── producer.properties
├── consumer.properties
└── topics.yaml

scripts/
├── create_kafka_topics.sh
└── run_stream_processor.sh
```

## Topic đề xuất

```text
traffic.raw
traffic.validated
traffic.invalid
traffic.dead-letter
```

## Acceptance criteria

* Có checkpoint.
* Có dead-letter queue.
* Event có `event_id`.
* Consumer xử lý idempotent.
* Không mất dữ liệu khi Spark restart.
* Có giới hạn API request.
* Có xử lý HTTP 429.
* Có thể replay dữ liệu.

---

# Phase 15 — Data quality, catalog và governance

## Mục tiêu

Biết dữ liệu đến từ đâu, chất lượng thế nào và phiên bản dataset nào đã train model.

## Task

* Data contract có version.
* Schema evolution.
* Kiểm tra dữ liệu bất thường.
* Quarantine dữ liệu lỗi.
* Theo dõi lineage:

```text
TomTom batch
→ raw partition
→ processed partition
→ training dataset
→ model version
```

* Chính sách giữ và xóa dữ liệu.
* Dataset versioning.
* Kiểm tra dữ liệu bị trùng hoặc đến trễ.
* Kiểm tra chênh lệch giữa offline Lab và TomTom live.

## File cần viết

```text
src/data_quality/
├── expectations.py
├── quality_runner.py
├── schema_registry.py
├── anomaly_detector.py
└── lineage_writer.py

config/data_quality/
├── raw_expectations.yaml
└── processed_expectations.yaml

docs/
├── data_retention_policy.md
├── schema_evolution.md
└── data_lineage.md
```

## Acceptance criteria

* Dữ liệu không đạt quality gate không được dùng để train.
* Mỗi model truy ngược được dataset đã sử dụng.
* Schema thay đổi phải được phát hiện.
* Có báo cáo chất lượng theo từng batch.
* Có chính sách dữ liệu đến muộn.

---

# Phase 16 — Production model serving API

## Mục tiêu

Tách inference khỏi Streamlit.

Kiến trúc:

```text
Browser
   ↓
Streamlit/Web frontend
   ↓ HTTP
Prediction API
   ↓
Model service
```

Không nên để mỗi người dùng mở dashboard lại tạo một SparkSession riêng.

## Công nghệ phù hợp

Có thể dùng:

```text
FastAPI
Gunicorn/Uvicorn
Redis cache
```

Model Spark có thể được load trong một prediction worker riêng. Nếu số địa điểm chỉ vài chục điểm, có thể chạy batch prediction định kỳ rồi API chỉ đọc kết quả đã tính sẵn.

## File cần viết

```text
src/api/
├── main.py
├── dependencies.py
├── schemas.py
├── routes/
│   ├── health.py
│   ├── live_traffic.py
│   ├── predictions.py
│   └── model_info.py
└── middleware/
    ├── request_id.py
    ├── authentication.py
    └── rate_limit.py

src/serving/
├── model_loader.py
├── prediction_service.py
├── live_traffic_service.py
├── result_cache.py
└── model_warmup.py

Dockerfile.api
tests/api/
```

## Endpoint dự kiến

```text
GET  /health/live
GET  /health/ready
GET  /v1/model
GET  /v1/traffic/live
POST /v1/predictions
```

## Acceptance criteria

* Có readiness và liveness endpoint.
* Model chỉ load một lần.
* Có request timeout.
* Có input validation.
* Có cache.
* Có giới hạn kích thước batch.
* API lỗi không trả prediction giả.
* Response chứa `model_version`, `data_source` và `prediction_time`.
* Streamlit chỉ gọi API, không trực tiếp train model.

---

# Phase 17 — Observability và alerting

## Mục tiêu

Biết hệ thống đang khỏe hay đã lỗi trước khi người dùng báo.

Prometheus hỗ trợ recording rules và alerting rules; Alertmanager nhận và định tuyến cảnh báo từ Prometheus. ([Prometheus][4])

## Thành phần

```text
Prometheus  → metrics
Grafana     → dashboard
Alertmanager → cảnh báo
Loki    → logs
OpenTelemetry → tracing
```

## Metrics cần theo dõi

```text
tomtom_requests_total
tomtom_request_errors_total
tomtom_rate_limit_total
ingested_rows_total
invalid_rows_total
spark_job_duration_seconds
prediction_latency_seconds
prediction_errors_total
model_rmse
model_data_age_seconds
hdfs_capacity_usage
api_http_requests_total
```

## File cần viết

```text
monitoring/
├── prometheus/
│   ├── prometheus.yml
│   └── rules/
│       ├── infrastructure.yml
│       ├── pipeline.yml
│       └── model.yml
├── alertmanager/
│   └── alertmanager.yml
└── grafana/
    ├── datasources/
    └── dashboards/

src/observability/
├── metrics.py
├── tracing.py
└── structured_logging.py
```

## Alert quan trọng

```text
TomTom API lỗi liên tục
Không có dữ liệu mới
ETL thất bại
HDFS gần đầy
API prediction lỗi cao
Prediction latency tăng
Model quá cũ
Data drift vượt ngưỡng
```

## Acceptance criteria

* Mỗi request có `request_id`.
* Log ở dạng JSON.
* Có dashboard hệ thống.
* Có cảnh báo khi dữ liệu live quá cũ.
* Có cảnh báo khi pipeline fail.
* Không gửi API key vào log hoặc tracing.

---

# Phase 18 — MLOps và model lifecycle

## Mục tiêu

Không ghi đè model mới lên model đang chạy mà không kiểm chứng.

MLflow Model Registry cung cấp UI và API để quản lý phiên bản và vòng đời model. ([MLflow AI Platform][5])

## Luồng model

```text
Training run
    ↓
Candidate model
    ↓
Offline validation
    ↓
Staging
    ↓
Canary/Shadow test
    ↓
Production
```

## Task

* Experiment tracking.
* Model registry.
* Versioning.
* Feature metadata.
* Dataset lineage.
* Approval gate.
* Champion/challenger.
* Rollback.
* Data drift.
* Prediction drift.
* Retraining policy.

## File cần viết

```text
src/mlops/
├── experiment_tracker.py
├── model_registry.py
├── model_validator.py
├── model_promoter.py
├── drift_detector.py
├── rollback.py
└── retraining_policy.py

config/mlops/
├── promotion_rules.yaml
└── drift_thresholds.yaml

tests/mlops/
```

## Promotion rule ví dụ

```yaml
candidate:
  maximum_rmse: 8.0
  minimum_r2: 0.60
  minimum_test_rows: 1000
  require_no_schema_change: true
```

Không nên chỉ yêu cầu model mới tốt hơn model cũ trên một metric duy nhất.

## Acceptance criteria

* Model đang production không bị ghi đè.
* Có thể rollback.
* Mỗi prediction ghi model version.
* Model candidate không tự động lên production nếu quality gate fail.
* Có cảnh báo drift.
* Có lịch retrain nhưng không bắt buộc promote.

---

# Phase 19 — CI/CD và software supply chain

## Mục tiêu

Mọi thay đổi code phải được test, build và kiểm tra trước khi deploy.

## Pipeline

```text
Pull request
→ lint
→ unit test
→ integration test
→ security scan
→ build image
→ push registry
→ deploy staging
→ smoke test
→ approval
→ production
```

## File cần viết

```text
.github/workflows/
├── ci.yml
├── build-images.yml
├── deploy-staging.yml
└── deploy-production.yml

deploy/
├── helm/
└── environments/

scripts/
├── smoke_test.sh
├── rollback_deployment.sh
└── generate_sbom.sh
```

## Acceptance criteria

* Docker image dùng tag bất biến, ví dụ Git SHA.
* Không deploy bằng tag `latest`.
* Test fail thì không build production.
* Staging smoke test fail thì không promote.
* Có vulnerability scan.
* Có rollback deployment.
* Migration và cấu hình được version hóa.

---

# Phase 20 — High availability và scaling

## Mục tiêu

Một container hoặc một máy hỏng không làm toàn bộ hệ thống ngừng.

Kubernetes cung cấp cơ chế quản lý vòng đời container và triển khai nhiều replica; tài liệu production của Kubernetes nhấn mạnh cần xem xét storage, authentication, networking và mức độ quản trị cluster. ([Kubernetes][6])

HDFS production nên loại bỏ điểm lỗi đơn tại NameNode bằng High Availability. Hadoop hỗ trợ mô hình HA với các NameNode và Quorum Journal Manager. ([Apache Hadoop][7])

## Task

* Chuyển workload production sang Kubernetes hoặc nền tảng managed.
* API có nhiều replica.
* Ingress/load balancer.
* Pod disruption budget.
* Resource request và limit.
* Horizontal autoscaling.
* HDFS HA:

  * Active NameNode;
  * Standby NameNode;
  * JournalNodes;
  * ZooKeeper failover controller.
* Nhiều DataNode.
* Nhiều Spark Worker.
* Persistent volumes.

## File cần viết

```text
deploy/kubernetes/
├── namespace.yaml
├── api-deployment.yaml
├── api-service.yaml
├── dashboard-deployment.yaml
├── ingress.yaml
├── hpa.yaml
├── pdb.yaml
├── network-policy.yaml
├── configmap.yaml
└── service-account.yaml

deploy/helm/traffic-platform/
```

## Acceptance criteria

* Xóa một API pod nhưng hệ thống vẫn phục vụ.
* Restart worker không mất dữ liệu.
* Có rolling update.
* Có rollback.
* Không có IP hard-code.
* NameNode không còn là single point of failure.
* Production data nằm trên persistent storage.

---

# Phase 21 — Backup và disaster recovery

## Mục tiêu

Khôi phục được hệ thống khi mất cluster, mất ổ đĩa hoặc triển khai lỗi.

## Phải backup

```text
HDFS metadata
Raw data quan trọng
Processed data cần giữ
MLflow database
Model artifacts
Airflow metadata database
Application configuration
Grafana dashboards
```

## File cần viết

```text
scripts/backup/
├── backup_hdfs_metadata.sh
├── backup_models.sh
├── backup_databases.sh
└── verify_backup.sh

scripts/restore/
├── restore_hdfs.sh
├── restore_mlflow.sh
└── restore_airflow.sh

docs/
├── disaster_recovery.md
├── backup_policy.md
└── restore_runbook.md
```

## Phải xác định

```text
RPO: chấp nhận mất tối đa bao nhiêu dữ liệu
RTO: hệ thống được phép ngừng bao lâu
```

## Acceptance criteria

* Backup được lưu ngoài cluster chính.
* Backup được mã hóa.
* Có retention.
* Có restore test định kỳ.
* Không chỉ kiểm tra “file backup tồn tại”; phải thực sự restore thử.
* Có hướng dẫn khôi phục từng thành phần.

---

# Phase 22 — Performance, resilience và load testing

## Mục tiêu

Biết hệ thống chịu được bao nhiêu tải và phản ứng thế nào khi thành phần bị lỗi.

## Task

* Load test Prediction API.
* Benchmark ETL.
* Benchmark training.
* Stress test dashboard.
* Test mất TomTom API.
* Test Kafka unavailable.
* Test HDFS unavailable.
* Test model corrupted.
* Test API pod restart.
* Test dữ liệu tăng gấp nhiều lần.
* Tuning partition và Spark executor.

## File cần viết

```text
tests/performance/
├── locustfile.py
├── k6_prediction.js
├── spark_benchmark.py
└── ingestion_benchmark.py

tests/resilience/
├── test_tomtom_outage.py
├── test_hdfs_failure.py
├── test_model_failure.py
└── test_duplicate_events.py

docs/
└── capacity_plan.md
```

## Acceptance criteria ví dụ

```text
Prediction API p95 < 1 giây
Error rate < 1%
Không mất event khi consumer restart
ETL hoàn thành trước batch kế tiếp
Dashboard không trực tiếp gây Spark job cho mỗi lần reload
```

Ngưỡng thật phải được xác định theo hạ tầng và yêu cầu nghiệp vụ, không nên viết cứng trước khi benchmark.

---

# Phase 23 — Operational readiness

## Mục tiêu

Đội vận hành biết phải làm gì khi hệ thống lỗi.

## File cần viết

```text
docs/runbooks/
├── tomtom_api_failure.md
├── no_new_data.md
├── hdfs_full.md
├── spark_job_failure.md
├── model_rollback.md
├── high_prediction_latency.md
└── security_incident.md

docs/
├── release_checklist.md
├── incident_response.md
├── on_call_guide.md
└── production_readiness_review.md
```

## Acceptance criteria

* Mỗi alert có liên kết tới runbook.
* Có người/nhóm chịu trách nhiệm từng service.
* Có severity level.
* Có quy trình rollback.
* Có postmortem template.
* Có maintenance window.
* Có production launch checklist.

# Mốc nào mới được gọi là production?

| Mức                                    | Phase cần có       |
| -------------------------------------- | ------------------ |
| Lab hoàn chỉnh                         | 0–11               |
| Production-lite trên một server nội bộ | 0–13, 16–19, 21–23 |
| Production có dữ liệu live ổn định     | Thêm 14–15         |
| Production ML có retraining            | Thêm 18            |
| Production HA nhiều máy                | Thêm 20            |
| Near-real-time quy mô lớn              | Bắt buộc 14 và 20  |

## Thứ tự nên triển khai

Không cần làm tất cả cùng lúc. Thứ tự thực tế nên là:

```text
12. Security/config
13. Orchestration
16. Serving API
17. Monitoring
19. CI/CD
21. Backup/restore
22. Load/resilience test
23. Operational readiness
15. Data governance
18. MLOps
20. High availability
14. Streaming nếu thật sự cần
```

**Điểm đạt production tối thiểu** là khi hệ thống có API serving tách biệt, secret management, scheduler, monitoring/alerting, CI/CD, backup/restore, load test và runbook. Kafka, Kubernetes, MLflow và HDFS HA là các phần tiếp theo tùy theo yêu cầu thời gian thực, quy mô và mức độ sẵn sàng cần đạt.

[1]: https://hadoop.apache.org/docs/stable/?utm_source=chatgpt.com "Apache Hadoop 3.3.5 - Apache Software Foundation"
[2]: https://airflow.apache.org/docs/apache-airflow/2.5.1/best-practices.html?utm_source=chatgpt.com "Best Practices — Airflow Documentation"
[3]: https://spark.apache.org/docs/latest/structured-streaming-programming-guide.html?utm_source=chatgpt.com "Structured Streaming Programming Guide"
[4]: https://prometheus.io/docs/alerting/latest/overview/?utm_source=chatgpt.com "Alerting overview | Prometheus"
[5]: https://mlflow.org/docs/latest/ml/model-registry/?utm_source=chatgpt.com "ML Model Registry | MLflow AI Platform"
[6]: https://kubernetes.io/docs/setup/production-environment/?utm_source=chatgpt.com "Production environment | Kubernetes"
[7]: https://hadoop.apache.org/docs/stable/hadoop-project-dist/hadoop-hdfs/HDFSHighAvailabilityWithQJM.html?utm_source=chatgpt.com "HDFS High Availability Using the Quorum Journal Manager"
