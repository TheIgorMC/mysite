#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "[deploy] Stopping running containers..."
docker compose stop || true

echo "[deploy] Pulling latest code..."
git pull --ff-only origin main

echo "[deploy] Building and starting stack..."
docker compose up -d --build

echo "[deploy] Done."
