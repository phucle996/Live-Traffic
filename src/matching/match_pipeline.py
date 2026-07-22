#!/usr/bin/env python3
# ==============================================================================
# Spatial Matching Pipeline (src/matching/match_pipeline.py)
# Phase HERE-4 / ROAD-2 — Pipeline Khớp Tọa Độ Provider Flow -> Road Catalog Segment ID
# ==============================================================================

import json
import sys
from pathlib import Path
from typing import List, Dict, Any

from geometry_matcher import compute_match_score

def load_road_catalog() -> List[Dict[str, Any]]:
    """Nạp danh mục các đoạn đường từ artifacts/road_catalog/road_segments.json."""
    project_root = Path(__file__).parent.parent.parent.resolve()
    cat_path = project_root / "artifacts" / "road_catalog" / "road_segments.json"

    if not cat_path.exists():
        print(f"[WARN] Không tìm thấy catalog tại {cat_path}. Đang sinh catalog mẫu...")
        from road_catalog.export_catalog import build_catalog_records
        return build_catalog_records()

    with open(cat_path, "r", encoding="utf-8") as f:
        return json.load(f)

def match_flow_observations(
    observations: List[Dict[str, Any]],
    catalog: List[Dict[str, Any]],
    min_score: float = 0.60
) -> Dict[str, Any]:
    """
    Thực hiện Spatial Matching cho danh sách các Flow Observations:
    Gán segment_id, match_score và phân loại:
    - matched    : score >= min_score
    - ambiguous  : score gần bằng nhau giữa top 1 và top 2
    - unmatched  : score < min_score
    """
    matched_items = []
    unmatched_items = []
    ambiguous_items = []

    for obs in observations:
        lat = obs.get("latitude", 0.0)
        lon = obs.get("longitude", 0.0)
        obs_bearing = obs.get("bearing")

        best_score = -1.0
        best_segment = None
        second_score = -1.0

        for seg in catalog:
            score = compute_match_score(lat, lon, seg, obs_bearing)
            if score > best_score:
                second_score = best_score
                best_score = score
                best_segment = seg
            elif score > second_score:
                second_score = score

        if best_segment and best_score >= min_score:
            # Kiểm tra xem có bị ambiguous (mờ nhạt giữa 2 segment gần nhau) không
            if (best_score - second_score) < 0.05:
                obs["matched_segment_id"] = best_segment["segment_id"]
                obs["match_score"] = best_score
                obs["match_status"] = "ambiguous"
                ambiguous_items.append(obs)
            else:
                obs["matched_segment_id"] = best_segment["segment_id"]
                obs["match_score"] = best_score
                obs["match_status"] = "matched"
                matched_items.append(obs)
        else:
            obs["matched_segment_id"] = None
            obs["match_score"] = best_score if best_score > 0 else 0.0
            obs["match_status"] = "unmatched"
            unmatched_items.append(obs)

    total = len(observations)
    matched_pct = (len(matched_items) / total * 100) if total > 0 else 0.0

    return {
        "total_observations": total,
        "matched_count":     len(matched_items),
        "ambiguous_count":   len(ambiguous_items),
        "unmatched_count":   len(unmatched_items),
        "matched_percentage": round(matched_pct, 2),
        "matched_items":     matched_items,
        "ambiguous_items":   ambiguous_items,
        "unmatched_items":   unmatched_items,
    }

if __name__ == "__main__":
    catalog = load_road_catalog()
    sample_obs = [
        {"latitude": 10.7727, "longitude": 106.6980, "current_speed_kph": 15.0},
        {"latitude": 10.8005, "longitude": 106.7100, "current_speed_kph": 25.0},
        {"latitude": 10.9999, "longitude": 106.9999, "current_speed_kph": 50.0}, # Out of bounds
    ]
    result = match_flow_observations(sample_obs, catalog)
    print(f"[OK] Spatial matching complete:")
    print(f"     Matched: {result['matched_count']}/{result['total_observations']} ({result['matched_percentage']}%)")
    print(f"     Unmatched: {result['unmatched_count']}")
