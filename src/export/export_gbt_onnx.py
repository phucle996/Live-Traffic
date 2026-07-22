# ==============================================================================
# ONNX Model Exporter (src/export/export_gbt_onnx.py)
# Exports PySpark GBT Model to ONNX TreeEnsembleRegressor Artifact & Manifest
# ==============================================================================

import hashlib
import json
from pathlib import Path
from typing import Dict, Any

import numpy as np
from pyspark.ml import PipelineModel
from pyspark.ml.regression import GBTRegressionModel

import onnxmltools
from onnxmltools.convert.common.data_types import FloatTensorType


from src.common.config import PROJECT_ROOT
from src.common.logging_utils import get_logger
from src.common.spark_session import get_spark_session

# Instantiate logger for ONNX export engine
logger = get_logger(__name__)


def export_gbt_onnx(model_dir: Path, output_dir: Path) -> Dict[str, Any]:
    """
    Converts PySpark GBT model to ONNX format (TreeEnsembleRegressor) and exports to candidate-onnx directory.
    """
    logger.info(f"Exporting PySpark GBT Model to ONNX format at '{output_dir}'...")

    # 1. Nạp Spark PipelineModel
    spark = get_spark_session(app_name="export-gbt-onnx")
    model_uri = f"file://{model_dir.resolve()}"
    pipeline_model = PipelineModel.load(model_uri)

    feature_names = []
    gbt_stage = None

    for stage in pipeline_model.stages:
        if hasattr(stage, "getInputCols"):
            feature_names = list(stage.getInputCols())
        if isinstance(stage, GBTRegressionModel):
            gbt_stage = stage

    if not gbt_stage:
        raise ValueError("Không tìm thấy GBTRegressionModel stage trong PipelineModel!")

    # 2. Định nghĩa kiểu dữ liệu đầu vào cho ONNX Model (Từng cột FloatTensorType([None, 1]))
    num_features = len(feature_names)
    initial_types = [(col_name, FloatTensorType([None, 1])) for col_name in feature_names]


    # 3. Ép cấu hình Spark fs.defaultFS sang file:/// để onnxmltools ghi temp file vào local disk thay vì HDFS
    spark.conf.set("fs.defaultFS", "file:///")

    # 4. Thực hiện chuyển đổi PySpark GBT model sang ONNX Model (Truyền spark_session vào convert_sparkml)
    logger.info(f"Converting PySpark GBT model ({num_features} features) to ONNX...")
    onnx_model = onnxmltools.convert_sparkml(
        pipeline_model,
        name="GBTRegressorTrafficModel",
        initial_types=initial_types,
        spark_session=spark,
    )





    # 4. Lưu file model.onnx
    output_dir.mkdir(parents=True, exist_ok=True)
    onnx_path = output_dir / "model.onnx"
    with open(onnx_path, "wb") as f:
        f.write(onnx_model.SerializeToString())

    # 5. Tính checksum SHA-256 của file ONNX
    with open(onnx_path, "rb") as f:
        checksum = hashlib.sha256(f.read()).hexdigest()

    # 6. Ghi file manifest.json cho candidate-onnx
    manifest = {
        "model_version": "v1.0.0",
        "format": "onnx",
        "checksum_sha256": checksum,
        "num_features": num_features,
        "feature_names": feature_names,
        "created_at": "2026-07-21T20:46:00Z",
    }
    manifest_path = output_dir / "manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    logger.info(f"[SUCCESS] Exported ONNX model artifact to: {onnx_path} (Checksum: {checksum[:12]}...)")
    return manifest


def main():
    model_dir = PROJECT_ROOT / "artifacts" / "models" / "gbt" / "latest"
    output_dir = PROJECT_ROOT / "artifacts" / "inference" / "candidate-onnx"
    manifest = export_gbt_onnx(model_dir, output_dir)
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
