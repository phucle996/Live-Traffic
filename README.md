# Traffic Prediction System (Lab 5)

A Distributed Urban Traffic Flow Ingestion, Spark ETL Processing, GBT Machine Learning Prediction, and Interactive Streamlit & Folium Visualization System.

---

## 1. System Architecture

```text
TomTom Traffic API / Seed CSV
          ↓
     Ingestion (src/ingestion/)
          ↓
     HDFS Raw Storage (/traffic_project/raw)
          ↓
     Spark ETL Processing (src/processing/)
          ↓
     HDFS Processed Parquet (/traffic_project/processed)
          ↓
 Spark MLlib GBTRegressor Training (src/training/)
          ↓
   Fitted GBT Pipeline Model (/traffic_project/models)
          ↓
   Serving Layer & Batch Predictor (src/prediction/)
          ↓
 Streamlit + Folium Interactive Dashboard (http://localhost:8501)
```

---

## 2. Directory Structure

```text
traffic-prediction-lab5/
├── docker-compose.yml           # Multi-container orchestration (HDFS, Spark, Streamlit)
├── Dockerfile                   # Python 3.10 & OpenJDK 11 application image
├── .env.example                 # Environment variable template
├── requirements.txt             # Pinned dependencies
├── Makefile                     # Command menu & shortcuts
├── README.md                    # System documentation
│
├── god_view/                    # Single Source of Truth (SOT) Phase Specifications
│   ├── phase_0_god_view.md
│   ├── phase_1_god_view.md
│   ├── phase_2_god_view.md
│   ├── phase_3_god_view.md
│   ├── phase_4_god_view.md
│   ├── phase_5_god_view.md
│   ├── phase_6_god_view.md
│   ├── phase_7_god_view.md
│   ├── phase_8_god_view.md
│   ├── phase_9_god_view.md
│   ├── phase_10_god_view.md
│   └── phase_11_god_view.md
│
├── config/                      # Application configuration files
│   ├── application.yaml         # Configuration defaults
│   ├── spark-defaults.conf      # Apache Spark engine configuration
│   └── log_config.yaml          # Logging formatters and handlers
│
├── data/                        # Input data locations & seed files
│   ├── locations/               # Geographical target coordinates CSV
│   └── seed/                    # Offline seed traffic CSV datasets
│
├── src/                         # Application source code
│   ├── common/                  # Shared config, logging, schemas, spark session
│   ├── ingestion/               # TomTom API client & seed loader
│   ├── processing/              # Spark ETL cleaning & EDA reports
│   ├── training/               # Spark MLlib GBT model trainer & evaluators
│   ├── prediction/              # Serving layer & batch predictor
│   └── dashboard/               # Streamlit & Folium web application
│
├── scripts/                     # Shell automation scripts
│   ├── wait_for_hdfs.sh
│   ├── init_hdfs.sh
│   ├── run_ingestion.sh
│   ├── upload_seed_data.sh
│   ├── run_processing.sh
│   ├── run_training.sh
│   ├── run_prediction.sh
│   ├── run_pipeline.sh
│   └── clean_project.sh
│
├── tests/                       # Unit & integration test suites
│   ├── unit/                    # Unit tests (config, client, validation, serving)
│   └── integration/             # Integration tests (HDFS, Spark, Model)
│
├── artifacts/                   # Output models, metrics, predictions, reports
│   ├── models/
│   ├── metrics/
│   ├── predictions/
│   └── reports/
│
└── docs/                        # Technical documentation & presentation guides
    ├── architecture.md
    ├── data_dictionary.md
    ├── api_ingestion.md
    ├── eda_report.md
    ├── model_report.md
    └── demo_guide.md
```

---

## 3. Quick Start Guide

### Step 1: Environment Setup
```bash
cp .env.example .env
```

### Step 2: Start Infrastructure & Run Full Pipeline
```bash
make up
make pipeline
```

### Step 3: Open Streamlit Web Dashboard
Access: **[http://localhost:8501](http://localhost:8501)**

---

## 4. Makefile Commands Menu

| Command | Description |
|---|---|
| `make up` | Start all Docker Compose containers |
| `make down` | Stop all Docker Compose containers |
| `make init` | Provision initial HDFS folder structure |
| `make ingest` | Run data ingestion pipeline (API / Seed mode) |
| `make process` | Run Apache Spark ETL processing job |
| `make eda` | Run Exploratory Data Analysis & export reports |
| `make train` | Train Spark MLlib GBTRegressor model |
| `make predict` | Run batch prediction smoke test |
| `make dashboard` | Start Streamlit web dashboard container |
| `make pipeline` | Execute full end-to-end master pipeline |
| `make test` | Run pytest unit & integration test suites |
| `make clean` | Clean temporary bytecode and caches |

---

## 5. Model Evaluation Results

- **Model Type**: Spark MLlib `GBTRegressor`
- **RMSE**: `3.8421 km/h`
- **MAE**: `2.9150 km/h`
- **R²**: `0.9142`
