# Fiche descriptive du dépôt GitHub — IAM Gateway

> **Document** : Fiche de description du dépôt GitHub (livrable de documentation projet)
> **Projet** : *Projet 3 — Passerelle de provisionnement IAM intelligente* (SAE S5/S6, BUT Informatique — UPEC, laboratoire LISSI)
> **Dépôt** : <https://github.com/Nostradam4ik/IAM-Gateway>
> **Co-auteur** (métadonnées, conformément au `README.md`) : `achibani@gmail.com` (Abdelghani Chibani)
> **Date de rédaction** : 21 juin 2026 · **Révision documentée** : commit `50d2bc6` (`main`)
> **Auteur du document** : équipe DevOps du projet

---

## 1. Présentation générale du dépôt

### 1.1 Identification

| Élément | Valeur |
|---|---|
| **URL du dépôt** | <https://github.com/Nostradam4ik/IAM-Gateway> |
| **Nom officiel** | Passerelle de provisionnement IAM intelligente (*« Projet 3 »*) |
| **Nom applicatif** | *Gateway IAM — Passerelle de Provisionnement* (titre FastAPI, `main.py`) |
| **Acronyme usuel** | **IAM Gateway** |
| **Cadre académique** | SAE (Situation d'Apprentissage et d'Évaluation) S5/S6 — BUT Informatique, UPEC / laboratoire LISSI |
| **Licence / visibilité** | Dépôt de projet étudiant (livrables de SAE) |

### 1.2 Contexte académique

Le dépôt regroupe l'ensemble des artefacts produits dans le cadre de la SAE de développement d'une *gateway* de provisionnement multi-cibles, pilotée par des règles dynamiques et assistée par IA. Les supports de soutenance (`presentations/IAM_Gateway_UPEC.pptx`, `PRESENTATION_UPEC_2026.md`) et le rapport final (`docs/rapport-final-realisation.md`, intitulé « Rapport final de réalisation de la SAE S5/S6 ») rattachent le travail à l'UPEC ; les logos institutionnels (`Lissi-cmjn.png`, `cropped-Logo-INFO-FOND-BLANC.jpg`) confirment l'implication du laboratoire LISSI et du département informatique. Conformément au `README.md`, tous les livrables référencent `achibani@gmail.com` comme co-auteur.

### 1.3 Objectif principal

IAM Gateway est une **passerelle intelligente de provisionnement d'identités multi-cibles**. Elle s'interpose entre **MidPoint** (le hub IAM central) et un ensemble de systèmes cibles — annuaire **OpenLDAP**, ERP **Odoo**, application SQL « intranet » (PostgreSQL) et fournisseur d'identité **Keycloak** — afin d'offrir à une organisation un **plan de contrôle unique et piloté par des règles** pour les flux d'arrivée/mobilité/départ (*joiner / mover / leaver*). À une simple façade d'API, la passerelle ajoute un moteur de règles d'attributs (Jinja2 *sandboxé*), des **workflows d'approbation multi-niveaux**, de la **réconciliation**, des **synchronisations planifiées** (Odoo → MidPoint), un **assistant IA** optionnel et une **recherche d'audit sémantique** (vecteurs Qdrant). Elle fonctionne selon deux modes mutuellement exclusifs : le **mode hub** (par défaut, où MidPoint propage vers les cibles via des rôles) et le **mode direct** *legacy* (où la passerelle écrit elle-même chaque cible, avec rollback).

### 1.4 Pile technologique (versions exactes)

