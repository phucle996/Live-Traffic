# ==============================================================================
# Unit Tests for Lab Asset Import & Manifest Generation (tests/unit/test_lab_asset_import.py)
# ==============================================================================

import json
from pathlib import Path
from src.common.config import PROJECT_ROOT
from scripts.import_lab_assets import import_lab_assets


def test_import_lab_assets_extracts_files():
    """
    Verifies that asset import extracts raw files and generates valid manifest.
    """
    manifest = import_lab_assets()

    assert manifest is not None
    assert manifest.get("total_imported_files", 0) > 0

    # Verify manifest JSON artifact exists
    manifest_path = PROJECT_ROOT / "artifacts" / "manifests" / "lab_assets.json"
    assert manifest_path.exists()

    with open(manifest_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert "entries" in data
    assert len(data["entries"]) > 0


if __name__ == "__main__":
    test_import_lab_assets_extracts_files()
    print("All test_lab_asset_import unit tests PASSED!")
