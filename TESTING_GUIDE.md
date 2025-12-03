# Guide de Test et Vérification - Gateway IAM

Ce guide vous permet de vérifier étape par étape que tous les composants du Gateway IAM fonctionnent correctement.

---

## 📋 Prérequis

- Docker et Docker Compose installés
- Ports disponibles : 3000, 6333, 6379, 8000, 8069, 8080, 8081, 8088, 10389
- Au moins 8 GB de RAM disponible

---

## Étape 1 : Préparation de l'Environnement

### 1.1 Vérifier Docker
```bash
docker --version
docker compose version
```
✅ **Attendu** : Versions affichées (Docker 20+ et Compose 2+)

### 1.2 Créer le fichier .env
```bash
cd /home/vboxuser/Desktop/Project3
cp .env.example .env
```
✅ **Attendu** : Fichier `.env` créé

### 1.3 Vérifier les fichiers du projet
```bash
ls -la gateway/
ls -la gateway/frontend/
ls -la docker-compose.yml
```
✅ **Attendu** : Tous les répertoires et fichiers présents

---

## Étape 2 : Démarrage des Services

### 2.1 Démarrer tous les services
```bash
./scripts/start.sh
```
⏱️ **Temps estimé** : 3-5 minutes

### 2.2 Vérifier que tous les containers sont démarrés
```bash
docker compose ps
```
✅ **Attendu** : Tous les services avec l'état "Up" ou "running"

Services attendus :
- gateway-iam
- gateway-frontend
- gateway-db
- gateway-redis
- gateway-qdrant
- midpoint-core
- midpoint-postgres
- openldap
- phpldapadmin
- odoo
- odoo-db
- intranet-db
- keycloak
- keycloak-db

### 2.3 Vérifier les logs en cas d'erreur
```bash
# Pour voir tous les logs
docker compose logs

# Pour un service spécifique
docker compose logs gateway
docker compose logs gateway-db
docker compose logs midpoint
```

---

## Étape 3 : Vérification des Bases de Données

### 3.1 Gateway Database
```bash
docker compose exec gateway-db psql -U gateway -d gateway -c "\dt"
```
✅ **Attendu** : Liste des tables (provisioning_operations, account_state_cache, etc.)

### 3.2 Initialiser la base de données Gateway
```bash
./scripts/init-db.sh
```
✅ **Attendu** : Message "Database initialization completed!"

### 3.3 Vérifier les données initiales
```bash
docker compose exec gateway-db psql -U gateway -d gateway -c "SELECT username, role FROM gateway_users;"
```
✅ **Attendu** : Utilisateur `admin` avec le rôle `admin`

### 3.4 Vérifier Intranet Database
```bash
docker compose exec intranet-db psql -U intranet -d intranet -c "\dt"
```
✅ **Attendu** : Tables users, permissions, groups créées

---

## Étape 4 : Vérification LDAP

### 4.1 Tester la connexion LDAP
```bash
docker compose exec openldap ldapsearch -x -H ldap://localhost -b "dc=example,dc=com" -D "cn=admin,dc=example,dc=com" -w secret
```
✅ **Attendu** : Structure LDAP affichée

### 4.2 Accéder à phpLDAPadmin
Ouvrir dans le navigateur : http://localhost:8088

- Cliquer sur "login"
- Login DN : `cn=admin,dc=example,dc=com`
- Password : `secret`

✅ **Attendu** : Interface phpLDAPadmin accessible avec la structure LDAP

---

## Étape 5 : Vérification MidPoint

### 5.1 Accéder à MidPoint
Ouvrir dans le navigateur : http://localhost:8080/midpoint

- Username : `administrator`
- Password : `admin`

✅ **Attendu** : Page de login MidPoint puis dashboard après connexion

### 5.2 Vérifier les ressources
Dans MidPoint :
1. Aller dans "Resources"
2. Vérifier qu'il n'y a pas d'erreurs

---

