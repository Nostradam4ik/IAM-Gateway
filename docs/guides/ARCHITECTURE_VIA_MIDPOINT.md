# Architecture IAM Gateway via MidPoint

**Date** : 5 janvier 2026
**Objectif** : Toutes les opérations passent par MidPoint comme hub central IAM

---

## 🎯 Architecture Cible

### Flux de Provisioning

```
┌──────────────┐
│     ODOO     │  Source RH (Système Source)
│   Employés   │  http://localhost:8069
└──────┬───────┘
       │
       │ (1) Données employés
       ↓
┌──────────────┐
│  GATEWAY IAM │  Orchestrateur Intelligent
│              │  http://localhost:8000
│  • Validation│  Port: 8000
│  • Workflows │  Frontend: 3000
│  • Audit     │
│  • IA        │
└──────┬───────┘
       │
       │ (2) REST API
       │     POST /ws/rest/users
       ↓
┌──────────────┐
│   MIDPOINT   │  Hub IAM Central
│              │  http://localhost:8080/midpoint
│  • Rôles     │  Login: administrator / 5ecr3t
│  • Mappings  │
│  • Synchro   │
└───┬──────┬───┘
    │      │
    │      │ (3) Connecteurs natifs MidPoint
    │      │     • Outbound Mappings
    │      │     • Live Sync
    ↓      ↓
┌────────┐ ┌───────────┐
│OpenLDAP│ │PostgreSQL │  Systèmes Cibles
│        │ │           │
│:10389  │ │  :55432   │
└────────┘ └───────────┘
```

###  Pourquoi Cette Architecture?

**Avant (connexion directe)**:
```
Gateway → LDAP (direct)
Gateway → PostgreSQL (direct)
```
❌ Pas de centralisation
❌ Pas de gestion des rôles
❌ Logique métier dans la Gateway

**Maintenant (via MidPoint)**:
```
Gateway → MidPoint → LDAP
Gateway → MidPoint → PostgreSQL
```
✅ Centralisation dans MidPoint
✅ Gestion des rôles sophistiquée
✅ Séparation des responsabilités

---

## 📋 Composants

### 1. Gateway IAM (Orchestrateur)

**Rôle** : Orchestration, validation, workflows

**Responsabilités**:
- Recevoir les demandes (UI/API)
- Valider les données
- Appliquer les règles métier
- Gérer les workflows d'approbation
- Transmettre à MidPoint
- Auditer toutes les opérations

**Code**:
- Service: `gateway/app/services/midpoint_provision_service_updated.py`
- API: `gateway/app/api/provision_via_midpoint.py`

### 2. MidPoint (Hub IAM)

**Rôle** : Hub central de gestion des identités

**Responsabilités**:
- Stocker les utilisateurs (référentiel central)
- Gérer les rôles et permissions
- Provisionner vers LDAP et PostgreSQL
- Synchroniser automatiquement
- Appliquer les mappings d'attributs

**Connecteurs configurés**:
- CSV Resource (Odoo import)
- OpenLDAP Resource
- PostgreSQL Resource

### 3. Systèmes Cibles

**OpenLDAP**: Annuaire d'entreprise
**PostgreSQL**: Base applicative (intranet)

---

## 🔧 Configuration

### Étape 1: Démarrer MidPoint

```bash
# Démarrer MidPoint
docker compose up -d midpoint

# Attendre que MidPoint démarre (2-3 minutes)
docker logs midpoint-core -f

# Accéder à l'interface
# URL: http://localhost:8080/midpoint
# Login: administrator
# Password: 5ecr3t (par défaut) ou Holimolly1
```

### Étape 2: Configurer les Connecteurs MidPoint

#### A. Connecteur OpenLDAP

1. Se connecter à MidPoint
2. Configuration → Repository Objects → Resources
3. Importer `infrastructure/midpoint/resources/openldap-resource.xml`

