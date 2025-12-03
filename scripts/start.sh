#!/bin/bash
# Gateway IAM - Start Script

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "========================================"
echo "  Gateway IAM - Starting Services"
echo "========================================"

cd "$PROJECT_DIR"

# Check if .env exists, if not copy from example
if [ ! -f ".env" ]; then
    echo "Creating .env from .env.example..."
    cp .env.example .env
    echo "Please edit .env with your configuration!"
fi

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "Error: Docker is not running. Please start Docker and try again."
    exit 1
fi

# Start services
echo ""
echo "Starting all services with Docker Compose..."
echo ""

docker compose up -d

echo ""
echo "Waiting for services to be healthy..."
sleep 10

# Check service status
echo ""
echo "Service Status:"
echo "----------------------------------------"
docker compose ps

echo ""
echo "========================================"
echo "  Services are starting!"
echo "========================================"
echo ""
echo "Access URLs:"
echo "  - Gateway API:        http://localhost:8000"
echo "  - Gateway Frontend:   http://localhost:3000"
echo "  - MidPoint:           http://localhost:8080/midpoint"
echo "  - Keycloak:           http://localhost:8081"
echo "  - Odoo:               http://localhost:8069"
echo "  - phpLDAPadmin:       http://localhost:8088"
echo "  - Qdrant Dashboard:   http://localhost:6333/dashboard"
echo ""
echo "Default Credentials:"
echo "  - Gateway:    admin / admin123"
echo "  - MidPoint:   administrator / admin"
echo "  - Keycloak:   admin / admin"
echo "  - LDAP:       cn=admin,dc=example,dc=com / secret"
echo "  - Odoo:       admin / admin"
echo ""
echo "To view logs: docker compose logs -f [service_name]"
echo "To stop all:  docker compose down"
echo ""
