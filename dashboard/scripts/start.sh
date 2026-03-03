#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────
#  PropAlgo Dashboard — Production Startup Script
# ─────────────────────────────────────────────────────────────
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DASHBOARD_DIR="$(dirname "$SCRIPT_DIR")"

cd "$DASHBOARD_DIR"

echo ""
echo "╔══════════════════════════════════════════════════════╗"
echo "║         PropAlgo Trading Dashboard — Startup        ║"
echo "╚══════════════════════════════════════════════════════╝"
echo ""

# Check .env exists
if [ ! -f ".env" ]; then
  echo "⚠️  .env file not found. Copying from .env.example..."
  cp .env.example .env
  echo "✅ .env created. Please edit it with your credentials."
  echo "   Then re-run this script."
  exit 1
fi

# Check Docker
if ! command -v docker &>/dev/null; then
  echo "❌ Docker not found. Please install Docker Desktop."
  exit 1
fi

if ! docker info &>/dev/null; then
  echo "❌ Docker daemon not running. Please start Docker Desktop."
  exit 1
fi

echo "🐳 Building and starting containers..."
docker compose up -d --build

echo ""
echo "⏳ Waiting for services to be healthy..."
sleep 10

# Health check
RETRIES=12
for i in $(seq 1 $RETRIES); do
  if curl -sf http://localhost:80/health &>/dev/null; then
    echo ""
    echo "✅ PropAlgo Dashboard is running!"
    echo ""
    echo "   🌐  Dashboard:  http://localhost:80"
    echo "   📡  API Docs:   http://localhost:80/api/docs"
    echo "   🔌  WebSocket:  ws://localhost:80/ws"
    echo ""
    echo "   Use Ctrl+C to stop watching logs, or:"
    echo "   docker compose logs -f    → follow logs"
    echo "   ./scripts/stop.sh         → stop all containers"
    echo ""
    docker compose logs --tail=20
    exit 0
  fi
  echo "   Waiting... ($i/$RETRIES)"
  sleep 5
done

echo ""
echo "❌ Health check failed after ${RETRIES} attempts."
echo "   Check logs with: docker compose logs"
exit 1
