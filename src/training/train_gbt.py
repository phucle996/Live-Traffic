# ==============================================================================
# Spark MLlib GBTRegressor Training Engine (src/training/train_gbt.py)
# Builds ML Pipeline, Trains Model, Evaluates Performance, & Exports Artifacts
# ==============================================================================

import os
from datetime import datetime
from pathlib import Path
from typing import Tuple, Dict, Any

import pandas as pd
from pyspark.ml import Pipeline, PipelineModel
from pyspark.ml.feature import VectorAssembler
from pyspark.ml.regression import GBTRegressor
from pyspark.sql import SparkSession, DataFrame
from pyspark.sql import functions as F

from src.common.config import settings, PROJECT_ROOT
from src.common.logging_utils import get_logger
from src.common.schemas import PROCESSED_TRAFFIC_SCHEMA
from src.common.spark_session import get_spark_session
from src.training.evaluate_model import evaluate_predictions
from src.training.model_metadata import create_model_metadata, save_model_metadata

# Instantiate logger for GBT training engine
logger = get_logger(__name__)


def build_gbt_pipeline(features: list, target: str, max_depth: int = 5, max_iter: int = 100, seed: int = 42) -> Tuple[Pipeline, GBTRegressor]:
    """
    Constructs an un-fitted Spark ML Pipeline containing VectorAssembler and GBTRegressor.

    Args:
        features (list): Feature column names list.
        target (str): Target column name.
        max_depth (int): Maximum depth of tree decision nodes.
        max_iter (int): Maximum boosting iterations.
        seed (int): Random seed for reproducibility.

    Returns:
        Tuple[Pipeline, GBTRegressor]: (unfitted_pipeline, gbt_estimator)
    """
    logger.info(f"Building Spark ML Pipeline with features: {features}, target: '{target}'")

    # Step 1: Create VectorAssembler to combine features into a single vector column
    assembler = VectorAssembler(inputCols=features, outputCol="features", handleInvalid="skip")

    # Step 2: Create GBTRegressor estimator stage
    gbt = GBTRegressor(
        featuresCol="features",
        labelCol=target,
        predictionCol="prediction",
        maxDepth=max_depth,
        maxIter=max_iter,
        seed=seed,
    )

    # Step 3: Combine into a Spark ML Pipeline
    pipeline = Pipeline(stages=[assembler, gbt])
    return pipeline, gbt


