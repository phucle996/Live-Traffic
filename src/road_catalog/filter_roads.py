#!/usr/bin/env python3
# ==============================================================================
# Road Catalog Filter (src/road_catalog/filter_roads.py)
# Phase ROAD-1 — Lọc danh mục các tuyến đường lớn và trung bình TP.HCM
# ==============================================================================

import sys
import json
from typing import Dict, Any, List

# Các phân loại đường OpenStreetMap được chấp nhận
ACCEPTED_ROAD_CLASSES = {
    "motorway",
    "motorway_link",
    "trunk",
    "trunk_link",
    "primary",
    "primary_link",
    "secondary",
    "secondary_link",
    "tertiary",
    "tertiary_link",
}

# Các loại đường bị loại bỏ hoàn toàn (hẻm, đường đi bộ, lối nội bộ)
REJECTED_ROAD_CLASSES = {
    "service",
    "track",
    "path",
    "footway",
    "cycleway",
    "steps",
    "living_street",
    "pedestrian",
}

def is_valid_road_feature(feature: Dict[str, Any]) -> bool:
    """
    Kiểm tra xem 1 feature GeoJSON/OSM có thỏa mãn tiêu chí làm road segment không.
    """
    props = feature.get("properties", {})
    highway = props.get("highway", "").lower()

    # Loại bỏ ngay các loại đường hẻm / đi bộ
    if highway in REJECTED_ROAD_CLASSES:
        return False

    # Chấp nhận các đường thuộc danh mục chính
    if highway in ACCEPTED_ROAD_CLASSES:
        return True

    # Bổ sung có điều kiện cho unclassified / residential nếu có tên đường
    if highway in {"unclassified", "residential"}:
        road_name = props.get("name", "").strip()
        if road_name and len(road_name) > 2:
            return True

    return False

def filter_road_features(features: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Lọc danh sách các features theo tiêu chuẩn ROAD-1."""
    filtered = [f for f in features if is_valid_road_feature(f)]
    print(f"[INFO] Lọc {len(features)} đường gốc -> Giữ lại {len(filtered)} đường đạt chuẩn.")
    return filtered

if __name__ == "__main__":
    print("[INFO] Road catalog filter module sẵn sàng.")
