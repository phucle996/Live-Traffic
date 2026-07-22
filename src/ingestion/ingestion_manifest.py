# ==============================================================================
# Ingestion Checksum Manifest Manager (src/ingestion/ingestion_manifest.py)
# Idempotency Engine Preventing Duplicate Ingestion of Unchanged Raw CSV Files
# ==============================================================================

import json
from pathlib import Path
from typing import Dict, Any

from src.common.config import PROJECT_ROOT
from src.common.file_manifest import compute_sha256
from src.common.logging_utils import get_logger

# Instantiate logger for ingestion manifest
logger = get_logger(__name__)


class IngestionManifest:
    """
    Tracks processed raw file checksums to guarantee ingestion idempotency.
    """

    def __init__(self, manifest_file: Path = None):
        self.manifest_path = manifest_file or (PROJECT_ROOT / "artifacts" / "manifests" / "ingestion_manifest.json")
        self.manifest_path.parent.mkdir(parents=True, exist_ok=True)
        self.processed_entries: Dict[str, Dict[str, Any]] = self._load_manifest()

    def _load_manifest(self) -> Dict[str, Dict[str, Any]]:
        """
        Loads ingestion manifest JSON file.
        """
        if self.manifest_path.exists():
            try:
                with open(self.manifest_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to read ingestion manifest at '{self.manifest_path}': {e}")
        return {}

    def is_file_processed(self, file_path: Path) -> bool:
        """
        Checks if file has already been ingested with matching SHA-256 checksum.

        Args:
            file_path (Path): Target file path.

        Returns:
            bool: True if already ingested and unchanged, else False.
        """
        rel_key = str(file_path.name)
        if rel_key not in self.processed_entries:
            return False

        current_hash = compute_sha256(file_path)
        recorded_hash = self.processed_entries[rel_key].get("sha256")
        return current_hash == recorded_hash

    def mark_file_processed(self, file_path: Path, row_count: int = 0) -> None:
        """
        Records file checksum, size, and ingested row count in manifest.

        Args:
            file_path (Path): Target file path.
            row_count (int): Number of ingested data rows.
        """
        rel_key = str(file_path.name)
        self.processed_entries[rel_key] = {
            "file_size": file_path.stat().st_size,
            "sha256": compute_sha256(file_path),
            "row_count": row_count,
        }
        self._save_manifest()

    def _save_manifest(self) -> None:
        """
        Saves manifest JSON to disk.
        """
        with open(self.manifest_path, "w", encoding="utf-8") as f:
            json.dump(self.processed_entries, f, indent=2)
