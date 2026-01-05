#!/bin/bash
# Synchronisation automatique Odoo → MidPoint
# Ce script récupère les employés Odoo, met à jour le CSV, et le Live Sync fait le reste

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="/tmp/odoo_midpoint_sync.log"

echo "$(date): Démarrage de la synchronisation Odoo → MidPoint" >> "$LOG_FILE"

# 1. Récupérer les données Odoo et créer le CSV
python3 "$SCRIPT_DIR/import_odoo_to_midpoint.py" >> "$LOG_FILE" 2>&1

# 2. Forcer le Live Sync immédiatement (optionnel)
curl -s -X POST "http://localhost:8080/midpoint/ws/rest/tasks/10000000-0000-0000-5555-000000000001/run" \
  -u administrator:Holimolly1 >> "$LOG_FILE" 2>&1

echo "$(date): Synchronisation terminée" >> "$LOG_FILE"
