#!/bin/bash
# Gateway IAM - Database Initialization Script

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "========================================"
echo "  Gateway IAM - Database Initialization"
echo "========================================"

cd "$PROJECT_DIR"

# Wait for database to be ready
echo "Waiting for database to be ready..."
sleep 5

# Run migrations inside the gateway container
echo "Running database migrations..."
docker compose exec -T gateway python -m app.db.migrations

echo ""
echo "Database initialization completed!"
echo ""
