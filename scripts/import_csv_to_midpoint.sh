#!/bin/bash
# Script d'import CSV vers MidPoint
# Usage: ./import_csv_to_midpoint.sh

set -e

MIDPOINT_URL="http://localhost:8080/midpoint"
MIDPOINT_USER="administrator"
MIDPOINT_PASSWORD="Holimolly1"
CSV_RESOURCE_OID="10000000-0000-0000-0000-000000000004"

echo "=============================================="
echo "Import CSV vers MidPoint"
echo "=============================================="

# 1. Exécuter le script Python pour récupérer les données Odoo
echo ""
echo "1. Récupération des données Odoo..."
python3 "$(dirname "$0")/import_odoo_to_midpoint.py"

# 2. Mettre à jour la ressource CSV dans MidPoint
echo ""
echo "2. Mise à jour de la ressource CSV..."
curl -s -X PUT "${MIDPOINT_URL}/ws/rest/resources/${CSV_RESOURCE_OID}" \
  -u "${MIDPOINT_USER}:${MIDPOINT_PASSWORD}" \
  -H "Content-Type: application/xml" \
  -d @"$(dirname "$0")/../infrastructure/midpoint/resources/csv-resource.xml"
echo "✅ Ressource mise à jour"

# 3. Tester la connexion
echo ""
echo "3. Test de la ressource CSV..."
TEST_RESULT=$(curl -s -X POST "${MIDPOINT_URL}/ws/rest/resources/${CSV_RESOURCE_OID}/test" \
  -u "${MIDPOINT_USER}:${MIDPOINT_PASSWORD}" \
  -H "Accept: application/xml" | grep -o "<status>success</status>" | head -1)

if [ -n "$TEST_RESULT" ]; then
    echo "✅ Ressource CSV fonctionnelle"
else
    echo "❌ Erreur de connexion à la ressource"
    exit 1
fi

# 4. Lancer l'import via tâche MidPoint
echo ""
echo "4. Lancement de l'import..."
IMPORT_TASK='<?xml version="1.0" encoding="UTF-8"?>
<task xmlns="http://midpoint.evolveum.com/xml/ns/public/common/common-3"
      xmlns:ri="http://midpoint.evolveum.com/xml/ns/public/resource/instance-3">
    <name>Import CSV Employees - '"$(date +%Y%m%d_%H%M%S)"'</name>
    <executionState>runnable</executionState>
    <activity>
        <work>
            <import>
                <resourceObjects>
                    <resourceRef oid="'"${CSV_RESOURCE_OID}"'"/>
                    <kind>account</kind>
                    <intent>default</intent>
                    <objectclass>ri:AccountObjectClass</objectclass>
                </resourceObjects>
            </import>
        </work>
    </activity>
</task>'

IMPORT_RESULT=$(curl -s -X POST "${MIDPOINT_URL}/ws/rest/tasks" \
  -u "${MIDPOINT_USER}:${MIDPOINT_PASSWORD}" \
  -H "Content-Type: application/xml" \
  -d "${IMPORT_TASK}")

if echo "$IMPORT_RESULT" | grep -q "fatal_error"; then
    echo "⚠️ Erreur lors de la création de la tâche"
    echo "$IMPORT_RESULT" | grep -o "<message>.*</message>" | head -1
else
    echo "✅ Tâche d'import lancée"
fi

# 5. Attendre et vérifier le résultat
echo ""
echo "5. Attente de l'import (10 secondes)..."
sleep 10

# Compter les utilisateurs
USER_COUNT=$(curl -s -u "${MIDPOINT_USER}:${MIDPOINT_PASSWORD}" \
  "${MIDPOINT_URL}/ws/rest/users" \
  -H "Accept: application/json" | python3 -c "
import json, sys
data = json.load(sys.stdin)
users = data.get('object', {}).get('object', [])
if isinstance(users, dict):
    users = [users]
print(len(users))
")

echo ""
echo "=============================================="
echo "✅ Import terminé!"
echo "Nombre d'utilisateurs dans MidPoint: ${USER_COUNT}"
echo "=============================================="
echo ""
echo "Accédez à MidPoint: ${MIDPOINT_URL}"
echo "Login: ${MIDPOINT_USER}"
