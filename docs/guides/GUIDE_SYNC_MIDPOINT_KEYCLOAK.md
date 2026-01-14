# Guide : Synchronisation MidPoint → Keycloak

## Introduction

Ce guide explique comment synchroniser les utilisateurs de MidPoint vers Keycloak. L'architecture utilise un **webhook** : MidPoint notifie la Gateway qui provisionne automatiquement vers Keycloak.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     ARCHITECTURE DE PROVISIONING                             │
└─────────────────────────────────────────────────────────────────────────────┘

                    ┌──────────────────────────────────────┐
                    │            GATEWAY IAM               │
                    │                                      │
                    │  ┌────────────────────────────────┐  │
                    │  │  Webhook Endpoint              │  │
                    │  │  /api/v1/webhooks/midpoint/    │  │
                    │  │  user-change                   │  │
                    │  └────────────────────────────────┘  │
                    │              │                       │
                    │              │ Appelle Keycloak API  │
                    │              ▼                       │
                    │  ┌────────────────────────────────┐  │
                    │  │  KeycloakProvisioner           │  │
                    │  │  - create_user()               │  │
                    │  │  - update_user()               │  │
                    │  │  - delete_user()               │  │
                    │  └────────────────────────────────┘  │
                    └──────────────────────────────────────┘
                              ▲              │
                              │              │
                    Webhook   │              │  REST API
                    (POST)    │              ▼
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│    ODOO     │────►│  MIDPOINT   │     │  KEYCLOAK   │
│   (Source)  │ CSV │   (Hub)     │     │   (SSO)     │
└─────────────┘     └─────────────┘     └─────────────┘
```

## Avantages de cette architecture

| Avantage | Description |
|----------|-------------|
| **MidPoint reste le hub** | Toutes les opérations passent par MidPoint |
| **Gateway contrôle le provisioning** | Logique centralisée dans la Gateway |
| **Pas de connecteur externe** | Utilise l'API REST standard de Keycloak |
| **Automatique** | Le webhook déclenche le provisioning |
| **Flexible** | Facile à modifier la logique de provisioning |

## Prérequis

### Services Docker

```bash
# Vérifier que les services sont actifs
docker ps | grep -E "midpoint|keycloak|gateway"

# Services requis :
# - midpoint-core (port 8080)
# - keycloak (port 8081)
# - gateway-iam (port 8000)
```

### Accès aux systèmes

| Système | URL | Identifiants |
|---------|-----|--------------|
| MidPoint | http://localhost:8080/midpoint | administrator / 5ecr3t |
| Keycloak | http://localhost:8081 | admin / admin |
| Gateway | http://localhost:8000 | - |

## Partie 1 : Endpoint Webhook dans la Gateway

### 1.1 Fichier source

```
gateway/app/api/webhooks.py
```

### 1.2 Endpoint disponible

```
POST /api/v1/webhooks/midpoint/user-change
```

### 1.3 Format du payload

```json
{
  "event": "user_change",
  "operation": "add",
  "user": {
    "oid": "user-oid-from-midpoint",
    "name": "username",
    "givenName": "John",
    "familyName": "Doe",
    "email": "john.doe@example.com"
  }
}
```

### 1.4 Opérations supportées

| Opération | Action Keycloak |
|-----------|-----------------|
| `add` / `create` | Créer l'utilisateur |
| `modify` / `update` | Mettre à jour l'utilisateur |
| `delete` | Supprimer l'utilisateur |

### 1.5 Tester le webhook manuellement

```bash
curl -X POST "http://localhost:8000/api/v1/webhooks/midpoint/user-change" \
  -H "Content-Type: application/json" \
  -d '{
    "event": "user_change",
    "operation": "add",
    "user": {
      "oid": "test-123",
      "name": "test.user",
      "givenName": "Test",
      "familyName": "User",
      "email": "test.user@example.com"
    }
  }'