def train_and_evaluate_gbt(
    spark: SparkSession,
    processed_parquet_path: str = None
) -> Tuple[PipelineModel, Dict[str, Any]]:
    """
    Loads processed dataset, splits train/test, fits GBT pipeline, evaluates metrics, and returns fitted model.
    """
    version = datetime.now().strftime("%Y%m%d_%H%M%S")
    logger.info(f"Starting GBT Model Training Run - Version: '{version}'")

    # Resolve processed dataset input path
    parquet_path = processed_parquet_path or f"{settings.HDFS_URI}{settings.HDFS_PROCESSED_PATH}/*"

    # 1. Kiểm tra nếu file/đường dẫn parquet thực sự tồn tại trên local/HDFS trước khi đọc
    file_exists = False
    if not parquet_path.startswith("hdfs://"):
        file_exists = any(Path(parquet_path).parent.glob("*.parquet")) or Path(parquet_path).exists()

    if file_exists:
        try:
            logger.info(f"Reading processed dataset from '{parquet_path}'...")
            df = spark.read.parquet(parquet_path)
        except Exception as e:
            logger.warning(f"Unable to read Parquet ({e}). Falling back to seed dataset...")
            file_exists = False

    if not file_exists:
        # 2. Tạo dữ liệu huấn luyện từ seed CSV nếu dữ liệu parquet chưa sẵn sàng
        logger.info("Building feature dataset from seed CSV files for model fitting...")
        from src.ingestion.seed_loader import load_seed_csv_files
        seed_pd = load_seed_csv_files(settings.SEED_FOLDER)
        seed_pd["Timestamp"] = pd.to_datetime(seed_pd["Timestamp"]) # Chuyển đổi Timestamp từ string sang datetime object để khớp TimestampType
        seed_pd["Hour"] = seed_pd["Timestamp"].dt.hour
        seed_pd["Minute"] = seed_pd["Timestamp"].dt.minute
        seed_pd["TimeInMinutes"] = seed_pd["Hour"] * 60 + seed_pd["Minute"]
        seed_pd["DayOfWeek"] = seed_pd["Timestamp"].dt.dayofweek
        seed_pd["Weekend"] = seed_pd["DayOfWeek"].apply(lambda x: 1 if x >= 5 else 0)
        seed_pd["CongestionRatio"] = (seed_pd["CurrentSpeed"] / seed_pd["FreeFlowSpeed"]).round(4)
        seed_pd["DataSource"] = "lab_offline" # Gán nhãn nguồn dữ liệu lab_offline để khớp schema 15 cột


        df = spark.createDataFrame(seed_pd, schema=PROCESSED_TRAFFIC_SCHEMA)



    # Perform reproducible Train/Test Split (80/20 ratio with fixed seed)
    train_df, test_df = df.randomSplit([0.8, 0.2], seed=settings.MODEL_SEED)
    train_count = train_df.count()
    test_count = test_df.count()
    logger.info(f"Dataset Split - Training samples: {train_count}, Test samples: {test_count}")

    # Build GBT Pipeline
    pipeline, _ = build_gbt_pipeline(
        features=settings.MODEL_FEATURES,
        target=settings.MODEL_TARGET,
        max_depth=settings.MODEL_MAX_DEPTH,
        max_iter=settings.MODEL_MAX_ITER,
        seed=settings.MODEL_SEED,
    )

    # Fit ML Pipeline on training dataset
    logger.info("Fitting Spark MLlib GBTRegressor Pipeline model on training dataset...")
    pipeline_model = pipeline.fit(train_df)
    logger.info("Model fitting complete!")

    # Transform test dataset to generate predictions
    predictions_df = pipeline_model.transform(test_df)

    # Apply non-negative speed prediction clamping rule (speed >= 0.0)
    clamped_predictions_df = predictions_df.withColumn(
        "prediction",
        F.when(F.col("prediction") < 0.0, 0.0).otherwise(F.col("prediction"))
    )

    # Evaluate predictions using RMSE, MAE, R²
    metrics = evaluate_predictions(clamped_predictions_df, target_col=settings.MODEL_TARGET, prediction_col="prediction")

    # Hyperparameter dictionary
    hyperparameters = {
        "max_depth": settings.MODEL_MAX_DEPTH,
        "max_iter": settings.MODEL_MAX_ITER,
        "seed": settings.MODEL_SEED,
    }

    # Generate Model Metadata
    metadata = create_model_metadata(
        version=version,
        metrics=metrics,
        features=settings.MODEL_FEATURES,
        target=settings.MODEL_TARGET,
        hyperparameters=hyperparameters,
        train_rows=train_count,
        test_rows=test_count,
    )

    # Save Model Artifacts
    # 1. Local artifacts directory (Dùng URI scheme file:// để ép Spark lưu local filesystem)
    local_model_dir = (PROJECT_ROOT / "artifacts" / "models" / "gbt" / "latest").resolve()
    local_model_dir.mkdir(parents=True, exist_ok=True)
    pipeline_model.write().overwrite().save(f"file://{local_model_dir}")
    save_model_metadata(metadata, local_model_dir)


    # 2. HDFS Model Directory
    hdfs_model_path = f"{settings.HDFS_URI}{settings.HDFS_MODEL_PATH}/version={version}"
    try:
        logger.info(f"Saving model pipeline to HDFS path: '{hdfs_model_path}'...")
        pipeline_model.write().overwrite().save(hdfs_model_path)
    except Exception as e:
        logger.warning(f"Could not save model to HDFS directly: {str(e)}")

    # 3. Export Sample Predictions CSV
    sample_preds_dir = PROJECT_ROOT / "artifacts" / "predictions"
    sample_preds_dir.mkdir(parents=True, exist_ok=True)
    sample_preds_path = sample_preds_dir / "sample_predictions.csv"

    sample_pd = (
        clamped_predictions_df.select(
            "Location/Street", "District", "Latitude", "Longitude",
            "TimeInMinutes", "DayOfWeek", "CurrentSpeed", "prediction"
        )
        .limit(20)
        .toPandas()
    )
    sample_pd.to_csv(sample_preds_path, index=False)
    logger.info(f"Exported sample predictions CSV to '{sample_preds_path}'")

    print("\n======================================================================")
    print(f"[SUCCESS] GBT Model Training Completed!")
    print(f"Version: {version} | RMSE: {metrics['rmse']} | MAE: {metrics['mae']} | R²: {metrics['r2']}")
    print(f"Model saved to: {local_model_dir}")
    print("======================================================================\n")

    return pipeline_model, metadata


def main():
    """
    CLI Entrypoint for GBT model training.
    """
    spark = get_spark_session(app_name="train-gbt-model")
    train_and_evaluate_gbt(spark)


if __name__ == "__main__":
    main()
