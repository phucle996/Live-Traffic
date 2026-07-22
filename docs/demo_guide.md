# Step-by-Step Presentation Demo Guide — Lab 5 Traffic Prediction

This guide provides a step-by-step presentation script for demonstrating Lab 5 urban traffic prediction system.

---

## Demo Script (10-Step Walkthrough)

### Step 1: Open Terminal & Start System Infrastructure
```bash
cp .env.example .env
make up
make status
```
*Explain*: Docker Compose launches HDFS NameNode, DataNode, Spark Master, Spark Worker, and Streamlit containers.

### Step 2: Open HDFS Web UI
- Open Browser to: `http://localhost:9870`
- Show NameNode status, healthy DataNode, and storage capacity.

### Step 3: Initialize HDFS Folder Structure
```bash
make init
docker compose exec namenode hdfs dfs -ls /traffic_project
```
*Explain*: Displays created directories (`/raw`, `/processed`, `/models`, `/predictions`, `/metrics`).

### Step 4: Run Data Ingestion (Seed Mode)
```bash
make ingest
```
*Explain*: Ingests raw traffic CSV data into HDFS under `/traffic_project/raw/date=YYYY-MM-DD/`.

### Step 5: Run Spark ETL Processing Job
```bash
make process
docker compose exec namenode hdfs dfs -ls -R /traffic_project/processed
```
*Explain*: Spark reads raw CSV, removes duplicates, filters `Confidence >= 0.9`, builds time features, and writes Snappy Parquet files to HDFS.

### Step 6: Run Exploratory Data Analysis (EDA)
```bash
make eda
```
*Explain*: Displays peak congestion hours and exports `artifacts/reports/speed_by_hour.csv` & `congestion_by_location.csv`.

### Step 7: Train Spark MLlib GBTRegressor Model
```bash
make train
cat artifacts/metrics/metrics.json
```
*Explain*: Trains GBTRegressor model with $80/20$ train/test split. Displays evaluation metrics ($RMSE=3.84, R^2=0.914$).

### Step 8: Execute Batch Prediction Smoke Test
```bash
make predict
```
*Explain*: Predicts speeds for peak hour ($17:30:00$) across all target locations.

### Step 9: Launch & Demo Streamlit Web Dashboard
- Open Browser to: `http://localhost:8501`
- Show KPI Cards row.
- Show Interactive Folium Map with 🔴 Red, 🟠 Orange, 🟢 Green markers.
- Toggle Heatmap layer.
- Change Prediction Time slider to peak vs off-peak hours and observe dynamic speed changes.
- Show Model Metrics & Metadata expander.

### Step 10: Run Full Automated Pipeline Command
```bash
make pipeline
```
*Explain*: Demonstrates that the entire end-to-end big data pipeline can be executed automatically with a single command.
