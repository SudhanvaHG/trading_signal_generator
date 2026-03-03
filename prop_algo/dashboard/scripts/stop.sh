#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$(dirname "$SCRIPT_DIR")"

echo "🛑 Stopping PropAlgo Dashboard..."
docker compose down
echo "✅ All containers stopped."
