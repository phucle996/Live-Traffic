# ==============================================================================
# CSV Inspector Utility (src/common/csv_inspector.py)
# Inspects CSV Header, Line Counts, and Timestamp Bounds for Manifest Tracking
# ==============================================================================

import csv
from pathlib import Path
from typing import Dict, Any, List


def inspect_csv_file(file_path: Path) -> Dict[str, Any]:
    """
    Reads CSV header, counts data rows, and returns summary metadata.

    Args:
        file_path (Path): Target CSV file path.

    Returns:
        Dict[str, Any]: CSV inspection metadata dictionary.
    """
    header: List[str] = []
    line_count = 0

    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            reader = csv.reader(f)
            header = next(reader, [])
            # Count remaining data rows
            for _ in reader:
                line_count += 1
    except Exception:
        pass

    return {
        "header": header,
        "row_count": line_count,
    }