## Étape 6 : Vérification Gateway API

### 6.1 Tester que l'API répond
```bash
curl http://localhost:8000/
```
✅ **Attendu** :
```json
{"message":"Gateway IAM API","version":"1.0.0","status":"running"}
```

### 6.2 Vérifier la documentation Swagger
Ouvrir dans le navigateur : http://localhost:8000/docs

✅ **Attendu** : Interface Swagger avec tous les endpoints

### 6.3 Tester l'authentification
```bash
curl -X POST http://localhost:8000/api/admin/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'
```
✅ **Attendu** : Token JWT retourné
```json
{"access_token":"eyJ...","token_type":"bearer"}
```

### 6.4 Récupérer le token pour les tests suivants
```bash
TOKEN=$(curl -s -X POST http://localhost:8000/api/admin/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}' | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)

echo $TOKEN
```
✅ **Attendu** : Token affiché

---

## Étape 7 : Test des Règles de Provisioning

### 7.1 Lister les règles existantes
```bash
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/rules
```
✅ **Attendu** : Liste des règles (ldap_employee_default, intranet_employee_default)

### 7.2 Créer une nouvelle règle
```bash
curl -X POST http://localhost:8000/api/rules \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "test_rule",
    "description": "Test rule for verification",
    "target_system": "ldap",
    "identity_type": "employee",
    "priority": 50,
    "attribute_mappings": {
      "uid": "{{ employee_id }}",
      "cn": "{{ first_name }} {{ last_name }}",
      "mail": "{{ email }}"
    }
  }'
```
✅ **Attendu** : Règle créée avec succès (status 200)

### 7.3 Tester le calcul de règles
```bash
curl -X POST http://localhost:8000/api/rules/calculate \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "target_system": "ldap",
    "identity_type": "employee",
    "source_attributes": {
      "employee_id": "E001",
      "first_name": "Jean",
      "last_name": "Dupont",
      "email": "jean.dupont@example.com"
    }
  }'
```
✅ **Attendu** : Attributs calculés retournés
```json
{
  "uid": "E001",
  "cn": "Jean Dupont",
  "mail": "jean.dupont@example.com"
}
```

---

## Étape 8 : Test de Provisioning

### 8.1 Créer un utilisateur dans LDAP
```bash
curl -X POST http://localhost:8000/api/provision \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "operation_type": "create",
    "identity_type": "employee",
    "identity_id": "E001",
    "target_systems": ["ldap"],
    "attributes": {
      "employee_id": "E001",
      "first_name": "Jean",
      "last_name": "Dupont",
      "email": "jean.dupont@example.com",
      "department": "IT"
    }
  }'
```
✅ **Attendu** : Opération de provisioning créée (status: "success" ou "pending")

### 8.2 Vérifier dans LDAP que l'utilisateur existe
```bash
docker compose exec openldap ldapsearch -x -H ldap://localhost \
  -b "dc=example,dc=com" \
  -D "cn=admin,dc=example,dc=com" \
  -w secret \
  "(uid=E001)"
```
✅ **Attendu** : Utilisateur Jean Dupont trouvé

### 8.3 Tester la modification
```bash
curl -X POST http://localhost:8000/api/provision \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "operation_type": "update",
    "identity_type": "employee",
    "identity_id": "E001",
    "target_systems": ["ldap"],
    "attributes": {
      "department": "Finance"
    }
  }'
```
✅ **Attendu** : Modification effectuée

---

## Étape 9 : Test des Workflows

### 9.1 Lister les workflows
```bash
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/workflow/configs
```
✅ **Attendu** : Liste avec workflow "new_employee_approval"

### 9.2 Créer une instance de workflow
```bash
curl -X POST http://localhost:8000/api/workflow/instances \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "workflow_config_id": "voir_id_du_workflow",
    "request_data": {
      "employee_id": "E002",
      "first_name": "Marie",
      "last_name": "Martin",
      "email": "marie.martin@example.com"
    }
  }'
```

