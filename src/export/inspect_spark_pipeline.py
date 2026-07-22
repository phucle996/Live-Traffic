# ==============================================================================
# Spark Pipeline Inspector (src/export/inspect_spark_pipeline.py)
# Inspects VectorAssembler, Feature Order, GBT Trees, Weights, & Thresholds
# ==============================================================================

import json
from pathlib import Path
from typing import Dict, Any

from pyspark.ml import PipelineModel
from pyspark.ml.regression import GBTRegressionModel

from src.common.config import PROJECT_ROOT
from src.common.logging_utils import get_logger
from src.common.spark_session import get_spark_session

# Instantiate logger for spark pipeline inspector
logger = get_logger(__name__)


def inspect_pipeline_model(model_dir: Path) -> Dict[str, Any]:
    """
    Loads fitted PySpark PipelineModel and extracts vector assembler inputs,
    GBT tree count, tree weights, and node structures.
    """
    logger.info(f"Inspecting Spark PipelineModel from '{model_dir}'...")

    # 1. Khởi tạo SparkSession local
    spark = get_spark_session(app_name="inspect-spark-pipeline")

    # 2. Nạp PipelineModel từ đĩa (dùng file:// scheme)
    model_uri = f"file://{model_dir.resolve()}"
    pipeline_model = PipelineModel.load(model_uri)

    info = {
        "pipeline_stages": len(pipeline_model.stages),
        "stages": [],
    }

    # 3. Duyệt từng stage trong Spark ML Pipeline
    for idx, stage in enumerate(pipeline_model.stages):
        stage_name = stage.__class__.__name__
        stage_info = {"index": idx, "stage_class": stage_name}

        # Nếu là VectorAssembler stage
        if hasattr(stage, "getInputCols"):
            stage_info["input_cols"] = stage.getInputCols()
            stage_info["output_col"] = stage.getOutputCol()

        # Nếu là GBTRegressionModel stage
        if isinstance(stage, GBTRegressionModel):
            stage_info["num_trees"] = len(stage.trees)
            stage_info["tree_weights"] = [float(w) for w in stage.treeWeights]
            stage_info["num_features"] = stage.numFeatures

        info["stages"].append(stage_info)

    logger.info(f"Pipeline inspection complete! Total stages: {info['pipeline_stages']}")
    return info


def main():
    model_dir = PROJECT_ROOT / "artifacts" / "models" / "gbt" / "latest"
    if not model_dir.exists():
        print(f"[ERROR] Model directory not found: {model_dir}")
        return

    info = inspect_pipeline_model(model_dir)
    print("\n======================================================================")
    print("                    SPARK PIPELINE MODEL INSPECTION                    ")
    print("======================================================================")
    print(json.dumps(info, indent=2, ensure_ascii=False))
    print("======================================================================\n")


if __name__ == "__main__":
    main()
