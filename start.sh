#!/usr/bin/env bash
# Launches the DevX full stack: FastAPI backend (in-memory store) on :8000
# and the static frontend console on :5500. Ctrl+C stops both.
set -e

cd "$(dirname "$0")"

if [ ! -d ".venv" ]; then
  echo "No .venv found — creating one and installing backend dependencies..."
  python3 -m venv .venv
  ./.venv/bin/pip install -q -r requirements.txt
fi

if [ ! -f ".env" ]; then
  cp .env.example .env
  echo "Created .env from .env.example"
fi

cleanup() {
  echo ""
  echo "Stopping..."
  kill "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

echo "Starting backend on http://127.0.0.1:8000 (docs at /docs) ..."
./.venv/bin/uvicorn app.main:app --reload &
BACKEND_PID=$!

echo "Starting frontend on http://127.0.0.1:5500 ..."
(cd frontend && python3 -m http.server 5500) &
FRONTEND_PID=$!

echo ""
echo "DevX is running:"
echo "  Console:  http://127.0.0.1:5500"
echo "  API docs: http://127.0.0.1:8000/docs"
echo "Press Ctrl+C to stop both."

wait
