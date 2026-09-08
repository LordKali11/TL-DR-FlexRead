#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

cd "${PROJECT_ROOT}"

# Activate virtualenv if present
if [ -d "backend/.venv" ]; then
    source backend/.venv/bin/activate
fi

export PYTHONPATH="${PROJECT_ROOT}"
echo "Starting NZZ FlexRead Backend on http://127.0.0.1:8000 ..."
python3 -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
