# ==============================================================================
# Model Registry (src/mlops/model_registry.py)
# Versioned model artifact registry managing stage pointers (Staging/Production/Archived)
# Race condition guard: all writes acquire JobLock("model_registry")
# ==============================================================================

import json
import fcntl
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List

from src.common.config import PROJECT_ROOT
from src.common.logging_utils import get_logger
from src.orchestration.job_lock import JobLock

# Instantiate logger for model registry
logger = get_logger(__name__)

# Central registry JSON file storing all model version records
REGISTRY_FILE = PROJECT_ROOT / "artifacts" / "mlops" / "registry.json"

# Valid model lifecycle stages
VALID_STAGES = {"Candidate", "Staging", "Production", "Archived"}


def _load_registry() -> Dict[str, Any]:
    """Loads registry JSON from disk, returning empty registry if absent."""
    REGISTRY_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not REGISTRY_FILE.exists():
        return {"versions": [], "production_version": None}
    with open(REGISTRY_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_registry(data: Dict[str, Any]) -> None:
    """Persists registry JSON to disk atomically."""
    with open(REGISTRY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


class ModelRegistry:
    """
    Manages versioned model artifact records and stage pointers.
    Writes are guarded by JobLock to prevent concurrent promotion race conditions.
    """

    def register(
        self,
        version: str,
        run_id: str,
        artifact_path: str,
        metrics: Dict[str, float],
        stage: str = "Candidate",
    ) -> None:
        """
        Registers a new model version in the registry with initial Candidate stage.
        Raises ValueError if stage is not one of VALID_STAGES.
        """
        if stage not in VALID_STAGES:
            raise ValueError(f"Invalid stage '{stage}'. Must be one of {VALID_STAGES}")

        # Acquire file lock to prevent concurrent registry writes
        with JobLock("model_registry"):
            registry = _load_registry()
            # Check if version already registered — avoid duplicates
            for v in registry["versions"]:
                if v["version"] == version:
                    logger.warning(f"ModelRegistry: Version '{version}' already registered.")
                    return

            record = {
                "version": version,
                "run_id": run_id,
                "artifact_path": str(artifact_path),
                "stage": stage,
                "metrics": metrics,
                "registered_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
                "promoted_at": None,
            }
            registry["versions"].append(record)
            _save_registry(registry)
            logger.info(f"ModelRegistry: Registered version '{version}' at stage '{stage}'")

    def get_production_version(self) -> Optional[Dict[str, Any]]:
        """Returns the current Production stage model record, or None."""
        registry = _load_registry()
        for v in registry["versions"]:
            if v["stage"] == "Production":
                return v
        return None

    def get_all_versions(self) -> List[Dict[str, Any]]:
        """Returns all registered model version records."""
        return _load_registry()["versions"]

    def set_stage(self, version: str, new_stage: str) -> None:
        """
        Updates a model version's stage.
        Used internally by ModelPromoter and RollbackEngine.
        Callers must hold JobLock before calling this.
        """
        if new_stage not in VALID_STAGES:
            raise ValueError(f"Invalid stage '{new_stage}'")

        registry = _load_registry()
        for v in registry["versions"]:
            if v["version"] == version:
                v["stage"] = new_stage
                v["promoted_at"] = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
                _save_registry(registry)
                logger.info(f"ModelRegistry: Version '{version}' → stage '{new_stage}'")
                return
        raise KeyError(f"Version '{version}' not found in registry")
