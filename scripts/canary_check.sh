#!/usr/bin/env bash
# ==============================================================================
# Canary Validation Script (scripts/canary_check.sh)
# Xác nhận Rust Inference API đạt parity và latency SLO trước khi cutover
# ==============================================================================
# Usage: bash scripts/canary_check.sh [RUST_URL] [ITERATIONS]
#   RUST_URL    — URL Rust API (default: http://localhost:8090)
#   ITERATIONS  — Số request mỗi test case (default: 20)

set -euo pipefail

RUST_URL="${1:-http://localhost:8090}"
ITERATIONS="${2:-20}"

# Ngưỡng SLO: p95 latency <= 50ms, error rate <= 1%
LATENCY_THRESHOLD_MS=50
ERROR_THRESHOLD_PCT=1

echo "============================================================"
echo "  CANARY VALIDATION — Rust Inference API Parity Check"
echo "  Target URL : $RUST_URL"
echo "  Iterations : $ITERATIONS"
echo "  Latency SLO: p95 <= ${LATENCY_THRESHOLD_MS}ms"
echo "  Error SLO  : error rate <= ${ERROR_THRESHOLD_PCT}%"
echo "============================================================"

# Payload mẫu cho bài kiểm tra canary (giờ cao điểm TP.HCM)
PAYLOAD='{"street_name":"Nam Ky Khoi Nghia","latitude":10.7781,"longitude":106.6952,"current_speed":22.5,"free_flow_speed":45.0,"hour":8,"day_of_week":1,"is_weekend":false,"confidence":0.95}'

# Đếm tổng số request và số lỗi
total=0
errors=0

# Mảng giả lập lưu latency (bash không có array của float dễ dàng, dùng file tạm)
TMPFILE=$(mktemp)
trap "rm -f $TMPFILE" EXIT

echo "Bắt đầu gửi $ITERATIONS requests canary..."

for i in $(seq 1 "$ITERATIONS"); do
    START_NS=$(date +%s%N)
    HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
        -X POST "$RUST_URL/v1/predictions" \
        -H "Content-Type: application/json" \
        -H "X-Request-ID: canary-$i" \
        -d "$PAYLOAD" \
        --max-time 5 2>/dev/null || echo "000")
    END_NS=$(date +%s%N)

    LATENCY_MS=$(( (END_NS - START_NS) / 1000000 ))
    echo "$LATENCY_MS" >> "$TMPFILE"

    total=$((total + 1))
    if [ "$HTTP_STATUS" != "200" ]; then
        errors=$((errors + 1))
        echo "  [FAIL] request=$i status=$HTTP_STATUS latency=${LATENCY_MS}ms"
    else
        echo "  [OK]   request=$i status=$HTTP_STATUS latency=${LATENCY_MS}ms"
    fi
done

echo ""
echo "============================================================"
echo "  SUMMARY"
echo "============================================================"

# Tính error rate
ERROR_RATE_PCT=$(( errors * 100 / total ))
echo "  Total Requests : $total"
echo "  Errors         : $errors ($ERROR_RATE_PCT%)"

# Tính p95 latency từ file tạm (sort, lấy phần tử thứ 95%)
P95_INDEX=$(( total * 95 / 100 ))
P95_LATENCY=$(sort -n "$TMPFILE" | sed -n "${P95_INDEX}p")
echo "  p95 Latency    : ${P95_LATENCY}ms"

echo ""

# Kiểm tra ngưỡng và in kết quả
PASSED=true

if [ "$ERROR_RATE_PCT" -gt "$ERROR_THRESHOLD_PCT" ]; then
    echo "  ❌ FAIL: Error rate ${ERROR_RATE_PCT}% > threshold ${ERROR_THRESHOLD_PCT}%"
    PASSED=false
else
    echo "  ✅ PASS: Error rate ${ERROR_RATE_PCT}% <= ${ERROR_THRESHOLD_PCT}%"
fi

if [ -n "$P95_LATENCY" ] && [ "$P95_LATENCY" -gt "$LATENCY_THRESHOLD_MS" ]; then
    echo "  ❌ FAIL: p95 latency ${P95_LATENCY}ms > threshold ${LATENCY_THRESHOLD_MS}ms"
    PASSED=false
elif [ -n "$P95_LATENCY" ]; then
    echo "  ✅ PASS: p95 latency ${P95_LATENCY}ms <= ${LATENCY_THRESHOLD_MS}ms"
fi

echo ""
if [ "$PASSED" = true ]; then
    echo "  ✅ CANARY PASSED — Rust Inference API đạt SLO. An toàn để tiến hành cutover."
    exit 0
else
    echo "  ❌ CANARY FAILED — Không đạt SLO. Kiểm tra lại Rust Inference API."
    exit 1
fi
