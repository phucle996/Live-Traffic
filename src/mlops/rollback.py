# ==============================================================================
# Rollback Engine (src/mlops/rollback.py)
# Reverts Production model pointer to the last Archived stable version
# JobLock prevents concurrent rollback race conditions
# ==============================================================================

from typing import Optional, Dict, Any

from src.common.logging_utils import get_logger
from src.mlops.model_registry import ModelRegistry
from src.orchestration.job_lock import JobLock

# Instantiate logger for rollback engine
logger = get_logger(__name__)


class RollbackEngine:
    """
    Reverts the active Production model to the most recently Archived stable version.
    Acquires JobLock("model_promoter") to prevent concurrent promotion conflicts.
    """

    def __init__(self):
        self._registry = ModelRegistry()

    def rollback(self) -> Optional[str]:
        """
        Finds the most recently archived model version and promotes it back to Production.
        Demotes the current Production version to Archived.

        Returns:
            Optional[str]: Version string rolled back to, or None if no archived version exists.
        """
        # Acquire lock — prevents concurrent promote/rollback race conditions
        with JobLock("model_promoter"):
            all_versions = self._registry.get_all_versions()

            # Identify current production version
            current_prod: Optional[Dict[str, Any]] = None
            for v in all_versions:
                if v["stage"] == "Production":
                    current_prod = v
                    break

            # Find most recently archived model (last in list)
            archived_versions = [v for v in all_versions if v["stage"] == "Archived"]

            if not archived_versions:
                logger.error("RollbackEngine: No Archived versions available for rollback.")
                return None

            # Use most recently archived version as rollback target
            rollback_target = archived_versions[-1]
            rollback_version = rollback_target["version"]

            # Demote current Production model to Archived
            if current_prod:
                self._registry.set_stage(current_prod["version"], "Archived")
                logger.info(
                    f"RollbackEngine: Current production '{current_prod['version']}' demoted to Archived."
                )

            # Restore archived model to Production
            self._registry.set_stage(rollback_version, "Production")
            logger.warning(
                f"RollbackEngine: ROLLBACK COMPLETE — '{rollback_version}' restored to Production."
            )

        return rollback_version
