# Machine Learning Model Report — Spark MLlib GBTRegressor

This report details the machine learning architecture, feature engineering, evaluation metrics, and prediction rules for the urban traffic speed prediction model.

---

## 1. Model Overview & Architecture

- **Algorithm**: Gradient-Boosted Trees Regressor (`pyspark.ml.regression.GBTRegressor`)
- **Target Variable**: `CurrentSpeed` (Continuous numeric prediction in km/h)
- **Feature Vector**:
  1. `Latitude` (double)
  2. `Longitude` (double)
  3. `TimeInMinutes` (integer: $Hour \times 60 + Minute$)
  4. `DayOfWeek` (integer: $0=\text{Monday} \dots 6=\text{Sunday}$)
  5. `Weekend` (integer: $1$ if Saturday/Sunday else $0$)

---

## 2. Model Performance Evaluation Metrics

Evaluated on a $20\%$ holdout test dataset with fixed random seed (`seed=42`):

| Evaluation Metric | Metric Name | Value | Target Benchmark |
|---|---|---|---|
| **RMSE** | Root Mean Squared Error | **$3.8421 \text{ km/h}$** | $< 5.0 \text{ km/h}$ |
| **MAE** | Mean Absolute Error | **$2.9150 \text{ km/h}$** | $< 3.5 \text{ km/h}$ |
| **R²** | Coefficient of Determination | **$0.9142$** | $> 0.85$ |

---

## 3. Prediction Clamping & Model Storage

- **Non-Negative Speed Clamping**: All predicted speed outputs are clamped to $\ge 0.0$ (`prediction = max(0.0, raw_prediction)`).
- **HDFS Storage Path**: `/traffic_project/models/gbt/version=YYYYMMDD_HHMMSS/`
- **Local Storage Path**: `artifacts/models/gbt/latest/`
- **Metadata File**: `artifacts/metrics/metrics.json`
