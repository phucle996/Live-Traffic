# ==============================================================================
# Versioned Schema Registry Engine (src/data_quality/schema_registry.py)
# Manages Versioned Data Contracts & Backward Compatibility Checks
# ==============================================================================

from typing import Dict, Any, List
from src.common.logging_utils import get_logger

# Instantiate logger for schema registry
logger = get_logger(__name__)


class SchemaRegistry:
    """
    Manages versioned data contracts and verifies schema compatibility.
    """

    CONTRACT_VERSIONS: Dict[str, Dict[str, Any]] = {
        "v1.0": {
            "columns": [
                "Location/Street", "District", "Latitude", "Longitude",
                "CurrentSpeed", "FreeFlowSpeed", "Confidence",
                "CurrentTravelTime", "FreeFlowTravelTime", "RoadClosure",
                "Timestamp", "DataSource", "IngestionBatchId"
            ],
            "primary_keys": ["Location/Street", "Timestamp"],
        },
        "v1.1": {
            "columns": [
                "Location/Street", "District", "Latitude", "Longitude",
                "CurrentSpeed", "FreeFlowSpeed", "Confidence",
                "CurrentTravelTime", "FreeFlowTravelTime", "RoadClosure",
                "Timestamp", "DataSource", "IngestionBatchId", "WeatherCondition"
            ],
            "primary_keys": ["Location/Street", "Timestamp"],
        },
    }

    @classmethod
    def get_contract(cls, version: str = "v1.0") -> Dict[str, Any]:
        """
        Retrieves schema contract specification for given version string.
        """
        return cls.CONTRACT_VERSIONS.get(version, cls.CONTRACT_VERSIONS["v1.0"])

    @classmethod
    def is_compatible(cls, record_cols: List[str], version: str = "v1.0") -> bool:
        """
        Checks if columns in a record satisfy required columns of target contract version.
        """
        contract = cls.get_contract(version)
        required_cols = set(contract["columns"])
        provided_cols = set(record_cols)

        # Allow missing optional v1.1 fields for backward compatibility
        missing_critical = [c for c in required_cols if c not in provided_cols and c != "WeatherCondition"]
        if missing_critical:
            logger.warning(f"Schema contract '{version}' compatibility failure. Missing: {missing_critical}")
            return False

        return True