### 9.3 Lister les instances en attente
```bash
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/workflow/instances?status=pending"
```
✅ **Attendu** : Liste des workflows en attente

---

## Étape 10 : Test du Cache Redis

### 10.1 Vérifier Redis
```bash
docker compose exec redis redis-cli ping
```
✅ **Attendu** : `PONG`

### 10.2 Voir les clés dans Redis
```bash
docker compose exec redis redis-cli keys "*"
```
✅ **Attendu** : Clés de cache du Gateway

---

## Étape 11 : Test Qdrant (Logs Vectoriels)

### 11.1 Accéder au dashboard Qdrant
Ouvrir dans le navigateur : http://localhost:6333/dashboard

✅ **Attendu** : Interface Qdrant accessible

### 11.2 Vérifier les collections
```bash
curl http://localhost:6333/collections
```
✅ **Attendu** : Collections existantes (audit_logs si des logs ont été créés)

---

## Étape 12 : Test Keycloak

### 12.1 Accéder à Keycloak
Ouvrir dans le navigateur : http://localhost:8081

- Username : `admin`
- Password : `admin`

✅ **Attendu** : Console d'administration Keycloak

### 12.2 Créer un realm pour le Gateway (optionnel)
1. Cliquer sur "Create Realm"
2. Nom : `gateway`
3. Créer

---

## Étape 13 : Test Odoo

### 13.1 Accéder à Odoo
Ouvrir dans le navigateur : http://localhost:8069

- Email : `admin`
- Password : `admin`

✅ **Attendu** : Interface Odoo accessible

### 13.2 Tester le connecteur Odoo (via API)
```bash
curl -X POST http://localhost:8000/api/provision \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "operation_type": "create",
    "identity_type": "employee",
    "identity_id": "E003",
    "target_systems": ["odoo"],
    "attributes": {
      "name": "Test User",
      "login": "testuser",
      "email": "test@example.com"
    }
  }'
```

---

## Étape 14 : Test Frontend Gateway

### 14.1 Accéder au Frontend
Ouvrir dans le navigateur : http://localhost:3000

✅ **Attendu** : Page de login du Gateway

### 14.2 Se connecter
- Username : `admin`
- Password : `admin123`

✅ **Attendu** : Dashboard affiché

### 14.3 Tester les pages
- ✅ Dashboard : Statistiques affichées
- ✅ Operations : Liste des opérations
- ✅ Rules : Gestion des règles
- ✅ Workflows : Gestion des workflows
- ✅ Reconciliation : Interface de réconciliation
- ✅ AI Assistant : Interface de l'assistant IA
- ✅ Audit Logs : Logs d'audit

---

## Étape 15 : Test de Réconciliation

### 15.1 Lancer une réconciliation
```bash
curl -X POST http://localhost:8000/api/reconcile/jobs \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "target_system": "ldap"
  }'
```
✅ **Attendu** : Job de réconciliation créé

### 15.2 Vérifier le statut
```bash
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/reconcile/jobs
```
✅ **Attendu** : Liste des jobs avec statuts

---

## Étape 16 : Test de l'Assistant IA (si OpenAI API configuré)

