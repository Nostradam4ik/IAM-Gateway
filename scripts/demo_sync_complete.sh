#!/bin/bash
#
# Script de Démonstration: Synchronisation Complète Sans Gateway
# Démontre que l'infrastructure IAM fonctionne sans la Gateway
#

set -e

echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║  DEMONSTRATION: SYNCHRONISATION DIRECTE SANS GATEWAY IAM      ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""

# Couleurs pour l'affichage
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Fonction pour afficher les étapes
step() {
    echo -e "${BLUE}[ETAPE]${NC} $1"
}

success() {
    echo -e "${GREEN}[OK]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[ATTENTION]${NC} $1"
}

error() {
    echo -e "${RED}[ERREUR]${NC} $1"
}

# Vérification des services
step "Vérification des services requis..."
echo ""

# Vérifier MidPoint
if curl -s -u administrator:Holimolly1 http://localhost:8080/midpoint/ws/rest/self >/dev/null 2>&1; then
    success "MidPoint est accessible (http://localhost:8080/midpoint)"
else
    warning "MidPoint n'est pas accessible. Démarrage en cours..."
    docker start midpoint-postgres midpoint-core 2>/dev/null || true
    echo "Attente du démarrage de MidPoint (60 secondes)..."
    sleep 60
fi

# Vérifier Odoo
if curl -s http://localhost:8069/web/database/selector >/dev/null 2>&1; then
    success "Odoo est accessible (http://localhost:8069)"
else
    warning "Odoo n'est pas accessible. Démarrage..."
    docker start odoo-db odoo 2>/dev/null || true
    sleep 15
fi

# Vérifier OpenLDAP
if docker exec openldap ldapsearch -x -H ldap://localhost -b "dc=example,dc=com" -D "cn=admin,dc=example,dc=com" -w secret >/dev/null 2>&1; then
    success "OpenLDAP est accessible (localhost:10389)"
else
    error "OpenLDAP n'est pas accessible"
    exit 1
fi

# Vérifier PostgreSQL Intranet
if docker exec intranet-db psql -U intranet -d intranet -c "SELECT 1;" >/dev/null 2>&1; then
    success "PostgreSQL Intranet est accessible (localhost:55432)"
else
    warning "PostgreSQL Intranet n'est pas accessible. Démarrage..."
    docker start intranet-db 2>/dev/null || true
    sleep 5
fi

echo ""
echo "════════════════════════════════════════════════════════════════"
step "SYNCHRONISATION 1: Odoo → MidPoint (via CSV)"
echo "════════════════════════════════════════════════════════════════"
echo ""

# Lancer le script de synchronisation Odoo → MidPoint
if [ -f "scripts/import_odoo_to_midpoint.py" ]; then
    echo "Exécution de import_odoo_to_midpoint.py..."
    python3 scripts/import_odoo_to_midpoint.py
    success "Script d'import Odoo → MidPoint exécuté"
else
    warning "Script import_odoo_to_midpoint.py non trouvé"
fi

echo ""
echo "Attente de l'import MidPoint (10 secondes)..."
sleep 10

echo ""
echo "════════════════════════════════════════════════════════════════"
step "VERIFICATION: Utilisateurs dans chaque système"
echo "════════════════════════════════════════════════════════════════"
echo ""

