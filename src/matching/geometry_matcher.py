#!/usr/bin/env python3
# ==============================================================================
# Spatial Geometry Matcher (src/matching/geometry_matcher.py)
# Phase HERE-4 / ROAD-2 — Tính điểm tương đồng (Match Score) giữa Flow Item & Segment
# ==============================================================================

import math
from typing import Dict, Any

def calculate_haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Tính khoảng cách Haversine giữa 2 tọa độ theo mét."""
    R = 6371000.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = math.sin(dphi / 2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def compute_distance_score(dist_m: float, max_dist_m: float = 150.0) -> float:
    """Quy đổi khoảng cách (mét) thành score từ 0.0 đến 1.0 (gần hơn -> điểm cao hơn)."""
    if dist_m >= max_dist_m:
        return 0.0
    return max(0.0, 1.0 - (dist_m / max_dist_m))

def compute_bearing_score(bearing1: float, bearing2: float, max_delta_deg: float = 45.0) -> float:
    """Tính điểm tương đồng hướng di chuyển (bearing)."""
    diff = abs(bearing1 - bearing2) % 360.0
    if diff > 180.0:
        diff = 360.0 - diff

    if diff >= max_delta_deg:
        return 0.0
    return max(0.0, 1.0 - (diff / max_delta_deg))

def compute_match_score(
    obs_lat: float,
    obs_lon: float,
    segment: Dict[str, Any],
    obs_bearing: float = None,
    weights: Dict[str, float] = None
) -> float:
    """
    Tính điểm match tổng hợp giữa 1 điểm observation từ provider và 1 road segment catalog.
    """
    if weights is None:
        weights = {"distance": 0.50, "bearing": 0.50}

    # 1. Tính khoảng cách từ điểm observation tới centroid của segment
    dist_m = calculate_haversine(obs_lat, obs_lon, segment["centroid_lat"], segment["centroid_lon"])
    score_dist = compute_distance_score(dist_m)

    # 2. Tính điểm bearing nếu có thông tin hướng
    score_bearing = 1.0
    if obs_bearing is not None and "bearing" in segment:
        score_bearing = compute_bearing_score(obs_bearing, segment["bearing"])

    # Tính điểm trọng số tổng hợp
    total_score = (score_dist * weights.get("distance", 0.5)) + (score_bearing * weights.get("bearing", 0.5))
    return round(total_score, 4)

if __name__ == "__main__":
    sample_seg = {"centroid_lat": 10.7727, "centroid_lon": 106.6980, "bearing": 90.0}
    score = compute_match_score(10.7728, 106.6981, sample_seg, 92.0)
    print(f"[INFO] Calculated match score: {score}")
