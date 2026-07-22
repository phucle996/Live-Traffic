#!/usr/bin/env python3
# ==============================================================================
# Road Catalog Enricher (src/road_catalog/enrich_segments.py)
# Phase ROAD-1 — Tính toán Centroid, Length (m), Bearing (deg), Direction & Hash
# ==============================================================================

import math
import hashlib
import uuid
from typing import Dict, Any, List, Tuple

def calculate_haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Tính khoảng cách Haversine giữa 2 tọa độ theo mét."""
    R = 6371000.0  # Bán kính Trái Đất tính bằng mét
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = math.sin(dphi / 2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def calculate_bearing(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Tính góc bearing (0 - 360 độ) từ điểm 1 đến điểm 2."""
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dlambda = math.radians(lon2 - lon1)

    y = math.sin(dlambda) * math.cos(phi2)
    x = math.cos(phi1) * math.sin(phi2) - math.sin(phi1) * math.cos(phi2) * math.cos(dlambda)
    bearing = math.degrees(math.atan2(y, x))
    return (bearing + 360.0) % 360.0

def bearing_to_direction(bearing: float) -> str:
    """Chuyển đổi góc bearing thành hướng địa lý (north, south, east, west, northeast, etc.)."""
    if 45.0 <= bearing < 135.0:
        return "east"
    elif 135.0 <= bearing < 225.0:
        return "south"
    elif 225.0 <= bearing < 315.0:
        return "west"
    else:
        return "north"

def generate_geometry_hash(coords: List[List[float]]) -> str:
    """Sinh hash SHA-256 duy nhất đại diện cho chuỗi tọa độ geometry."""
    raw = json_dumps = str(coords)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]

def enrich_road_segment(
    coords: List[List[float]],
    road_name: str,
    road_class: str,
    district: str = "Unknown District",
    catalog_version: str = "v2.0"
) -> Dict[str, Any]:
    """
    Bổ sung các chỉ số hình học cho 1 đoạn đường:
    length_m, bearing, direction, centroid, geometry_hash, stable segment_id.
    """
    if len(coords) < 2:
        raise ValueError("LineString phải chứa ít nhất 2 điểm tọa độ.")

    # Tính tổng chiều dài
    total_length = 0.0
    for i in range(len(coords) - 1):
        lon1, lat1 = coords[i][0], coords[i][1]
        lon2, lat2 = coords[i+1][0], coords[i+1][1]
        total_length += calculate_haversine_distance(lat1, lon1, lat2, lon2)

    # Tính bearing giữa điểm đầu và điểm cuối
    start_lon, start_lat = coords[0][0], coords[0][1]
    end_lon, end_lat = coords[-1][0], coords[-1][1]
    bearing = calculate_bearing(start_lat, start_lon, end_lat, end_lon)
    direction = bearing_to_direction(bearing)

    # Tính centroid
    avg_lon = sum(pt[0] for pt in coords) / len(coords)
    avg_lat = sum(pt[1] for pt in coords) / len(coords)

    geom_hash = generate_geometry_hash(coords)

    # Sinh deterministic UUID v5 từ (catalog_version + road_name + direction + geom_hash)
    ns = uuid.NAMESPACE_DNS
    seed_str = f"{catalog_version}:{road_name}:{direction}:{geom_hash}"
    segment_id = str(uuid.uuid5(ns, seed_str))

    return {
        "segment_id":       segment_id,
        "catalog_version":  catalog_version,
        "road_name":        road_name,
        "road_class":       road_class,
        "direction":        direction,
        "length_m":         round(total_length, 2),
        "bearing":          round(bearing, 2),
        "lanes":            3 if road_class in {"motorway", "trunk", "primary"} else 2,
        "speed_limit_kph":  60.0 if road_class in {"motorway", "trunk"} else 50.0,
        "district":         district,
        "centroid_lat":     round(avg_lat, 6),
        "centroid_lon":     round(avg_lon, 6),
        "geometry_hash":    geom_hash,
        "coordinates":      coords,
        "active":           True,
    }

if __name__ == "__main__":
    sample = enrich_road_segment([[106.6970, 10.7727], [106.6990, 10.7727]], "Cho Ben Thanh", "primary")
    print("[INFO] Sample enriched segment:")
    print(f"       Segment ID: {sample['segment_id']}")
    print(f"       Length    : {sample['length_m']}m | Bearing: {sample['bearing']} deg ({sample['direction']})")
