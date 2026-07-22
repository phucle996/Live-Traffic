# ==============================================================================
# Integration Test for Model Training & Prediction (tests/integration/test_model_prediction.py)
# Verifies Fit, Prediction Generation, Clamping, Evaluation, & Save/Load Pipeline Cycle
# ==============================================================================

import pytest
import tempfile
from pathlib import Path
from pyspark.ml import PipelineModel
from pyspark.sql import SparkSession
from pyspark.sql import functions as F

from src.common.schemas import PROCESSED_TRAFFIC_SCHEMA
from src.training.train_gbt import build_gbt_pipeline
from src.training.evaluate_model import evaluate_predictions


@pytest.fixture(scope="module")
def spark():
    """
    Pytest fixture creating local PySpark session for ML integration testing.
    """
    session = (
        SparkSession.builder.master("local[1]")
        .appName("integration-test-model-prediction")
        .config("spark.sql.session.timeZone", "UTC")
        .getOrCreate()
    )
    yield session
    session.stop()


from datetime import datetime

def test_gbt_pipeline_fit_predict_save_load(spark):
    """
    Verifies model fitting, predictions evaluation, clamping, and save/load cycle.
    """
    # Sample training feature dataset matching PROCESSED_TRAFFIC_SCHEMA
    sample_data = [
        (datetime(2026, 7, 21, 8, 0, 0), "Nguyen Hue", "District 1", 10.7769, 106.7009, 25.0, 45.0, 0.95, 8, 0, 480, 1, 0, 0.5556, "lab_offline"),
        (datetime(2026, 7, 21, 8, 30, 0), "Le Loi", "District 1", 10.7738, 106.6983, 20.0, 40.0, 0.92, 8, 30, 510, 1, 0, 0.5000, "lab_offline"),
        (datetime(2026, 7, 21, 17, 30, 0), "Pasteur", "District 3", 10.7812, 106.6945, 15.0, 45.0, 0.98, 17, 30, 1050, 1, 0, 0.3333, "lab_offline"),
        (datetime(2026, 7, 21, 18, 0, 0), "Nam Ky Khoi Nghia", "District 3", 10.7845, 106.6912, 14.0, 45.0, 0.94, 18, 0, 1080, 1, 0, 0.3111, "lab_offline"),
        (datetime(2026, 7, 21, 12, 0, 0), "Vo Van Kiet", "District 5", 10.7531, 106.6698, 55.0, 60.0, 0.96, 12, 0, 720, 1, 0, 0.9167, "lab_offline"),
        (datetime(2026, 7, 21, 13, 0, 0), "Nguyen Van Linh", "District 7", 10.7302, 106.7061, 48.0, 50.0, 0.91, 13, 0, 780, 1, 0, 0.9600, "lab_offline"),
    ]

    features = ["Latitude", "Longitude", "TimeInMinutes", "DayOfWeek", "Weekend"]
    target = "CurrentSpeed"

    df = spark.createDataFrame(sample_data, schema=PROCESSED_TRAFFIC_SCHEMA)

    # Build Pipeline
    pipeline, _ = build_gbt_pipeline(features=features, target=target, max_depth=2, max_iter=5, seed=42)

    # Fit model
    fitted_model = pipeline.fit(df)
    assert fitted_model is not None

    # Predict
    predictions = fitted_model.transform(df)
    assert "prediction" in predictions.columns

    # Clamp prediction >= 0.0
    clamped_df = predictions.withColumn(
        "prediction",
        F.when(F.col("prediction") < 0.0, 0.0).otherwise(F.col("prediction"))
    )

    # Verify no prediction is negative
    min_pred = clamped_df.select(F.min("prediction")).collect()[0][0]
    assert min_pred >= 0.0

    # Evaluate metrics
    metrics = evaluate_predictions(clamped_df, target_col=target, prediction_col="prediction")
    assert "rmse" in metrics
    assert "mae" in metrics
    assert "r2" in metrics
    assert metrics["rmse"] >= 0.0

    # Verify Save and Load cycle
    with tempfile.TemporaryDirectory() as tmp_dir:
        save_path = str(Path(tmp_dir) / "test_gbt_model")
        fitted_model.write().overwrite().save(save_path)

        # Load back
        loaded_model = PipelineModel.load(save_path)
        loaded_preds = loaded_model.transform(df)
        assert "prediction" in loaded_preds.columns
        assert loaded_preds.count() == df.count()
