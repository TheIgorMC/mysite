#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "[deploy] Stopping running containers..."
docker compose stop || true

echo "[deploy] Pulling latest code..."
git pull --ff-only origin main

echo "[deploy] Merging tracked updates into local_data/..."
if command -v python3 >/dev/null 2>&1; then
	python3 scripts/setup_local_data.py
elif command -v python >/dev/null 2>&1; then
	python scripts/setup_local_data.py
else
	echo "[deploy] ERROR: Python is required to run scripts/setup_local_data.py"
	exit 1
fi

echo "[deploy] Building and recreating stack..."
docker compose up -d --build --force-recreate

echo "[deploy] Done."
