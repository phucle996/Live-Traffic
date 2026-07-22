#!/usr/bin/env python3
# ==============================================================================
# scripts/provider_pilot/summarize_here_pilot.py
# Phase HERE-0 — Tổng hợp và phân tích raw response từ HERE Traffic API pilot
# Đọc raw JSON + meta trong artifacts/provider_pilot/raw/
# Xuất pilot_report.json và normalized samples sang artifacts/provider_pilot/
# ==============================================================================
# Cách dùng:
#   python3 scripts/provider_pilot/summarize_here_pilot.py
#   python3 scripts/provider_pilot/summarize_here_pilot.py --raw-dir /path/to/raw
# ==============================================================================

import json
import os
import sys
import glob
import argparse
import statistics
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

# --- Đường dẫn mặc định ---
SCRIPT_DIR = Path(__file__).parent.resolve()
PROJECT_ROOT = SCRIPT_DIR.parent.parent
RAW_DIR     = PROJECT_ROOT / "artifacts" / "provider_pilot" / "raw"
NORM_DIR    = PROJECT_ROOT / "artifacts" / "provider_pilot" / "normalized"
REPORT_PATH = PROJECT_ROOT / "artifacts" / "provider_pilot" / "pilot_report.json"

# --- Ngưỡng acceptance criteria (có thể override bằng config) ---
COVERAGE_THRESHOLD_PERCENT = 80.0  # % tổng chiều dài đường mục tiêu
MAX_LATENCY_MS             = 5000  # giới hạn latency chấp nhận được
MIN_ITEMS_PER_ZONE         = 5     # số flow item tối thiểu để coi là có dữ liệu


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Summarize HERE Traffic API pilot results")
    parser.add_argument(
        "--raw-dir",
        type=Path,
        default=RAW_DIR,
        help="Thư mục chứa raw JSON responses từ pilot script"
    )
    parser.add_argument(
        "--out-report",
        type=Path,
        default=REPORT_PATH,
        help="Đường dẫn ghi pilot_report.json"
    )
    return parser.parse_args()


def load_raw_files(raw_dir: Path) -> list[dict]:
    """
    Quét raw_dir tìm tất cả cặp *.json (response) + *.meta.json.
    Trả về list record gồm path, meta và summary.
    """
    records = []

    # Tìm tất cả file meta
    meta_files = sorted(raw_dir.glob("*.meta.json"))
    if not meta_files:
        print(f"[WARN] Không tìm thấy file meta nào trong: {raw_dir}", file=sys.stderr)
        print(f"       Chạy run_here_flow_pilot.sh trước.", file=sys.stderr)
        return records

    for meta_path in meta_files:
        # Tìm response JSON tương ứng (cùng tên bỏ .meta.json -> .json)
        stem = meta_path.name.replace(".meta.json", "")
        resp_path = meta_path.parent / f"{stem}.json"

        record: dict[str, Any] = {
            "meta_path": str(meta_path),
            "resp_path": str(resp_path),
            "meta":      {},
            "summary":   {}
        }

        # Load meta
        try:
            with open(meta_path, "r", encoding="utf-8") as f:
                record["meta"] = json.load(f)
        except Exception as e:
            record["meta"]["error"] = str(e)

        # Load và parse response nếu tồn tại
        if resp_path.exists():
            record["summary"] = extract_summary(resp_path, record["meta"])
        else:
            # Kiểm tra có file lỗi không
            error_files = list(meta_path.parent.glob(f"{stem}.error_*.json"))
            invalid_files = list(meta_path.parent.glob(f"{stem}.invalid.json"))
            if error_files or invalid_files:
                record["summary"] = {
                    "status": "error",
                    "error_files": [str(f) for f in error_files + invalid_files]
                }
            else:
                record["summary"] = {"status": "missing_response"}

        records.append(record)

    return records


