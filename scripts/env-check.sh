#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

echo "[kty04] cwd: $ROOT_DIR"

if ! command -v uv >/dev/null 2>&1; then
  echo "[kty04] error: uv not found"
  exit 1
fi

uv sync >/dev/null

echo "[kty04] python: $(uv run python -V 2>&1)"
echo "[kty04] executable: $(uv run python -c 'import sys; print(sys.executable)')"

uv run python -c "import flask, pygroupsig; print('[kty04] imports ok')"

echo "[kty04] env check passed"
