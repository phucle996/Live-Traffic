# God View — Data Flow
# Luồng: Infrastructure → Data Sources → Ingestion → Streaming → ETL → Data Quality & Governance

---

## 1. Infrastructure & Distributed Storage Topology

```text
docker-compose.yml
  ├── namenode       (HDFS NameNode — fs.defaultFS=hdfs://namenode:9000)
  ├── datanode       (HDFS DataNode — replication=1 locally, 3 in prod)
  ├── spark-master   (Spark Master — spark://spark-master:7077)
  ├── spark-worker   (Spark Worker)
  ├── kafka          (confluentinc/cp-kafka:7.5.0 — port 9092)
  ├── zookeeper      (confluentinc/cp-zookeeper:7.5.0)
  └── streamlit      (Dashboard + API — port 8501)
```

- **HDFS** stores all raw, processed, and model artifact data.
- **Spark** runs ETL, training, and batch prediction as distributed jobs.
- **Kafka + ZooKeeper** provide real-time streaming buffer.
- All services communicate via Docker internal DNS — no hardcoded IPs.

**Production extension (Phase 20)**: Kubernetes multi-node cluster; HDFS HA with Active + Standby NameNode, 3 JournalNodes, 3 ZooKeeper (ZKFC automatic failover).

---

## 2. Data Source Routing & Fallback

```text
User / Airflow invokes ingestion
            │
            ▼
     SourceRouter.resolve(mode)
            │
    ┌───────┴───────────┐
    │                   │
  "offline"           "online"
    │                   │
OfflineLab          ApiHealthCheck
CsvSource           ─── passes? ──► OnlineTomTomSource
    │                         FAIL → fallback to offline
    ▼                               FallbackReporter logs
  DataNormalizer                    badge: OFFLINE SNAPSHOT
    ▼
Unified Raw Schema (14 fields)
```

**DataSourceMode enum**: `offline | online | auto`
- `auto`: tries online → falls back to offline transparently if API fails or budget exceeded.
- `RequestBudgetGuard`: enforces `ONLINE_REQUEST_BUDGET_PER_DAY` daily API call cap.
- `FallbackReporter`: writes status badge and report markdown when fallback occurs.
- API key is **always masked** (`***MASKED***`) in logs.

**Source files**:
- `src/ingestion/source_router.py` — SourceRouter, DataSourceMode
- `src/ingestion/online_tomtom_source.py` — TomTom API crawler
- `src/ingestion/request_budget.py` — RequestBudgetGuard
- `src/ingestion/api_healthcheck.py` — ApiHealthCheck
- `src/ingestion/fallback_report.py` — FallbackReporter

---

## 3. Unified Data Contract (Schema)

All ingestion sources (offline CSV + online TomTom) normalize to identical schema before writing to HDFS:

| Field | Type | Description |
|---|---|---|
| `location_id` | StringType | Unique location identifier |
| `street_name` | StringType | Street name (Vietnamese) |
| `latitude` | DoubleType | GPS latitude |
| `longitude` | DoubleType | GPS longitude |
| `speed_kmh` | DoubleType | Current speed (km/h) |
| `free_flow_speed` | DoubleType | Free-flow speed baseline |
| `current_travel_time` | IntegerType | Current travel time (seconds) |
| `free_flow_travel_time` | IntegerType | Free-flow travel time (seconds) |
| `confidence` | DoubleType | TomTom confidence score |
| `road_closure` | BooleanType | Road closure flag |
| `timestamp` | TimestampType | Observation UTC timestamp |
| `source` | StringType | `"online"` / `"offline"` |
| `partition_date` | StringType | `YYYY-MM-DD` partition key |
| `partition_hour` | IntegerType | Hour partition (0–23) |

Schema enforced by: `src/common/schema.py`, `src/streaming/stream_schema.py`, `src/data_quality/schema_registry.py`.

**HDFS output path**: `hdfs://namenode:9000/data/traffic/raw/date=YYYY-MM-DD/hour=HH/`

---

## 4. Offline Lab CSV Ingestion

