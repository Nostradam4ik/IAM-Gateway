#!/bin/bash
# ═══════════════════════════════════════════════════════════════
#  IAM Gateway - Script de demarrage complet
#  Usage : ./start.sh [--reset] [--logs]
#  Options :
#    --reset   Recrée les containers (garde les volumes)
#    --logs    Affiche les logs apres le demarrage
# ═══════════════════════════════════════════════════════════════

set -e

# ── Couleurs ──
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

RESET=false
SHOW_LOGS=false
for arg in "$@"; do
    case $arg in
        --reset) RESET=true ;;
        --logs)  SHOW_LOGS=true ;;
    esac
done

# ── Se placer dans le dossier du projet ──
cd "$(dirname "$0")"

echo ""
echo -e "${BOLD}${BLUE}╔══════════════════════════════════════════╗${NC}"
echo -e "${BOLD}${BLUE}║        IAM Gateway - Demarrage           ║${NC}"
echo -e "${BOLD}${BLUE}╚══════════════════════════════════════════╝${NC}"
echo ""

# ── Reset optionnel ──
if [ "$RESET" = true ]; then
    echo -e "${YELLOW}[RESET] Suppression des containers (volumes conserves)...${NC}"
    docker compose down --remove-orphans 2>/dev/null || true
    echo ""
fi

# ── Etape 1 : Bases de donnees ──
echo -e "${CYAN}[1/4] Demarrage des bases de donnees...${NC}"
docker compose up -d \
    gateway-db \
    midpoint-postgres \
    odoo-db \
    keycloak-db \
    intranet-db

echo -e "      Attente que les BDD soient prets (20s)..."
sleep 20

# Verifier que les BDD sont healthy
for db in gateway-db midpoint-postgres odoo-db keycloak-db intranet-db; do
    status=$(docker inspect --format='{{.State.Health.Status}}' "$db" 2>/dev/null || docker inspect --format='{{.State.Status}}' "$db" 2>/dev/null)
    if [[ "$status" == "healthy" || "$status" == "running" ]]; then
        echo -e "      ${GREEN}✓ $db${NC}"
    else
        echo -e "      ${YELLOW}⚠ $db : $status (on continue quand meme)${NC}"
    fi
done

# ── Etape 2 : Services IAM ──
echo ""
echo -e "${CYAN}[2/4] Demarrage des services IAM (LDAP, Keycloak, MidPoint, Odoo)...${NC}"
docker compose up -d \
    openldap \
    phpldapadmin \
    keycloak \
    odoo \
    midpoint

echo -e "      Attente que les services IAM demarrent (30s)..."
sleep 30

# ── Etape 3 : Gateway backend ──
echo ""
echo -e "${CYAN}[3/4] Demarrage de la Gateway API (FastAPI)...${NC}"
docker compose up -d \
    redis \
    qdrant \
    gateway

echo -e "      Attente que la Gateway API demarre (15s)..."
sleep 15

# Verifier la Gateway
GATEWAY_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health 2>/dev/null)
if [ "$GATEWAY_STATUS" = "200" ]; then
    echo -e "      ${GREEN}✓ Gateway API repond (HTTP 200)${NC}"
else
    echo -e "      ${YELLOW}⚠ Gateway API: HTTP $GATEWAY_STATUS - on redemarre...${NC}"
    docker restart gateway-iam 2>/dev/null || docker restart gateway 2>/dev/null || true
    sleep 10
fi

# ── Etape 4 : Frontend ──
echo ""
echo -e "${CYAN}[4/4] Demarrage du Frontend React...${NC}"
docker compose up -d gateway-frontend

sleep 5

# ── Verification finale ──
echo ""
echo -e "${BOLD}${BLUE}╔══════════════════════════════════════════╗${NC}"
echo -e "${BOLD}${BLUE}║           Etat des services              ║${NC}"
echo -e "${BOLD}${BLUE}╚══════════════════════════════════════════╝${NC}"
echo ""

check_service() {
    local name=$1
    local url=$2
    # -k pour accepter les certificats auto-signes (phpLDAPadmin HTTPS)
    local code=$(curl -sk -o /dev/null -w "%{http_code}" --max-time 5 "$url" 2>/dev/null)
    if [ "$code" = "200" ] || [ "$code" = "302" ] || [ "$code" = "303" ] || [ "$code" = "301" ]; then
        echo -e "  ${GREEN}✓${NC} ${BOLD}$name${NC} → $url"
    else
        echo -e "  ${RED}✗${NC} ${BOLD}$name${NC} → $url ${YELLOW}(HTTP $code)${NC}"
    fi
}

check_service "Gateway Frontend    " "http://localhost:3000"         "200"
check_service "Gateway API         " "http://localhost:8000/health"  "200"
check_service "Gateway Swagger     " "http://localhost:8000/docs"    "200"
check_service "MidPoint            " "http://localhost:8080"         "200"
check_service "Odoo ERP            " "http://localhost:8069"         "200"
check_service "Keycloak SSO        " "http://localhost:8081"         "200"
check_service "phpLDAPadmin        " "http://localhost:8443"         "200"

echo ""
echo -e "${BOLD}Identifiants par defaut :${NC}"
echo -e "  Gateway    → ${CYAN}http://localhost:3000${NC}  admin / admin"
echo -e "  MidPoint   → ${CYAN}http://localhost:8080${NC}  administrator / 5ecr3t"
echo -e "  Odoo       → ${CYAN}http://localhost:8069${NC}  admin / admin"
echo -e "  Keycloak   → ${CYAN}http://localhost:8081${NC}  admin / admin"
echo -e "  phpLDAP    → ${CYAN}http://localhost:8443${NC}  cn=admin,dc=example,dc=org / admin"
echo ""

if [ "$SHOW_LOGS" = true ]; then
    echo -e "${YELLOW}[LOGS] Affichage des logs (Ctrl+C pour quitter)...${NC}"
    docker compose logs -f gateway
fi

echo -e "${GREEN}${BOLD}✓ IAM Gateway pret !${NC}"
echo ""