def extract_summary(resp_path: Path, meta: dict) -> dict:
    """
    Parse HERE /v7/flow JSON response và trích xuất các metric chính:
    - flow_item_count: số lượng flow items
    - geometry_count: số item có shape geometry
    - speeds: danh sách current speed
    - free_flow_speeds: danh sách free-flow speed
    - jam_factors: danh sách jam factor
    - response_size_bytes
    """
    summary: dict[str, Any] = {
        "status":             "ok",
        "http_status":        meta.get("http_status", "unknown"),
        "zone":               meta.get("zone", "unknown"),
        "time_slot":          meta.get("time_slot", "unknown"),
        "request_timestamp":  meta.get("request_timestamp_utc", ""),
        "response_size_bytes": resp_path.stat().st_size,
        "flow_item_count":    0,
        "geometry_count":     0,
        "speeds_kph":         [],
        "free_flow_speeds_kph": [],
        "jam_factors":        [],
        "road_closed_count":  0,
        "has_data":           False,
    }

    try:
        with open(resp_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        summary["status"] = "invalid_json"
        summary["parse_error"] = str(e)
        return summary

    # HERE /v7/flow response structure:
    # { "results": [ { "location": {...}, "currentFlow": {...} }, ... ] }
    results = data.get("results", [])
    summary["flow_item_count"] = len(results)

    for item in results:
        # Geometry check — HERE v7 shape trong location
        loc = item.get("location", {})
        if loc.get("shape") or loc.get("geometry"):
            summary["geometry_count"] += 1

        # Current flow data
        flow = item.get("currentFlow", {})
        speed = flow.get("speed")          # km/h
        ff    = flow.get("freeFlow")       # km/h
        jam   = flow.get("jamFactor")      # 0–10
        closed = flow.get("roadClosed", False)

        if speed is not None and speed >= 0:
            summary["speeds_kph"].append(speed)
        if ff is not None and ff >= 0:
            summary["free_flow_speeds_kph"].append(ff)
        if jam is not None:
            summary["jam_factors"].append(jam)
        if closed:
            summary["road_closed_count"] += 1

    summary["has_data"] = summary["flow_item_count"] > 0

    # Tính thống kê tốc độ
    if summary["speeds_kph"]:
        speeds = summary["speeds_kph"]
        summary["speed_stats"] = {
            "min":    min(speeds),
            "max":    max(speeds),
            "mean":   round(statistics.mean(speeds), 2),
            "median": round(statistics.median(speeds), 2),
            "stdev":  round(statistics.stdev(speeds), 2) if len(speeds) > 1 else 0,
        }
    if summary["jam_factors"]:
        jams = summary["jam_factors"]
        summary["jam_factor_stats"] = {
            "min":    min(jams),
            "max":    max(jams),
            "mean":   round(statistics.mean(jams), 2),
        }

    return summary


def write_normalized(records: list[dict], norm_dir: Path) -> None:
    """
    Xuất normalized samples sang norm_dir.
    Mỗi record → một file JSON với các trường chuẩn hóa,
    bỏ raw geometry và redact sensitive fields.
    """
    norm_dir.mkdir(parents=True, exist_ok=True)

    for rec in records:
        meta = rec["meta"]
        summary = rec["summary"]

        zone     = meta.get("zone", "unknown")
        ts       = meta.get("request_timestamp_utc", "unknown").replace(":", "-")
        slot     = meta.get("time_slot", "unknown")
        out_name = f"norm_{ts}_{zone}_{slot}.json"
        out_path = norm_dir / out_name

        # Cấu trúc normalized record — KHÔNG chứa raw geometry
        normalized = {
            "schema_version":      "here0_normalized_v1",
            "source":              "here_traffic_api_v7",
            "note":                "NOT for training - license not yet confirmed",
            "zone":                zone,
            "bbox":                meta.get("bbox", {}),
            "time_slot":           slot,
            "request_timestamp":   meta.get("request_timestamp_utc"),
            "http_status":         summary.get("http_status"),
            "flow_item_count":     summary.get("flow_item_count", 0),
            "geometry_count":      summary.get("geometry_count", 0),
            "has_data":            summary.get("has_data", False),
            "response_size_bytes": summary.get("response_size_bytes", 0),
            "speed_stats":         summary.get("speed_stats", {}),
            "jam_factor_stats":    summary.get("jam_factor_stats", {}),
            "road_closed_count":   summary.get("road_closed_count", 0),
            "status":              summary.get("status", "unknown"),
        }

        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(normalized, f, indent=2, ensure_ascii=False)

    print(f"[OK] Normalized samples: {norm_dir}/")


def evaluate_acceptance(records: list[dict]) -> dict:
    """
    Kiểm tra acceptance criteria của Phase HERE-0:
    1. Coverage: ít nhất COVERAGE_THRESHOLD_PERCENT zone có dữ liệu.
    2. Multi-slot: có nhiều time slot khác nhau.
    3. No training (reminder).
    4. Decision ready.
    """
    results = []
    zones_with_data = set()
    slots_seen = set()
    total_items = 0

    for rec in records:
        summary = rec["summary"]
        meta    = rec["meta"]

        if summary.get("has_data"):
            zones_with_data.add(meta.get("zone"))
        if summary.get("flow_item_count", 0) > 0:
            slots_seen.add(meta.get("time_slot"))
        total_items += summary.get("flow_item_count", 0)

    total_zones = 4  # 4 pilot zones theo spec
    coverage_pct = (len(zones_with_data) / total_zones) * 100 if total_zones > 0 else 0

    criteria = {
        "coverage_zones_with_data": {
            "required": f">= {COVERAGE_THRESHOLD_PERCENT}% zones có data",
            "actual":   f"{coverage_pct:.1f}% ({len(zones_with_data)}/{total_zones})",
            "passed":   coverage_pct >= COVERAGE_THRESHOLD_PERCENT,
        },
        "multi_slot_data": {
            "required": "Có data ở ≥ 2 time slots khác nhau",
            "actual":   f"{len(slots_seen)} slots: {list(slots_seen)}",
            "passed":   len(slots_seen) >= 2,
        },
        "no_training_before_license": {
            "required": "Không dùng data train trước khi xác nhận license",
            "actual":   "Reminder — cần xác nhận manually",
            "passed":   None,  # Manual check
        },
        "decision_documented": {
            "required": "Có decision trong docs/providers/provider_decision.md",
            "actual":   "Cần review và điền thủ công",
            "passed":   None,  # Manual check
        },
    }

    # Tổng kết
    passed_auto   = sum(1 for c in criteria.values() if c.get("passed") is True)
    failed_auto   = sum(1 for c in criteria.values() if c.get("passed") is False)
    manual_needed = sum(1 for c in criteria.values() if c.get("passed") is None)

    return {
        "summary": {
            "total_records":       len(records),
            "zones_with_data":     list(zones_with_data),
            "slots_seen":          list(slots_seen),
            "total_flow_items":    total_items,
            "coverage_percent":    round(coverage_pct, 1),
        },
        "criteria":        criteria,
        "passed_auto":     passed_auto,
        "failed_auto":     failed_auto,
        "manual_needed":   manual_needed,
        "overall_auto":    "PASS" if failed_auto == 0 else "FAIL",
    }


def build_report(records: list[dict], acceptance: dict) -> dict:
    """Build pilot_report.json."""
    return {
        "schema_version":    "here0_pilot_report_v1",
        "generated_at":      datetime.now(timezone.utc).isoformat(),
        "phase":             "HERE-0",
        "description":       "HERE Traffic API v7 pilot — TP.HCM 4-zone feasibility",
        "note":              "Raw data NOT for training until license explicitly confirmed",
        "zones": [
            {"name": "quan1",       "bbox": "10.760,106.692 → 10.790,106.710"},
            {"name": "binh_thanh",  "bbox": "10.795,106.700 → 10.820,106.730"},
            {"name": "thu_duc",     "bbox": "10.845,106.770 → 10.890,106.820"},
            {"name": "tan_son_nhat","bbox": "10.800,106.655 → 10.830,106.685"},
        ],
        "records":    [
            {
                "zone":              r["meta"].get("zone"),
                "time_slot":         r["meta"].get("time_slot"),
                "request_timestamp": r["meta"].get("request_timestamp_utc"),
                "http_status":       r["summary"].get("http_status"),
                "flow_item_count":   r["summary"].get("flow_item_count", 0),
                "geometry_count":    r["summary"].get("geometry_count", 0),
                "has_data":          r["summary"].get("has_data", False),
                "speed_stats":       r["summary"].get("speed_stats", {}),
                "jam_factor_stats":  r["summary"].get("jam_factor_stats", {}),
                "status":            r["summary"].get("status"),
            }
            for r in records
        ],
        "acceptance": acceptance,
    }


def main() -> None:
    args = parse_args()
    raw_dir    = args.raw_dir
    out_report = args.out_report

    print("=" * 60)
    print(" Phase HERE-0 — Pilot Report Summarizer")
    print(f" Raw dir : {raw_dir}")
    print(f" Report  : {out_report}")
    print("=" * 60)

    # 1. Load raw files
    records = load_raw_files(raw_dir)
    if not records:
        print("[WARN] Không có dữ liệu để tổng hợp.")
        sys.exit(0)

    print(f"[INFO] Tìm thấy {len(records)} record(s) từ raw dir.")

    # 2. Xuất normalized samples
    write_normalized(records, NORM_DIR)

    # 3. Đánh giá acceptance criteria
    acceptance = evaluate_acceptance(records)

    # 4. Build và ghi report
    report = build_report(records, acceptance)
    out_report.parent.mkdir(parents=True, exist_ok=True)
    with open(out_report, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"[OK] Report: {out_report}")

    # 5. In tóm tắt acceptance criteria
    print("\n--- Acceptance Criteria ---")
    for key, val in acceptance["criteria"].items():
        status = "✅" if val["passed"] is True else ("❌" if val["passed"] is False else "⚠️  MANUAL")
        print(f"  {status}  {key}")
        print(f"       Required: {val['required']}")
        print(f"       Actual  : {val['actual']}")

    print(f"\n  Auto PASS: {acceptance['passed_auto']}  "
          f"Auto FAIL: {acceptance['failed_auto']}  "
          f"Manual: {acceptance['manual_needed']}")
    print(f"\n  Overall AUTO: {acceptance['overall_auto']}")
    print("\nBước tiếp:")
    print("  1. Điền docs/providers/here_licensing_questions.md")
    print("  2. Điền docs/providers/provider_decision.md")
    print("  3. Nếu decision = approved → tiến sang HERE-1")
    print("=" * 60)


if __name__ == "__main__":
    main()