```

Réponse attendue :
```json
{
  "status": "accepted",
  "message": "User change event received, processing in background"
}
```

## Partie 2 : Configuration MidPoint (Notifications)

Pour que MidPoint appelle automatiquement le webhook, configurez les notifications système.

### 2.1 Fichier de configuration

```
infrastructure/midpoint/objects/keycloak-notification.xml
```

### 2.2 Configuration des notifications

Dans MidPoint, ajoutez à la configuration système :

```xml
<systemConfiguration>
    <notificationConfiguration>
        <handler>
            <simpleUserNotifier>
                <name>Keycloak Provisioning Webhook</name>
                <operation>add</operation>
                <operation>modify</operation>
                <status>success</status>
                <transport>custom:keycloakWebhook</transport>
            </simpleUserNotifier>
        </handler>

        <customTransport>
            <name>keycloakWebhook</name>
            <type>http</type>
            <urlExpression>
                <script>
                    <code>"http://gateway:8000/api/v1/webhooks/midpoint/user-change"</code>
                </script>
            </urlExpression>
            <method>POST</method>
            <contentType>application/json</contentType>
        </customTransport>
    </notificationConfiguration>
</systemConfiguration>
```

## Partie 3 : Provisioning via Script (Alternative)

En attendant la configuration des notifications MidPoint, utilisez les scripts :

### 3.1 Synchroniser tous les utilisateurs

```bash
python3 /home/vboxuser/Desktop/Project3/scripts/midpoint_to_keycloak_sync.py --sync
```

### 3.2 Provisionner un utilisateur spécifique

```bash
python3 /home/vboxuser/Desktop/Project3/scripts/midpoint_to_keycloak_sync.py --user u1008
```

### 3.3 Lister les utilisateurs Keycloak

```bash
python3 /home/vboxuser/Desktop/Project3/scripts/midpoint_to_keycloak_sync.py --list
```

## Partie 4 : Classe KeycloakProvisioner

### 4.1 Configuration

```python
# Variables d'environnement (avec valeurs par défaut)
KEYCLOAK_URL = "http://keycloak:8080"      # URL interne Docker
KEYCLOAK_REALM = "gateway"                  # Realm cible
KEYCLOAK_ADMIN_USER = "admin"               # Admin Keycloak
KEYCLOAK_ADMIN_PASSWORD = "admin"           # Mot de passe admin
```

### 4.2 Méthodes disponibles

| Méthode | Description |
|---------|-------------|
| `get_token()` | Obtient un token admin Keycloak |
| `user_exists(username)` | Vérifie si l'utilisateur existe |
| `create_user(user_data)` | Crée un utilisateur |
| `update_user(user_id, user_data)` | Met à jour un utilisateur |
| `delete_user(user_id)` | Supprime un utilisateur |
| `provision_user(user_data, operation)` | Provisionne selon l'opération |

### 4.3 Mappings des attributs

| Attribut MidPoint | Attribut Keycloak | Description |
|-------------------|-------------------|-------------|
| `name` | `username` | Identifiant de connexion |
| `givenName` | `firstName` | Prénom |
| `familyName` | `lastName` | Nom de famille |
| `email` | `email` | Adresse email |
| - | `enabled` | Toujours `true` |
| - | `emailVerified` | Toujours `true` |

### 4.4 Mot de passe par défaut

```python
"credentials": [{
    "type": "password",
    "value": "changeme123",    # Mot de passe initial
    "temporary": True           # Force le changement au premier login
}]
```

## Partie 5 : Flux Complet de Démonstration

### Méthode 1 : Via Webhook (automatique)

```bash
# 1. Appeler le webhook directement
curl -X POST "http://localhost:8000/api/v1/webhooks/midpoint/user-change" \
  -H "Content-Type: application/json" \
  -d '{
    "event": "user_change",
    "operation": "add",
    "user": {
      "name": "demo.user",
      "givenName": "Demo",
      "familyName": "User",
      "email": "demo.user@example.com"
    }
  }'

