# ==============================================================================
# Lab Asset Import & Inventory Script (scripts/import_lab_assets.py)
# Unpacks Lab ZIP Archives or Indexes Existing data/ Directory & Generates Manifest
# ==============================================================================

import argparse
import json
import os
import shutil
import tempfile
import zipfile
from pathlib import Path
from typing import Dict, Any

from src.common.config import PROJECT_ROOT
from src.common.file_manifest import generate_file_metadata
from src.common.csv_inspector import inspect_csv_file
from src.common.logging_utils import get_logger

# Instantiate logger for asset importer
logger = get_logger(__name__)


def import_lab_assets(data_zip_path: str = None, code_zip_path: str = None) -> Dict[str, Any]:
    """
    Unpacks Lab data and code ZIP files if present, or indexes existing data/ directory,
    generating artifacts/manifests/lab_assets.json manifest.
    """
    logger.info("Executing Lab Assets Importer / Indexer...")

    # Default ZIP file paths in project root
    data_zip = Path(data_zip_path or (PROJECT_ROOT / "Data & process_data-20260709T105216Z-3-001.zip"))
    code_zip = Path(code_zip_path or (PROJECT_ROOT / "Code & Model-20260709T105215Z-2-001.zip"))

    # Define target extraction directories
    lab_raw_dir = PROJECT_ROOT / "data" / "lab_raw"
    lab_ref_dir = PROJECT_ROOT / "data" / "lab_reference"
    locations_dir = PROJECT_ROOT / "data" / "locations"

    lab_raw_dir.mkdir(parents=True, exist_ok=True)
    lab_ref_dir.mkdir(parents=True, exist_ok=True)
    locations_dir.mkdir(parents=True, exist_ok=True)

    manifest_entries = []

    # If ZIP file exists, extract it
    if data_zip.exists():
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            logger.info(f"Extracting Data ZIP archive '{data_zip.name}' to temporary directory...")

            with zipfile.ZipFile(data_zip, "r") as zf:
                zf.extractall(tmp_path)

            for root, _, files in os.walk(tmp_path):
                for file in files:
                    src_file = Path(root) / file
                    if file.endswith("_traffic_data_from_traffic.csv") or "traffic_data" in file:
                        dst_file = lab_raw_dir / file
                        shutil.copy2(src_file, dst_file)
                    elif file == "data_converted.csv":
                        dst_file = locations_dir / file
                        shutil.copy2(src_file, dst_file)
                    elif file == "process_data_spark.csv":
                        dst_file = lab_ref_dir / file
                        shutil.copy2(src_file, dst_file)

    # Index all CSV files in data/lab_raw, data/locations, data/lab_reference
    for target_dir, category in [(lab_raw_dir, "lab_raw"), (locations_dir, "locations"), (lab_ref_dir, "lab_reference")]:
        if target_dir.exists():
            for p in target_dir.rglob("*.csv"):
                meta = generate_file_metadata(p)
                meta.update(inspect_csv_file(p))
                meta["category"] = category
                manifest_entries.append(meta)

    # Save Manifest Artifact JSON
    manifest_dir = PROJECT_ROOT / "artifacts" / "manifests"
    manifest_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = manifest_dir / "lab_assets.json"

    manifest_data = {
        "generated_at": str(manifest_path.stat().st_mtime if manifest_path.exists() else 0),
        "data_zip_source": data_zip.name if data_zip.exists() else "Extracted (ZIP removed)",
        "code_zip_source": code_zip.name if code_zip.exists() else "Extracted (ZIP removed)",
        "total_imported_files": len(manifest_entries),
        "entries": manifest_entries,
    }

    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest_data, f, indent=2)

    logger.info(f"Import/Indexing complete! Created manifest at '{manifest_path}' with {len(manifest_entries)} entry(ies).")
    return manifest_data


def main():
    """
    CLI Entrypoint for importing lab assets.
    """
    parser = argparse.ArgumentParser(description="Import and Inventory Lab 5 Assets")
    parser.add_argument("--data-zip", type=str, default=None, help="Path to Data & process_data ZIP file")
    parser.add_argument("--code-zip", type=str, default=None, help="Path to Code & Model ZIP file")
    args = parser.parse_args()

    manifest = import_lab_assets(args.data_zip, args.code_zip)
    print("\n======================================================================")
    print(f"[SUCCESS] Lab Assets Imported! Total files: {manifest.get('total_imported_files', 0)}")
    print("======================================================================\n")


if __name__ == "__main__":
    main()
