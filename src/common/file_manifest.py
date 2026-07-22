# ==============================================================================
# File Manifest & Checksum Utility (src/common/file_manifest.py)
# Generates Cryptographic Checksums, File Sizes, & Inventory Metadata
# ==============================================================================

import hashlib
import os
from pathlib import Path
from typing import Dict, Any


def compute_sha256(file_path: Path) -> str:
    """
    Computes SHA-256 hash checksum of a file.

    Args:
        file_path (Path): Path to target file.

    Returns:
        str: Hexadecimal SHA-256 digest.
    """
    sha256_hash = hashlib.sha256()
    # Read file in 64KB chunks to optimize memory usage
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(65536), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def generate_file_metadata(file_path: Path) -> Dict[str, Any]:
    """
    Generates file metadata dictionary containing size, checksum, and relative path.

    Args:
        file_path (Path): Path to target file.

    Returns:
        Dict[str, Any]: File metadata dictionary.
    """
    file_stat = file_path.stat()
    return {
        "filename": file_path.name,
        "relative_path": str(file_path),
        "size_bytes": file_stat.st_size,
        "sha256": compute_sha256(file_path),
    }
