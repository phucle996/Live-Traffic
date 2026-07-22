#!/usr/bin/env bash
# ==============================================================================
# Staging Smoke Test Script (scripts/smoke_test.sh)
# Tests critical API endpoints on staging before production promotion.
# EXIT 1 if any check fails — this BLOCKS the deploy-production.yml workflow.
# Usage: bash scripts/smoke_test.sh <STAGING_API_URL>
# ==============================================================================

set -euo pipefail

# Resolve staging API base URL from argument or environment
STAGING_URL="${1:-${STAGING_API_URL:-http://localhost:8000}}"

# Track overall test pass/fail state
PASS=0
FAIL=0

# Helper: HTTP GET check with expected status code
check_get() {
    local name="$1"
    local endpoint="$2"
    local expected_status="${3:-200}"

    http_status=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 "${STAGING_URL}${endpoint}")
    if [ "$http_status" = "$expected_status" ]; then
        echo "[PASS] ${name} → GET ${endpoint} returned HTTP ${http_status}"
        PASS=$((PASS + 1))
    else
        echo "[FAIL] ${name} → GET ${endpoint} expected HTTP ${expected_status}, got ${http_status}"
        FAIL=$((FAIL + 1))
    fi
}

# Helper: HTTP POST check with JSON payload
check_post() {
    local name="$1"
    local endpoint="$2"
    local payload="$3"
    local expected_status="${4:-200}"

    http_status=$(curl -s -o /dev/null -w "%{http_code}" \
        --max-time 10 \
        -X POST \
        -H "Content-Type: application/json" \
        -d "${payload}" \
        "${STAGING_URL}${endpoint}")

    if [ "$http_status" = "$expected_status" ]; then
        echo "[PASS] ${name} → POST ${endpoint} returned HTTP ${http_status}"
        PASS=$((PASS + 1))
    else
        echo "[FAIL] ${name} → POST ${endpoint} expected HTTP ${expected_status}, got ${http_status}"
        FAIL=$((FAIL + 1))
    fi
}

echo "========================================================"
echo "  Smoke Test: ${STAGING_URL}"
echo "========================================================"

# Test 1: Root endpoint
check_get "Root Endpoint" "/"

# Test 2: Liveness probe — critical path for Kubernetes health
check_get "Liveness Probe" "/health/live"

# Test 3: Readiness probe — model must be loaded and ready
check_get "Readiness Probe" "/health/ready"

# Test 4: Model info endpoint
check_get "Model Info" "/v1/model"

# Test 5: Prediction endpoint — core business logic
check_post "Prediction Endpoint" "/v1/predictions" \
    '{"street_name":"Nam Ky Khoi Nghia","hour":17,"is_weekend":false}'

# Test 6: Live traffic endpoint
check_get "Live Traffic" "/v1/traffic/live"

echo "========================================================"
echo "  Results: ${PASS} passed, ${FAIL} failed"
echo "========================================================"

# Exit 1 if any smoke test failed — blocks production promotion
if [ "$FAIL" -gt 0 ]; then
    echo "[ERROR] Smoke tests FAILED. Production deploy is BLOCKED."
    exit 1
fi

echo "[SUCCESS] All smoke tests passed. Production deploy is ALLOWED."
exit 0