```xml
<!-- Configuration LDAP -->
<resource oid="10000000-0000-0000-0000-000000000001">
    <name>OpenLDAP Directory</name>
    <connectorRef>
        <type>ConnectorType</type>
        <filter>
            <q:equal>
                <q:path>connectorType</q:path>
                <q:value>com.evolveum.polygon.connector.ldap.LdapConnector</q:value>
            </q:equal>
        </filter>
    </connectorRef>
    <connectorConfiguration>
        <icfc:configurationProperties>
            <icfcldap:host>openldap</icfcldap:host>
            <icfcldap:port>389</icfcldap:port>
            <icfcldap:bindDn>cn=admin,dc=example,dc=com</icfcldap:bindDn>
            <icfcldap:bindPassword>secret</icfcldap:bindPassword>
            <icfcldap:baseContext>dc=example,dc=com</icfcldap:baseContext>
        </icfc:configurationProperties>
    </connectorConfiguration>
</resource>
```

**Test de connexion**:
```bash
curl -u administrator:5ecr3t \
  -X POST http://localhost:8080/midpoint/ws/rest/resources/10000000-0000-0000-0000-000000000001/test
```

#### B. Connecteur PostgreSQL

1. Importer `infrastructure/midpoint/resources/database-resource.xml`

```xml
<!-- Configuration PostgreSQL -->
<resource oid="10000000-0000-0000-0000-000000000003">
    <name>PostgreSQL Intranet Database</name>
    <connectorRef>
        <type>ConnectorType</type>
        <filter>
            <q:equal>
                <q:path>connectorType</q:path>
                <q:value>com.evolveum.polygon.connector.jdbc.JdbcConnector</q:value>
            </q:equal>
        </filter>
    </connectorRef>
    <connectorConfiguration>
        <icfc:configurationProperties>
            <jdbcUrlTemplate>jdbc:postgresql://intranet-db:5432/intranet</jdbcUrlTemplate>
            <username>intranet</username>
            <password>intranet</password>
            <table>users</table>
        </icfc:configurationProperties>
    </connectorConfiguration>
</resource>
```

### Étape 3: Créer les Rôles MidPoint

#### Rôle LDAP User

Crée automatiquement un compte LDAP quand assigné.

```xml
<role oid="role-ldap-user-oid">
    <name>LDAP User</name>
    <description>Provisionne l'utilisateur vers OpenLDAP</description>
    <inducement>
        <construction>
            <resourceRef oid="10000000-0000-0000-0000-000000000001"/>
        </construction>
    </inducement>
</role>
```

#### Rôle Database User

Crée automatiquement un compte PostgreSQL quand assigné.

```xml
<role oid="role-database-user-oid">
    <name>Database User</name>
    <description>Provisionne l'utilisateur vers PostgreSQL</description>
    <inducement>
        <construction>
            <resourceRef oid="10000000-0000-0000-0000-000000000003"/>
        </construction>
    </inducement>
</role>
```

### Étape 4: Configurer les Mappings

Les mappings définissent comment les attributs sont transformés.

**Exemple - Mapping LDAP**:
```xml
<attribute>
    <ref>ri:cn</ref>
    <outbound>
        <source>
            <path>fullName</path>
        </source>
    </outbound>
</attribute>

<attribute>
    <ref>ri:mail</ref>
    <outbound>
        <source>
            <path>emailAddress</path>
        </source>
    </outbound>
</attribute>
```

---

## 🚀 Utilisation

### API - Créer un Utilisateur

```bash
# Obtenir un token
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin"}' | jq -r '.access_token')

# Créer un utilisateur via MidPoint
curl -X POST http://localhost:8000/api/v1/provision-midpoint/users \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "jdoe",
    "firstname": "John",
    "lastname": "Doe",
    "email": "john.doe@example.com",
    "employee_id": "EMP001",
    "department": "IT",
    "phone": "+33123456789",
    "assign_roles": ["role-ldap-user-oid", "role-database-user-oid"]
  }'
```

**Résultat**:
```json
{
  "success": true,
  "message": "User created in MidPoint and provisioned to target systems",
  "data": {
    "oid": "12345-67890-abcde",
    "username": "jdoe",
    "midpoint_status": "created",
    "roles_assigned": 2,
    "target_systems": {
      "OpenLDAP Directory": {
        "status": "enabled",
        "oid": "shadow-ldap-oid"
      },
      "PostgreSQL Intranet Database": {
        "status": "enabled",
        "oid": "shadow-db-oid"
      }
    }
  }
}
```

### Vérification

