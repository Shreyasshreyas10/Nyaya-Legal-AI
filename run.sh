#!/bin/bash
# run.sh — start all Nyaya services
# Usage: bash run.sh

set -e

echo "=== Nyaya Legal AI System ==="
echo ""

# 1. Start Ollama (if not already running)
if ! pgrep -x "ollama" > /dev/null; then
    echo "[1/3] Starting Ollama..."
    ollama serve &
    sleep 3
else
    echo "[1/3] Ollama already running."
fi

# 2. Start Arize Phoenix
echo "[2/3] Starting Arize Phoenix at http://localhost:6006 ..."
python -m phoenix.server.main &
sleep 2

# 3. Start FastAPI
echo "[3/3] Starting Nyaya API at http://localhost:8000 ..."
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload

# Ctrl+C to stop all
trap "echo 'Shutting down...'; kill 0" SIGINT
wait
