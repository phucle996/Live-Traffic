#!/usr/bin/env python3
# ==============================================================================
# Road Catalog PostGIS Importer (src/road_catalog/import_to_postgres.py)
# Phase ROAD-1 — Import road catalog JSON artifacts sang PostgreSQL/PostGIS database
# ==============================================================================

import json
import os
import sys
import subprocess
from pathlib import Path

def import_catalog_to_psql():
    project_root = Path(__file__).parent.parent.parent.resolve()
    json_path = project_root / "artifacts" / "road_catalog" / "road_segments.json"

    if not json_path.exists():
        print(f"[ERROR] Không tìm thấy {json_path}. Hãy chạy export_catalog.py trước.")
        sys.exit(1)

    with open(json_path, "r", encoding="utf-8") as f:
        segments = json.load(f)

    sql_statements = []
    sql_statements.append("BEGIN;")

    for seg in segments:
        seg_id    = seg["segment_id"]
        cat_ver   = seg["catalog_version"]
        road_name = seg["road_name"].replace("'", "''")
        road_cls  = seg["road_class"]
        direction = seg["direction"]
        length_m  = seg["length_m"]
        bearing   = seg["bearing"]
        lanes     = seg.get("lanes", 2)
        speed_lim = seg.get("speed_limit_kph", 50.0)
        district  = seg.get("district", "Unknown").replace("'", "''")

        c_lat = seg["centroid_lat"]
        c_lon = seg["centroid_lon"]
        geom_hash = seg["geometry_hash"]

        # Dựng WKT LineString từ chuỗi coordinates [[lon, lat], ...]
        coords = seg["coordinates"]
        line_pts = ", ".join([f"{pt[0]} {pt[1]}" for pt in coords])
        wkt_line = f"ST_GeomFromText('LINESTRING({line_pts})', 4326)"
        wkt_point = f"ST_GeomFromText('POINT({c_lon} {c_lat})', 4326)"

        sql = f"""
        INSERT INTO road_segment (
            segment_id, catalog_version, road_name, road_class, direction,
            length_m, bearing, lanes, speed_limit_kph, district,
            geometry, centroid, geometry_hash, active
        ) VALUES (
            '{seg_id}', '{cat_ver}', '{road_name}', '{road_cls}', '{direction}',
            {length_m}, {bearing}, {lanes}, {speed_lim}, '{district}',
            {wkt_line}, {wkt_point}, '{geom_hash}', TRUE
        ) ON CONFLICT (segment_id) DO UPDATE SET
            road_name = EXCLUDED.road_name,
            length_m = EXCLUDED.length_m,
            active = TRUE;
        """
        sql_statements.append(sql)

    sql_statements.append("COMMIT;")
    full_sql = "\n".join(sql_statements)

    # Chạy psql qua docker exec
    cmd = ["sudo", "docker", "exec", "-i", "postgres-postgis", "psql", "-U", "postgres", "-d", "traffic_db"]
    proc = subprocess.run(cmd, input=full_sql, text=True, capture_output=True)

    if proc.returncode != 0:
        print(f"[ERROR] Import psql thất bại: {proc.stderr}")
        sys.exit(1)

    print(f"[OK] Đã import thành công {len(segments)} road segments vào PostGIS `road_segment` table.")

if __name__ == "__main__":
    import_catalog_to_psql()
