#!/bin/bash
# Gateway IAM - Stop Script

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "========================================"
echo "  Gateway IAM - Stopping Services"
echo "========================================"

cd "$PROJECT_DIR"

echo ""
echo "Stopping all services..."
docker compose down

echo ""
echo "All services stopped."
echo ""