# 2. Vérifier dans Keycloak
# URL: http://localhost:8081 → gateway → Users → demo.user
```

### Méthode 2 : Via Scripts (manuel)

```bash
# 1. Créer employé dans Odoo
# URL: http://localhost:8069

# 2. Synchroniser Odoo → MidPoint
python3 scripts/odoo_to_midpoint_sync.py

# 3. Synchroniser MidPoint → Keycloak
python3 scripts/midpoint_to_keycloak_sync.py --sync

# 4. Vérifier dans Keycloak
python3 scripts/midpoint_to_keycloak_sync.py --list
```

### Méthode 3 : Via API Gateway

```bash
# Utiliser l'endpoint de provisioning MidPoint de la Gateway
curl -X POST "http://localhost:8000/api/v1/provision-midpoint/users" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "username": "api.user",
    "firstname": "API",
    "lastname": "User",
    "email": "api.user@example.com"
  }'
```

## Partie 6 : Dépannage

### Problème : "Webhook ne répond pas"

```bash
# Vérifier que la Gateway est active
docker ps | grep gateway
curl http://localhost:8000/health

# Vérifier les logs
docker logs gateway-iam --tail 50
```

### Problème : "User created in Keycloak" mais pas visible

```bash
# Vérifier le bon realm
# URL Keycloak doit être sur "gateway" (pas "master")
```

### Problème : "Failed to get Keycloak token"

```bash
# Vérifier la connexion à Keycloak depuis Gateway
docker exec gateway-iam curl -s http://keycloak:8080/realms/master

# Vérifier les credentials dans le code
```

### Problème : "HTTP 409 Conflict"

L'utilisateur existe déjà. Le système va faire un update au lieu d'un create.

## Partie 7 : Logs et Monitoring

### 7.1 Voir les logs de provisioning

```bash
# Logs Gateway
docker logs gateway-iam --tail 50 | grep -i keycloak

# Format des logs de succès
# {"username": "test.user", "event": "User created in Keycloak", ...}
```

### 7.2 Endpoints de monitoring

```bash
# Health check Gateway
curl http://localhost:8000/health

# Health check Webhooks
curl http://localhost:8000/api/v1/webhooks/health
```

## Partie 8 : Sécurité

### 8.1 Variables d'environnement

En production, utilisez des variables d'environnement :

```bash
export KEYCLOAK_URL="https://keycloak.example.com"
export KEYCLOAK_ADMIN_USER="admin"
export KEYCLOAK_ADMIN_PASSWORD="secure_password"
```

### 8.2 HTTPS

En production, utilisez HTTPS pour toutes les communications :
- Gateway ↔ Keycloak
- MidPoint ↔ Gateway
- Clients ↔ Gateway

### 8.3 Authentification du webhook

Ajoutez une validation du token pour sécuriser le webhook :

```python
# Exemple de validation
@router.post("/midpoint/user-change")
async def webhook(request: Request):
    token = request.headers.get("X-MidPoint-Token")
    if token != EXPECTED_TOKEN:
        raise HTTPException(status_code=401)
    # ... traitement
```

## Ressources

### Fichiers du projet

| Fichier | Description |
|---------|-------------|
| `gateway/app/api/webhooks.py` | Endpoint webhook et KeycloakProvisioner |
| `scripts/midpoint_to_keycloak_sync.py` | Script de synchronisation manuel |
| `infrastructure/midpoint/objects/keycloak-notification.xml` | Config notifications MidPoint |

### URLs de référence

| Service | URL |
|---------|-----|
| Gateway API Docs | http://localhost:8000/docs |
| Keycloak Admin | http://localhost:8081/admin |
| MidPoint | http://localhost:8080/midpoint |

### API Keycloak

- Documentation : https://www.keycloak.org/docs-api/latest/rest-api/
- Users endpoint : `/admin/realms/{realm}/users`

---

*Documentation créée pour le projet IAM Gateway - Synchronisation MidPoint → Gateway → Keycloak*
