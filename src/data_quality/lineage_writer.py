# ==============================================================================
# Data Lineage Writer Engine (src/data_quality/lineage_writer.py)
# Records End-to-End Lineage Metadata Graphs from Raw Ingestion to ML Model
# ==============================================================================

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

from src.common.config import PROJECT_ROOT
from src.common.logging_utils import get_logger

# Instantiate logger for lineage writer
logger = get_logger(__name__)


class LineageWriter:
    """
    Writes end-to-end data lineage metadata graph to artifacts/reports/data_lineage.json.
    """

    LINEAGE_FILE = PROJECT_ROOT / "artifacts" / "reports" / "data_lineage.json"

    @classmethod
    def record_lineage(
        cls,
        batch_id: str,
        source: str,
        raw_partition: str,
        processed_dataset: str,
        schema_version: str = "v1.0",
        model_version: str = "v1.0.0",
        quality_passed: bool = True
    ) -> Dict[str, Any]:
        """
        Appends or updates lineage metadata record.

        Returns:
            Dict[str, Any]: Lineage metadata record dictionary.
        """
        cls.LINEAGE_FILE.parent.mkdir(parents=True, exist_ok=True)
        lineage_history = cls.read_lineage()

        record = {
            "batch_id": batch_id,
            "source": source,
            "raw_partition": raw_partition,
            "processed_dataset": processed_dataset,
            "schema_version": schema_version,
            "model_version": model_version,
            "quality_gate_passed": quality_passed,
            "created_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        }

        lineage_history[batch_id] = record

        with open(cls.LINEAGE_FILE, "w", encoding="utf-8") as f:
            json.dump(lineage_history, f, indent=2)

        logger.info(f"Recorded Data Lineage graph for batch '{batch_id}' -> Model '{model_version}'")
        return record

    @classmethod
    def read_lineage(cls) -> Dict[str, Any]:
        """
        Reads lineage metadata history from artifacts/reports/data_lineage.json.
        """
        if cls.LINEAGE_FILE.exists():
            try:
                with open(cls.LINEAGE_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to read lineage JSON: {e}")

        return {}
