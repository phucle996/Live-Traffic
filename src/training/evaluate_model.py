# ==============================================================================
# Model Evaluation Engine Module (src/training/evaluate_model.py)
# Evaluates Regression Models using RMSE, MAE, and R^2 Metrics via PySpark Evaluators
# ==============================================================================

from typing import Dict
from pyspark.ml.evaluation import RegressionEvaluator
from pyspark.sql import DataFrame
from pyspark.sql import functions as F

from src.common.logging_utils import get_logger

# Instantiate logger for model evaluator
logger = get_logger(__name__)


def evaluate_predictions(predictions_df: DataFrame, target_col: str = "CurrentSpeed", prediction_col: str = "prediction") -> Dict[str, float]:
    """
    Evaluates regression prediction results calculating RMSE, MAE, and R^2.

    Args:
        predictions_df (DataFrame): PySpark DataFrame containing target and prediction columns.
        target_col (str): True label target column name.
        prediction_col (str): Predicted output column name.

    Returns:
        Dict[str, float]: Evaluation metrics dictionary containing 'rmse', 'mae', and 'r2'.
    """
    logger.info(f"Evaluating regression predictions for target '{target_col}'...")

    # Ensure prediction column is non-negative (clamping rule)
    clamped_df = predictions_df.withColumn(
        prediction_col,
        F.when(F.col(prediction_col) < 0.0, 0.0).otherwise(F.col(prediction_col))
    )

    # Instantiate PySpark RegressionEvaluators
    rmse_evaluator = RegressionEvaluator(labelCol=target_col, predictionCol=prediction_col, metricName="rmse")
    mae_evaluator = RegressionEvaluator(labelCol=target_col, predictionCol=prediction_col, metricName="mae")
    r2_evaluator = RegressionEvaluator(labelCol=target_col, predictionCol=prediction_col, metricName="r2")

    # Compute evaluation metrics
    rmse = float(rmse_evaluator.evaluate(clamped_df))
    mae = float(mae_evaluator.evaluate(clamped_df))
    r2 = float(r2_evaluator.evaluate(clamped_df))

    metrics = {
        "rmse": round(rmse, 4),
        "mae": round(mae, 4),
        "r2": round(r2, 4),
    }

    logger.info(f"[EVALUATION METRICS] RMSE: {metrics['rmse']}, MAE: {metrics['mae']}, R²: {metrics['r2']}")
    return metrics