#### Dans MidPoint
```
http://localhost:8080/midpoint
→ Users → Rechercher "jdoe"
→ Voir les assignments (rôles)
→ Voir les projections (comptes liés)
```

#### Dans LDAP
```bash
docker exec openldap ldapsearch -x -H ldap://localhost \
  -b "ou=people,dc=example,dc=com" \
  -D "cn=admin,dc=example,dc=com" -w secret \
  "(uid=jdoe)"
```

#### Dans PostgreSQL
```bash
docker exec intranet-db psql -U intranet -d intranet \
  -c "SELECT * FROM users WHERE username = 'jdoe';"
```

---

## 📊 Flux Complet - Exemple

### Scénario: Nouvel Employé dans Odoo

```
1. HR crée l'employé dans Odoo
   └─> Nom: Jean Dupont
   └─> Email: jean.dupont@example.com
   └─> Département: IT

2. Gateway IAM détecte le nouvel employé
   └─> Validation des données
   └─> Application des règles métier
   └─> Workflow d'approbation (si nécessaire)

3. Gateway crée l'utilisateur dans MidPoint
   POST /midpoint/ws/rest/users
   └─> MidPoint génère un OID unique
   └─> MidPoint stocke l'utilisateur

4. MidPoint assigne les rôles automatiquement
   └─> Rôle "LDAP User" → déclenche provisioning LDAP
   └─> Rôle "Database User" → déclenche provisioning PostgreSQL

5. MidPoint provisionne vers les cibles
   a) LDAP
      └─> Crée: uid=jdupont,ou=people,dc=example,dc=com
      └─> Attributs: cn, mail, ou, telephoneNumber

   b) PostgreSQL
      └─> INSERT INTO users (username, email, department, ...)
      └─> Compte créé dans la table users

6. Gateway récupère les statuts
   └─> Interroge MidPoint pour les shadow objects
   └─> Vérifie que tout est OK

7. Gateway retourne le résultat
   └─> UI affiche le succès
   └─> Audit enregistré
```

---

## 🔍 Avantages de Cette Architecture

### 1. Centralisation
- **Un seul référentiel** : MidPoint
- Tous les utilisateurs dans une base centrale
- Source de vérité unique

### 2. Gestion des Rôles
- Rôles MidPoint déclenchent le provisioning
- RBAC (Role-Based Access Control)
- Gestion fine des permissions

### 3. Automatisation
- Provisioning automatique via rôles
- Synchronisation bidirectionnelle
- Dé-provisioning automatique

### 4. Séparation des Responsabilités
- Gateway: Orchestration, validation, workflow
- MidPoint: Provisioning, rôles, synchronisation
- Systèmes cibles: Stockage final

### 5. Évolutivité
- Ajouter de nouveaux systèmes cibles facilement
- Créer de nouveaux rôles sans coder
- Modifier les mappings via configuration

---

## 📝 Checklist de Démonstration

- [ ] MidPoint démarré et accessible
- [ ] Connecteur LDAP configuré et testé
- [ ] Connecteur PostgreSQL configuré et testé
- [ ] Rôles LDAP et Database créés
- [ ] Gateway modifiée pour utiliser MidPoint
- [ ] API `/provision-midpoint/users` fonctionnelle
- [ ] Test: Créer un utilisateur
- [ ] Vérification dans MidPoint
- [ ] Vérification dans LDAP
- [ ] Vérification dans PostgreSQL
- [ ] Captures d'écran prêtes

---

## 🎓 Points Clés pour la Présentation

1. **Architecture en 3 couches**
   - Gateway IAM (orchestration)
   - MidPoint (hub IAM)
   - Systèmes cibles (LDAP, PostgreSQL)

2. **Tout passe par MidPoint**
   - Pas de connexion directe Gateway → LDAP/PostgreSQL
   - MidPoint comme point central obligatoire

3. **Gestion basée sur les rôles**
   - Assignation de rôle = provisioning automatique
   - Révocation de rôle = dé-provisioning automatique

4. **Standards IAM**
   - Utilise les standards MidPoint
   - Connecteurs natifs
   - REST API standard

---

**Auteur** : Claude Code
**Date** : 5 janvier 2026
**Projet** : IAM Gateway - Project3
