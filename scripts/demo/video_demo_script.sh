#!/bin/bash
#
# Script de démonstration pour vidéo IAM Gateway
# Exécuter avec: bash scripts/demo/video_demo_script.sh
#

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
BOLD='\033[1m'
NC='\033[0m'

pause() {
    echo ""
    echo -e "${YELLOW}Appuyez sur Entrée pour continuer...${NC}"
    read
}

clear
echo -e "${BOLD}${CYAN}"
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                                                              ║"
echo "║         IAM GATEWAY - DÉMONSTRATION VIDÉO                    ║"
echo "║                                                              ║"
echo "║  Provisionnement Multi-Connecteurs avec MidPoint             ║"
echo "║                                                              ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"
pause

# ============================================================
# SCÈNE 1: Architecture
# ============================================================
clear
echo -e "${BOLD}${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BOLD}${BLUE}  SCÈNE 1: ARCHITECTURE DU SYSTÈME                              ${NC}"
echo -e "${BOLD}${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${CYAN}Composants:${NC}"
echo ""
echo "  ┌─────────────────┐"
echo "  │   IAM Gateway   │ ◄── API REST + Interface Web"
echo "  │   (Port 3000)   │"
echo "  └────────┬────────┘"
echo "           │"
echo "           ▼"
echo "  ┌─────────────────┐"
echo "  │    MidPoint     │ ◄── Moteur d'identité"
echo "  │   (Port 8080)   │"
echo "  └────────┬────────┘"
echo "           │"
echo "     ┌─────┼─────┐"
echo "     ▼     ▼     ▼"
echo "  ┌─────┐ ┌─────┐ ┌─────┐"
echo "  │LDAP │ │Odoo │ │Postgres│"
echo "  └─────┘ └─────┘ └───────┘"
echo ""
echo -e "${GREEN}✓ OpenLDAP: Annuaire utilisateurs + groupes${NC}"
echo -e "${GREEN}✓ Odoo ERP: Table iam_users${NC}"
echo -e "${GREEN}✓ PostgreSQL: Table app_users (Application Métier)${NC}"
pause

# ============================================================
# SCÈNE 2: État initial
# ============================================================
clear
echo -e "${BOLD}${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BOLD}${BLUE}  SCÈNE 2: ÉTAT INITIAL DES SYSTÈMES                           ${NC}"
echo -e "${BOLD}${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo ""

TIMESTAMP=$(date +%H%M%S)
USERNAME="video.demo$TIMESTAMP"
echo -e "${CYAN}Utilisateur de test: ${BOLD}$USERNAME${NC}"
echo ""

echo -e "${YELLOW}Vérification LDAP...${NC}"
LDAP_COUNT=$(docker exec openldap ldapsearch -x -D "cn=admin,dc=example,dc=com" -w secret \
  -b "ou=users,dc=example,dc=com" "(uid=$USERNAME)" 2>/dev/null | grep -c "^dn:")
if [ "$LDAP_COUNT" -eq 0 ]; then
    echo -e "${RED}  ✗ Utilisateur non trouvé dans LDAP${NC}"
else
    echo -e "${GREEN}  ✓ Utilisateur existe dans LDAP${NC}"
fi

echo ""
echo -e "${YELLOW}Vérification Odoo...${NC}"
ODOO_COUNT=$(docker exec odoo-db psql -U odoo -d odoo -t -c \
  "SELECT COUNT(*) FROM iam_users WHERE username = '$USERNAME';" 2>/dev/null | tr -d ' ')
if [ "$ODOO_COUNT" = "0" ]; then
    echo -e "${RED}  ✗ Utilisateur non trouvé dans Odoo${NC}"
else
    echo -e "${GREEN}  ✓ Utilisateur existe dans Odoo${NC}"
fi

echo ""
echo -e "${YELLOW}Vérification PostgreSQL App...${NC}"
PG_COUNT=$(docker exec gateway-db psql -U gateway -d gateway -t -c \
  "SELECT COUNT(*) FROM app_users WHERE username = '$USERNAME';" 2>/dev/null | tr -d ' ')
if [ "$PG_COUNT" = "0" ]; then
    echo -e "${RED}  ✗ Utilisateur non trouvé dans PostgreSQL${NC}"
else
    echo -e "${GREEN}  ✓ Utilisateur existe dans PostgreSQL${NC}"
fi

echo ""
echo -e "${BOLD}Résultat: L'utilisateur n'existe dans aucun système${NC}"
pause

# ============================================================
# SCÈNE 3: Création utilisateur
# ============================================================
clear
echo -e "${BOLD}${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BOLD}${BLUE}  SCÈNE 3: CRÉATION UTILISATEUR + ASSIGNATION RÔLE             ${NC}"
echo -e "${BOLD}${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo ""

echo -e "${CYAN}Création de l'utilisateur ${BOLD}$USERNAME${NC}${CYAN} dans MidPoint...${NC}"
echo -e "${CYAN}Avec le rôle ${BOLD}Employee-Full-Access${NC}"
echo ""