### 16.1 Tester une suggestion de mapping
```bash
curl -X POST http://localhost:8000/api/ai/suggest-mapping \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "source_attributes": ["employee_id", "first_name", "last_name"],
    "target_system": "ldap",
    "target_schema": ["uid", "cn", "sn", "givenName"]
  }'
```
✅ **Attendu** : Suggestions de mapping (ou message mock si pas d'API key)

---

## Étape 17 : Test des Audit Logs

### 17.1 Récupérer les logs
```bash
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/admin/audit-logs?limit=10"
```
✅ **Attendu** : Liste des événements d'audit

### 17.2 Recherche dans les logs
```bash
curl -X POST http://localhost:8000/api/admin/audit-logs/search \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "provisioning",
    "limit": 5
  }'
```
✅ **Attendu** : Logs pertinents retournés

---

## Étape 18 : Test Multi-Cibles

### 18.1 Provisionner sur tous les systèmes
```bash
curl -X POST http://localhost:8000/api/provision \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "operation_type": "create",
    "identity_type": "employee",
    "identity_id": "E100",
    "target_systems": ["ldap", "sql_intranet"],
    "attributes": {
      "employee_id": "E100",
      "first_name": "Multi",
      "last_name": "Target",
      "email": "multi.target@example.com",
      "department": "IT",
      "job_title": "Engineer"
    }
  }'
```
✅ **Attendu** : Création sur LDAP et SQL

### 18.2 Vérifier dans LDAP
```bash
docker compose exec openldap ldapsearch -x -H ldap://localhost \
  -b "dc=example,dc=com" \
  -D "cn=admin,dc=example,dc=com" \
  -w secret \
  "(uid=E100)"
```

### 18.3 Vérifier dans SQL Intranet
```bash
docker compose exec intranet-db psql -U intranet -d intranet \
  -c "SELECT * FROM users WHERE employee_id='E100';"
```
✅ **Attendu** : Utilisateur présent dans les deux systèmes

---

## Étape 19 : Test de Rollback

### 19.1 Créer une opération qui échoue
```bash
curl -X POST http://localhost:8000/api/provision \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "operation_type": "create",
    "identity_type": "employee",
    "identity_id": "E100",
    "target_systems": ["ldap"],
    "attributes": {
      "employee_id": "E100",
      "first_name": "Duplicate",
      "last_name": "Test"
    }
  }'
```
✅ **Attendu** : Erreur car utilisateur existe déjà

---

## Étape 20 : Vérification de la Performance

### 20.1 Temps de réponse API
```bash
time curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/rules
```
✅ **Attendu** : Réponse en moins de 500ms

### 20.2 Utilisation des ressources
```bash
docker stats --no-stream
```
✅ **Attendu** : Utilisation CPU/RAM raisonnable

---

## 🔍 Résolution des Problèmes Courants

### Container n'est pas "healthy"
```bash
docker compose logs [nom_du_service]
docker compose restart [nom_du_service]
```

### Port déjà utilisé
```bash
# Trouver quel process utilise le port
sudo lsof -i :[PORT]
# ou
sudo netstat -tlnp | grep [PORT]
```

### Base de données non initialisée
```bash
docker compose restart gateway
docker compose exec gateway python -m app.db.migrations
```

### Erreur de connexion entre services
```bash
# Vérifier le réseau
docker network inspect iam-network

# Redémarrer tous les services
docker compose down
docker compose up -d
```

### Logs complets pour debug
```bash
docker compose logs --tail=100 -f
```

---

## 📊 Checklist Finale

- [ ] Tous les containers démarrent sans erreur
- [ ] Toutes les bases de données sont initialisées
- [ ] LDAP est accessible et fonctionnel
- [ ] MidPoint est accessible
- [ ] Gateway API répond correctement
- [ ] Authentification JWT fonctionne
- [ ] Règles de provisioning fonctionnent
- [ ] Provisioning LDAP réussit
- [ ] Provisioning SQL Intranet réussit
- [ ] Workflows sont créés et listés
- [ ] Redis répond au ping
- [ ] Qdrant est accessible
- [ ] Keycloak est accessible
- [ ] Odoo est accessible
- [ ] Frontend Gateway est accessible
- [ ] Login frontend fonctionne
- [ ] Réconciliation peut être lancée
- [ ] Audit logs sont enregistrés
- [ ] Provisioning multi-cibles fonctionne

---

## 🎉 Succès !

Si toutes les étapes sont ✅, votre Gateway IAM est **complètement fonctionnel** !

Pour arrêter tous les services :
```bash
./scripts/stop.sh
```

Pour redémarrer :
```bash
./scripts/start.sh
```
