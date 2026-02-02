#!/bin/bash
#=============================================================================
# VIDÉO : Synchronisation Odoo → MidPoint via CSV
#=============================================================================
#
# CAS 1 : Export CSV depuis Odoo et import dans MidPoint
#
# Usage:
#     ./export_odoo_csv_demo.sh
#
#=============================================================================

set -e

# Couleurs pour l'affichage
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
CSV_FILE="/tmp/odoo_employees.csv"
MIDPOINT_CSV_DIR="/opt/midpoint/var/import"
MIDPOINT_CONTAINER="midpoint"

echo ""
echo "======================================================================"
echo "   SYNCHRONISATION ODOO → MIDPOINT VIA CSV"
echo "   CAS 1 : Export CSV et Import dans MidPoint"
echo "======================================================================"
echo "   Date : $(date '+%Y-%m-%d %H:%M:%S')"
echo "======================================================================"
echo ""

#------------------------------------------------------------------------------
# ÉTAPE 1 : Export des employés depuis Odoo vers CSV
#------------------------------------------------------------------------------
echo "----------------------------------------------------------------------"
echo -e "${BLUE}ÉTAPE 1 : Export des employés Odoo vers CSV${NC}"
echo "----------------------------------------------------------------------"
echo ""

# Créer le fichier CSV avec les employés d'Odoo via Python
python3 << 'PYTHON_SCRIPT'
import xmlrpc.client
import csv
import sys

ODOO_URL = 'http://localhost:8069'
ODOO_DB = 'odoo'
ODOO_USER = 'admin'
ODOO_PASSWORD = 'admin'
CSV_FILE = '/tmp/odoo_employees.csv'

print("   Connexion à Odoo...")

try:
    common = xmlrpc.client.ServerProxy(f'{ODOO_URL}/xmlrpc/2/common')
    uid = common.authenticate(ODOO_DB, ODOO_USER, ODOO_PASSWORD, {})

    if not uid:
        print("   ❌ Échec authentification Odoo")
        sys.exit(1)

    print(f"   ✅ Connecté à Odoo (UID: {uid})")

    models = xmlrpc.client.ServerProxy(f'{ODOO_URL}/xmlrpc/2/object')

    # Récupérer les employés
    employees = models.execute_kw(
        ODOO_DB, uid, ODOO_PASSWORD,
        'hr.employee', 'search_read',
        [[]],
        {'fields': ['name', 'work_email', 'work_phone', 'department_id', 'job_id']}
    )

    print(f"   ✅ {len(employees)} employé(s) trouvé(s)")

    # Écrire le CSV
    with open(CSV_FILE, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f, delimiter=';')

        # En-tête
        writer.writerow(['uid', 'givenName', 'familyName', 'fullName', 'email', 'phone', 'department'])

        for emp in employees:
            name = emp.get('name', '')
            parts = name.split(' ', 1)
            given = parts[0] if parts else ''
            family = parts[1] if len(parts) > 1 else ''
            login = f"{given.lower()}.{family.lower().replace(' ', '')}".replace('..', '.')
            email = emp.get('work_email', '') or ''
            phone = emp.get('work_phone', '') or ''
            dept = emp.get('department_id')
            dept_name = dept[1] if dept else ''

            writer.writerow([login, given, family, name, email, phone, dept_name])
            print(f"   • {name} → {login}")

    print(f"\n   ✅ Fichier CSV créé : {CSV_FILE}")

except Exception as e:
    print(f"   ❌ Erreur : {e}")
    sys.exit(1)
PYTHON_SCRIPT

echo ""
read -p "   Appuyez sur Entrée pour voir le contenu du CSV..."

#------------------------------------------------------------------------------
# ÉTAPE 2 : Afficher le contenu du CSV
#------------------------------------------------------------------------------
echo ""
echo "----------------------------------------------------------------------"
echo -e "${BLUE}ÉTAPE 2 : Contenu du fichier CSV${NC}"
echo "----------------------------------------------------------------------"
echo ""
echo "   Fichier : $CSV_FILE"
echo ""
echo "   Contenu :"
echo "   ---------"
cat "$CSV_FILE" | while IFS= read -r line; do
    echo "   $line"
done
echo ""

read -p "   Appuyez sur Entrée pour copier le CSV vers MidPoint..."

#------------------------------------------------------------------------------
# ÉTAPE 3 : Copier le CSV dans le conteneur MidPoint
#------------------------------------------------------------------------------
echo ""
echo "----------------------------------------------------------------------"
echo -e "${BLUE}ÉTAPE 3 : Copie du CSV vers MidPoint${NC}"
echo "----------------------------------------------------------------------"
echo ""

# Trouver le nom exact du conteneur MidPoint
CONTAINER_NAME=$(docker ps --format '{{.Names}}' | grep -i midpoint | grep -v db | head -1)

if [ -z "$CONTAINER_NAME" ]; then
    echo -e "   ${RED}❌ Conteneur MidPoint non trouvé${NC}"
    exit 1
fi

echo "   Conteneur MidPoint : $CONTAINER_NAME"
echo "   Fichier source : $CSV_FILE"
echo "   Destination : $MIDPOINT_CSV_DIR/hr_employees.csv"
echo ""

# Créer le répertoire si nécessaire
docker exec "$CONTAINER_NAME" mkdir -p "$MIDPOINT_CSV_DIR" 2>/dev/null || true

# Copier le fichier
docker cp "$CSV_FILE" "$CONTAINER_NAME:$MIDPOINT_CSV_DIR/hr_employees.csv"

if [ $? -eq 0 ]; then
    echo -e "   ${GREEN}✅ Fichier CSV copié avec succès${NC}"
else
    echo -e "   ${RED}❌ Erreur lors de la copie${NC}"
    exit 1
fi

echo ""
read -p "   Appuyez sur Entrée pour lancer l'import dans MidPoint..."

#------------------------------------------------------------------------------
# ÉTAPE 4 : Lancer l'import dans MidPoint
#------------------------------------------------------------------------------
echo ""
echo "----------------------------------------------------------------------"
echo -e "${BLUE}ÉTAPE 4 : Lancement de l'import dans MidPoint${NC}"
echo "----------------------------------------------------------------------"
echo ""

echo "   Pour terminer l'import :"
echo ""
echo "   1. Ouvrir MidPoint : http://localhost:8080/midpoint"
echo "   2. Menu → Resources → All resources"
echo "   3. Cliquer sur 'HR CSV Resource'"
echo "   4. Bouton 'Import' ou créer une tâche d'import"
echo ""
echo "   Ou utiliser le script Python :"
echo "   python scripts/demo/sync_odoo_to_midpoint_demo.py"
echo ""

echo "======================================================================"
echo -e "   ${GREEN}EXPORT CSV TERMINÉ${NC}"
echo "======================================================================"
echo ""
