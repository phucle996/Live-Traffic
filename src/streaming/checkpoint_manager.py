# ==============================================================================
# HDFS Checkpoint Manager Engine (src/streaming/checkpoint_manager.py)
# Manages HDFS Offset Checkpoint Locations for Spark Structured Streaming
# ==============================================================================

from pathlib import Path
from src.common.config import settings
from src.common.logging_utils import get_logger

# Instantiate logger for checkpoint manager
logger = get_logger(__name__)


class CheckpointManager:
    """
    Manages Spark Structured Streaming HDFS checkpoint locations for fault-tolerant state recovery.
    """

    DEFAULT_BASE_CHECKPOINT = "/traffic_project/checkpoints"

    @classmethod
    def get_checkpoint_location(cls, query_name: str) -> str:
        """
        Returns HDFS checkpoint directory path for given streaming query.

        Args:
            query_name (str): Identifier name for streaming query.

        Returns:
            str: HDFS URI or local path for checkpoint storage.
        """
        hdfs_uri = getattr(settings, "HDFS_BASE_URI", "file:///home/phucle/Desktop/lab5/data/output")
        base_dir = getattr(settings, "HDFS_CHECKPOINT_DIR", cls.DEFAULT_BASE_CHECKPOINT)
        checkpoint_path = f"{hdfs_uri}{base_dir}/{query_name}"
        logger.info(f"Resolved HDFS Checkpoint Location for query '{query_name}': '{checkpoint_path}'")
        return checkpoint_path
