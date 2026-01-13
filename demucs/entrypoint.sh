#!/usr/bin/env bash
set -euo pipefail

# Ensure dirs exist
mkdir -p /app/uploads /app/output

echo "[demucs] entrypoint: starting watcher"
exec python /app/watcher.py