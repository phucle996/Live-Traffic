#!/usr/bin/env bash
# ==============================================================================
# Rollback Deployment Script (scripts/rollback_deployment.sh)
# Executes helm rollback to previous revision and sends Slack notification.
# Usage: bash scripts/rollback_deployment.sh <RELEASE_NAME> <NAMESPACE>
# ==============================================================================

set -euo pipefail

RELEASE_NAME="${1:-traffic-prediction}"
NAMESPACE="${2:-production}"
SLACK_WEBHOOK="${SLACK_WEBHOOK:-}"

echo "========================================================"
echo "  ROLLBACK INITIATED"
echo "  Release: ${RELEASE_NAME}"
echo "  Namespace: ${NAMESPACE}"
echo "========================================================"

# Step 1: Query the current revision number before rollback
CURRENT_REVISION=$(helm history "${RELEASE_NAME}" \
    --namespace "${NAMESPACE}" \
    --max 1 \
    --output json \
    2>/dev/null | python3 -c "import sys,json; h=json.load(sys.stdin); print(h[0]['revision'])" || echo "unknown")

echo "[INFO] Current helm revision: ${CURRENT_REVISION}"

# Step 2: Execute helm rollback — reverts to the previous revision
# helm rollback with no revision number defaults to previous revision
helm rollback "${RELEASE_NAME}" 0 \
    --namespace "${NAMESPACE}" \
    --wait \
    --timeout 5m

ROLLBACK_STATUS=$?

if [ "${ROLLBACK_STATUS}" -eq 0 ]; then
    echo "[SUCCESS] Helm rollback completed successfully."
    NOTIFICATION_STATUS="ROLLBACK SUCCESSFUL"
else
    echo "[ERROR] Helm rollback FAILED. Manual intervention required."
    NOTIFICATION_STATUS="ROLLBACK FAILED — MANUAL ACTION REQUIRED"
fi

# Step 3: Send Slack notification if webhook is configured
if [ -n "${SLACK_WEBHOOK}" ]; then
    PAYLOAD=$(printf '{"text":"[Traffic Prediction] %s\\nRelease: %s | Namespace: %s"}' \
        "${NOTIFICATION_STATUS}" "${RELEASE_NAME}" "${NAMESPACE}")
    curl -s -X POST -H "Content-Type: application/json" \
        -d "${PAYLOAD}" "${SLACK_WEBHOOK}" || true
    echo "[INFO] Slack notification sent."
fi

# Exit with rollback status so CI workflow captures failure
exit "${ROLLBACK_STATUS}"
