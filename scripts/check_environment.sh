#!/bin/bash
# Script de vérification de l'environnement MidPoint

set -e

echo "========================================="
echo "Vérification de l'environnement MidPoint"
echo "========================================="
echo ""

# Couleurs
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

check_passed=0
check_failed=0

# Fonction de vérification
check() {
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓${NC} $1"
        ((check_passed++))
    else
        echo -e "${RED}✗${NC} $1"
        ((check_failed++))
    fi
}

# 1. Vérifier Docker
echo "1. Vérification de Docker..."
docker --version > /dev/null 2>&1
check "Docker installé"

docker compose version > /dev/null 2>&1
check "Docker Compose installé"

# 2. Vérifier les conteneurs
echo ""
echo "2. Vérification des conteneurs..."

docker ps | grep -q "midpoint-core"
check "Conteneur MidPoint en cours d'exécution"

docker ps | grep -q "midpoint-postgres"
check "Conteneur PostgreSQL MidPoint en cours d'exécution"

docker ps | grep -q "apacheds"
check "Conteneur ApacheDS en cours d'exécution"

docker ps | grep -q "odoo"
check "Conteneur Odoo en cours d'exécution"

docker ps | grep -q "intranet-db"
check "Conteneur Intranet DB en cours d'exécution"

# 3. Vérifier la santé de MidPoint
echo ""
echo "3. Vérification de la santé de MidPoint..."

docker inspect midpoint-core --format='{{.State.Health.Status}}' | grep -q "healthy"
check "MidPoint container healthy"

# 4. Vérifier les ports
echo ""
echo "4. Vérification des ports..."

nc -z localhost 8080 2>/dev/null
check "Port 8080 (MidPoint) accessible"

nc -z localhost 10389 2>/dev/null
check "Port 10389 (LDAP) accessible"

nc -z localhost 8069 2>/dev/null
check "Port 8069 (Odoo) accessible"

# 5. Vérifier les fichiers XML
echo ""
echo "5. Vérification des fichiers de configuration..."

[ -f "infrastructure/midpoint/resources/ldap-resource.xml" ]
check "Fichier ldap-resource.xml présent"

[ -f "infrastructure/midpoint/resources/hr-csv.xml" ]
check "Fichier hr-csv.xml présent"

[ -f "infrastructure/midpoint/roles/role-ldap-basic.xml" ]
check "Fichier role-ldap-basic.xml présent"

[ -f "infrastructure/midpoint/roles/role-crm-agent.xml" ]
check "Fichier role-crm-agent.xml présent"

[ -f "infrastructure/midpoint/roles/role-intranet-user.xml" ]
check "Fichier role-intranet-user.xml présent"

# 6. Vérifier le fichier CSV dans le conteneur
echo ""
echo "6. Vérification du fichier CSV dans le conteneur..."

docker exec midpoint-core test -f /opt/midpoint/var/import/hr_sample.csv
check "Fichier CSV copié dans le conteneur MidPoint"

# 7. Vérifier la structure des répertoires
echo ""
echo "7. Vérification de la structure des répertoires..."

[ -d "media/midpoint" ]
check "Répertoire media/midpoint créé"

[ -d "media/apacheds" ]
check "Répertoire media/apacheds créé"

[ -d "media/odoo" ]
check "Répertoire media/odoo créé"

# Résumé
echo ""
echo "========================================="
echo "RÉSUMÉ"
echo "========================================="
echo -e "${GREEN}Vérifications réussies : $check_passed${NC}"
echo -e "${RED}Vérifications échouées : $check_failed${NC}"
echo ""

if [ $check_failed -eq 0 ]; then
    echo -e "${GREEN}✓ Environnement prêt !${NC}"
    echo ""
    echo "Prochaines étapes :"
    echo "1. Ouvrir http://localhost:8080/midpoint"
    echo "2. Se connecter avec administrator/admin"
    echo "3. Suivre le guide : infrastructure/midpoint/CONFIGURATION_GUIDE.md"
    exit 0
else
    echo -e "${RED}✗ Des problèmes ont été détectés${NC}"
    echo ""
    echo "Actions recommandées :"
    echo "1. Vérifier que Docker est démarré"
    echo "2. Relancer : bash infrastructure/scripts/setup_midpoint.sh"
    echo "3. Vérifier les logs : docker logs midpoint-core"
    exit 1
fi
