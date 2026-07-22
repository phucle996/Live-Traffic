#!/usr/bin/env bash
# ==============================================================================
# Project Cleanup Utility Script (scripts/clean_project.sh)
# Removes Bytecode Caches, Pytest Files, Temporary Output Files, & Build Artifacts
# ==============================================================================

set -eo pipefail

echo "======================================================================"
echo "[INFO] Cleaning Project Temporary Files & Cache Artifacts..."
echo "======================================================================"

# Resolve project root directory
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "${PROJECT_ROOT}"

# Remove Python bytecode cache directories
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true
find . -type f -name "*.pyo" -delete 2>/dev/null || true

# Remove Pytest cache & coverage files
rm -rf .pytest_cache/ .coverage htmlcov/ 2>/dev/null || true

# Clean temporary local ingestion outputs (keep .gitkeep)
find data/output -type f ! -name ".gitkeep" -delete 2>/dev/null || true

echo "======================================================================"
echo "[SUCCESS] Project Cleanup Complete!"
echo "======================================================================"
