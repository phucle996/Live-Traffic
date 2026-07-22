# ==============================================================================
# Hyperparameter Tuning Engine (src/training/hyperparameter_tuning.py)
# Grid Search & CrossValidation Tuning for GBTRegressor Model Parameters
# ==============================================================================

from pyspark.ml.tuning import ParamGridBuilder, CrossValidator
from pyspark.ml.evaluation import RegressionEvaluator
from pyspark.ml.regression import GBTRegressor
from pyspark.ml import Pipeline
from pyspark.sql import DataFrame

from src.common.logging_utils import get_logger

# Instantiate logger for hyperparameter tuning
logger = get_logger(__name__)


def tune_gbt_hyperparameters(train_df: DataFrame, pipeline: Pipeline, gbt: GBTRegressor, num_folds: int = 3) -> Pipeline:
    """
    Executes Cross-Validation to search for optimal GBT hyperparameters (maxDepth, maxIter).

    Args:
        train_df (DataFrame): Training PySpark DataFrame.
        pipeline (Pipeline): Base Spark ML Pipeline.
        gbt (GBTRegressor): GBTRegressor estimator instance.
        num_folds (int): Cross-validation folds count.

    Returns:
        Pipeline: Best fitted Pipeline model.
    """
    logger.info(f"Setting up GBT hyperparameter tuning with {num_folds}-fold cross validation...")

    # Build hyperparameter search grid
    param_grid = (
        ParamGridBuilder()
        .addGrid(gbt.maxDepth, [3, 5, 7])
        .addGrid(gbt.maxIter, [20, 50, 100])
        .build()
    )

    # Define evaluator for cross-validation
    evaluator = RegressionEvaluator(labelCol=gbt.getLabelCol(), predictionCol=gbt.getPredictionCol(), metricName="rmse")

    # Set up CrossValidator
    cross_val = CrossValidator(
        estimator=pipeline,
        estimatorParamMaps=param_grid,
        evaluator=evaluator,
        numFolds=num_folds,
        seed=42,
    )

    logger.info("Executing CrossValidator fit over parameter grid...")
    cv_model = cross_val.fit(train_df)
    logger.info("Hyperparameter tuning complete!")

    return cv_model.bestModel
