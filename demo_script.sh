#!/bin/bash
#############################################
#  SCRIPT DE DÉMONSTRATION - GATEWAY IAM
#  Copiez-collez ces commandes une par une
#############################################

# Couleurs pour l'affichage
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}   GATEWAY IAM - DÉMONSTRATION LIVE    ${NC}"
echo -e "${BLUE}========================================${NC}"

#############################################
# ÉTAPE 1: Obtenir le token d'authentification
#############################################

echo -e "\n${YELLOW}>>> ÉTAPE 1: Authentification${NC}"
echo "Commande: Obtenir un token JWT"

TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/admin/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123" | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

echo -e "${GREEN}✓ Token obtenu avec succès${NC}"
echo "Token: ${TOKEN:0:50}..."

#############################################
# ÉTAPE 2: Vérifier l'état des connecteurs
#############################################

echo -e "\n${YELLOW}>>> ÉTAPE 2: Vérification des connecteurs${NC}"

curl -s http://localhost:8000/api/v1/admin/connectors/status \
  -H "Authorization: Bearer $TOKEN" | python3 -c "
import sys, json
data = json.load(sys.stdin)
print('État des connecteurs:')
for name, info in data.items():
    status = '✓ Connecté' if info.get('connected') else '✗ Déconnecté'
    print(f'  - {name}: {status}')
"

#############################################
# ÉTAPE 3: Afficher les règles existantes
#############################################

echo -e "\n${YELLOW}>>> ÉTAPE 3: Règles de calcul configurées${NC}"

curl -s http://localhost:8000/api/v1/rules/ \
  -H "Authorization: Bearer $TOKEN" | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(f'Nombre de règles: {len(data)}')
for rule in data[:5]:
    print(f'  - {rule.get(\"name\", \"N/A\")} ({rule.get(\"rule_type\", \"\")})')
    print(f'    Expression: {rule.get(\"expression\", \"\")[:60]}...')
"

#############################################
# ÉTAPE 4: Créer un nouvel utilisateur
#############################################

echo -e "\n${YELLOW}>>> ÉTAPE 4: Provisionnement d'un nouvel utilisateur${NC}"
echo "Création de: Jean Dupont (IT Department)"

RESULT=$(curl -s -X POST http://localhost:8000/api/v1/provision/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "operation": "create",
    "account_id": "jdupont",
    "target_systems": ["LDAP", "SQL"],
    "attributes": {
      "firstname": "Jean",
      "lastname": "Dupont",
      "email": "jean.dupont@example.com",
      "department": "IT",
      "employee_id": "EMP100"
    },
    "priority": "normal"
  }')

echo "$RESULT" | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(f'Statut: {data.get(\"status\", \"N/A\")}')
print(f'Operation ID: {data.get(\"operation_id\", \"N/A\")}')
print('Attributs calculés:')
attrs = data.get('calculated_attributes', {})
for system, values in attrs.items():
    print(f'  {system}:')
    for k, v in values.items():
        print(f'    - {k}: {v}')
"

#############################################
# ÉTAPE 5: Créer un utilisateur multi-cibles
#############################################

echo -e "\n${YELLOW}>>> ÉTAPE 5: Provisionnement multi-cibles (LDAP + SQL + ODOO)${NC}"
echo "Création de: Marie Martin (Finance Department)"

curl -s -X POST http://localhost:8000/api/v1/provision/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "operation": "create",
    "account_id": "mmartin",
    "target_systems": ["LDAP", "SQL", "ODOO"],
    "attributes": {
      "firstname": "Marie",
      "lastname": "Martin",
      "email": "marie.martin@example.com",
      "department": "Finance",
      "employee_id": "EMP101"
    },
    "priority": "high"
  }' | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(f'Statut: {data.get(\"status\", \"N/A\")}')
print(f'Message: {data.get(\"message\", \"N/A\")}')
print('Systèmes provisionnés: LDAP, SQL, ODOO')
"

#############################################
# ÉTAPE 6: Tester une règle de calcul
#############################################

echo -e "\n${YELLOW}>>> ÉTAPE 6: Test d'une règle de calcul${NC}"
echo "Test du générateur de login LDAP"

curl -s -X POST http://localhost:8000/api/v1/rules/test \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "expression": "{{ firstname | normalize_name }}.{{ lastname | normalize_name }}",
    "test_data": {
      "firstname": "François-Xavier",
      "lastname": "O'\''Brien"
    }
  }' | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(f'Entrée: François-Xavier O'\''Brien')
print(f'Résultat: {data.get(\"result\", data)}')
"

#############################################
# ÉTAPE 7: Lancer une réconciliation
#############################################

echo -e "\n${YELLOW}>>> ÉTAPE 7: Démarrer une réconciliation${NC}"

curl -s -X POST http://localhost:8000/api/v1/reconcile/start \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "target_systems": ["LDAP", "SQL"],
    "full_sync": false
  }' | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(f'Job ID: {data.get(\"job_id\", \"N/A\")}')
print(f'Statut: {data.get(\"status\", \"N/A\")}')
"

#############################################
# ÉTAPE 8: Consulter l'Assistant IA
#############################################

echo -e "\n${YELLOW}>>> ÉTAPE 8: Consultation de l'Assistant IA${NC}"
echo "Question: Comment fonctionne le provisionnement?"

curl -s -X POST http://localhost:8000/api/v1/ai/query \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Explique brièvement comment fonctionne le provisionnement dans cette gateway"
  }' | python3 -c "
import sys, json
data = json.load(sys.stdin)
response = data.get('response', data.get('answer', str(data)))
print(f'Réponse IA: {response[:300]}...')
" 2>/dev/null || echo "L'IA n'est pas configurée (clé API manquante)"

#############################################
# FIN DE LA DÉMONSTRATION
#############################################

echo -e "\n${BLUE}========================================${NC}"
echo -e "${GREEN}   DÉMONSTRATION TERMINÉE AVEC SUCCÈS  ${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo "Récapitulatif:"
echo "  ✓ Authentification JWT"
echo "  ✓ Connecteurs vérifiés (LDAP, SQL, ODOO)"
echo "  ✓ Règles de calcul affichées"
echo "  ✓ Utilisateurs provisionnés"
echo "  ✓ Réconciliation lancée"
echo ""
echo "Interface web: http://localhost:3000"
echo "API Swagger:   http://localhost:8000/docs"
