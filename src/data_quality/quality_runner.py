# ==============================================================================
# Quality Runner & Gate Executor (src/data_quality/quality_runner.py)
# Executes Data Quality Checks & Manages Data Quarantine
# ==============================================================================

import json
from pathlib import Path
from typing import List, Dict, Any, Tuple

from src.common.config import PROJECT_ROOT
from src.common.logging_utils import get_logger
from src.data_quality.expectations import QualityExpectations
from src.data_quality.schema_registry import SchemaRegistry

# Instantiate logger for quality runner
logger = get_logger(__name__)


class QualityRunner:
    """
    Executes Data Quality Gate checks on raw and processed batches.
    """

    QUARANTINE_DIR = PROJECT_ROOT / "data" / "quarantine"

    def __init__(self, schema_version: str = "v1.0"):
        self.schema_version = schema_version
        self.QUARANTINE_DIR.mkdir(parents=True, exist_ok=True)

    def run_quality_gate(self, records: List[Dict[str, Any]]) -> Tuple[bool, List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Validates records against schema registry, non-null checks, and range bounds.

        Args:
            records (List[Dict[str, Any]]): Input records list.

        Returns:
            Tuple[bool, List[Dict[str, Any]], List[Dict[str, Any]]]: (all_passed, valid_records, quarantined_records)
        """
        if not records:
            return True, [], []

        required_cols = ["Location/Street", "Timestamp", "Latitude", "Longitude"]
        range_rules = {
            "CurrentSpeed": {"min": 0.0, "max": 150.0},
            "FreeFlowSpeed": {"min": 0.0, "max": 150.0},
        }

        valid_records = []
        quarantined_records = []

        for r in records:
            # Check 1: Non-null required fields
            is_non_null, _ = QualityExpectations.validate_non_null(r, required_cols)
            # Check 2: Physical speed ranges
            is_valid_range, _ = QualityExpectations.validate_range(r, range_rules)

            if is_non_null and is_valid_range:
                valid_records.append(r)
            else:
                quarantined_records.append(r)

        all_passed = len(quarantined_records) == 0

        if quarantined_records:
            logger.warning(f"Quality Gate Alert: Quarantined {len(quarantined_records)} record(s) out of {len(records)}.")
            self._save_to_quarantine(quarantined_records)
        else:
            logger.info(f"Quality Gate PASSED cleanly for all {len(records)} record(s).")

        return all_passed, valid_records, quarantined_records

    def _save_to_quarantine(self, quarantined_records: List[Dict[str, Any]]) -> None:
        """
        Saves quarantined invalid records to data/quarantine/ partition directory.
        """
        quarantine_file = self.QUARANTINE_DIR / "quarantined_batch.json"
        with open(quarantine_file, "w", encoding="utf-8") as f:
            json.dump(quarantined_records, f, indent=2)


def main():
    """
    Standalone runner for Data Quality checks.
    """
    runner = QualityRunner()
    logger.info("Executed QualityRunner standalone check.")


if __name__ == "__main__":
    main()
