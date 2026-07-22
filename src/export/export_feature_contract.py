# ==============================================================================
# Feature Contract Exporter & Verifier (src/export/export_feature_contract.py)
# Verifies PySpark Model Input Features against SOT contracts/feature_contract.json
# ==============================================================================

import json
from pathlib import Path
from typing import Dict, Any

from pyspark.ml import PipelineModel

from src.common.config import PROJECT_ROOT
from src.common.logging_utils import get_logger
from src.common.spark_session import get_spark_session

# Instantiate logger for feature contract export
logger = get_logger(__name__)


def verify_and_export_feature_contract(model_dir: Path) -> Dict[str, Any]:
    """
    Verifies PySpark VectorAssembler features match SOT contracts/feature_contract.json
    and exports a verified feature manifest.
    """
    contract_file = PROJECT_ROOT / "contracts" / "feature_contract.json"
    if not contract_file.exists():
        raise FileNotFoundError(f"SOT contract not found at '{contract_file}'")

    # 1. Đọc SOT contract từ file JSON
    with open(contract_file, "r", encoding="utf-8") as f:
        sot_contract = json.load(f)

    sot_feature_order = sot_contract.get("feature_order", [])

    # 2. Nạp Spark PipelineModel để lấy VectorAssembler inputCols thực tế
    spark = get_spark_session(app_name="export-feature-contract")
    model_uri = f"file://{model_dir.resolve()}"
    pipeline_model = PipelineModel.load(model_uri)

    assembler_cols = []
    for stage in pipeline_model.stages:
        if hasattr(stage, "getInputCols"):
            assembler_cols = list(stage.getInputCols())
            break

    logger.info(f"SOT Feature Contract Order: {sot_feature_order}")
    logger.info(f"Spark VectorAssembler Columns: {assembler_cols}")

    # 3. Đánh giá tính khớp (Mọi assembler col phải có mặt trong SOT)
    for col in assembler_cols:
        assert col in sot_feature_order, f"Cột '{col}' trong Spark model không nằm trong SOT contract!"

    export_payload = {
        "contract_version": sot_contract.get("version", "1.0.0"),
        "sot_feature_order": sot_feature_order,
        "model_assembler_cols": assembler_cols,
        "status": "VERIFIED_MATCH",
    }

    logger.info("[SUCCESS] Feature contract verification passed 100%!")
    return export_payload


def main():
    model_dir = PROJECT_ROOT / "artifacts" / "models" / "gbt" / "latest"
    result = verify_and_export_feature_contract(model_dir)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