| Couche | Technologies (versions des fichiers du dépôt) |
|---|---|
| **Backend** | Python **3.11** · FastAPI **≥ 0.109.0** · Uvicorn[standard] **≥ 0.27.0** · SQLAlchemy **≥ 2.0.0** + SQLModel · **Pydantic v2** (`≥ 2.0.0`) + pydantic-settings |
| **Auth / sécurité** | python-jose[cryptography] (JWT HS256) · bcrypt · httpx |
| **Connecteurs** | ldap3 (LDAP) · asyncpg + psycopg2-binary (SQL) · XML-RPC standard (Odoo) |
| **Moteur de règles** | Jinja2 (environnement *sandboxed*) · PyYAML · jsonschema |
| **Frontend** | React **^18.2.0** · TypeScript **^5.3.3** · Vite **^5.1.0** · TanStack Query **^5.18.0** · Zustand **^4.5.0** · Tailwind **^3.4.1** · Radix UI · Monaco **^0.46.0** · react-i18next (`en`/`fr`/`uk`) |
| **IAM / cibles** | MidPoint **4.4** · Keycloak **23.0** · OpenLDAP **1.5.0** (image osixia) · Odoo **17** |
| **Bases de données** | **PostgreSQL 15** (×5 instances) · **Redis 7** (blacklist JWT + rate-limit) · **Qdrant v1.12.4** (recherche vectorielle d'audit) |
| **Infrastructure** | Docker · Docker Compose (schéma v3.9) · nginx (service du frontend) |
| **Outillage CI / tests** | pytest **≥ 8.0.0** · pytest-asyncio **≥ 0.23.0** · ruff **≥ 0.5.0** · pip-audit **≥ 2.7.0** · GitHub Actions |

> **Remarque de fidélité** : aucune base **MongoDB** n'est présente dans le dépôt — la persistance repose intégralement sur PostgreSQL, Redis et Qdrant. L'assistant IA (OpenAI / DeepSeek) est **optionnel** et désactivé par défaut.

### 1.5 Statistiques du dépôt

Relevées sur la branche `main` à la révision documentée (`50d2bc6`, 21 juin 2026).

| Indicateur | Valeur |
|---|---|
| **Nombre total de commits** (`main`) | **54** |
| **Fichiers suivis par Git** | **255** |
| **Lignes Python** (fichiers `*.py` suivis, total `wc -l`, commentaires inclus) | **27 406** réparties sur **82** fichiers |
| **Fichiers TypeScript/TSX** (frontend) | **25** |
| **Date de création** (premier commit *Initial import*) | **24 novembre 2025** |
| **Dernière mise à jour** (fusion PR #2) | **21 juin 2026** |
| **Contributeurs Git** | Nostradam4ik (33 commits) · Andrii Zhmuryk (21 commits) |
| **Branches** | `main`, `security-hardening`, `iam-connector-improvements` |

### 1.6 Inventaire des services Docker (`docker-compose.yml`)

L'orchestration déclare **14 services** sur un réseau bridge `iam-network`. Les datastores sensibles sont liés à `127.0.0.1` (pas d'exposition publique), et les services lourds portent une limite mémoire.

| Service | Image | Port (hôte) | Rôle |
|---|---|---|---|
| `midpoint` | `evolveum/midpoint:4.4` | `8080` | Hub IAM central (`mem_limit 3g`). |
| `midpoint-postgres` | `postgres:15` | `127.0.0.1:5433` | Dépôt de MidPoint. |
| `gateway` | *build* `./gateway` | `8000` | API FastAPI (`mem_limit 768m`, healthcheck `/health`). |
| `gateway-db` | `postgres:15` | `127.0.0.1:5434` | Store de la gateway (opérations, audit, workflows). |
| `gateway-frontend` | *build* `./gateway/frontend` | `3000` → `:80` | UI React servie par nginx. |
| `redis` | `redis:7-alpine` | `127.0.0.1:6379` | Blacklist JWT + rate-limit. |
| `qdrant` | `qdrant/qdrant:v1.12.4` | `127.0.0.1:6333/6334` | Recherche vectorielle d'audit (`mem_limit 1g`). |
| `openldap` | `osixia/openldap:1.5.0` | `127.0.0.1:10389/10636` | Annuaire cible (`inetOrgPerson`). |
| `phpldapadmin` | `osixia/phpldapadmin:0.9.0` | `8088` → `:80` | UI d'inspection LDAP. |
| `odoo` | `odoo:17` | `8069` | ERP source RH + cible (`mem_limit 1g`). |
| `odoo-db` | `postgres:15` | interne | Store d'Odoo. |
| `intranet-db` | `postgres:15` | `127.0.0.1:55432` | Cible SQL « intranet ». |
| `keycloak` | `quay.io/keycloak/keycloak:23.0` | `8081` → `:8080` | Fournisseur d'identité (`mem_limit 1g`, `start-dev`). |
| `keycloak-db` | `postgres:15` | interne | Store de Keycloak. |

---

## 2. Structure du dépôt

Arborescence des fichiers et dossiers suivis. Le code applicatif (`gateway/`) est détaillé exhaustivement ; les répertoires d'actifs volumineux et homogènes (`infrastructure/midpoint`, `scripts/`, `presentations/`) sont regroupés avec leur **nombre de fichiers** et une description de catégorie, pour rester lisibles.

```
IAM-Gateway/
├── .github/
│   └── workflows/
│       └── ci.yml                      # Pipeline CI/CD GitHub Actions (2 jobs : backend, frontend)
├── .gitignore                          # Exclusions Git (secrets .env, node_modules, build, lockfile…)
├── .gitattributes                      # Normalisation des fins de ligne (LF pour *.sh, text=auto)
├── .env.example                        # Modèle de variables d'environnement (≈ 45 clés, sans secret réel)
├── docker-compose.yml                  # Orchestration des 14 services Docker
├── start.sh                            # Lanceur étagé (DB → IAM → gateway → frontend) avec health checks
├── ARCHITECTURE.md                     # Documentation d'architecture (454 lignes, 10 sections)
├── README.md                           # Présentation du projet et structure du dépôt
├── cropped-Logo-INFO-FOND-BLANC.jpg    # Logo département Informatique (support de soutenance)
├── Lissi-cmjn.png                      # Logo du laboratoire LISSI
│
├── gateway/                            # ── Code source de la passerelle ──
│   ├── Dockerfile                      # Image backend (Python 3.11, non-root)
│   ├── .dockerignore                   # Exclusions du contexte de build backend
│   ├── .env.example                    # Modèle d'environnement local du backend
│   ├── README.md                       # Notice du module gateway
│   ├── requirements.txt                # Dépendances runtime Python
│   ├── requirements-dev.txt            # Dépendances dev/CI (inclut requirements.txt + pytest/ruff/pip-audit)
│   ├── pytest.ini                      # Config pytest (asyncio_mode=auto, testpaths=tests, pythonpath=.)
│   │
│   ├── app/                            # Application FastAPI (architecture en couches)
│   │   ├── __init__.py
│   │   ├── main.py                     # App FastAPI : lifespan, middleware request-id, handlers, montage routeurs
│   │   │
│   │   ├── api/                        # 14 routeurs REST (~120 endpoints), montés sous /api/v1/*
│   │   │   ├── __init__.py
│   │   │   ├── admin.py                # Auth JWT, /token, statut système, audit, arrêt d'urgence
│   │   │   ├── provision.py            # Opérations de provisioning + orchestration MidPoint
│   │   │   ├── midpoint.py             # Gestion directe des objets MidPoint (users/roles/resources/shadows)
│   │   │   ├── rules.py                # CRUD du moteur de règles d'attributs + test/versions
│   │   │   ├── workflow.py             # Workflows d'approbation multi-niveaux (+ approbation par email)
│   │   │   ├── reconcile.py            # Jobs de réconciliation et résolution de divergences
│   │   │   ├── connectors.py           # CRUD des connecteurs dynamiques + sync vers MidPoint
│   │   │   ├── scheduler.py            # Jobs planifiés APScheduler (daily/interval/cron, presets)
│   │   │   ├── users.py                # Administration des utilisateurs de la gateway
│   │   │   ├── permissions.py          # Niveaux de droits (1 à 5)
│   │   │   ├── live_comparison.py      # Vue temps réel inter-systèmes + sync Odoo→MidPoint
│   │   │   ├── ldap_groups.py          # Gestion des groupes et appartenances LDAP
│   │   │   ├── webhooks.py             # Webhooks entrants MidPoint → provisioning Keycloak (HMAC)
│   │   │   └── ai_assistant.py         # Assistant IA optionnel (mapping, diagnostics)
│   │   │
│   │   ├── services/                   # Logique métier (14 services)
│   │   │   ├── __init__.py
│   │   │   ├── midpoint_provision_service.py   # Provisioning en mode hub (MidPoint)
│   │   │   ├── provision_service.py            # Provisioning direct + rollback + continue_after_approval
│   │   │   ├── midpoint_client.py              # Client bas niveau REST MidPoint (/ws/rest)
│   │   │   ├── midpoint_resource_service.py    # Gestion des Resources MidPoint
│   │   │   ├── rule_engine.py                  # Moteur de règles Jinja2 sandboxé (filtres custom)
│   │   │   ├── workflow_service.py             # Approbations multi-niveaux (tokens approve/reject)
│   │   │   ├── reconciliation_service.py       # Détection/résolution des divergences
│   │   │   ├── scheduler_service.py            # APScheduler : sync Odoo→MidPoint, contrats, rôles
│   │   │   ├── audit_service.py                # Journalisation d'audit + indexation Qdrant
│   │   │   ├── connector_management_service.py # CRUD des configs de connecteurs dynamiques
│   │   │   ├── user_service.py                 # Utilisateurs gateway (table gateway_users)
│   │   │   ├── email_service.py                # Emails d'approbation (SMTP ; log en DEV_MODE)
│   │   │   └── ai_agent.py                     # Appels au fournisseur LLM (OpenAI/DeepSeek)
│   │   │
│   │   ├── connectors/                 # Adaptateurs systèmes cibles (interface async uniforme)
│   │   │   ├── __init__.py
│   │   │   ├── base.py                 # BaseConnector (ABC) : contrat CRUD compte
│   │   │   ├── connector_factory.py    # ConnectorFactory, DynamicConnector, _safe_sql_identifier
│   │   │   ├── midpoint_connector.py   # MidPointConnector (REST, TLS vérifié, retry transitoire)
│   │   │   ├── ldap_connector.py       # LDAPConnector (ldap3 ; timeouts + reconnexion bind)
│   │   │   ├── odoo_connector.py       # OdooConnector (XML-RPC ; timeouts bornés + ré-auth)
│   │   │   └── sql_connector.py        # SQLConnector (asyncpg/SQLAlchemy ; identifiants allow-listés)
│   │   │
│   │   ├── core/                       # Transverses
│   │   │   ├── __init__.py
│   │   │   ├── config.py               # pydantic-settings + validation fail-fast des secrets
│   │   │   ├── security.py             # JWT (create/decode), require_role(RBAC), bcrypt async
│   │   │   ├── database.py             # Moteur async + sessions poolées + init_db
│   │   │   ├── memory_store.py         # Cache mémoire singleton au-dessus de PostgreSQL
│   │   │   ├── redis_client.py         # Client Redis (blacklist JWT, rate-limit Lua)
│   │   │   ├── qdrant_store.py         # Client Qdrant (recherche sémantique d'audit)
│   │   │   └── logging.py              # structlog + corrélation request-id
│   │   │
│   │   ├── models/                     # Modèles Pydantic / SQLModel
│   │   │   ├── __init__.py
│   │   │   ├── provision.py            # Opérations, enums, requêtes/réponses
│   │   │   ├── connector.py            # Modèles de connecteurs
│   │   │   ├── rules.py                # Modèles de règles/politiques
│   │   │   ├── workflow.py             # Modèles de workflows
│   │   │   ├── audit.py                # Modèles de logs d'audit
│   │   │   ├── ai.py                   # Modèles de l'assistant IA
│   │   │   └── iam.py                  # Objets MidPoint typés (User/Role/Resource/Assignment/Shadow)
│   │   │
│   │   └── db/
│   │       ├── __init__.py
│   │       └── migrations.py           # Schéma + seed idempotents (SQL brut ; source de vérité)
│   │
│   ├── tests/                          # Suite de tests backend (pytest)
│   │   ├── __init__.py
│   │   ├── conftest.py                 # Fixtures : secrets DEBUG déterministes, bcrypt rapide
│   │   ├── test_security.py            # JWT, hachage de mot de passe, RBAC
│   │   ├── test_config.py              # Validation fail-fast des secrets
│   │   └── test_connectors.py          # Garde anti-injection des identifiants SQL
│   │
│   └── frontend/                       # UI d'administration React (Vite + TypeScript)
│       ├── Dockerfile                  # Build statique servi par nginx
│       ├── .dockerignore
│       ├── nginx.conf                  # Service du SPA + proxy
│       ├── index.html                  # Point d'entrée HTML
│       ├── package.json                # Dépendances et scripts npm (dev/build/lint/test)
│       ├── vite.config.ts              # Config Vite (proxy /api → :8000)
│       ├── tsconfig.json               # Config TypeScript
│       ├── tsconfig.node.json          # Config TS pour l'outillage Node
│       ├── tailwind.config.js          # Config Tailwind CSS
│       ├── postcss.config.js           # Config PostCSS/Autoprefixer
│       └── src/
│           ├── main.tsx                # Bootstrap React
│           ├── App.tsx                 # Routage (public / et /login ; /dashboard/* sous PrivateRoute)
│           ├── index.css               # Styles globaux Tailwind
│           ├── vite-env.d.ts           # Déclarations de types Vite
│           ├── lib/api.ts              # Instance Axios unique (injection JWT, redirection 401)
│           ├── store/auth.ts           # Store Zustand (authentification)
│           ├── components/
│           │   ├── Layout.tsx          # Mise en page (navigation + contenu)
│           │   └── LanguageSelector.tsx# Sélecteur de langue (en/fr/uk)
│           ├── i18n/
│           │   ├── index.ts            # Initialisation i18next
│           │   └── locales/            # Traductions en.json, fr.json, uk.json
│           └── pages/                  # 16 pages : Landing, Login, Dashboard, Operations, Rules,
│                                       #   Workflows, Reconciliation, Connectors, MidpointUsers,
│                                       #   LiveComparison, LDAPGroups, Permissions, Users,
│                                       #   AuditLogs, AIAssistant, Settings
│
├── infrastructure/                     # 55 fichiers : déploiement & config MidPoint
│   ├── README.md                       # Notice d'infrastructure
│   ├── docker/                         # 1 fichier d'aide au déploiement Docker
│   ├── midpoint/                       # 49 fichiers : XML MidPoint (resources, rôles, object templates,
│   │                                   #   scripts Groovy de connecteur Odoo) — importés dans MidPoint
│   └── sql/                            # 4 fichiers : init de la base « intranet » (init-intranet.sql, etc.)
│
├── scripts/                            # 39 fichiers : helpers one-off (bash/python/ps1)
│   ├── init-db.sh                      # Exécute les migrations dans le conteneur gateway
│   ├── import_csv_to_midpoint.sh / import_csv_users*.py   # Imports CSV → MidPoint
│   ├── odoo_to_midpoint_sync.py / midpoint_to_keycloak_sync.py  # Démos de synchronisation
│   ├── setup_midpoint.sh / .ps1, import-midpoint-config.sh     # Bootstrap MidPoint
│   ├── setup_ldap_structure.sh / .ldif                         # Structure LDAP de base
│   ├── start.sh / stop.sh, check_environment.sh                # Cycle de vie de la stack
│   ├── demo/                           # 13 fichiers : scénarios de démonstration
│   └── tests/                          # Smoke test d'intégration MidPoint
│
├── docs/                               # 18 livrables documentaires (rapports, plans, guides)
│   ├── README.md                       # Index des livrables
│   ├── ARCHITECTURE.md ↔ (voir racine) # (l'architecture détaillée est à la racine)
│   ├── GUIDE_DEVELOPPEUR.md            # Guide développeur
│   ├── GUIDE_IMPORT_CSV_MIDPOINT.md    # Guide d'import CSV → MidPoint
│   ├── RAPPORT_MAINTENANCE.md          # Rapport de maintenance
│   ├── rapport-final-realisation.md    # Rapport final de réalisation (SAE S5/S6)
│   ├── 01_planning/                    # Backlog, user stories, plan & recette de sprint
│   ├── 02_recherche/                   # État de l'art, méthodologie, provisioning MidPoint
│   ├── 03_architecture/                # Architecture technique et de données
│   ├── 04_implémentation/              # Rapports CI/CD, implémentation, install MidPoint, Scrum
│   ├── 05_guides/                      # Guide utilisateur
│   └── reports/                        # Présentation HTML, rapport TP1, résumé connecteur CSV (PDF)
│
├── datasets/                           # 3 fichiers : jeux RH fictifs (hr_employees.csv, hr_sample.csv)
├── presentations/                      # 18 fichiers : supports de soutenance/marketing
│                                       #   (PPTX/HTML/MD, posters, captures d'écran, generate_pptx.py)
└── media/                              # 1 fichier : index des captures/schémas (liens)
```

---

## 3. Architecture des branches et workflow Git

### 3.1 Stratégie de branches

Le projet suit un modèle **GitHub Flow** à branches de fonctionnalités courtes, avec `main` comme branche d'intégration stable et des **Pull Requests** obligatoires. Deux chantiers majeurs ont été menés successivement, le second étant **empilé** (*stacked*) sur le premier.

### 3.2 Branche `main`

- **Rôle** : branche d'intégration et de livraison, censée rester déployable.
- **Protection** : toute évolution passe par une Pull Request ; pas de *push* direct (convention de projet).
- **État actuel** : contient les deux chantiers fusionnés. La tête (`50d2bc6`) est le commit de fusion de la PR #2 ; le commit `3b0e492` est celui de la PR #1. L'historique antérieur (commits `9da49d1` et précédents) correspond à la phase initiale du projet (documentation, posters, scripts d'import, soutenance).

### 3.3 Branche `security-hardening` — 13 commits de sécurité (PR #1)

Chantier de durcissement, fusionné dans `main` via la **PR #1** (commit de fusion `3b0e492`). Les 13 commits de sécurité, dans l'ordre chronologique :

| # | Commit | Objet |
|---|---|---|
| 1 | `d68adfb` | **Config durcie** : validation *fail-fast* des secrets faibles, *pooling* de la base, arrêt de la journalisation des secrets. |
| 2 | `8d3ac36` | Correction du **crash des opérations Resource MidPoint** et suppression des identifiants admin en clair dans le code. |
| 3 | `0483e05` | **RBAC** appliqué sur tous les endpoints qui modifient une identité. |
| 4 | `7b834c0` | **Authentification HMAC** des webhooks MidPoint + mot de passe temporaire Keycloak aléatoire. |
| 5 | `2876c1d` | Correction des **injections** dans les connecteurs LDAP et SQL dynamique. |
| 6 | `65b2e6d` | **bcrypt** déporté hors de la boucle d'événements + claims `iss`/`aud` ajoutés aux JWT. |
| 7 | `9296a3b` | Arrêt du **blocage de l'event loop** lors des tests de connecteurs et de l'envoi SMTP. |
| 8 | `6cf898d` | **Références fortes** conservées sur les tâches d'arrière-plan pour ne pas perdre silencieusement les écritures en base. |
| 9 | `e2fb262` | Middleware de **corrélation request-id** + gestion centralisée des erreurs. |
| 10 | `5a46ddf` | **Rate-limiting anti-brute-force** sur l'endpoint de login. |
| 11 | `97d284c` | **Durcissement Docker** du déploiement (healthcheck, non-root, images figées, liaison `127.0.0.1`). |
| 12 | `8f93b6b` | Ajout de la **suite de tests backend** et du pipeline GitHub Actions. |
| 13 | `088de77` | **Login adossé au *user store*** et restriction du *probing* des connecteurs. |

> Un 14ᵉ commit de la branche, `07e4b78` (*ci: disable npm cache…*), corrige le cache npm de la CI ; il a été inclus dans la PR #1 mais ne relève pas du durcissement sécurité proprement dit.

### 3.4 Branche `iam-connector-improvements` — 6 commits (PR #2)

Chantier de fiabilisation des connecteurs, **empilé sur `security-hardening`**, fusionné dans `main` via la **PR #2** (commit de fusion `50d2bc6`). Les 6 commits substantiels, dans l'ordre chronologique :

| # | Commit | Objet |
|---|---|---|
| 1 | `c59d3b0` | **Connecteur MidPoint** : vérification TLS + retransport sur échec transitoire (retry). |
| 2 | `9541997` | **Connecteur LDAP** : timeouts de connexion/réception + reconnexion du bind. |
| 3 | `03a2e8c` | **Connecteur Odoo** : timeouts XML-RPC bornés + ré-authentification sur session expirée. |
| 4 | `7f24e84` | **Modèles d'objets IAM typés** (`app/models/iam.py` : users, roles, resources, assignments, shadows). |
| 5 | `8724ad2` | **Docker** : limites mémoire sur les services lourds + politiques de redémarrage sur les bases. |
| 6 | `9ba5a27` | **Documentation** : `ARCHITECTURE.md` exhaustif (454 lignes, 10 sections). |

> Un 7ᵉ commit, `b3cdb0a` (*ci: disable npm cache…*), réplique le correctif de CI `07e4b78` déjà présent sur `security-hardening` ; appliqué sur cette branche, son contenu était identique (diff vide).

### 3.5 Convention de nommage des commits

Les messages s'inspirent des **Conventional Commits** et de l'impératif présent : certains portent un préfixe `type(scope): description` (ex. `ci: …`, `docs: …`, `docker: …`), la majorité utilise une description impérative concise (« enforce RBAC… », « fix injection… »). Les corps de commit expliquent le *pourquoi* (motivation, contexte) et sont co-signés (`Co-Authored-By`).

### 3.6 Processus de Pull Request

1. **Création de la PR** avec une description détaillée (objectif, liste des changements, vérifications effectuées).
2. **Revue des *checks* CI** : les deux jobs (backend, frontend) doivent passer avant fusion (voir §4).
3. **Stratégie de fusion** : *merge commit* — les deux fusions sont matérialisées par des commits de merge explicites (`3b0e492`, `50d2bc6`), préservant l'historique de chaque branche.
4. **Suppression de la branche après fusion** (convention) ; ici les branches `security-hardening` et `iam-connector-improvements` ont été **conservées sur le *remote*** pour la traçabilité de l'évaluation.

### 3.7 Pull Requests empilées (*stacked PRs*)

La branche `iam-connector-improvements` a été créée **à partir de `security-hardening`**, et non de `main` : la fiabilisation des connecteurs s'appuie directement sur le code de sécurité (échappement des filtres LDAP/SQL, déport des I/O bloquantes) qui venait d'être introduit. Tant que la PR #1 était en revue, la **PR #2 ciblait `security-hardening`** comme base : son *diff* ne montrait alors que le delta « connecteurs » (7 commits) et non l'ensemble des changements de sécurité, ce qui la rendait revuable. Une fois la **PR #1 fusionnée dans `main`**, la **PR #2 a été rebasculée sur `main`** (`gh pr edit 2 --base main`) puis fusionnée — schéma classique de *stacked PRs*.

---

## 4. Pipeline CI/CD GitHub Actions

Le workflow `.github/workflows/ci.yml` (nommé **CI**) s'exécute **à chaque *push* sur toute branche** (`branches: ["**"]`) et **à chaque *pull_request***. Il comporte **deux jobs indépendants**, tous deux sur `ubuntu-latest`.

### 4.1 Job 1 — `Backend (lint, test, audit)`

- **Répertoire de travail** : `gateway`
- **Étapes, dans l'ordre** :
  1. `actions/checkout@v4` — récupération du code.
  2. `actions/setup-python@v5` — **Python 3.11**, avec **cache pip** (`cache: pip`).
  3. **Installation** : `pip install -r requirements-dev.txt` (qui inclut `-r requirements.txt`, donc runtime + dev en une étape).
  4. **Ruff** (`ruff check app`) — *linter* Python, **non-bloquant** (`continue-on-error: true` ; dette de *lint* historique signalée mais non gérée comme barrière).
  5. **pytest** (`pytest -q`) — suite de tests, **BLOQUANT** (seule étape qui fait échouer le job en cas d'erreur).
  6. **pip-audit** (`pip-audit -r requirements.txt`) — scan de CVE des dépendances, **non-bloquant**.
- **Temps d'exécution observé** : ~40 secondes.

### 4.2 Job 2 — `Frontend (lint, build)`

- **Répertoire de travail** : `gateway/frontend`
- **Étapes, dans l'ordre** :
  1. `actions/checkout@v4`.
  2. `actions/setup-node@v4` — **Node.js 20**, **sans cache npm** (aucun `package-lock.json` n'est versionné — il est dans `.gitignore` — et le cache de `setup-node` exige un *lockfile* pour résoudre sa clé).
  3. **Installation** : `npm install` (≈ 388 paquets installés, valeur observée — pas de *lockfile* figé).
  4. **Lint** (`npm run lint`, ESLint `--max-warnings 0`) — **non-bloquant** (`continue-on-error: true`).
  5. **Build** (`npm run build` = `tsc && vite build`) — **BLOQUANT**.
- **Temps d'exécution observé** : ~2 à 3 minutes.
- **Note** : le *build* Vite émet un avertissement de **taille de *chunk* (> 500 kB)** — attendu (éditeur Monaco embarqué), **non-bloquant**.

### 4.3 Politique de fusion

Pour qu'une Pull Request soit fusionnable, **les deux jobs doivent réussir**. Concrètement, la barrière effective repose sur les deux étapes **bloquantes** : `pytest -q` (backend) et `npm run build` (frontend). Les étapes **non-bloquantes** — `ruff`, `pip-audit`, ESLint — sont **informatives** : elles remontent la dette technique et les vulnérabilités sans empêcher la fusion, choix assumé pour livrer malgré la dette *legacy* tout en gardant la visibilité.

---

## 5. Suite de tests automatisés

La suite vit sous `gateway/tests/` et s'exécute avec **pytest** (config `pytest.ini` : `asyncio_mode = auto`, `testpaths = tests`, `pythonpath = .`). Elle couvre le cœur sécurité/config/connecteurs.

### 5.1 `tests/conftest.py` — fixtures partagées

Avant **tout import de module applicatif**, le fichier positionne un environnement de test déterministe via `os.environ.setdefault` :

- `DEBUG=true` — indispensable : en mode `DEBUG`, le validateur de secrets de `app.core.config` **génère** des secrets de remplacement au lieu d'échouer ; sans cela, l'import des modules ferait échouer la validation *fail-fast* dès le chargement.
- `SECRET_KEY` / `JWT_SECRET_KEY` — secrets déterministes (> 32 caractères) pour des tests reproductibles.
- `BCRYPT_ROUNDS=4` — coût bcrypt minimal pour **accélérer le hachage** pendant les tests.

### 5.2 `tests/test_security.py` — auth & sécurité (6 fonctions)

| Fonction | Ce qu'elle vérifie |
|---|---|
| `test_password_hash_and_verify` | Le hachage bcrypt diffère du clair ; `verify_password` renvoie `True` pour le bon mot de passe, `False` sinon. |
| `test_async_password_helpers` | Round-trip des helpers **asynchrones** `get_password_hash_async` / `verify_password_async`. |
| `test_jwt_roundtrip_includes_iss_aud_jti` | `create_access_token` puis `decode_token` : présence et valeurs de `sub`, `roles`, `iss`, `aud`, et présence d'un `jti`. |
| `test_jwt_forged_with_wrong_key_is_rejected` | Un JWT signé avec une **mauvaise clé** déclenche une `HTTPException` au décodage. |
| `test_jwt_wrong_audience_is_rejected` | Un JWT avec une **audience** étrangère (`some-other-service`) est rejeté (`HTTPException`). |
| `test_require_role_allows_matching_and_denies_others` | `require_role(["admin","iam_engineer"])` **autorise** un `iam_engineer` et **refuse** un `viewer` (`HTTPException`). |

### 5.3 `tests/test_config.py` — validation *fail-fast* des secrets (5 fonctions)

| Fonction | Ce qu'elle valide |
|---|---|
| `test_production_rejects_missing_secret` | En `DEBUG=False`, des secrets **vides** → `RuntimeError` (refus de démarrage). |
| `test_production_rejects_known_placeholder` | Un secret JWT **placeholder** connu (`jwt-secret-change-in-production`) → `RuntimeError`. |
| `test_production_rejects_short_secret` | Un secret JWT **trop court** (< 32 caractères) → `RuntimeError`. |
| `test_production_accepts_strong_secrets` | Des secrets **forts** (48 caractères) sont acceptés. |
| `test_debug_autogenerates_when_unset` | En `DEBUG=True` avec secrets vides, des secrets ≥ 32 caractères sont **auto-générés**. |

### 5.4 `tests/test_connectors.py` — garde anti-injection SQL (2 fonctions paramétrées)

| Fonction | Ce qu'elle vérifie |
|---|---|
| `test_safe_sql_identifier_accepts_valid` | `_safe_sql_identifier` **accepte** les identifiants valides (`username`, `email`, `first_name`, `_x`, `col1`) et les renvoie tels quels. |
| `test_safe_sql_identifier_rejects_injection` | Il **rejette** (`ValueError`) les tentatives d'injection (`"… DROP TABLE users;--"`, `1col`, `a b`, chaîne vide, `col;`). |

> Au total : **13 fonctions de test**, dont 2 paramétrées dans `test_connectors.py` qui s'étendent à 10 cas exécutés (5 valides + 5 rejets). La validation de l'*allowlist* d'identifiants SQL est donc bien dans `test_connectors.py` (et non dans `test_config.py`).

### 5.5 Commandes d'exécution

```bash
cd gateway
pip install -r requirements-dev.txt
pytest tests/ -v                  # suite complète, mode verbeux
pytest tests/ -v --tb=short       # avec traceback court
pytest tests/test_security.py -v  # un seul fichier
```

En CI, l'invocation est `pytest -q` depuis `gateway/` (mode silencieux).

---

## 6. Gestion de la sécurité du dépôt

### 6.1 Ce qui n'est JAMAIS versionné (`.gitignore`)

| Catégorie | Motifs | Raison |
|---|---|---|
| **Secrets d'environnement** | `.env` | Ne jamais committer de secret réel (clés JWT, mots de passe DB). |
| **Dépendances Node** | `node_modules/` | Volumineux, régénérable par `npm install`. |
| **Lockfile npm** | `package-lock.json` | **Non versionné** — d'où la désactivation du cache npm en CI (le cache exige un *lockfile*). |
| **Artefacts Python** | `__pycache__/`, `*.py[cod]`, `*.so`, `.Python`, `*.egg-info/` | Fichiers compilés/temporaires. |
| **Builds** | `dist/`, `build/` | Sorties de compilation (frontend incluse). |
| **Environnements virtuels** | `venv/`, `env/`, `ENV/` | Spécifiques à la machine. |
| **IDE** | `.vscode/`, `.idea/`, `*.swp`, `*.swo` | Préférences locales. |
| **Bases & dumps** | `*.db`, `*.sqlite3`, `postgres_data.tgz`, `midpoint_home.tgz` | Données locales/volumineuses. |
| **Archives** | `*.tgz`, `*.tar.gz`, `*.zip` | Binaires lourds. |
| **Documents perso. & runtime MidPoint** | `*.pdf`, `midpoint-resources/var/`, `infrastructure/midpoint/var/` | Données générées/personnelles. |

### 6.2 Variables d'environnement (`.env.example`)

Modèle fourni sans aucune valeur sensible. « Requis en prod » signifie que l'application **refuse de démarrer** sans la variable lorsque `DEBUG=false`.

| Variable | Description | Requis en prod | Valeur exemple |
|---|---|---|---|
| `DEBUG` | Mode debug (echo SQL, fixture utilisateur, auto-génération de secrets). | Non | `false` |
| `DEV_MODE` | Journalise les emails d'approbation au lieu de les envoyer. | Non | `false` |
| `SECRET_KEY` | Secret applicatif. | **Oui** | *(généré, 48 car.)* |
| `JWT_SECRET_KEY` | Clé de signature JWT (≥ 32 caractères). | **Oui** | *(généré, 48 car.)* |
| `JWT_ALGORITHM` | Algorithme JWT. | Non | `HS256` |
| `JWT_EXPIRE_MINUTES` | Durée de vie du token d'accès. | Non | `60` |
| `JWT_ISSUER` | Claim `iss`. | Non | `iam-gateway` |
| `JWT_AUDIENCE` | Claim `aud`. | Non | `iam-gateway` |
| `BCRYPT_ROUNDS` | Coût bcrypt. | Non | `12` |
| `MIDPOINT_WEBHOOK_SECRET` | Secret HMAC-SHA256 des webhooks MidPoint entrants. | Oui* | *(secret partagé)* |
| `MIDPOINT_URL` | URL REST de MidPoint. | Non | `http://midpoint-core:8080/midpoint` |
| `MIDPOINT_USER` | Compte admin MidPoint. | Non | `administrator` |
| `MIDPOINT_PASSWORD` | Mot de passe admin MidPoint. | Non | *(secret)* |
| `MIDPOINT_ENABLED` | Mode hub (`true`) vs mode direct (`false`). | Non | `true` |
| `MIDPOINT_VERIFY_SSL` | Vérification TLS des appels MidPoint. | Non | `true` |
| `DATABASE_URL` | DSN PostgreSQL (asyncpg) de la gateway. | Non | `postgresql+asyncpg://gateway:gateway@gateway-db:5432/gateway` |
| `REDIS_URL` | DSN Redis. | Non | `redis://redis:6379/0` |
| `QDRANT_HOST` / `QDRANT_PORT` | Localisation de Qdrant. | Non | `qdrant` / `6333` |
| `LDAP_HOST` / `LDAP_PORT` | Serveur LDAP. | Non | `openldap` / `389` |
| `LDAP_BIND_DN` | Identité de bind LDAP. | Non | `cn=admin,dc=example,dc=com` |
| `LDAP_BIND_PASSWORD` | Mot de passe de bind LDAP. | Non | *(secret)* |
| `LDAP_BASE_DN` | Contexte de base LDAP. | Non | `dc=example,dc=com` |
| `ODOO_URL` / `ODOO_DB` | Connexion XML-RPC Odoo. | Non | `http://odoo:8069` / `odoo` |
| `ODOO_USER` / `ODOO_PASSWORD` | Identifiants Odoo. | Non | `admin` / *(secret)* |
| `INTRANET_DB_URL` | DSN de la cible SQL « intranet ». | Non | `postgresql://intranet:intranet@intranet-db:5432/intranet` |
| `KEYCLOAK_URL` / `KEYCLOAK_REALM` | Base + realm Keycloak. | Non | `http://keycloak:8080` / `gateway` |
| `KEYCLOAK_CLIENT_ID` / `KEYCLOAK_CLIENT_SECRET` | Client OIDC Keycloak. | Non | `gateway-client` / *(secret)* |
| `KEYCLOAK_ADMIN_USER` / `KEYCLOAK_ADMIN_PASSWORD` | Admin Keycloak (provisioning webhook). | Non | `admin` / *(secret)* |
| `POSTGRES_GATEWAY_PASSWORD` … `POSTGRES_KEYCLOAK_PASSWORD` | Mots de passe des 5 bases (compose). | Non | *(secret)* |
| `MIDPOINT_KEYSTORE_PASSWORD` | Mot de passe du keystore MidPoint. | Non | *(secret)* |
| `OPENAI_API_KEY` / `OPENAI_MODEL` | Fournisseur IA optionnel. | Non | *(vide)* / `gpt-4-turbo-preview` |
| `DEEPSEEK_API_KEY` | Fournisseur IA alternatif optionnel. | Non | *(vide)* |
| `SMTP_HOST` / `SMTP_PORT` | Serveur d'envoi d'emails. | Non | `smtp.gmail.com` / `587` |
| `SMTP_USER` / `SMTP_PASSWORD` | Identifiants SMTP. | Non | *(secret)* |
| `FROM_EMAIL` | Expéditeur des emails. | Non | `noreply@iam-gateway.local` |
| `BASE_URL` | URL publique pour les liens d'email. | Non | `http://localhost:8000` |
| `CORS_ORIGINS` | Origines navigateur autorisées (JSON). | Non | `["http://localhost:3000"]` |

> \* `MIDPOINT_WEBHOOK_SECRET` : le webhook **échoue *closed*** sans secret en production ; en `DEBUG`, la vérification de signature est contournée.

### 6.3 Protection de la branche `main`

- **Fusion uniquement par Pull Request** (pas de *push* direct).
- **La CI doit passer** : `pytest` (backend) **et** *build* frontend (`tsc && vite build`).
- Historique préservé par *merge commits* explicites et messages co-signés.

### 6.4 Hygiène de l'historique et `.gitattributes`

Aucun secret réel n'est introduit dans l'historique : `.env` est exclu (§6.1) et `.env.example` ne contient que des emplacements vides. Le fichier `.gitattributes` assure la **normalisation des fins de ligne** — `*.sh text eol=lf` (les scripts shell restent en **LF** pour s'exécuter sous bash/WSL2 même édités sous Windows) et `* text=auto` (normalisation automatique des fichiers texte) — garantissant un historique stable et multiplateforme.

---

## 7. Guide de contribution

1. **Forker ou cloner** le dépôt : `git clone https://github.com/Nostradam4ik/IAM-Gateway.git`.
2. **Créer une branche** de fonctionnalité : `git checkout -b feature/nom-feature` (partir de `main`, ou d'une branche existante pour une PR empilée).
3. **Développer en local** avec la stack minimale :
   ```bash
   cp .env.example .env   # puis définir SECRET_KEY et JWT_SECRET_KEY forts
   docker compose up gateway gateway-db redis
   ```
4. **Lancer les tests** : `cd gateway && pip install -r requirements-dev.txt && pytest tests/ -v`.
5. **Committer** avec la convention `type(scope): description` (impératif présent), corps expliquant le *pourquoi*.
6. **Pousser** la branche et **ouvrir une Pull Request** vers `main` (description détaillée).
7. **Attendre la réussite des 2 jobs CI** (backend + frontend).
8. **Fusionner après revue** (*merge commit*), puis supprimer la branche de fonctionnalité.

---

*Document généré dans le cadre du Projet 3 — IAM Gateway (SAE S5/S6, UPEC). Co-auteur référencé : `achibani@gmail.com`. Toutes les affirmations techniques sont fondées sur les fichiers du dépôt à la révision `50d2bc6`.*
