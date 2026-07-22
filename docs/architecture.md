# System Architecture & Technical Specification — Lab 5 Urban Traffic Prediction

This document details the end-to-end system architecture, data flow topology, 12-Factor Cloud-Native design, High Availability (HA) considerations, and storage durability.

---

## 1. End-to-End System Topology

```text
+-----------------------+      +-----------------------+
|  TomTom Traffic API   |      | Local Seed CSVs       |
|  (Live Crawling)      |      | (Offline Fallback)    |
+-----------+-----------+      +-----------+-----------+
            |                              |
            +--------------+---------------+
                           |
                           v
             +---------------------------+
             | Ingestion Engine          |
             | (src/ingestion/)          |
             +-------------+-------------+
                           |
                           v
             +---------------------------+
             | HDFS Raw Storage          |
             | /traffic_project/raw/     |
             +-------------+-------------+
                           |
                           v
             +---------------------------+
             | Apache Spark ETL Engine   |
             | (src/processing/)         |
             +-------------+-------------+
                           |
                           v
             +---------------------------+
             | HDFS Processed Parquet    |
             | /traffic_project/processed|
             +-------------+-------------+
                           |
                           v
             +---------------------------+
             | Spark MLlib GBTRegressor  |
             | (src/training/)           |
             +-------------+-------------+
                           |
                           v
             +---------------------------+
             | Serving Layer Predictor   |
             | (src/prediction/)         |
             +-------------+-------------+
                           |
                           v
             +---------------------------+
             | Streamlit + Folium App    |
             | (src/dashboard/app.py)    |
             +---------------------------+
```

---

## 2. Core Architectural Pillars

### 2.1 12-Factor Cloud Native Design
1. **I. Codebase**: One repository tracked in Git with modular Python packages under `src/`.
2. **III. Config**: Strict separation of config from code via `.env` and `config/application.yaml`. Secrets (`TOMTOM_API_KEY`) injected via environment variables.
3. **XI. Logs**: All log output streamed to `stdout`/`stderr` with structured formatting (Console & JSON loggers).

### 2.2 High Availability (HA) & Data Durability
- **NameNode & DataNode Durability**: Docker named volumes (`namenode_data`, `datanode_data`) ensure HDFS metadata and data blocks persist across container restarts.
- **Safemode Race Condition Safeguard**: `scripts/wait_for_hdfs.sh` polls NameNode status (`hdfs dfsadmin -safemode get`) until `Safe mode is OFF` before executing HDFS directory initialization.

### 2.3 Feature Engineering Unification
- `FeatureBuilder` in `src/prediction/feature_builder.py` serves as the single source of feature truth for training, batch inference, and Streamlit dashboard UI.
