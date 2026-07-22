# God View — Training & MLOps
# Luồng: EDA → Feature Analysis → Model Training → Evaluation → MLOps Lifecycle → Drift → Retrain

---

## 1. Exploratory Data Analysis (EDA)

```text
Processed HDFS Parquet
        │
        ▼
SparkSession.read.parquet(processed_path)
        │
        ▼
EDA Engine (src/eda/)
  ├── compute_speed_stats()        → mean, std, percentiles per street
  ├── compute_hourly_patterns()    → avg speed by hour (0–23)
  ├── compute_congestion_by_loc()  → congestion ratio by location_id
  ├── compute_weekend_effect()     → weekend vs weekday speed delta
  └── generate_report()           → artifacts/reports/*.csv + summary
```

**Key findings used in model design**:
- Peak congestion: 07:00–09:00, 17:00–19:00.
- Weekend speeds average 15–25% higher than weekdays.
- Congestion ratio drives model feature engineering.

---

## 2. GBTRegressor Model Training Pipeline

```text
Processed HDFS Parquet
        │
        ▼
TrafficTrainer (src/training/trainer.py)
  │
  ├── Feature assembly (VectorAssembler):
  │     features = [hour, day_of_week, is_weekend, congestion_ratio,
  │                 free_flow_speed, latitude, longitude]
  │     label   = speed_kmh
  │
  ├── Train/test split (80/20, stratified by street_name)
  │
  ├── Spark MLlib GBTRegressor:
  │     maxDepth=5, maxIter=20, stepSize=0.1, subsamplingRate=0.8
  │
  ├── Evaluate:
  │     RegressionEvaluator → RMSE, R², MAE
  │
  └── Save:
        model artifact  → HDFS/models/gbt_model/
        metrics.json    → artifacts/metrics/metrics.json
        feature_importance.json → artifacts/
```

**Acceptance**: RMSE ≤ 8.0 km/h, R² ≥ 0.60, evaluated on ≥ 1000 test rows.

**Source files**: `src/training/trainer.py`, `src/training/evaluator.py`, `src/training/feature_builder.py`

---

## 3. Experiment Tracking

```text
TrainingRun
     │
     ▼
ExperimentTracker (src/mlops/experiment_tracker.py)
  ├── run_id = UUID[:8]
  ├── log_params()  → maxDepth, maxIter, stepSize, subsamplingRate
  ├── log_metrics() → rmse, r2, mae, test_rows
  ├── log_artifact()→ model artifact path
  ├── log_dataset() → source, partition dates, row counts
  └── finish()      → artifacts/mlops/experiments/{run_id}.json

One JSON file per run. Persisted to disk for traceability.
```

---

## 4. Model Validation Gate

```text
Candidate Model
     │
     ▼
ModelValidator (src/mlops/model_validator.py)
  reads: config/mlops/promotion_rules.yaml
  │
  ├── Gate 1: RMSE ≤ 8.0 km/h
  ├── Gate 2: R² ≥ 0.60
  ├── Gate 3: test_rows ≥ 1000
  └── Gate 4: no breaking schema change
        │
    ┌───┴──────┐
    │ FAIL     │ PASS
    ▼          ▼
  Quarantine  Promote to Staging
  (reject)    ModelPromoter
```

---

## 5. Model Registry & Lifecycle Stages

```text
artifacts/mlops/registry.json  (SOT for all model versions)

Version stages:
  Candidate → Staging → Production
                              │
                         (prev version) → Archived

ModelRegistry (src/mlops/model_registry.py)
  ├── register()     — race-guarded by JobLock("model_registry")
  ├── set_stage()    — atomic stage transition
  └── get_production_version() → current serving model

ModelPromoter (src/mlops/model_promoter.py)
  ├── promote_to_staging()    — validates first, then acquires JobLock
  └── promote_to_production() — archives old Production atomically
       JobLock("model_promoter") prevents concurrent promotions
```

**Race condition guard**: `JobLock("model_registry")` and `JobLock("model_promoter")` are exclusive file locks stored at `artifacts/locks/`. Concurrent Airflow DAG runs cannot simultaneously promote different candidates.

---

## 6. Data Drift & Prediction Drift Detection

```text
[Live Observations (rolling window)]
              │
              ▼
DriftDetector (src/mlops/drift_detector.py)
  reads: config/mlops/drift_thresholds.yaml

  Feature Drift:
    KS-statistic = max|CDF_baseline - CDF_live|
    Threshold: ks_stat > 0.15 → drift_detected = True

  Prediction Drift:
    mean_delta = |live_mean - baseline_mean|  → threshold: > 5.0 km/h
    std_ratio  = live_std / baseline_std      → threshold: > 1.5
    Either exceeded → prediction_drift = True
```

---

## 7. Retraining Policy

```text
DriftDetector fires → consecutive_drift_count++

RetrainingPolicy (src/mlops/retraining_policy.py)
  should_retrain = (
      consecutive_drift_count >= 3         # persists for 3 checks
      AND new_rows_since_last_train >= 5000 # enough new data
  )
  → True: trigger model_training_dag in Airflow
  → False: monitor and wait
```

---

## 8. Rollback Engine

```text
Production model quality degrades
        │
        ▼
RollbackEngine (src/mlops/rollback.py)
  acquires JobLock("model_promoter")
  ├── Demote current Production → Archived
  └── Promote most recent Archived → Production
        │
        ▼
  Restart API pods to reload previous model
  kubectl rollout restart deployment/traffic-prediction-api

Trigger conditions:
  - RMSE rises above 12.0 km/h (Prometheus alert: ModelRMSEDegradation)
  - Prediction drift detected for 3 consecutive checks
  - Manual operator decision
```