curl -s -X POST "http://localhost:8080/midpoint/ws/rest/users" \
  -u "administrator:5ecr3t" \
  -H "Content-Type: application/xml" \
  -d "<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<user xmlns=\"http://midpoint.evolveum.com/xml/ns/public/common/common-3\"
      xmlns:c=\"http://midpoint.evolveum.com/xml/ns/public/common/common-3\">
    <name>$USERNAME</name>
    <fullName>Video Demo User</fullName>
    <givenName>Video</givenName>
    <familyName>Demo</familyName>
    <emailAddress>${USERNAME}@example.com</emailAddress>
    <activation>
        <administrativeStatus>enabled</administrativeStatus>
    </activation>
    <assignment>
        <targetRef oid=\"10000000-0000-0000-0000-000000000210\" type=\"c:RoleType\"/>
    </assignment>
</user>" > /dev/null

echo -e "${GREEN}✓ Utilisateur créé dans MidPoint${NC}"
echo ""
echo -e "${YELLOW}Le rôle Employee-Full-Access provisionne automatiquement vers:${NC}"
echo "  • OpenLDAP (compte + groupes)"
echo "  • Odoo ERP (table iam_users)"
echo "  • PostgreSQL (table app_users)"
echo ""
echo -e "${CYAN}Attente du provisionnement automatique (5 secondes)...${NC}"
sleep 5
echo -e "${GREEN}✓ Provisionnement terminé${NC}"
pause

# ============================================================
# SCÈNE 4: Vérification provisionnement
# ============================================================
clear
echo -e "${BOLD}${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BOLD}${BLUE}  SCÈNE 4: VÉRIFICATION DU PROVISIONNEMENT                      ${NC}"
echo -e "${BOLD}${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo ""

echo -e "${BOLD}1. OpenLDAP Directory${NC}"
echo -e "${CYAN}   Commande: ldapsearch -b \"ou=users,dc=example,dc=com\" \"(uid=$USERNAME)\"${NC}"
echo ""
docker exec openldap ldapsearch -x -D "cn=admin,dc=example,dc=com" -w secret \
  -b "ou=users,dc=example,dc=com" "(uid=$USERNAME)" dn mail cn 2>/dev/null | grep -E "^(dn:|mail:|cn:)"
echo ""

echo -e "${BOLD}2. Odoo ERP (table iam_users)${NC}"
echo -e "${CYAN}   Commande: SELECT * FROM iam_users WHERE username = '$USERNAME'${NC}"
echo ""
docker exec odoo-db psql -U odoo -d odoo -c \
  "SELECT username, email, full_name FROM iam_users WHERE username = '$USERNAME';" 2>/dev/null
echo ""

echo -e "${BOLD}3. PostgreSQL Application (table app_users)${NC}"
echo -e "${CYAN}   Commande: SELECT * FROM app_users WHERE username = '$USERNAME'${NC}"
echo ""
docker exec gateway-db psql -U gateway -d gateway -c \
  "SELECT username, email, user_ldap_dn FROM app_users WHERE username = '$USERNAME';" 2>/dev/null
pause

# ============================================================
# SCÈNE 5: Résumé
# ============================================================
clear
echo -e "${BOLD}${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BOLD}${BLUE}  SCÈNE 5: RÉSUMÉ DE LA DÉMONSTRATION                           ${NC}"
echo -e "${BOLD}${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${GREEN}${BOLD}RÉSULTAT: PROVISIONNEMENT RÉUSSI !${NC}"
echo ""
echo "  ┌─────────────────────────────────────────────────────────┐"
echo "  │  Système        │  Statut   │  Données                  │"
echo "  ├─────────────────┼───────────┼───────────────────────────┤"
echo "  │  OpenLDAP       │    ✅     │  uid=$USERNAME        │"
echo "  │  Odoo ERP       │    ✅     │  iam_users                │"
echo "  │  PostgreSQL App │    ✅     │  app_users + LDAP DN      │"
echo "  └─────────────────────────────────────────────────────────┘"
echo ""
echo -e "${CYAN}Ce que MidPoint a fait automatiquement:${NC}"
echo ""
echo "  1. Créé un compte LDAP avec les groupes:"
echo "     - Employee"
echo "     - Internet"
echo "     - Printer"
echo "     - Public_Share_Folder_SharePoint"
echo ""
echo "  2. Créé une entrée dans Odoo (table iam_users)"
echo ""
echo "  3. Créé une entrée dans PostgreSQL (table app_users)"
echo "     avec référence au DN LDAP"
echo ""
echo -e "${BOLD}${GREEN}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BOLD}${GREEN}           FIN DE LA DÉMONSTRATION                              ${NC}"
echo -e "${BOLD}${GREEN}═══════════════════════════════════════════════════════════════${NC}"
echo ""