```text
data/lab_raw/*.csv
       │
       ▼
OfflineLabCsvSource.ingest()
       ├── SHA-256 checksum idempotency check (skip if already written)
       ├── DataNormalizer.normalize() → Unified Raw Schema
       ├── SparkSession.write.parquet() → HDFS partitioned
       └── FileManifest.record()  → artifacts/ingestion_manifest.json
```

**Idempotency**: SHA-256 of each CSV file stored in manifest; re-runs skip duplicate files.
**Source files**: `src/ingestion/offline_lab_source.py`, `src/common/data_normalizer.py`

---

## 5. Online TomTom Real-Time Ingestion

```text
TomTom Flow Segment Data API
  37 Ho Chi Minh City target locations
       │
       ▼
RequestBudgetGuard (daily cap enforcement)
       │
OnlineTomTomSource.fetch_all_locations()
  ├── Retry: exponential backoff (max 3 retries, 429/5xx)
  ├── API key injected from SecretProvider (never CLI/log)
  ├── DataNormalizer.normalize() → Unified Raw Schema
  └── SparkSession.write.parquet() → HDFS hourly partition

Modes:
  --once   → single crawl and exit
  --daemon → polling every POLLING_INTERVAL_MINUTES (default: 30m)
```

**Source files**: `src/ingestion/online_tomtom_source.py`, `scripts/run_online_ingestion.sh`

---

## 6. Real-Time Streaming (Kafka Buffer)

```text
[TomTom API / Live Events]
         │
         ▼
KafkaProducer (src/streaming/kafka_producer.py)
  ├── Idempotent producer (enable.idempotence=true)
  ├── UUID event_id injected per message (deduplication)
  └── Topic: traffic.realtime.raw (3 partitions, replication=3)
         │
         ▼
Spark Structured Streaming Consumer
  (src/streaming/traffic_stream_processor.py)
  ├── CheckpointManager: HDFS offset checkpoints
  ├── Stream schema validation
  ├── DeadLetterHandler: invalid messages → traffic.dead_letter topic
  └── micro-batch write → HDFS partitioned Parquet

Kafka config:
  config/kafka/producer.properties — idempotent, acks=all
  config/kafka/consumer.properties — auto.offset.reset=earliest
  config/kafka/topics.yaml         — topic definitions
```

**Race condition guard**: CheckpointManager stores HDFS offsets atomically — consumer restart always resumes from last committed offset, no event loss.

---

## 7. Spark ETL Processing

```text
HDFS raw Parquet
     │
     ▼
SparkSession (src/common/spark_session.py)
     │
process_spark.py (src/processing/)
  ├── Load raw Parquet from HDFS
  ├── Feature engineering:
  │     hour = hour(timestamp)
  │     day_of_week = dayofweek(timestamp)
  │     is_weekend = (day_of_week ∈ {1, 7})
  │     congestion_ratio = speed_kmh / free_flow_speed
  ├── Drop nulls + outliers (speed > 0, speed < 150)
  └── Write processed Parquet → HDFS
        hdfs://namenode:9000/data/traffic/processed/
```

**Output schema**: Processed features table with `speed_kmh`, `hour`, `is_weekend`, `congestion_ratio`, `street_name`, `latitude`, `longitude`.

---

## 8. Data Quality, Schema Registry & Governance

```text
Raw Parquet                          Processed Parquet
     │                                      │
     ▼                                      ▼
QualityRunner                         QualityRunner
  ├── ExpectationRules                  ├── ExpectationRules
  │   (config/data_quality/             │   (config/data_quality/
  │    raw_expectations.yaml)           │    processed_expectations.yaml)
  ├── SchemaRegistry                    ├── AnomalyDetector
  │   Contract v1.0 validation          │   Z-score threshold = 2.0
  ├── AnomalyDetector (Z-score)         └── LineageWriter
  └── Quarantine if FAIL                     records lineage graph
        → HDFS/quarantine/

Schema versioning: v1.0 → v1.1 (additive only, no breaking changes)
Lineage graph: stored at artifacts/lineage/lineage_graph.json
```

**Source files**: `src/data_quality/quality_runner.py`, `schema_registry.py`, `anomaly_detector.py`, `lineage_writer.py`, `expectations.py`
