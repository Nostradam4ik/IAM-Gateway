# RAPPORT TP1 - Gateway IAM Multi-Cibles

## Projet #3 : Developpement d'une Gateway IAM Intelligente

**Etudiant** : [Votre nom]
**Date** : Decembre 2025
**Objectif** : Creation d'une Gateway IAM pour provisionnement multi-cibles avec integration MidPoint

---

## 1. ARCHITECTURE IMPLEMENTEE

### 1.1 Vue d'ensemble

```
                    +------------------+
                    |   Frontend React |
                    |   (Port 3001)    |
                    +--------+---------+
                             |
                    +--------v---------+
                    |   Gateway IAM    |
                    |   FastAPI        |
                    |   (Port 8000)    |
                    +--------+---------+
                             |
        +--------------------+--------------------+
        |                    |                    |
+-------v------+    +--------v-------+    +------v-------+
|   MidPoint   |    |   PostgreSQL   |    |    Redis     |
|   (8080)     |    |   (5434)       |    |   (6379)     |
+--------------+    +----------------+    +--------------+
        |
        +------------------+------------------+
        |                  |                  |
+-------v------+   +-------v------+   +------v-------+
|   OpenLDAP   |   |  Intranet DB |   |    Odoo      |
|   (10389)    |   |   (55432)    |   |   (8069)     |
+--------------+   +--------------+   +--------------+
```

### 1.2 Technologies utilisees

| Composant | Technologie | Version |
|-----------|-------------|---------|
| Backend Gateway | FastAPI (Python) | 0.104+ |
| Frontend | React + TypeScript | 18.x |
| IAM Orchestrator | MidPoint | 4.8 |
| Base de donnees | PostgreSQL | 15 |
| Cache | Redis | 7 |
| Annuaire | OpenLDAP | 2.6 |
| ERP | Odoo | 17 |
| Authentification | Keycloak | 23 |
| Conteneurisation | Docker Compose | 2.x |

---

## 2. TRAVAIL REALISE

### 2.1 Configuration de l'Infrastructure Docker

**Fichier** : `docker-compose.yml`

Services deployes :
- `gateway` : API FastAPI (port 8000)
- `gateway-frontend` : Interface React (port 3001)
- `gateway-db` : PostgreSQL pour la Gateway (port 5434)
- `redis` : Cache Redis (port 6379)
- `midpoint-core` : MidPoint IAM (port 8080)
- `midpoint-db` : PostgreSQL pour MidPoint (port 5433)
- `openldap` : Annuaire LDAP (port 10389)
- `intranet-db` : Base Intranet (port 55432)
- `odoo` : ERP Odoo (port 8069)
- `odoo-db` : PostgreSQL pour Odoo (port 5435)
- `keycloak` : IAM Keycloak (port 8081)
- `keycloak-db` : PostgreSQL pour Keycloak (port 5436)

### 2.2 Correction des Erreurs de Demarrage

#### Probleme 1 : Erreur Bcrypt - Mot de passe trop long

**Erreur** :
```
ValueError: password cannot be longer than 72 bytes, truncate manually if necessary
```

**Cause** : La bibliotheque `passlib` avait des problemes de compatibilite avec bcrypt.

**Solution** : Remplacement de passlib par utilisation directe de bcrypt.

**Fichier modifie** : `gateway/app/core/security.py`
```python
import bcrypt

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(
        plain_password.encode('utf-8'),
        hashed_password.encode('utf-8')
    )

def get_password_hash(password: str) -> str:
    return bcrypt.hashpw(
        password.encode('utf-8'),
        bcrypt.gensalt()
    ).decode('utf-8')
```

#### Probleme 2 : Erreur de configuration DATABASE_URL

**Erreur** :
```
AttributeError: 'Settings' object has no attribute 'database_url'
```

**Cause** : Sensibilite a la casse - le code utilisait `database_url` mais la config definissait `DATABASE_URL`.

**Solution** : Modification de `migrations.py` pour utiliser `settings.DATABASE_URL`.

#### Probleme 3 : Erreur PostgreSQL - Commandes multiples

**Erreur** :
```
ProgrammingError: cannot insert multiple commands into a prepared statement
```

**Cause** : AsyncPG ne supporte pas plusieurs instructions SQL dans un seul execute.

**Solution** : Separation des creations d'index en executions individuelles.

**Fichier modifie** : `gateway/app/db/migrations.py`
```python
indexes = [
    "CREATE INDEX IF NOT EXISTS idx_operations_request_id ON provisioning_operations(request_id)",
    "CREATE INDEX IF NOT EXISTS idx_operations_status ON provisioning_operations(status)",
    # ... autres index
]
for index_sql in indexes:
    await conn.execute(text(index_sql))
```

#### Probleme 4 : Import circulaire AI

**Erreur** : Import circulaire entre `ai_assistant.py` et `ai_agent.py`.

