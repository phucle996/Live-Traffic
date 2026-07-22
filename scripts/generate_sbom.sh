#!/usr/bin/env bash
# ==============================================================================
# SBOM Generation Script (scripts/generate_sbom.sh)
# Generates a Software Bill of Materials for software supply chain auditing.
# Uses syft if available, otherwise falls back to pip-audit (Python dependencies).
# Usage: bash scripts/generate_sbom.sh <IMAGE_TAG>
# ==============================================================================

set -euo pipefail

IMAGE_TAG="${1:-unknown}"
OUTPUT_FILE="sbom.json"
REGISTRY="${REGISTRY:-ghcr.io/traffic-prediction}"
IMAGE_REF="${REGISTRY}/traffic-prediction-api:${IMAGE_TAG}"

echo "========================================================"
echo "  Generating SBOM for: ${IMAGE_REF}"
echo "========================================================"

# Strategy 1: Use syft if installed (produces rich CycloneDX / SPDX SBOM)
if command -v syft &> /dev/null; then
    echo "[INFO] Using syft to generate full container SBOM..."
    syft "${IMAGE_REF}" -o cyclonedx-json > "${OUTPUT_FILE}"
    echo "[SUCCESS] SBOM generated via syft → ${OUTPUT_FILE}"

# Strategy 2: Fallback to pip-audit for Python dependency SBOM
elif command -v pip-audit &> /dev/null; then
    echo "[INFO] syft not found. Using pip-audit to generate Python dependency SBOM..."
    pip-audit --format json --output "${OUTPUT_FILE}" || true
    echo "[SUCCESS] Python dependency SBOM generated via pip-audit → ${OUTPUT_FILE}"

# Strategy 3: Minimal fallback — generate pip freeze manifest as JSON
else
    echo "[WARNING] Neither syft nor pip-audit found. Generating minimal pip manifest..."
    python3 -c "
import json, subprocess, datetime
result = subprocess.run(['pip', 'freeze'], capture_output=True, text=True)
packages = []
for line in result.stdout.strip().split('\n'):
    if '==' in line:
        name, version = line.split('==')
        packages.append({'name': name, 'version': version})
sbom = {
    'generated_at': datetime.datetime.utcnow().isoformat() + 'Z',
    'image_tag': '${IMAGE_TAG}',
    'components': packages
}
print(json.dumps(sbom, indent=2))
" > "${OUTPUT_FILE}"
    echo "[SUCCESS] Minimal pip manifest SBOM generated → ${OUTPUT_FILE}"
fi

# Validate output file was created and is non-empty
if [ ! -s "${OUTPUT_FILE}" ]; then
    echo "[ERROR] SBOM file is empty or missing: ${OUTPUT_FILE}"
    exit 1
fi

echo "[INFO] SBOM size: $(wc -c < "${OUTPUT_FILE}") bytes"
echo "[DONE] SBOM ready for archival as build artifact."
