# God View — Serving, Dashboard & Observability
# Luồng: API Request → Model Inference → Dashboard → Metrics → Alerts

---

## 1. Decoupled Prediction API Architecture

```text
[Client / Streamlit Dashboard]
         │  HTTP POST /v1/predictions
         │  GET /health/live, /health/ready
         │  GET /v1/model, /v1/traffic/live
         ▼
[Nginx Ingress / Load Balancer]
         │
         ▼
[FastAPI Server — src/api/main.py]
  3 replicas in production (topologySpreadConstraints)
         │
  Middlewares:
    ├── RequestIDMiddleware — injects X-Request-ID UUID into every request/response
    └── CORSMiddleware

  Routes:
    ├── GET  /health/live         → 200 OK (liveness probe)
    ├── GET  /health/ready        → model_loaded: true/false (readiness probe)
    ├── GET  /v1/model            → version, RMSE, R², loaded_at
    ├── GET  /v1/traffic/live     → real-time observations
    └── POST /v1/predictions      → PredictionService → speed_kmh, congestion_level
```

---

## 2. Model Loading (Singleton Pattern)

```text
FastAPI startup (lifespan)
        │
        ▼
ModelLoader.load_model()   — singleton, loaded ONCE into RAM
  ├── Reads artifacts/metrics/metrics.json
  ├── Loads TrafficPredictor (GBTRegressor PySpark model)
  │     OR falls back to FallbackPredictor (heuristic)
  └── model_warmup.warmup_model()
        → dummy prediction to eliminate JVM cold-start latency
        → first real user request has no cold-start penalty

ModelLoader._instance is shared across all API workers.
```

---

## 3. Prediction Request Flow

```text
POST /v1/predictions { street_name, hour, is_weekend }
         │
         ▼
PredictionService (src/serving/prediction_service.py)
  ├── Build cache key: SHA(street_name, hour, is_weekend)
  ├── ResultCache.get(key)
  │     HIT  → return cached result immediately (TTL=300s)
  │     MISS → continue
  ├── Feature engineering:
  │     congestion_ratio = lookup from live observations
  │     Assemble feature vector for model
  ├── ModelLoader.model.predict(features)
  │     → predicted_speed_kmh
  ├── congestion_level:
  │     THÔNG THOÁNG / CHẬM / ĐÔNG ĐÚC / TẮC ĐƯỜNG
  ├── ResultCache.set(key, result, ttl=300s)
  └── Return PredictionResponse:
        { street_name, hour, is_weekend, predicted_speed_kmh,
          congestion_level, model_version, data_source, prediction_time }

ResultCache: in-memory LRU + TTL (src/serving/result_cache.py)
  Reduces redundant inference for repeated requests (same street+hour).
```

---

## 4. Batch Prediction Layer

```text
Processed HDFS Parquet
        │
        ▼
TrafficPredictor (src/prediction/predictor.py)
  ├── Load GBTRegressor model from HDFS (PipelineModel.load)
  ├── predict_batch(df) → SparkDataFrame with predictions
  └── Save predictions → artifacts/predictions/

PredictionFormatter (src/prediction/prediction_formatter.py)
  → formats rows into { location_id, predicted_speed, congestion_level }

Used by: Airflow batch_prediction_dag (daily)
```

---

## 5. Streamlit Dashboard & Interactive Map

```text
Streamlit app (src/dashboard/)
        │
        ├── map_builder.py — Folium map, colored markers by congestion
        ├── dashboard_service.py — get_realtime_traffic(), get_model_metrics()
        │     ├── Calls FastAPI /v1/traffic/live (real-time observations)
        │     ├── Calls FastAPI /v1/model (model info)
        │     └── Falls back to HDFS predictions if API offline
        ├── ui_components.py — KPI cards, metric gauges, sidebar filters
        └── visualization.py — Plotly charts, heatmaps, time-series

Dashboard sections:
  1. Live Traffic Map (Folium + colored markers)
  2. Hourly Speed Patterns (Plotly line chart)
  3. Congestion KPI Cards (peak hour, avg speed, worst street)
  4. Model Info Card (version, RMSE, R², loaded_at)
  5. Data Source Badge (LIVE / OFFLINE SNAPSHOT)
```

---

## 6. End-to-End Orchestrated Pipeline (Airflow)

```text
Airflow DAGs (airflow/dags/)
  ├── traffic_ingestion_dag    (every 30 min) — SourceRouter → HDFS raw
  ├── traffic_etl_dag          (hourly)       — Spark ETL → HDFS processed
  ├── model_training_dag       (weekly)       — Train → Validate → Register
  └── model_monitoring_dag     (daily)        — DriftDetector → RetrainingPolicy

Each DAG task:
  ├── Acquires JobLock (distributed file lock at artifacts/locks/)
  ├── Executes operator (PythonOperator / BashOperator)
  ├── Updates PipelineStateTracker
  └── Calls notify_job_failure() on error → Slack/Email

Race condition prevention:
  JobLock ensures no 2 DAGs concurrently write to same HDFS partition
  or promote models simultaneously.
```

---

## 7. Observability: Metrics, Tracing & Logging

```text
Every API request:
  ├── RequestIDMiddleware → X-Request-ID (UUID) propagated through all logs
  ├── TracingManager (src/observability/tracing.py) → ContextVar request_id
  └── JSONStructuredLogFormatter → { timestamp, level, request_id, message }
        ⚠ Secrets are auto-masked before emission (key=***MASKED***)

Prometheus MetricsRegistry (src/observability/metrics.py):
  Counters:
    tomtom_requests_total, tomtom_request_errors_total
    ingested_rows_total, invalid_rows_total
    api_http_requests_total, prediction_errors_total
  Histograms:
    prediction_latency_seconds  (p95 target < 1.0s)
    spark_job_duration_seconds
  Gauges:
    model_rmse, model_data_age_seconds, hdfs_capacity_usage

Alert Rules (monitoring/prometheus/rules/):
  infrastructure.yml  → HDFS > 85%, API latency p95 > 1s
  pipeline.yml        → TomTom errors spike, data stale > 3600s
  model.yml           → RMSE > 12.0 km/h sustained 15m

Alertmanager → Email / Slack
Grafana → traffic_system_dashboard.json
  Panels: ingested rows, p95 latency timeseries, RMSE gauge
```

---

## 8. Security in the Serving Layer

```text
SecretProvider (src/security/secret_provider.py)
  Hierarchy: /run/secrets/<name> → env var → default
  Masks raw secret strings in all log output.

Authentication (src/security/authentication.py)
  Bearer token validation for API endpoints.

Rate Limiter (src/security/rate_limiter.py)
  Sliding window algorithm: max 100 req/s per client IP.
  Nginx Ingress annotation: nginx.ingress.kubernetes.io/limit-rps: "100"

RBAC (src/security/authorization.py)
  Roles: viewer, analyst, admin
  Route permission map enforced per endpoint.
```