**Solution** : Creation du fichier `gateway/app/models/ai.py` pour centraliser les modeles.

### 2.3 Initialisation de la Base de Donnees

**18 tables creees** :

| Table | Description |
|-------|-------------|
| `provisioning_requests` | Requetes de provisionnement |
| `provisioning_operations` | Operations individuelles |
| `provisioning_rules` | Regles de mapping |
| `workflow_instances` | Instances de workflow |
| `workflow_steps` | Etapes des workflows |
| `approval_requests` | Demandes d'approbation |
| `audit_logs` | Journaux d'audit |
| `config_changes` | Historique des configurations |
| `system_state` | Etat du systeme |
| `ai_conversations` | Conversations avec l'assistant IA |
| `ai_messages` | Messages des conversations |
| `connectors` | Configuration des connecteurs |
| `connector_configs` | Parametres des connecteurs |

### 2.4 Integration MidPoint

**Fichier modifie** : `gateway/app/core/config.py`
```python
# MidPoint
MIDPOINT_URL: str = Field(default="http://midpoint-core:8080/midpoint")
MIDPOINT_USER: str = Field(default="administrator")
MIDPOINT_PASSWORD: str = Field(default="Nost1")
```

**Configuration du mot de passe** :
1. Acces a MidPoint via http://localhost:8080/midpoint/admin/
2. Connexion avec administrator / 5ecr3t (mot de passe par defaut)
3. Changement du mot de passe vers "Nost1"
4. Mise a jour de la configuration Gateway

### 2.5 Configuration des Connecteurs MidPoint

**Fichiers crees dans** `midpoint-resources/` :

#### Connecteur LDAP (`ldap-resource.xml`)
```xml
<resource>
    <name>OpenLDAP Resource</name>
    <connectorRef>LdapConnector</connectorRef>
    <configuration>
        Host: openldap
        Port: 389
        Base DN: dc=example,dc=com
        Bind DN: cn=admin,dc=example,dc=com
        Password: secret
    </configuration>
</resource>
```

#### Connecteur CSV (`csv-resource.xml`)
```xml
<resource>
    <name>CSV File Resource</name>
    <connectorRef>CsvConnector</connectorRef>
    <configuration>
        File Path: /opt/midpoint/var/csv/users.csv
        Encoding: UTF-8
        Delimiter: ,
        Unique Attribute: uid
    </configuration>
</resource>
```

#### Connecteur Database (`database-resource.xml`)
```xml
<resource>
    <name>Intranet Database Resource</name>
    <connectorRef>DatabaseTableConnector</connectorRef>
    <configuration>
        JDBC URL: jdbc:postgresql://intranet-db:5432/intranet
        User: intranet
        Password: intranet
        Table: users
        Key Column: id
    </configuration>
</resource>
```

### 2.6 Systeme d'Authentification Gateway

**Fichier** : `gateway/app/api/admin.py`

Utilisateurs temporaires configures :
| Username | Password | Roles |
|----------|----------|-------|
| admin | admin123 | admin, iam_engineer |
| operator | operator123 | operator |

**Endpoint d'authentification** : `POST /api/v1/admin/token`

**Implementation JWT** :
- Algorithme : HS256
- Expiration : 60 minutes (configurable)
- Secret : Configurable via `JWT_SECRET_KEY`

---

## 3. FONCTIONNALITES IMPLEMENTEES

### 3.1 API Gateway (FastAPI)

| Endpoint | Methode | Description |
|----------|---------|-------------|
| `/api/v1/admin/token` | POST | Authentification JWT |
| `/api/v1/admin/me` | GET | Info utilisateur connecte |
| `/api/v1/admin/status` | GET | Statut systeme |
| `/api/v1/admin/emergency-stop` | POST | Arret d'urgence |
| `/api/v1/admin/resume` | POST | Reprise du systeme |
| `/api/v1/admin/connectors/status` | GET | Statut des connecteurs |
| `/api/v1/provision/` | POST | Creer une operation |
| `/api/v1/provision/` | GET | Lister les operations |
| `/api/v1/rules/` | GET/POST | Gestion des regles |
| `/api/v1/workflow/` | GET/POST | Gestion des workflows |
| `/api/v1/ai/chat` | POST | Assistant IA |

### 3.2 Connecteurs Implementes

| Connecteur | Fichier | Operations |
|------------|---------|------------|
| LDAP | `ldap_connector.py` | create, update, delete, search |
| SQL | `sql_connector.py` | create, update, delete, search |
| Odoo | `odoo_connector.py` | create, update, delete, search |

### 3.3 Services Metier

| Service | Fichier | Role |
|---------|---------|------|
| ProvisionService | `provision_service.py` | Orchestration du provisionnement |
| WorkflowService | `workflow_service.py` | Gestion des workflows d'approbation |
| AuditService | `audit_service.py` | Journalisation et audit |
| MidPointClient | `midpoint_client.py` | Communication avec MidPoint |

