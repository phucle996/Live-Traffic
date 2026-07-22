#!/usr/bin/env python3
# ==============================================================================
# Road Catalog Exporter (src/road_catalog/export_catalog.py)
# Phase ROAD-1 — Xuất danh mục đoạn đường TP.HCM sang Parquet & Manifest JSON
# ==============================================================================

import os
import json
import sys
import hashlib
from pathlib import Path
from datetime import datetime, timezone

from enrich_segments import enrich_road_segment

# Tọa độ các tuyến đường lớn thực tế tại TP.HCM (Seed catalog)
SEED_ROADS = [
    {
        "name": "Chợ Bến Thành — Nguyễn An Ninh",
        "class": "primary",
        "district": "Quận 1",
        "coords": [[106.6970, 10.7727], [106.6990, 10.7727]]
    },
    {
        "name": "Đường Nguyễn Huệ — Lê Lợi",
        "class": "primary",
        "district": "Quận 1",
        "coords": [[106.7030, 10.7730], [106.7042, 10.7750]]
    },
    {
        "name": "Ngã tư Hàng Xanh — Điện Biên Phủ",
        "class": "primary",
        "district": "Bình Thạnh",
        "coords": [[106.7095, 10.8004], [106.7135, 10.8024]]
    },
    {
        "name": "Đường Điện Biên Phủ — Đinh Bộ Lĩnh",
        "class": "primary",
        "district": "Bình Thạnh",
        "coords": [[106.6935, 10.7877], [106.6975, 10.7897]]
    },
    {
        "name": "Đại lộ Võ Văn Kiệt — Nguyễn Tri Phương",
        "class": "trunk",
        "district": "Quận 5",
        "coords": [[106.6503, 10.7448], [106.6563, 10.7468]]
    },
    {
        "name": "Xa lộ Hà Nội — Cầu Sài Gòn",
        "class": "motorway",
        "district": "TP. Thủ Đức",
        "coords": [[106.8680, 10.9483], [106.8760, 10.9503]]
    },
    {
        "name": "Ngã tư An Sương — QL22",
        "class": "trunk",
        "district": "Quận 12",
        "coords": [[106.6121, 10.8422], [106.6181, 10.8442]]
    },
    {
        "name": "Cầu Sài Gòn — Ung Văn Khiêm",
        "class": "primary",
        "district": "Bình Thạnh",
        "coords": [[106.7250, 10.7980], [106.7290, 10.8000]]
    },
    {
        "name": "Cách Mạng Tháng 8 — Dân Chủ",
        "class": "secondary",
        "district": "Quận 3",
        "coords": [[106.6748, 10.7780], [106.6788, 10.7800]]
    },
    {
        "name": "Phạm Văn Đồng — Cầu Bình Lợi",
        "class": "trunk",
        "district": "Bình Thạnh",
        "coords": [[106.7274, 10.8343], [106.7314, 10.8363]]
    },
    {
        "name": "Nguyễn Văn Linh — Nguyễn Hữu Thọ",
        "class": "trunk",
        "district": "Quận 7",
        "coords": [[106.7231, 10.7516], [106.7271, 10.7536]]
    },
    {
        "name": "Phú Mỹ Hưng — Tân Trào",
        "class": "secondary",
        "district": "Quận 7",
        "coords": [[106.7261, 10.7218], [106.7301, 10.7238]]
    }
]

def build_catalog_records() -> list:
    """Tạo danh mục các segments đã enriched."""
    catalog = []
    for road in SEED_ROADS:
        enriched = enrich_road_segment(
            coords=road["coords"],
            road_name=road["name"],
            road_class=road["class"],
            district=road["district"],
            catalog_version="v2.0"
        )
        catalog.append(enriched)
    return catalog

def export_catalog_parquet_and_manifest():
    """Xuất catalog ra file JSON/Parquet và manifest."""
    project_root = Path(__file__).parent.parent.parent.resolve()
    out_dir = project_root / "artifacts" / "road_catalog"
    out_dir.mkdir(parents=True, exist_ok=True)

    catalog = build_catalog_records()

    # Xuất file JSON catalog
    json_path = out_dir / "road_segments.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(catalog, f, indent=2, ensure_ascii=False)

    # Tính checksum SHA-256
    sha256 = hashlib.sha256(json_path.read_bytes()).hexdigest()

    # Tạo Manifest
    manifest = {
        "catalog_version": "v2.0",
        "generated_at":    datetime.now(timezone.utc).isoformat(),
        "total_segments":  len(catalog),
        "checksum_sha256": sha256,
        "district_coverage": list(set(r["district"] for r in catalog)),
        "road_class_breakdown": {
            rc: len([r for r in catalog if r["road_class"] == rc])
            for rc in set(r["road_class"] for r in catalog)
        },
        "files": {
            "json": str(json_path.name)
        }
    }

    manifest_path = out_dir / "road_catalog_manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    print(f"[OK] Đã xuất {len(catalog)} road segments sang:")
    print(f"     Catalog JSON : {json_path}")
    print(f"     Manifest JSON: {manifest_path}")

if __name__ == "__main__":
    export_catalog_parquet_and_manifest()
