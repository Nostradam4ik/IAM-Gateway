# Guide Developpeur - Gateway IAM

> Guide complet pour les developpeurs et toute personne souhaitant installer, comprendre et contribuer au projet Gateway IAM.

---

## Table des matieres

1. [Vue d'ensemble du projet](#1-vue-densemble-du-projet)
2. [Prerequisites](#2-prerequisites)
3. [Installation rapide](#3-installation-rapide)
4. [Architecture du projet](#4-architecture-du-projet)
5. [Structure des fichiers](#5-structure-des-fichiers)
6. [Services Docker (14 conteneurs)](#6-services-docker-14-conteneurs)
7. [Backend (FastAPI / Python)](#7-backend-fastapi--python)
8. [Frontend (React / TypeScript)](#8-frontend-react--typescript)
9. [Variables d'environnement](#9-variables-denvironnement)
10. [Endpoints API](#10-endpoints-api)
11. [Base de donnees](#11-base-de-donnees)
12. [Systemes cibles](#12-systemes-cibles)
13. [Developpement au quotidien](#13-developpement-au-quotidien)
14. [Build et deploiement](#14-build-et-deploiement)
15. [Scripts utilitaires](#15-scripts-utilitaires)
16. [Depannage (Troubleshooting)](#16-depannage-troubleshooting)
17. [Conventions du code](#17-conventions-du-code)

---

## 1. Vue d'ensemble du projet

**Gateway IAM** est une passerelle de provisionnement d'identites multi-cibles. Elle permet de gerer les comptes utilisateurs sur plusieurs systemes (LDAP, SQL, Odoo, Keycloak) via une interface web unique, avec MidPoint comme hub central IGA (Identity Governance & Administration).

### Ce que fait la Gateway :

| Fonctionnalite | Description |
|---|---|
| **Provisionnement** | Creer/modifier/supprimer des comptes sur LDAP, SQL, Odoo, Keycloak |
| **Regles de mapping** | Transformer les attributs source -> cible via Jinja2 |
| **Workflows d'approbation** | Validation multi-niveaux (Manager -> RH -> IT Admin) |
| **Reconciliation** | Detecter et resoudre les divergences entre systemes |
| **Comparaison Live** | Vue temps reel des donnees Odoo vs LDAP/MidPoint |
| **Groupes LDAP** | Gestion visuelle des groupes et membres |
| **Utilisateurs MidPoint** | CRUD complet avec assignation de roles |
| **Assistant IA** | Chat intelligent pour aide au mapping et diagnostic |
| **Audit** | Logs complets avec recherche semantique (Qdrant) |
| **Connecteurs dynamiques** | Wizard no-code pour configurer de nouveaux connecteurs |

### Stack technique :

- **Backend** : Python 3.11, FastAPI, SQLAlchemy 2.0, asyncpg, structlog
- **Frontend** : React 18, TypeScript, Vite 5, Tailwind CSS 3, Zustand 4
- **Base de donnees** : PostgreSQL 15 (4 instances), Redis 7, Qdrant
- **IAM** : MidPoint 4.4, OpenLDAP 1.5, Keycloak 23
- **ERP** : Odoo 17
- **Infrastructure** : Docker Compose, nginx

---

## 2. Prerequisites

### Logiciels requis

| Logiciel | Version minimale | Verification |
|---|---|---|
| Docker | 20.10+ | `docker --version` |
| Docker Compose | 2.0+ | `docker compose version` |
| Git | 2.30+ | `git --version` |
| Node.js | 20+ (dev frontend) | `node --version` |
| npm | 9+ (dev frontend) | `npm --version` |
| Python | 3.11+ (dev backend) | `python3 --version` |

### Ressources systeme recommandees

- **RAM** : 8 Go minimum (14 conteneurs Docker)
- **Disque** : 10 Go d'espace libre (images Docker + volumes)
- **CPU** : 4 coeurs recommandes
- **OS** : Linux (Ubuntu 22.04+), macOS, Windows (WSL2)

### Ports utilises

Assurez-vous que ces ports sont libres avant de lancer le projet :

| Port | Service |
|---|---|
| 3000 | Frontend React (nginx) |
| 8000 | Backend FastAPI (Gateway) |
| 8069 | Odoo ERP |
| 8080 | MidPoint IGA |
| 8081 | Keycloak IAM |
| 8088 | phpLDAPAdmin |
| 5433 | PostgreSQL MidPoint |
| 5434 | PostgreSQL Gateway |
| 55432 | PostgreSQL Intranet |
| 6333 | Qdrant (REST API) |
| 6334 | Qdrant (gRPC) |
| 6379 | Redis |
| 10389 | OpenLDAP |
| 10636 | OpenLDAP (SSL) |

---

## 3. Installation rapide

### Etape 1 : Cloner le projet

```bash
git clone <url-du-repo> Project3-clean
cd Project3-clean
```

### Etape 2 : Configurer l'environnement

```bash
# Copier le fichier d'exemple
cp .env.example .env

# Editer le fichier .env (optionnel pour le dev)
nano .env
```

Contenu du `.env` :
```env
# Securite - CHANGER EN PRODUCTION
SECRET_KEY=change-me-in-production-use-openssl-rand-hex-32
JWT_SECRET_KEY=jwt-secret-change-in-production

# IA (optionnel - pour l'assistant IA)
OPENAI_API_KEY=

# Keycloak (optionnel - pour OAuth2)
KEYCLOAK_CLIENT_SECRET=

# Debug
DEBUG=false
```

> **Note** : Pour le developpement local, les valeurs par defaut dans `docker-compose.yml` suffisent. Pas besoin de remplir `.env` sauf pour l'assistant IA (cle OpenAI).

### Etape 3 : Lancer tous les services

```bash
# Demarrer les 14 conteneurs
docker compose up -d

# Suivre les logs (optionnel)
docker compose logs -f
```

Le premier demarrage prend **5 a 10 minutes** :
1. Telechargement des images Docker (~3 Go)
2. Build du backend Gateway et du frontend React
3. Initialisation des bases de donnees
4. Demarrage de MidPoint (le plus long ~2-3 min)

### Etape 4 : Verifier que tout tourne

```bash
# Voir l'etat de tous les conteneurs
docker compose ps

# Tous doivent etre "Up" ou "healthy"
```

### Etape 5 : Acceder aux interfaces

| Interface | URL | Identifiants par defaut |
|---|---|---|
| **Frontend Gateway** | http://localhost:3000 | admin / admin123 |
| **API Swagger** | http://localhost:8000/docs | (token JWT) |
| **MidPoint** | http://localhost:8080/midpoint | administrator / 5ecr3t |
| **Odoo** | http://localhost:8069 | admin / admin |
| **Keycloak** | http://localhost:8081 | admin / admin |
| **phpLDAPAdmin** | http://localhost:8088 | cn=admin,dc=example,dc=com / secret |
| **Qdrant Dashboard** | http://localhost:6333/dashboard | (pas d'auth) |

### Etape 6 : Initialiser les donnees (optionnel)

```bash
# Configurer la structure LDAP (OU groups, users)
cd scripts
bash setup_ldap_structure.sh

# Importer la configuration MidPoint (ressources, taches)
bash import-midpoint-config.sh

# Synchroniser les utilisateurs Odoo -> MidPoint
python3 odoo_to_midpoint_sync.py
```

---

## 4. Architecture du projet

### Schema global

```
┌─────────────┐     ┌──────────────┐     ┌─────────────────┐
│   Frontend   │────>│   Backend    │────>│   MidPoint      │
│  React/nginx │     │   FastAPI    │     │  (Hub IGA)      │
│  port 3000   │     │  port 8000   │     │  port 8080      │
└─────────────┘     └──────┬───────┘     └────────┬────────┘
                           │                       │
                    ┌──────┼───────┐        ┌──────┼───────┐
                    │      │       │        │      │       │
               ┌────▼──┐ ┌▼────┐ ┌▼─────┐  │   Systemes   │
               │ Postgr │ │Redis│ │Qdrant│  │    cibles    │
               │  SQL   │ │     │ │      │  │              │
               └────────┘ └─────┘ └──────┘  └──────────────┘
                                            ┌──────────────┐
                                            │  OpenLDAP    │
                                            │  Odoo        │
                                            │  Intranet DB │
                                            │  Keycloak    │
                                            └──────────────┘
```

### Flux de donnees typique (provisionnement)

1. L'utilisateur remplit le formulaire dans le **Frontend** (React)
2. Le frontend envoie un POST a `/api/v1/provision/` via **axios**
3. Le **Backend** (FastAPI) recoit la requete, applique les **regles Jinja2**
4. Si un workflow est requis, le provisionnement est **mis en pause** en attendant l'approbation
5. Une fois approuve, le backend provisionne sur les **systemes cibles** via les connecteurs
6. Les **logs d'audit** sont enregistres dans PostgreSQL + Qdrant (vectoriel)
7. Le resultat est retourne au frontend

### Flux nginx (reverse proxy)

```
Navigateur --> nginx (port 3000)
                ├── /api/*  --> proxy_pass --> FastAPI (port 8000)
                └── /*      --> fichiers statiques React (SPA)
```

---

## 5. Structure des fichiers

```
Project3-clean/
├── docker-compose.yml          # Orchestration des 14 services
├── .env.example                # Variables d'environnement (template)
├── .env                        # Variables d'environnement (local, gitignore)
│
├── gateway/                    # === APPLICATION PRINCIPALE ===
│   ├── Dockerfile              # Image Docker backend (Python 3.11)
│   ├── requirements.txt        # Dependances Python (FastAPI, SQLAlchemy, etc.)
│   │
│   ├── app/                    # Code source backend
│   │   ├── main.py             # Point d'entree FastAPI + 14 routeurs
│   │   │
│   │   ├── api/                # Endpoints REST (routeurs FastAPI)
│   │   │   ├── admin.py        # Auth (login/register), statut, arret urgence
│   │   │   ├── provision.py    # CRUD provisionnement multi-cibles
│   │   │   ├── rules.py        # CRUD regles de mapping Jinja2
│   │   │   ├── workflow.py     # Approbation multi-niveaux + email
│   │   │   ├── reconcile.py    # Lancement reconciliation + divergences
│   │   │   ├── live_comparison.py  # Comparaison temps reel Odoo/LDAP/SQL
│   │   │   ├── connectors.py   # CRUD connecteurs dynamiques
│   │   │   ├── midpoint.py     # Pilotage MidPoint (users, roles, tasks)
│   │   │   ├── ldap_groups.py  # Gestion groupes LDAP
│   │   │   ├── users.py        # CRUD utilisateurs gateway
│   │   │   ├── permissions.py  # Niveaux de droits (1-5)
│   │   │   ├── ai_assistant.py # Chat IA + config provider
│   │   │   ├── scheduler.py    # Jobs de synchronisation planifies
│   │   │   └── webhooks.py     # Notifications entrantes MidPoint
│   │   │
│   │   ├── services/           # Logique metier
│   │   │   ├── provision_service.py    # Orchestration provisionnement
│   │   │   ├── rule_engine.py          # Moteur de regles Jinja2 (sandbox)
│   │   │   ├── workflow_service.py     # Machine a etats workflows
│   │   │   ├── reconciliation_service.py # Detection divergences
│   │   │   ├── midpoint_client.py      # Client HTTP MidPoint REST
│   │   │   ├── midpoint_provision_service.py  # Provisionnement via MidPoint
│   │   │   ├── midpoint_resource_service.py   # Gestion ressources MidPoint
│   │   │   ├── connector_management_service.py # Registre connecteurs
│   │   │   ├── scheduler_service.py    # APScheduler (taches periodiques)
│   │   │   ├── audit_service.py        # Logging audit + Qdrant
│   │   │   ├── ai_agent.py            # Integration LLM (OpenAI, etc.)
│   │   │   ├── email_service.py       # Envoi notifications SMTP
│   │   │   └── user_service.py        # Logique utilisateurs gateway
│   │   │
│   │   ├── core/               # Infrastructure technique
│   │   │   ├── config.py       # Toutes les variables d'env (pydantic-settings)
│   │   │   ├── database.py     # Engine asyncpg + get_session()
│   │   │   ├── security.py     # JWT + bcrypt + get_current_user()
│   │   │   ├── memory_store.py # Cache local (singleton) charge depuis PostgreSQL
│   │   │   ├── redis_client.py # Client Redis (sessions, blacklist tokens)
│   │   │   ├── qdrant_store.py # Client Qdrant (recherche semantique audit)
│   │   │   └── logging.py      # structlog JSON + niveaux
│   │   │
│   │   ├── connectors/         # Connecteurs vers systemes cibles
│   │   │   ├── base.py         # Classe abstraite BaseConnector
│   │   │   ├── ldap_connector.py   # LDAP via ldap3
│   │   │   ├── sql_connector.py    # SQL via SQLAlchemy
│   │   │   ├── odoo_connector.py   # Odoo via XML-RPC
│   │   │   ├── midpoint_connector.py # MidPoint via REST API
│   │   │   └── connector_factory.py  # Factory pattern (registre)
│   │   │
│   │   ├── models/             # Schemas Pydantic (request/response)
│   │   │   ├── provision.py    # ProvisionRequest, ProvisionResult, enums
│   │   │   ├── rules.py        # Rule, RuleCreate, RuleType
│   │   │   ├── workflow.py     # WorkflowInstance, ApprovalLevel
│   │   │   ├── connector.py    # ConnectorConfig, ConnectorType
│   │   │   ├── audit.py        # AuditEvent, SearchQuery
│   │   │   └── ai.py           # AIQueryRequest, MappingSuggestion
│   │   │
│   │   └── db/
│   │       └── migrations.py   # Creation automatique des tables SQL
│   │
│   └── frontend/               # === APPLICATION FRONTEND ===
│       ├── Dockerfile          # Image Docker frontend (Node 20 + nginx)
│       ├── nginx.conf          # Config nginx (proxy /api -> backend)
│       ├── package.json        # Dependances npm
│       ├── vite.config.ts      # Configuration Vite (bundler)
│       ├── tsconfig.json       # Configuration TypeScript
│       ├── tailwind.config.js  # Configuration Tailwind CSS
│       │
│       └── src/
│           ├── main.tsx        # Point d'entree (React, QueryClient, Router, i18n)
│           ├── App.tsx         # Routage (13 pages protegees + 2 publiques)
│           ├── index.css       # Styles globaux Tailwind
│           │
│           ├── components/
│           │   ├── Layout.tsx          # Sidebar + header + navigation
│           │   └── LanguageSelector.tsx # Selecteur FR/EN/UK
│           │
│           ├── pages/
│           │   ├── Landing.tsx         # Page marketing (publique)
│           │   ├── Login.tsx           # Formulaire connexion
│           │   ├── Dashboard.tsx       # Vue d'ensemble
│           │   ├── Operations.tsx      # Provisionnement
│           │   ├── Rules.tsx           # Regles de mapping
│           │   ├── Workflows.tsx       # Approbation
│           │   ├── Reconciliation.tsx  # Sync / divergences
│           │   ├── LiveComparison.tsx  # Vue temps reel
│           │   ├── Connectors.tsx      # Wizard connecteurs
│           │   ├── MidpointUsers.tsx   # Utilisateurs MidPoint
│           │   ├── Users.tsx           # Utilisateurs gateway
│           │   ├── LDAPGroups.tsx      # Groupes LDAP
│           │   ├── Permissions.tsx     # Niveaux de droits
│           │   ├── AIAssistant.tsx     # Chat IA
│           │   ├── AuditLogs.tsx       # Logs + recherche
│           │   └── Settings.tsx        # Parametres systeme
│           │
│           ├── lib/
│           │   └── api.ts      # Client axios + toutes les fonctions API
│           │
│           ├── store/
│           │   └── auth.ts     # Store Zustand (JWT + user)
│           │
│           └── i18n/
│               ├── index.ts    # Config i18next (3 langues)
│               └── locales/
│                   ├── fr.json # Traductions francais
│                   ├── en.json # Traductions anglais
│                   └── uk.json # Traductions ukrainien
│
├── scripts/                    # Scripts d'administration et import
│   ├── start.sh                # Demarrage complet
│   ├── stop.sh                 # Arret complet
│   ├── init-db.sh              # Initialisation base de donnees
│   ├── setup_ldap_structure.sh # Creation OU LDAP
│   ├── setup_ldap_structure.ldif # Donnees LDIF
│   ├── import-midpoint-config.sh # Import config MidPoint
│   ├── midpoint_import_config.py # Import config Python
│   ├── import_csv_users.py     # Import utilisateurs CSV
│   ├── import_csv_to_midpoint.sh # Import CSV shell
│   ├── odoo_to_midpoint_sync.py  # Sync Odoo -> MidPoint
│   ├── midpoint_to_keycloak_sync.py # Sync MidPoint -> Keycloak
│   ├── change-midpoint-password.py  # Changement mot de passe MidPoint
│   ├── check_environment.sh    # Verification prerequis
│   ├── demo/                   # Scripts de demonstration
│   └── tests/                  # Tests d'integration
│
├── infrastructure/             # Configuration infrastructure
│   ├── docker/                 # Configs Docker supplementaires
│   ├── midpoint/               # Configs MidPoint (ressources, taches)
│   └── sql/
│       └── init-intranet.sql   # Schema initial base intranet
│
└── docs/                       # Documentation
    ├── RAPPORT_MAINTENANCE.md  # Rapport de maintenance
    ├── GUIDE_DEVELOPPEUR.md    # Ce fichier
    └── ...                     # Presentations, schemas, etc.
```

---

## 6. Services Docker (14 conteneurs)

Tous les services sont definis dans `docker-compose.yml` et communiquent via le reseau Docker `iam-network`.

### Vue d'ensemble

| # | Service | Container | Image | Port | Role |
|---|---|---|---|---|---|
| 1 | **gateway** | gateway-iam | Build local | 8000 | Backend FastAPI (API REST) |
| 2 | **gateway-frontend** | gateway-frontend | Build local | 3000 | Frontend React (nginx) |
| 3 | **gateway-db** | gateway-db | postgres:15 | 5434 | BDD principale Gateway |
| 4 | **redis** | gateway-redis | redis:7-alpine | 6379 | Cache, sessions JWT, blacklist |
| 5 | **qdrant** | gateway-qdrant | qdrant/qdrant | 6333 | Recherche vectorielle (audit) |
| 6 | **midpoint** | midpoint-core | evolveum/midpoint:4.4 | 8080 | Hub IGA central |
| 7 | **midpoint-postgres** | midpoint-postgres | postgres:15 | 5433 | BDD MidPoint |
| 8 | **openldap** | openldap | osixia/openldap:1.5.0 | 10389 | Annuaire LDAP |
| 9 | **phpldapadmin** | phpldapadmin | osixia/phpldapadmin | 8088 | Interface web LDAP |
| 10 | **odoo** | odoo | odoo:17 | 8069 | ERP Odoo |
| 11 | **odoo-db** | odoo-db | postgres:15 | - | BDD Odoo |
| 12 | **intranet-db** | intranet-db | postgres:15 | 55432 | BDD Intranet (cible SQL) |
| 13 | **keycloak** | keycloak | keycloak:23.0 | 8081 | SSO / OAuth2 |
| 14 | **keycloak-db** | keycloak-db | postgres:15 | - | BDD Keycloak |

### Dependances au demarrage

```
midpoint-postgres (healthy) --> midpoint
gateway-db (healthy) ---------> gateway
redis (healthy) --------------> gateway
qdrant (started) -------------> gateway
gateway -----------------------> gateway-frontend
openldap ---------------------> phpldapadmin
odoo-db (healthy) ------------> odoo
keycloak-db (healthy) --------> keycloak
```

### Volumes persistants (12)

Les donnees sont persistees dans des volumes Docker nommes :

```
midpoint_postgres_data   # Donnees BDD MidPoint
midpoint_home            # Configuration MidPoint (/opt/midpoint/var)
gateway_db_data          # Donnees BDD Gateway
gateway_logs             # Logs applicatifs
redis_data               # Donnees Redis
qdrant_data              # Index vectoriels
openldap_data            # Donnees LDAP (/var/lib/ldap)
openldap_config          # Config LDAP (slapd.d)
odoo_db_data             # Donnees BDD Odoo
odoo_data                # Fichiers Odoo
odoo_addons              # Addons Odoo custom
intranet_db_data         # Donnees BDD Intranet
keycloak_db_data         # Donnees BDD Keycloak
```

### Commandes Docker utiles

```bash
# Voir tous les conteneurs et leur etat
docker compose ps

# Logs d'un service specifique
docker compose logs -f gateway
docker compose logs -f midpoint

# Redemarrer un seul service
docker compose restart gateway

# Reconstruire et redemarrer le backend
docker compose up -d --build gateway

# Acceder au shell d'un conteneur
docker exec -it gateway-iam bash
docker exec -it midpoint-core bash

# Supprimer tout et repartir de zero
docker compose down -v   # ATTENTION: supprime toutes les donnees !
```

---

## 7. Backend (FastAPI / Python)

### Architecture

Le backend suit une architecture en couches :

```
API (routeurs)  -->  Services (logique metier)  -->  Connecteurs (systemes cibles)
     │                       │                              │
     └── models/          core/                        base.py (abstraction)
    (Pydantic)    (config, db, security)           ldap, sql, odoo, midpoint
```

### Point d'entree : `main.py`

Le fichier `gateway/app/main.py` :
1. Configure l'application FastAPI (titre, CORS, version)
2. Enregistre les **14 routeurs** avec leurs prefixes
3. Gere le **cycle de vie** (startup/shutdown) :
   - Startup : Logs -> PostgreSQL -> Cache -> Redis -> Qdrant -> Scheduler
   - Shutdown : Scheduler -> Redis

### Les 14 routeurs API

| Routeur | Prefixe | Description |
|---|---|---|
| `admin` | `/api/v1/admin` | Login, register, status, arret urgence |
| `provision` | `/api/v1/provision` | Provisionnement CRUD |
| `rules` | `/api/v1/rules` | Regles de mapping CRUD |
| `workflow` | `/api/v1/workflow` | Workflows d'approbation |
| `reconcile` | `/api/v1/reconcile` | Reconciliation source/cible |
| `live_comparison` | `/api/v1/live` | Vue temps reel |
| `connectors` | `/api/v1/connectors` | Connecteurs dynamiques |
| `midpoint` | `/api/v1` | Pilotage MidPoint |
| `ldap_groups` | `/api/v1` | Groupes LDAP |
| `users` | `/api/v1/users` | Utilisateurs gateway |
| `permissions` | `/api/v1/permissions` | Niveaux de droits |
| `ai_assistant` | `/api/v1/ai` | Assistant IA |
| `scheduler` | `/api/v1/scheduler` | Planification sync |
| `webhooks` | (pas de prefixe) | Webhooks MidPoint |

### Authentification (JWT)

Le systeme d'authentification est dans `core/security.py` :

1. **Login** (`POST /api/v1/admin/login`) : Retourne un JWT token
2. Le token est inclus dans le header `Authorization: Bearer <token>`
3. `get_current_user()` est un **Depends** FastAPI qui valide le token
4. Les tokens revoques sont stockes dans une **blacklist Redis**
5. Les mots de passe sont hashes avec **bcrypt**

```python
# Exemple : proteger un endpoint
from app.core.security import get_current_user

@router.get("/protected")
async def protected_route(current_user: dict = Depends(get_current_user)):
    return {"user": current_user["username"]}
```

### Moteur de regles (Jinja2)

Le fichier `services/rule_engine.py` gere la transformation des attributs :

- Les regles sont des **expressions Jinja2** executees dans un sandbox
- 4 types de regles : `mapping`, `calculation`, `validation`, `aggregation`
- Les regles sont executees par **priorite** (la plus haute en premier)
- Chaque regle est versionnee

Exemple de regle :
```
# Type: mapping
# Expression Jinja2 :
{{ first_name | lower }}.{{ last_name | lower }}
# Resultat : "jean.dupont"
```

### Cache hybride (MemoryStore + PostgreSQL)

Le fichier `core/memory_store.py` implemente un cache local :

1. Au demarrage, les donnees sont chargees depuis PostgreSQL dans un `dict` Python
2. Les lectures API utilisent le cache (rapide)
3. Les ecritures mettent a jour le cache ET PostgreSQL
4. Avantage : pas de requete SQL pour chaque lecture

> **Limitation connue** : Certaines donnees (workflows, conversations IA) ne sont stockees qu'en memoire et sont perdues au redemarrage du conteneur.

### Dependances Python

Fichier `gateway/requirements.txt` :

| Package | Role |
|---|---|
| fastapi | Framework web async |
| uvicorn | Serveur ASGI |
| sqlalchemy + asyncpg | ORM + driver PostgreSQL async |
| redis | Client Redis |
| ldap3 | Connecteur LDAP |
| python-jose + bcrypt | JWT + hashing |
| httpx | Client HTTP async (MidPoint) |
| jinja2 | Moteur de templates (regles) |
| pydantic + pydantic-settings | Validation + config |
| structlog | Logging structure JSON |
| apscheduler | Planification taches |
| openai | Integration IA (optionnel) |
| qdrant-client | Recherche vectorielle (optionnel) |

---

## 8. Frontend (React / TypeScript)

### Architecture

```
main.tsx (providers)
  └── App.tsx (routage)
        ├── Landing.tsx (publique)
        ├── Login.tsx (publique)
        └── Layout.tsx (sidebar + header)
              └── [13 pages protegees]
```

### Technologies

| Technologie | Role |
|---|---|
| React 18 | Framework UI |
| TypeScript 5.3 | Typage statique |
| Vite 5 | Bundler / dev server |
| React Router 6 | Routage SPA |
| TanStack React Query 5 | Gestion requetes API (cache 5 min, retry 1) |
| Zustand 4 | State management (auth) |
| Tailwind CSS 3 | Styles utilitaires |
| Lucide React | Icones SVG |
| i18next | Internationalisation (FR/EN/UK) |
| Monaco Editor | Editeur de code (regles) |
| Axios | Client HTTP |
| date-fns | Manipulation dates |
| Radix UI | Composants accessibles (dialog, tabs, dropdown) |

### Routage (App.tsx)

| Route | Page | Description |
|---|---|---|
| `/` | Landing | Page marketing publique |
| `/login` | Login | Formulaire connexion |
| `/dashboard` | Dashboard | Vue d'ensemble |
| `/dashboard/operations` | Operations | Provisionnement |
| `/dashboard/rules` | Rules | Regles de mapping |
| `/dashboard/workflows` | Workflows | Approbation |
| `/dashboard/reconciliation` | Reconciliation | Sync / divergences |
| `/dashboard/live` | LiveComparison | Vue temps reel |
| `/dashboard/permissions` | Permissions | Niveaux de droits |
| `/dashboard/connectors` | Connectors | Connecteurs |
| `/dashboard/midpoint-users` | MidpointUsers | Utilisateurs MidPoint |
| `/dashboard/gateway-users` | Users | Utilisateurs gateway |
| `/dashboard/ai` | AIAssistant | Chat IA |
| `/dashboard/audit` | AuditLogs | Logs |
| `/dashboard/settings` | Settings | Parametres |

### Client API (`lib/api.ts`)

Toutes les fonctions d'appel API sont centralisees dans `lib/api.ts` :

```typescript
// Instance axios avec intercepteur JWT
const api = axios.create({ baseURL: '/api/v1' })

// L'intercepteur ajoute automatiquement le Bearer token
api.interceptors.request.use((config) => {
  const token = useAuthStore.getState().token
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})
```

Les fonctions sont organisees par section :
- `login()`, `register()`, `getStatus()` - Auth
- `createProvision()`, `getOperations()` - Provisionnement
- `getRules()`, `createRule()`, `testRule()` - Regles
- `getWorkflows()`, `approveWorkflow()` - Workflows
- `getConnectors()`, `testConnector()` - Connecteurs
- `getMidpointUsers()`, `createMidpointUser()` - MidPoint
- `getLDAPGroups()`, `addMember()` - Groupes LDAP
- etc.

### Store d'authentification (`store/auth.ts`)

Utilise Zustand avec persistence localStorage :

```typescript
// Le token et l'utilisateur sont persistes dans localStorage['auth-storage']
const { token, user, isAuthenticated, login, logout } = useAuthStore()
```

### Internationalisation (i18n)

3 langues supportees : Francais, English, Ukrainien

- Les fichiers de traduction sont dans `src/i18n/locales/`
- La langue est detectee automatiquement (navigateur) et sauvegardee dans localStorage
- Le selecteur de langue est dans le header (`LanguageSelector.tsx`)

### Commandes frontend

```bash
cd gateway/frontend

# Serveur de dev (hot reload, port 5173)
npm run dev

# Build production (-> dist/)
npm run build

# Preview du build
npm run preview

# Lint
npm run lint

# Tests
npm run test
```

---

## 9. Variables d'environnement

Toutes les variables sont definies dans `gateway/app/core/config.py` avec des valeurs par defaut.

### Application

| Variable | Defaut | Description |
|---|---|---|
| `APP_NAME` | Gateway IAM | Nom de l'application |
| `DEBUG` | false | Mode debug |
| `SECRET_KEY` | (a changer) | Cle secrete application |
| `LOG_LEVEL` | INFO | Niveau de log (DEBUG, INFO, WARNING, ERROR) |
| `BASE_URL` | http://localhost:8000 | URL publique du backend |
| `DEV_MODE` | true | Mode developpement |

### Base de donnees

| Variable | Defaut | Description |
|---|---|---|
| `DATABASE_URL` | postgresql+asyncpg://gateway:gateway@localhost:5434/gateway | URL PostgreSQL |
| `REDIS_URL` | redis://localhost:6379/0 | URL Redis |

### JWT (authentification)

| Variable | Defaut | Description |
|---|---|---|
| `JWT_SECRET_KEY` | (a changer) | Cle secrete JWT |
| `JWT_ALGORITHM` | HS256 | Algorithme de signature |
| `JWT_EXPIRE_MINUTES` | 60 | Duree de vie du token (minutes) |

### MidPoint

| Variable | Defaut | Description |
|---|---|---|
| `MIDPOINT_URL` | http://midpoint-core:8080/midpoint | URL MidPoint |
| `MIDPOINT_USER` | administrator | Utilisateur admin |
| `MIDPOINT_PASSWORD` | 5ecr3t | Mot de passe admin |
| `MIDPOINT_ENABLED` | true | Activer le hub MidPoint |

### LDAP

| Variable | Defaut | Description |
|---|---|---|
| `LDAP_HOST` | localhost | Hote LDAP |
| `LDAP_PORT` | 10389 | Port LDAP |
| `LDAP_BIND_DN` | cn=admin,dc=example,dc=com | DN de bind |
| `LDAP_BIND_PASSWORD` | secret | Mot de passe bind |
| `LDAP_BASE_DN` | dc=example,dc=com | Base DN |

### Odoo

| Variable | Defaut | Description |
|---|---|---|
| `ODOO_URL` | http://localhost:8069 | URL Odoo |
| `ODOO_DB` | odoo | Base de donnees Odoo |
| `ODOO_USER` | admin | Utilisateur Odoo |
| `ODOO_PASSWORD` | admin | Mot de passe Odoo |

### Intranet (SQL cible)

| Variable | Defaut | Description |
|---|---|---|
| `INTRANET_DB_URL` | postgresql://intranet:intranet@localhost:55432/intranet | URL PostgreSQL intranet |

### Keycloak

| Variable | Defaut | Description |
|---|---|---|
| `KEYCLOAK_URL` | http://localhost:8081 | URL Keycloak |
| `KEYCLOAK_REALM` | gateway | Realm Keycloak |
| `KEYCLOAK_CLIENT_ID` | gateway-client | Client ID |
| `KEYCLOAK_CLIENT_SECRET` | (vide) | Client secret |

### IA

| Variable | Defaut | Description |
|---|---|---|
| `OPENAI_API_KEY` | (vide) | Cle API OpenAI |
| `OPENAI_MODEL` | gpt-4-turbo-preview | Modele OpenAI |
| `DEEPSEEK_API_KEY` | (vide) | Cle API DeepSeek |

### Qdrant

| Variable | Defaut | Description |
|---|---|---|
| `QDRANT_HOST` | localhost | Hote Qdrant |
| `QDRANT_PORT` | 6333 | Port Qdrant |

### Email / SMTP

| Variable | Defaut | Description |
|---|---|---|
| `SMTP_HOST` | smtp.gmail.com | Serveur SMTP |
| `SMTP_PORT` | 587 | Port SMTP |
| `SMTP_USER` | (vide) | Utilisateur SMTP |
| `SMTP_PASSWORD` | (vide) | Mot de passe SMTP |
| `FROM_EMAIL` | noreply@iam-gateway.local | Adresse expediteur |

### Workflow

| Variable | Defaut | Description |
|---|---|---|
| `WORKFLOW_DEFAULT_TIMEOUT_HOURS` | 72 | Timeout approbation (heures) |
| `WORKFLOW_MAX_LEVELS` | 5 | Niveaux max d'approbation |

### CORS

| Variable | Defaut | Description |
|---|---|---|
| `CORS_ORIGINS` | ["http://localhost:3000", "http://localhost:3001", "http://localhost:8080"] | Origines autorisees |

---

## 10. Endpoints API

La documentation interactive Swagger est accessible a **http://localhost:8000/docs**.

### Principaux endpoints

#### Authentification (`/api/v1/admin`)
```
POST   /api/v1/admin/login       # Connexion (retourne JWT)
POST   /api/v1/admin/register    # Inscription
POST   /api/v1/admin/logout      # Deconnexion (blacklist token)
GET    /api/v1/admin/status      # Etat des services
POST   /api/v1/admin/emergency-stop  # Arret d'urgence
```

#### Provisionnement (`/api/v1/provision`)
```
GET    /api/v1/provision/                # Liste des operations
POST   /api/v1/provision/               # Nouvelle operation
GET    /api/v1/provision/{id}           # Details d'une operation
GET    /api/v1/provision/{id}/status    # Statut d'une operation
POST   /api/v1/provision/{id}/test      # Test a blanc
```

#### Regles (`/api/v1/rules`)
```
GET    /api/v1/rules/           # Liste des regles
POST   /api/v1/rules/          # Creer une regle
GET    /api/v1/rules/{id}      # Details d'une regle
PUT    /api/v1/rules/{id}      # Modifier une regle
DELETE /api/v1/rules/{id}      # Supprimer une regle
POST   /api/v1/rules/{id}/test # Tester une regle
```

#### Workflows (`/api/v1/workflow`)
```
GET    /api/v1/workflow/                    # Liste des workflows
GET    /api/v1/workflow/{id}               # Details
POST   /api/v1/workflow/{id}/approve       # Approuver
POST   /api/v1/workflow/{id}/reject        # Rejeter
GET    /api/v1/workflow/approve-by-email   # Approbation par email
```

#### Reconciliation (`/api/v1/reconcile`)
```
POST   /api/v1/reconcile/start              # Lancer une reconciliation
GET    /api/v1/reconcile/jobs               # Liste des jobs
GET    /api/v1/reconcile/divergences        # Divergences detectees
POST   /api/v1/reconcile/divergences/{id}/resolve  # Resoudre
```

#### Comparaison Live (`/api/v1/live`)
```
GET    /api/v1/live/stats                   # Statistiques
GET    /api/v1/live/comparison              # Comparaison Odoo vs MidPoint
GET    /api/v1/live/search                  # Recherche d'utilisateurs
POST   /api/v1/live/sync-user              # Sync un utilisateur
POST   /api/v1/live/full-sync             # Sync complete
POST   /api/v1/live/schedule              # Planifier une sync
```

#### Connecteurs (`/api/v1/connectors`)
```
GET    /api/v1/connectors/          # Liste
POST   /api/v1/connectors/         # Creer
PUT    /api/v1/connectors/{id}     # Modifier
DELETE /api/v1/connectors/{id}     # Supprimer
POST   /api/v1/connectors/{id}/test  # Tester la connexion
```

#### MidPoint (`/api/v1/midpoint`)
```
GET    /api/v1/midpoint/users              # Liste utilisateurs
POST   /api/v1/midpoint/users             # Creer utilisateur
PUT    /api/v1/midpoint/users/{oid}       # Modifier
DELETE /api/v1/midpoint/users/{oid}       # Supprimer
POST   /api/v1/midpoint/users/{oid}/enable   # Activer
POST   /api/v1/midpoint/users/{oid}/disable  # Desactiver
GET    /api/v1/midpoint/roles              # Liste roles
POST   /api/v1/midpoint/users/{oid}/roles  # Assigner role
```

#### Groupes LDAP (`/api/v1/ldap/groups`)
```
GET    /api/v1/ldap/groups                      # Liste groupes
GET    /api/v1/ldap/groups/{name}               # Details d'un groupe
POST   /api/v1/ldap/groups/{name}/members       # Ajouter membre
DELETE /api/v1/ldap/groups/{name}/members/{uid}  # Retirer membre
GET    /api/v1/ldap/groups/users/search         # Recherche utilisateurs
GET    /api/v1/ldap/groups/user/{uid}/memberships  # Groupes d'un user
```

#### Assistant IA (`/api/v1/ai`)
```
POST   /api/v1/ai/query              # Question en langage naturel
POST   /api/v1/ai/suggest-mappings   # Suggestions de mapping
POST   /api/v1/ai/generate-connector # Generation de connecteur
POST   /api/v1/ai/analyze-error      # Analyse d'erreur
POST   /api/v1/ai/explain-rule       # Explication de regle
GET    /api/v1/ai/config             # Config IA actuelle
POST   /api/v1/ai/config             # Mettre a jour config IA
```

---

## 11. Base de donnees

### PostgreSQL Gateway (`gateway-db`, port 5434)

La base `gateway` contient les tables principales :

| Table | Description |
|---|---|
| `users` | Utilisateurs de la gateway (admin, manager, etc.) |
| `operations` | Historique des operations de provisionnement |
| `audit_events` | Logs d'audit |
| `rules` | Regles de mapping |
| `workflow_instances` | Instances de workflows |
| `connectors` | Configuration des connecteurs |
| `ai_configuration` | Configuration du provider IA |

Les tables sont creees automatiquement au demarrage via `db/migrations.py`.

### Acces direct a la base

```bash
# Se connecter a la base gateway
docker exec -it gateway-db psql -U gateway -d gateway

# Lister les tables
\dt

# Voir les utilisateurs
SELECT * FROM users;

# Voir les operations
SELECT * FROM operations ORDER BY created_at DESC LIMIT 10;
```

### Redis (`gateway-redis`, port 6379)

Utilise pour :
- **Blacklist JWT** : tokens revoques (cle: `blacklist:<token>`)
- **Cache de sessions** : acceleration des requetes frequentes

```bash
# Se connecter a Redis
docker exec -it gateway-redis redis-cli

# Voir les cles
KEYS *

# Verifier un token blackliste
GET blacklist:<token>
```

### Qdrant (`gateway-qdrant`, port 6333)

Base vectorielle pour la **recherche semantique** dans les logs d'audit :
- Collection : `audit_events`
- Dimension des vecteurs : 384 (sentence-transformers)
- Interface web : http://localhost:6333/dashboard

---

## 12. Systemes cibles

### MidPoint (Hub IGA central)

- **Role** : Orchestrateur central de provisionnement
- **URL interne** : http://midpoint-core:8080/midpoint
- **API** : REST API MidPoint (XML/JSON)
- **Fonctionnalites utilisees** :
  - Gestion des utilisateurs (focus objects)
  - Attribution de roles
  - Taches de reconciliation
  - Ressources (LDAP, CSV, etc.)
  - Shadows (comptes sur systemes cibles)

### OpenLDAP (Annuaire)

- **Role** : Annuaire d'entreprise
- **URL interne** : ldap://openldap:389
- **Structure** :
  - `dc=example,dc=com` (racine)
  - `ou=users,dc=example,dc=com` (utilisateurs)
  - `ou=groups,dc=example,dc=com` (groupes)
- **Types de groupes** : groupOfUniqueNames, groupOfNames, posixGroup

### Odoo (ERP)

- **Role** : Source RH (employes, departements, contrats)
- **URL interne** : http://odoo:8069
- **Protocole** : XML-RPC (`/xmlrpc/2/common` et `/xmlrpc/2/object`)
- **Modeles utilises** : `hr.employee`, `hr.department`, `hr.contract`

### Intranet DB (SQL)

- **Role** : Base intranet (cible de provisionnement SQL)
- **URL interne** : postgresql://intranet:intranet@intranet-db:5432/intranet
- **Table initiale** : definie dans `infrastructure/sql/init-intranet.sql`

### Keycloak (SSO)

- **Role** : Single Sign-On et OAuth2
- **URL interne** : http://keycloak:8080
- **Realm** : `gateway`
- **Protocole** : OpenID Connect

---

## 13. Developpement au quotidien

### Modifier le backend (Python)

Le code backend est monte en volume dans le conteneur Docker :
```yaml
volumes:
  - ./gateway/app:/app/app  # Le code local est synchronise
```

**Avantage** : Modifiez les fichiers Python localement, le conteneur les voit directement.

**Limitation** : Uvicorn ne fait pas de hot-reload automatique en Docker. Pour appliquer les changements :
```bash
# Methode 1 : Redemarrer le conteneur
docker compose restart gateway

# Methode 2 : Reconstruire (si requirements.txt change)
docker compose up -d --build gateway
```

### Modifier le frontend (React)

#### Option 1 : Dev server local (recommande pour le dev)

```bash
cd gateway/frontend
npm install
npm run dev
# -> http://localhost:5173 (hot reload automatique)
```

Configurer le proxy Vite pour pointer vers le backend Docker :
```typescript
// vite.config.ts - ajouter un proxy
server: {
  proxy: {
    '/api': 'http://localhost:8000'
  }
}
```

#### Option 2 : Build + deploiement Docker

```bash
cd gateway/frontend
npm run build

# Copier le build dans le conteneur
docker cp dist/. gateway-frontend:/usr/share/nginx/html/

# Redemarrer nginx
docker restart gateway-frontend
```

### Ajouter un nouvel endpoint API

1. Creer le fichier dans `gateway/app/api/mon_module.py`
2. Definir le routeur : `router = APIRouter()`
3. Ajouter les endpoints avec `@router.get()`, `@router.post()`, etc.
4. Enregistrer le routeur dans `main.py` :
   ```python
   from app.api import mon_module
   app.include_router(mon_module.router, prefix="/api/v1/mon-module", tags=["Mon Module"])
   ```
5. Proteger avec `Depends(get_current_user)` si besoin d'authentification

### Ajouter une nouvelle page frontend

1. Creer le composant dans `gateway/frontend/src/pages/MaPage.tsx`
2. Ajouter la route dans `App.tsx` :
   ```tsx
   <Route path="/ma-page" element={<MaPage />} />
   ```
3. Ajouter le lien dans la sidebar (`Layout.tsx`)
4. Ajouter les traductions dans `i18n/locales/fr.json`, `en.json`, `uk.json`

### Ajouter un nouveau connecteur

1. Creer la classe dans `gateway/app/connectors/mon_connecteur.py`
2. Heriter de `BaseConnector` (`connectors/base.py`)
3. Implementer les methodes abstraites :
   - `test_connection()`
   - `create_account()`
   - `update_account()`
   - `delete_account()`
   - `get_account()`
4. Enregistrer dans `connector_factory.py`

---

## 14. Build et deploiement

### Build du frontend (production)

```bash
cd gateway/frontend

# Build TypeScript + Vite -> dist/
npm run build

# Le resultat est dans dist/ (~600 Ko JS, ~50 Ko CSS)
```

### Deployer sur les conteneurs Docker

```bash
# 1. Build le frontend
cd gateway/frontend && npm run build

# 2. Copier dans le conteneur nginx
docker cp dist/. gateway-frontend:/usr/share/nginx/html/

# 3. Redemarrer nginx
docker restart gateway-frontend

# 4. Reconstruire le backend si necessaire
docker compose up -d --build gateway
```

### Reconstruire tout depuis zero

```bash
# Arreter et supprimer les conteneurs (garder les volumes)
docker compose down

# Reconstruire toutes les images
docker compose build --no-cache

# Relancer
docker compose up -d
```

### Reset complet (perte de donnees)

```bash
# Tout supprimer y compris les volumes
docker compose down -v

# Relancer
docker compose up -d
```

---

## 15. Scripts utilitaires

Tous les scripts sont dans le dossier `scripts/` :

| Script | Description |
|---|---|
| `start.sh` | Demarrage complet du projet |
| `stop.sh` | Arret complet |
| `init-db.sh` | Initialisation de la base de donnees |
| `check_environment.sh` | Verifier que tous les prerequis sont installes |
| `setup_ldap_structure.sh` | Creer les OU LDAP (users, groups) |
| `setup_ldap_structure.ldif` | Donnees LDIF pour la structure LDAP |
| `import-midpoint-config.sh` | Importer la configuration MidPoint |
| `midpoint_import_config.py` | Import config MidPoint (Python) |
| `import_csv_users.py` | Importer des utilisateurs depuis un CSV |
| `import_csv_to_midpoint.sh` | Import CSV vers MidPoint (shell) |
| `odoo_to_midpoint_sync.py` | Synchroniser Odoo -> MidPoint |
| `midpoint_to_keycloak_sync.py` | Synchroniser MidPoint -> Keycloak |
| `change-midpoint-password.py` | Changer le mot de passe MidPoint |
| `setup_midpoint.sh` | Configuration initiale MidPoint |

### Exemple d'utilisation :

```bash
cd scripts

# Verifier l'environnement
bash check_environment.sh

# Initialiser LDAP
bash setup_ldap_structure.sh

# Importer la config MidPoint
bash import-midpoint-config.sh

# Synchroniser Odoo vers MidPoint
pip install -r requirements.txt
python3 odoo_to_midpoint_sync.py
```

---

## 16. Depannage (Troubleshooting)

### Le conteneur gateway-iam est en "Restarting"

**Cause** : La gateway n'arrive pas a se connecter a PostgreSQL ou Redis au demarrage.

**Solution** :
```bash
# Verifier que les dependances sont healthy
docker compose ps gateway-db redis

# Voir les logs d'erreur
docker compose logs gateway | tail -50

# Redemarrer dans l'ordre
docker compose restart gateway-db redis
sleep 10
docker compose restart gateway
```

### MidPoint met longtemps a demarrer

C'est normal. MidPoint necessite 2-3 minutes pour initialiser sa base de donnees et demarrer le serveur Tomcat. Verifier avec :
```bash
docker compose logs -f midpoint
# Attendre "Started MidPointApplication"
```

### Erreur "host not found in upstream 'gateway'" (nginx)

**Cause** : Le conteneur frontend (nginx) ne peut pas resoudre le nom DNS du backend.

**Solution** :
```bash
# Redemarrer le frontend apres que le backend soit up
docker compose restart gateway-frontend
```

### Erreur LDAP "Can't contact LDAP server"

**Cause** : OpenLDAP n'est pas demarre ou le port est different.

**Solution** :
```bash
# Verifier qu'OpenLDAP tourne
docker compose ps openldap

# En local (hors Docker), utiliser le port mappe
# LDAP_HOST=localhost, LDAP_PORT=10389

# En Docker (dans le reseau), utiliser le nom du conteneur
# LDAP_HOST=openldap, LDAP_PORT=389
```

### La page frontend affiche une erreur 502

**Cause** : Le backend FastAPI est arrete ou en cours de redemarrage.

**Solution** :
```bash
docker compose ps gateway
docker compose logs gateway | tail -20
docker compose restart gateway
```

### Comment reinitialiser un mot de passe utilisateur gateway ?

```bash
# Se connecter a la base
docker exec -it gateway-db psql -U gateway -d gateway

# Voir les utilisateurs
SELECT username, roles FROM users;

# Le plus simple : supprimer et recreer via l'API /register
```

### Les donnees sont perdues apres un redemarrage

Certaines donnees sont stockees uniquement en memoire :
- Conversations IA
- Certains workflows en cours
- Jobs du scheduler

Les donnees persistees en PostgreSQL (operations, audit, regles, utilisateurs) survivent au redemarrage.

### Comment voir la documentation API interactive ?

Acceder a http://localhost:8000/docs (Swagger UI) ou http://localhost:8000/redoc (ReDoc).

---

## 17. Conventions du code

### Backend (Python)

- **Framework** : FastAPI avec typage Pydantic
- **Style** : PEP 8
- **Logging** : `structlog` (JSON structure) - pas de `print()`
- **Async** : Toutes les fonctions API sont `async def`
- **Authentification** : `Depends(get_current_user)` sur chaque endpoint protege
- **Erreurs** : `HTTPException` avec codes HTTP standards
- **Config** : Variables d'environnement via `pydantic-settings`

```python
# Exemple d'endpoint typique
@router.get("/{item_id}")
async def get_item(
    item_id: str,
    current_user: dict = Depends(get_current_user),
    session=Depends(get_session)
):
    """Docstring claire en francais."""
    try:
        result = await service.get(item_id)
        if not result:
            raise HTTPException(status_code=404, detail="Non trouve")
        return result
    except Exception as e:
        logger.error("Action failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
```

### Frontend (TypeScript/React)

- **Framework** : React 18 avec hooks
- **Typage** : TypeScript strict
- **Styles** : Tailwind CSS (classes utilitaires)
- **Etat** : React Query pour les donnees serveur, Zustand pour l'auth
- **Composants** : Functional components avec hooks
- **API** : Toutes les fonctions dans `lib/api.ts`
- **i18n** : Utiliser `useTranslation()` pour les textes affichables

```tsx
// Exemple de composant typique
export default function MaPage() {
  const { t } = useTranslation()
  const { data, isLoading } = useQuery({
    queryKey: ['items'],
    queryFn: getItems
  })

  if (isLoading) return <div>Chargement...</div>

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold">{t('my_page.title')}</h1>
      {/* contenu */}
    </div>
  )
}
```

### Nommage

| Element | Convention | Exemple |
|---|---|---|
| Fichiers Python | snake_case | `provision_service.py` |
| Fichiers TypeScript | PascalCase (pages/composants) | `MidpointUsers.tsx` |
| Variables Python | snake_case | `user_name` |
| Variables TypeScript | camelCase | `userName` |
| Composants React | PascalCase | `LiveComparison` |
| Endpoints API | kebab-case | `/api/v1/live/sync-user` |
| Tables SQL | snake_case | `audit_events` |

---

> **Ce guide a ete genere le 19/02/2026.** Pour toute question, consultez la documentation Swagger (http://localhost:8000/docs) ou le code source commente.
