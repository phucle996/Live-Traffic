#!/usr/bin/env bash
# =============================================================================
# scripts/provider_pilot/run_here_flow_pilot.sh
# Phase HERE-0 — Pilot script gọi HERE Traffic API v7 /flow endpoint
# theo từng bounding box của 4 vùng pilot TP.HCM và lưu raw response
# =============================================================================
# Cách dùng:
#   export HERE_API_KEY=<your_key>
#   bash scripts/provider_pilot/run_here_flow_pilot.sh
#
# Output:
#   artifacts/provider_pilot/raw/YYYY-MM-DD_HH-MM-SS_<zone>_<slot>.json
# =============================================================================

set -euo pipefail

# --- 1. Kiểm tra phụ thuộc ---
for cmd in curl jq python3; do
  if ! command -v "$cmd" &>/dev/null; then
    echo "[ERROR] '$cmd' chưa được cài. Cần: curl jq python3" >&2
    exit 1
  fi
done

# --- 2. Kiểm tra API key ---
if [[ -z "${HERE_API_KEY:-}" ]]; then
  echo "[ERROR] Biến môi trường HERE_API_KEY chưa được set." >&2
  echo "  export HERE_API_KEY=<your_development_key>" >&2
  exit 1
fi

# --- 3. Cấu hình thư mục output ---
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
RAW_DIR="${PROJECT_ROOT}/artifacts/provider_pilot/raw"
mkdir -p "${RAW_DIR}"

# --- 4. HERE Traffic API v7 endpoint ---
HERE_FLOW_URL="https://data.traffic.hereapi.com/traffic/6.3/flow.json"
# Lưu ý: Endpoint v7 dùng /v7/flow với bearer token
# Endpoint sau là tương đương Free Tier:
HERE_FLOW_V7="https://data.traffic.hereapi.com/traffic/6.3/flow.json"

# --- 5. Bốn vùng pilot TP.HCM ---
# Định dạng: "name:south,west,north,east"
declare -a PILOT_ZONES=(
  "quan1:10.760,106.692,10.790,106.710"
  "binh_thanh:10.795,106.700,10.820,106.730"
  "thu_duc:10.845,106.770,10.890,106.820"
  "tan_son_nhat:10.800,106.655,10.830,106.685"
)

# --- 6. Time slots thu thập mẫu ---
# Pilot script chạy ngay; slots được ghi trong metadata
declare -a TIME_SLOTS=(
  "peak_morning"
  "off_peak"
  "peak_evening"
  "weekend"
)

# Lấy slot hiện tại dựa vào giờ máy
get_time_slot() {
  local hour
  hour=$(date +%H)
  local dow
  dow=$(date +%u)  # 1=Mon, 7=Sun

  if [[ "$dow" -ge 6 ]]; then
    echo "weekend"
    return
  fi

  if [[ "$hour" -ge 7 && "$hour" -le 9 ]]; then
    echo "peak_morning"
  elif [[ "$hour" -ge 16 && "$hour" -le 19 ]]; then
    echo "peak_evening"
  else
    echo "off_peak"
  fi
}

TIME_SLOT="$(get_time_slot)"
TIMESTAMP="$(date +%Y-%m-%d_%H-%M-%S)"

echo "========================================================"
echo " Phase HERE-0 — HERE Traffic API Pilot"
echo " Timestamp : ${TIMESTAMP}"
echo " Time Slot : ${TIME_SLOT}"
echo " Zones     : ${#PILOT_ZONES[@]}"
echo "========================================================"

# --- 7. Vòng lặp crawl từng vùng ---
for zone_spec in "${PILOT_ZONES[@]}"; do
  zone_name="${zone_spec%%:*}"
  bbox="${zone_spec#*:}"

  # Tách bbox thành 4 góc
  IFS=',' read -r bbox_south bbox_west bbox_north bbox_east <<< "$bbox"

  echo ""
  echo "[INFO] Zone: ${zone_name} | BBox: ${bbox}"

  OUTPUT_FILE="${RAW_DIR}/${TIMESTAMP}_${zone_name}_${TIME_SLOT}.json"
  META_FILE="${RAW_DIR}/${TIMESTAMP}_${zone_name}_${TIME_SLOT}.meta.json"

  # Ghi metadata request trước khi gọi API
  request_ts="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  cat > "${META_FILE}" <<METAEOF
{
  "schema_version": "here0_pilot_v1",
  "zone": "${zone_name}",
  "time_slot": "${TIME_SLOT}",
  "request_timestamp_utc": "${request_ts}",
  "bbox": {
    "south": ${bbox_south},
    "west": ${bbox_west},
    "north": ${bbox_north},
    "east": ${bbox_east}
  },
  "endpoint": "HERE Traffic API v7 /flow",
  "note": "Raw response - NOT for training until license confirmed"
}
METAEOF

  # --- 8. Gọi HERE /v7/flow với bounding box ---
  # Query parameter "bbox" HERE v7 format: south,west,north,east
  HTTP_CODE=$(curl -s -w "%{http_code}" \
    --max-time 30 \
    --connect-timeout 10 \
    -H "Authorization: Bearer ${HERE_API_KEY}" \
    -H "Accept: application/json" \
    --output "${OUTPUT_FILE}.tmp" \
    "https://data.traffic.hereapi.com/traffic/6.3/flow.json?bbox=${bbox_west}%2C${bbox_south}%2C${bbox_east}%2C${bbox_north}&responseattributes=sh,fc&units=metric" \
    2>&1 || true)

  # Ghi HTTP status code vào meta
  python3 - <<PYEOF
import json, os

meta_path = "${META_FILE}"
with open(meta_path, "r") as f:
    meta = json.load(f)
meta["http_status"] = "${HTTP_CODE}"
with open(meta_path, "w") as f:
    json.dump(meta, f, indent=2)
PYEOF

  if [[ "${HTTP_CODE}" == "200" ]]; then
    # Kiểm tra JSON hợp lệ
    if jq empty "${OUTPUT_FILE}.tmp" 2>/dev/null; then
      mv "${OUTPUT_FILE}.tmp" "${OUTPUT_FILE}"

      # Đo nhanh số lượng flow item
      item_count=$(jq '[.results // [] | .[] | .location.shape // empty] | length' "${OUTPUT_FILE}" 2>/dev/null || echo "0")
      file_size=$(du -sh "${OUTPUT_FILE}" | cut -f1)
      echo "[OK]  HTTP 200 | File: $(basename ${OUTPUT_FILE}) | Size: ${file_size} | Items: ~${item_count}"
    else
      echo "[WARN] HTTP 200 nhưng JSON không hợp lệ. Giữ file .tmp để debug."
      mv "${OUTPUT_FILE}.tmp" "${OUTPUT_FILE}.invalid.json"
    fi
  else
    echo "[ERROR] HTTP ${HTTP_CODE} cho zone ${zone_name}. Xem ${OUTPUT_FILE}.tmp để debug."
    mv "${OUTPUT_FILE}.tmp" "${OUTPUT_FILE}.error_${HTTP_CODE}.json" || true
  fi

  # Tránh hammering API — delay 2s giữa các zone
  sleep 2
done

echo ""
echo "========================================================"
echo " Raw output đã lưu tại: ${RAW_DIR}/"
echo " Bước tiếp: chạy summarize_here_pilot.py để phân tích"
echo "   python3 scripts/provider_pilot/summarize_here_pilot.py"
echo "========================================================"