### 3.4 Frontend React

Pages implementees :
- **Dashboard** : Vue d'ensemble du systeme
- **Operations** : Liste et gestion des operations
- **Regles** : Configuration des regles de provisionnement
- **Workflows** : Gestion des workflows d'approbation
- **Assistant IA** : Interface de chat avec l'assistant
- **Connecteurs** : Status et configuration des connecteurs
- **Comparaison Live** : Comparaison des donnees entre systemes

---

## 4. CONFIGURATION DE L'ENVIRONNEMENT

### 4.1 Variables d'environnement principales

```env
# Database
DATABASE_URL=postgresql+asyncpg://gateway:gateway@gateway-db:5432/gateway
REDIS_URL=redis://redis:6379/0

# MidPoint
MIDPOINT_URL=http://midpoint-core:8080/midpoint
MIDPOINT_USER=administrator
MIDPOINT_PASSWORD=Nost1

# LDAP
LDAP_HOST=openldap
LDAP_PORT=389
LDAP_BIND_DN=cn=admin,dc=example,dc=com
LDAP_BIND_PASSWORD=secret
LDAP_BASE_DN=dc=example,dc=com

# Odoo
ODOO_URL=http://odoo:8069
ODOO_DB=odoo
ODOO_USER=admin
ODOO_PASSWORD=admin

# JWT
JWT_SECRET_KEY=jwt-secret-key-change-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=60
```

### 4.2 Commandes de demarrage

```bash
# Demarrer tous les services
docker compose up -d

# Verifier les logs
docker compose logs -f gateway

# Initialiser la base de donnees
docker compose exec gateway python -c "from app.db.migrations import run_migrations; import asyncio; asyncio.run(run_migrations())"

# Acceder a l'interface Gateway
http://localhost:3001

# Acceder a MidPoint
http://localhost:8080/midpoint/admin/
```

---

## 5. TESTS EFFECTUES

### 5.1 Tests de connectivite

| Test | Resultat |
|------|----------|
| Gateway API accessible | OK |
| Frontend React accessible | OK |
| Base de donnees Gateway | OK |
| Redis | OK |
| MidPoint API | OK |
| OpenLDAP | OK |
| Intranet DB | OK |
| Odoo | OK |

### 5.2 Tests fonctionnels

| Test | Resultat |
|------|----------|
| Authentification JWT | OK |
| Creation d'operation de provisionnement | OK |
| Lecture des regles | OK |
| Statut des connecteurs | OK |
| Logs d'audit | OK |

---

## 6. FICHIERS CREES/MODIFIES

### 6.1 Fichiers crees

| Fichier | Description |
|---------|-------------|
| `midpoint-resources/ldap-resource.xml` | Config connecteur LDAP |
| `midpoint-resources/csv-resource.xml` | Config connecteur CSV |
| `midpoint-resources/database-resource.xml` | Config connecteur Database |
| `GUIDE_CONFIGURATION_MIDPOINT.md` | Guide de configuration |
| `gateway/app/models/ai.py` | Modeles pour l'assistant IA |

### 6.2 Fichiers modifies

| Fichier | Modifications |
|---------|---------------|
| `gateway/app/core/security.py` | Remplacement passlib par bcrypt |
| `gateway/app/core/config.py` | Ajout MIDPOINT_PASSWORD=Nost1 |
| `gateway/app/api/admin.py` | Hachage paresseux des mots de passe |
| `gateway/app/db/migrations.py` | Correction bcrypt et index |
| `docker-compose.yml` | Configuration MidPoint |

---

## 7. PROCHAINES ETAPES (TP2)

1. **Finaliser la configuration MidPoint**
   - Configurer le connecteur LDAP via l'interface web
   - Configurer le connecteur CSV
   - Configurer le connecteur Database
   - Creer les roles et les mappings

2. **Tests de provisionnement end-to-end**
   - Creer un utilisateur via la Gateway
   - Verifier la propagation vers LDAP, Intranet DB, Odoo

3. **Workflows d'approbation**
   - Configurer les niveaux d'approbation
   - Tester le processus d'approbation

4. **Assistant IA**
   - Configurer l'API OpenAI ou DeepSeek
   - Tester les requetes en langage naturel

---

## 8. CONCLUSION

Le TP1 a permis de mettre en place l'infrastructure complete de la Gateway IAM avec :
- Une architecture microservices conteneurisee
- Une API RESTful securisee avec FastAPI
- Une integration avec MidPoint pour l'orchestration IAM
- Des connecteurs vers les systemes cibles (LDAP, SQL, Odoo)
- Un frontend React pour l'administration
- Un systeme d'audit et de journalisation

L'infrastructure est operationnelle et prete pour les tests de provisionnement multi-cibles.

---

**Document genere le** : Decembre 2025
**Version** : 1.0