# Compter les utilisateurs dans MidPoint
echo -n "📊 MidPoint: "
MIDPOINT_COUNT=$(curl -s -u administrator:Holimolly1 \
  http://localhost:8080/midpoint/ws/rest/users 2>/dev/null | grep -c "<user" || echo "N/A")
echo "${MIDPOINT_COUNT} utilisateurs"

# Compter les utilisateurs dans LDAP
echo -n "📊 OpenLDAP: "
LDAP_COUNT=$(docker exec openldap ldapsearch -x -H ldap://localhost \
  -b "ou=people,dc=example,dc=com" \
  -D "cn=admin,dc=example,dc=com" -w secret \
  "(objectClass=inetOrgPerson)" 2>/dev/null | grep -c "^dn:" || echo "N/A")
echo "${LDAP_COUNT} entrées"

# Compter les utilisateurs dans PostgreSQL
echo -n "📊 PostgreSQL: "
POSTGRES_COUNT=$(docker exec intranet-db psql -U intranet -d intranet -t \
  -c "SELECT COUNT(*) FROM users;" 2>/dev/null | tr -d ' ' || echo "N/A")
echo "${POSTGRES_COUNT} utilisateurs"

echo ""
echo "════════════════════════════════════════════════════════════════"
step "SYNCHRONISATION 2: MidPoint → OpenLDAP"
echo "════════════════════════════════════════════════════════════════"
echo ""

echo "ℹ️  La synchronisation MidPoint → LDAP est configurée via:"
echo "   - Ressource: OpenLDAP Directory (OID: 10000000-0000-0000-0000-000000000001)"
echo "   - Fichier: infrastructure/midpoint/resources/openldap-resource.xml"
echo ""

# Tester la ressource LDAP
echo "Test de connexion à la ressource LDAP..."
LDAP_TEST=$(curl -s -X POST -u administrator:Holimolly1 \
  http://localhost:8080/midpoint/ws/rest/resources/10000000-0000-0000-0000-000000000001/test 2>/dev/null || echo "FAIL")

if echo "$LDAP_TEST" | grep -q "success"; then
    success "Ressource OpenLDAP: Status OK"
else
    warning "Ressource OpenLDAP: Vérifier la configuration dans MidPoint"
fi

echo ""
echo "════════════════════════════════════════════════════════════════"
step "SYNCHRONISATION 3: MidPoint → PostgreSQL"
echo "════════════════════════════════════════════════════════════════"
echo ""

echo "ℹ️  La synchronisation MidPoint → PostgreSQL est configurée via:"
echo "   - Ressource: Database Resource"
echo "   - Fichier: infrastructure/midpoint/resources/database-resource.xml"
echo ""

# Vérifier si la table users existe
echo "Vérification de la table 'users' dans PostgreSQL..."
TABLE_EXISTS=$(docker exec intranet-db psql -U intranet -d intranet -t \
  -c "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'users');" 2>/dev/null | tr -d ' ')

if [ "$TABLE_EXISTS" = "t" ]; then
    success "Table 'users' existe dans la base intranet"
else
    warning "Table 'users' n'existe pas. Création..."
    docker exec intranet-db psql -U intranet -d intranet <<EOF
CREATE TABLE IF NOT EXISTS users (
    username VARCHAR(100) PRIMARY KEY,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    email VARCHAR(255) UNIQUE,
    department VARCHAR(100),
    active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
EOF
    success "Table 'users' créée"
fi

echo ""
echo "════════════════════════════════════════════════════════════════"
step "RESULTATS DE LA DEMONSTRATION"
echo "════════════════════════════════════════════════════════════════"
echo ""

echo "📈 Statistiques de synchronisation:"
echo ""
printf "%-20s | %10s\n" "Système" "Utilisateurs"
echo "───────────────────────────────────────────"
printf "%-20s | %10s\n" "MidPoint" "$MIDPOINT_COUNT"
printf "%-20s | %10s\n" "OpenLDAP" "$LDAP_COUNT"
printf "%-20s | %10s\n" "PostgreSQL" "$POSTGRES_COUNT"
echo ""

echo "✅ Points de vérification:"
echo ""
echo "1. Odoo (Source RH):"
echo "   → http://localhost:8069"
echo "   → Login: admin / admin"
echo ""
echo "2. MidPoint (Hub IAM):"
echo "   → http://localhost:8080/midpoint"
echo "   → Login: administrator / Holimolly1"
echo ""
echo "3. phpLDAPadmin (LDAP Interface):"
echo "   → http://localhost:8088"
echo "   → Login DN: cn=admin,dc=example,dc=com / secret"
echo ""
echo "4. PostgreSQL (Base Intranet):"
echo "   → psql -h localhost -p 55432 -U intranet -d intranet"
echo ""

echo "════════════════════════════════════════════════════════════════"
success "DEMONSTRATION TERMINEE"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "📝 Documentation complète:"
echo "   → docs/guides/DEMONSTRATION_SYNC_DIRECTE.md"
echo ""
echo "🔧 Commandes utiles:"
echo "   → python3 scripts/import_odoo_to_midpoint.py  # Re-synchroniser Odoo"
echo "   → docker logs midpoint-core                    # Logs MidPoint"
echo "   → docker exec openldap ldapsearch ...          # Recherche LDAP"
echo ""
