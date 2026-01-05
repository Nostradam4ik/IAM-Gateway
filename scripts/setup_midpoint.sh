#!/usr/bin/env bash
set -euo pipefail

COMPOSE_FILE="$(dirname "$0")/../docker/docker-compose.midpoint.yml"

if [[ ! -f "$COMPOSE_FILE" ]]; then
  echo "docker-compose file not found: $COMPOSE_FILE" >&2
  exit 1
fi

if [[ "${1:-}" == "--recreate" ]]; then
  docker compose -f "$COMPOSE_FILE" down --remove-orphans
fi

docker compose -f "$COMPOSE_FILE" up -d

cat <<'EOF'
MidPoint stack started:
  MidPoint UI     -> http://localhost:8080/midpoint  (admin/admin)
  ApacheDS LDAP   -> ldap://localhost:10389         (cn=admin,dc=example,dc=com)
  Odoo            -> http://localhost:8069
  Intranet DB     -> postgres://intranet:intranet@localhost:55432/intranet

Stop stack:
  docker compose -f infrastructure/docker/docker-compose.midpoint.yml down
EOF

