# Fiche d'architecture — IAM Gateway

> **Document** : Description d'architecture technique (livrable solutions architecture)
> **Projet** : *Projet 3 — Passerelle de provisionnement IAM intelligente* (SAE S5/S6, BUT Informatique — UPEC, laboratoire LISSI)
> **Dépôt** : <https://github.com/Nostradam4ik/IAM-Gateway>
> **Co-auteur** (métadonnées, conformément au `README.md`) : `achibani@gmail.com` (Abdelghani Chibani)
> **Sources** : `ARCHITECTURE.md`, `docker-compose.yml`, et le code de `gateway/app/` (révision `50d2bc6`)

---

## 1. Introduction et contexte

### 1.1 Problématique métier : la gestion des identités numériques

**Qu'est-ce que l'IAM ?** L'*Identity and Access Management* (gestion des identités et des accès) désigne l'ensemble des processus et outils permettant de créer, modifier, désactiver et auditer les **comptes** et les **droits** des utilisateurs sur les systèmes d'information d'une organisation. Une identité (un employé, un prestataire) se matérialise par des comptes dans de multiples systèmes hétérogènes : annuaire (LDAP/Active Directory), ERP, applications métier, fournisseur d'authentification (SSO), etc.

**Pourquoi est-ce critique en entreprise ?**
- **Sécurité** : un compte « orphelin » (resté actif après un départ) ou sur-privilégié est un vecteur d'attaque majeur (élévation de privilèges, mouvement latéral). Le principe du moindre privilège impose un cycle de vie maîtrisé.
- **Conformité (RGPD, ISO 27001)** : le RGPD exige de limiter l'accès aux données personnelles aux seules personnes habilitées et de pouvoir **prouver** qui a eu accès à quoi. Cela suppose une révocation rapide et une **piste d'audit** complète et immuable.
- **Auditabilité** : chaque opération de provisionnement (création, modification, suppression, attribution de rôle) doit être tracée, horodatée et rattachée à son auteur et à son motif (demande, approbation).

**Le problème du « joiner / mover / leaver » (JML).** Le cycle de vie d'une identité comporte trois moments clés :
- **Joiner** (arrivée) : créer les comptes et octroyer les droits adaptés au poste, dès le premier jour.
- **Mover** (mobilité) : ajuster les droits lors d'un changement de poste/service — en retirant les anciens, souvent négligé.
- **Leaver** (départ) : désactiver **immédiatement et partout** les accès à l'expiration du contrat.

**Limites des approches manuelles.** Provisionner « à la main », système par système, est : *lent* (délais d'activation), *source d'erreurs* (oublis de révocation, incohérences entre systèmes), *non traçable* (pas de journal centralisé) et *non scalable* (chaque nouveau système cible multiplie la charge). Le risque résiduel — comptes orphelins, droits dormants — croît mécaniquement avec le nombre de cibles.

*Exemple concret.* Pour un départ (*leaver*), une révocation manuelle suppose de retrouver et désactiver le compte dans **chaque** système (annuaire, ERP, SSO, applications) ; un seul oubli laisse un accès exploitable après le départ. IAM Gateway ramène ce geste à une **opération unique** propagée par le hub, et l'**automatise** via le contrôle d'expiration des contrats Odoo (job planifié).

### 1.2 Objectif de la plateforme IAM Gateway

IAM Gateway répond à cette problématique par un **plan de contrôle unique** au-dessus d'un hub IAM (MidPoint) et de ses systèmes cibles :
- **Plan de contrôle unifié** : une seule API et une seule UI pour piloter le provisionnement vers tous les systèmes cibles (LDAP, Odoo, SQL « intranet », Keycloak), au lieu d'opérer chaque système séparément.
- **Automatisation des flux JML** : synchronisation planifiée Odoo (source RH) → MidPoint, attribution automatique de rôles par département, et désactivation pilotée par l'expiration des contrats.
- **Interface *no-code*** pour les équipes non techniques : un moteur de règles d'attributs (Jinja2 *sandboxé*) éditable depuis l'UI (éditeur Monaco), et des workflows d'approbation multi-niveaux configurables.
- **Traçabilité et audit complets** : chaque opération est journalisée, persistée et indexée pour une **recherche sémantique** (Qdrant).

### 1.3 Périmètre du projet

**Couvert par le projet :**
- Provisionnement multi-cibles via MidPoint (mode hub, par défaut) **ou** en direct (mode *legacy* avec rollback).
- Cibles : OpenLDAP, Odoo ERP, base SQL « intranet », Keycloak (via webhook).
- Moteur de règles, workflows d'approbation multi-niveaux, réconciliation, synchronisations planifiées, assistant IA optionnel, audit sémantique.
- Sécurité applicative : authentification JWT, RBAC, durcissement (cf. §6), CI automatisée.

**Hors-périmètre (assumé) :**
- Connecteurs GLPI et Firebase : volontairement non implémentés en statique (`NotImplementedError`) — ajoutables à chaud comme connecteurs dynamiques.
- Terminaison TLS / reverse-proxy de production, gestionnaire de secrets externe, immuabilité de la piste d'audit, sauvegarde/restauration des bases — identifiés comme travaux restants.
- Aucune base **MongoDB** : la persistance repose exclusivement sur PostgreSQL, Redis et Qdrant (voir §3.12).

---

## 2. Vue d'ensemble de l'architecture

### 2.1 Diagramme d'architecture complet

Tous les conteneurs partagent un unique réseau Docker **bridge `iam-network`**. Sur l'hôte, les **datastores** sont publiés sur `127.0.0.1` uniquement (non exposés publiquement) ; seuls les ports applicatifs sont ouverts plus largement.

```
                          UTILISATEURS EXTERNES
        ┌──────────────┐      ┌──────────────┐      ┌────────────────────────┐
        │  Navigateur  │      │  Client API  │      │  MidPoint (rappel       │
        │  (opérateur) │      │  (scripts)   │      │  webhook sortant)       │
        └──────┬───────┘      └──────┬───────┘      └───────────┬────────────┘
               │ HTTP/JSON           │ REST + JWT               │ POST /webhooks
               │ :3000               │ :8000 (Bearer)           │ HMAC-SHA256
═══════════════╪═════════════════════╪══════════════════════════╪═══════════════════════
 DOCKER HOST   │   réseau bridge « iam-network »                 │
               ▼                     ▼                          ▼
        ┌───────────────┐    ┌───────────────────────────────────────────────┐
        │ gateway-      │    │           FastAPI Gateway  (:8000)             │
        │ frontend      │───▶│   api/ (149 endpoints) → services/ →           │
        │ (nginx :80    │    │   connectors/ → systèmes externes              │
        │  → hôte :3000)│    │   JWT • RBAC • règles • workflows • scheduler  │
        └───────────────┘    └──┬─────────┬─────────┬──────────┬──────────────┘
                                │ asyncpg │ RESP    │ HTTP     │ REST/Basic + retry(2)
                                │ :5432   │ :6379   │ :6333    │ :8080  timeout 60 s
                                ▼         ▼         ▼          ▼
                         ┌──────────┐┌─────────┐┌─────────┐┌──────────────────────────┐
                         │gateway-db││ redis 7 ││ qdrant  ││   MidPoint 4.4  (:8080)   │
                         │ PG 15    ││ :6379   ││ v1.12.4 ││   HUB IAM central         │
                         │ hôte:5434││ hôte    ││ :6333/4 ││   /ws/rest/* (Basic Auth) │
                         │ (cache + ││ 6379    ││ audit   ││   repo: midpoint-postgres │
                         │  audit)  ││ JWT-bl. ││ vecteur ││   (PG 15, hôte:5433)      │
                         └──────────┘└─────────┘└─────────┘└───┬─────────┬─────────┬───┘
                          127.0.0.1   127.0.0.1  127.0.0.1     │ LDAP    │ XML-RPC │ SQL
                                                               │ :389    │ :8069   │ :5432
                                       (MidPoint propage via   ▼         ▼         ▼
                                        ses propres connecteurs)
                                              ┌──────────┐┌──────────┐┌──────────────┐
                                              │ OpenLDAP ││ Odoo 17  ││ intranet-db  │
                                              │ :389     ││ :8069    ││ PG 15        │
                                              │ :636 SSL ││ XML-RPC  ││ hôte:55432   │
                                              │ hôte     ││ res.users││ (cible SQL)  │
                                              │ 10389/   ││ hr.*     │└──────────────┘
                                              │ 10636    │└──────────┘
                                              └────┬─────┘
                                                   │ phpLDAPadmin (:80 → hôte :8088)
                                                   ▼
  ┌──────────────────────────────────────────────────────────────────────────────────┐
  │  PROVISIONING SECONDAIRE (SSO)                                                      │
  │  MidPoint ──(notif. user-change, HMAC-SHA256)──▶ Gateway /api/v1/webhooks/...       │
  │           ──▶ KeycloakProvisioner (httpx, REST admin API, token admin-cli, 10 s)    │
  │           ──▶ Keycloak 23.0 (:8080 → hôte :8081)  ◀── keycloak-db (PG 15, interne)  │
  └──────────────────────────────────────────────────────────────────────────────────┘

  Légende protocoles : RESP = protocole Redis · asyncpg = PostgreSQL async · REST = HTTP/JSON
  · LDAP = ldap3 (389 clair / 636 TLS) · XML-RPC = Odoo (sur HTTP :8069) · HMAC = signature webhook
```

**Lecture du diagramme.** Une requête d'opérateur entre par le frontend (`:3000`) ou directement sur l'API (`:8000`) avec un JWT. La gateway l'authentifie, applique le RBAC, puis — en mode hub — appelle **MidPoint** (`:8080`, Basic Auth, *retry* ×2) qui propage vers LDAP/Odoo/SQL via ses propres connecteurs. En retour, MidPoint notifie la gateway (webhook signé HMAC) pour répliquer le changement vers **Keycloak**. Les trois datastores de la gateway (PostgreSQL `gateway-db`, Redis, Qdrant) restent confinés à l'hôte (`127.0.0.1`).

### 2.2 Couches architecturales

L'ensemble se structure en **4 couches**, le flux des requêtes allant du haut vers le bas :

1. **Couche présentation** — le *frontend* React (Vite + TypeScript), servi en statique par **nginx** (`:3000 → :80`). SPA d'administration : formulaires de provisionnement, éditeur de règles (Monaco), workflows, réconciliation, connecteurs, audit. Tout passe par une instance Axios unique qui injecte le JWT et redirige sur `/login` en cas de 401.
2. **Couche API** — la **gateway FastAPI** (`:8000`). Couche *mince* : elle parse/valide (Pydantic v2), applique l'authentification (JWT) et l'autorisation (RBAC via `require_role`), puis délègue aux services. Expose 149 endpoints sous `/api/v1/*`, plus `/health` et Swagger `/docs`.
3. **Couche intégration** — les **connecteurs** (`MidPointConnector`, `LDAPConnector`, `OdooConnector`, `SQLConnector`, et `KeycloakProvisioner`) derrière l'interface uniforme `BaseConnector`. En **mode hub**, seul MidPoint est piloté directement ; il propage ensuite vers ses *Resources* (LDAP/Odoo/SQL). Keycloak est provisionné via le webhook.
4. **Couche données** — **PostgreSQL** (5 instances), **Redis** (blacklist JWT + rate-limit), **Qdrant** (recherche sémantique d'audit). La gateway lit principalement depuis un cache mémoire (`MemoryStore`) alimenté par PostgreSQL.

**Communication entre couches.** Le flux est strictement descendant : la présentation n'appelle jamais directement un système cible, et les connecteurs ne sont jamais invoqués depuis un routeur sans passer par un service. Cette séparation rend les couches substituables (p. ex. ajouter une cible = ajouter un connecteur sans toucher à l'API) et concentre l'authentification/autorisation dans la couche API.

### 2.3 Le choix structurant : mode hub vs mode direct

`settings.MIDPOINT_ENABLED` (par défaut `True`) commute entre deux chemins de provisionnement radicalement différents — c'est la décision d'architecture centrale du projet :

- **Mode hub (défaut)** — `MidPointProvisionService` : la gateway ne parle qu'à **MidPoint**, qui détient les identités et propage vers les systèmes cibles via ses **rôles** (cible → nom de rôle : `LDAP → "ldap-user"`, `ODOO → "odoo-user"`, `SQL → "intranet-user"`). Les *shadows* et la réconciliation relèvent de MidPoint.
- **Mode direct *legacy*** — `ProvisionService` : la gateway écrit **elle-même** chaque connecteur cible via `ConnectorFactory`, en suivant chaque opération avec des **actions de rollback** (`RollbackAction`) pour annuler un succès partiel, et en maintenant son propre cache d'état des comptes.

`continue_after_approval` (dans `provision_service.py`) combine les deux : il tente d'abord MidPoint, puis retombe sur des écritures directes. Ce double mode permet de démontrer l'orchestration par un hub IGA mature **et** de conserver un chemin autonome si MidPoint est indisponible.

---

## 3. Description détaillée des composants

Caractéristiques relevées dans `docker-compose.yml` (versions, ports, `mem_limit`, healthcheck, `restart`, volumes) et dans le `Dockerfile` de la gateway.

**Vue d'ensemble des 14 services** (synthèse ; détail par composant ci-dessous) :

| Service | Image | Port hôte | mem_limit | Healthcheck | Restart |
|---|---|---|---|---|---|
| `gateway` | build (`python:3.11-slim`) | 8000 | 768m | `/health` | unless-stopped |
| `gateway-frontend` | build (nginx) | 3000→80 | — | — | unless-stopped |
| `midpoint` | `evolveum/midpoint:4.4` | 8080 | 3g | — | unless-stopped |
| `keycloak` | `quay.io/keycloak/keycloak:23.0` | 8081→8080 | 1g | — | unless-stopped |
| `openldap` | `osixia/openldap:1.5.0` | 10389/10636 | — | — | unless-stopped |
| `phpldapadmin` | `osixia/phpldapadmin:0.9.0` | 8088→80 | — | — | unless-stopped |
| `odoo` | `odoo:17` | 8069 | 1g | — | unless-stopped |
| `gateway-db` | `postgres:15` | 5434 (127.0.0.1) | — | `pg_isready` | unless-stopped |
| `midpoint-postgres` | `postgres:15` | 5433 (127.0.0.1) | — | `pg_isready` | unless-stopped |
| `intranet-db` | `postgres:15` | 55432 (127.0.0.1) | — | `pg_isready` | unless-stopped |
| `odoo-db` | `postgres:15` | interne | — | `pg_isready` | unless-stopped |
| `keycloak-db` | `postgres:15` | interne | — | `pg_isready` | unless-stopped |
| `redis` | `redis:7-alpine` | 6379 (127.0.0.1) | — | `redis-cli ping` | unless-stopped |
| `qdrant` | `qdrant/qdrant:v1.12.4` | 6333/6334 (127.0.0.1) | 1g | — | unless-stopped |

### 3.1 FastAPI Gateway (le cœur)
- **Rôle** : plan de contrôle. Authentification/RBAC, moteur de règles, workflows, scheduler, et tous les connecteurs.
- **Version / image** : construite localement (`build: ./gateway`, base `python:3.11-slim`), exécutée en **utilisateur non-root `appuser` (UID 10001)**.
- **Port** : `8000` (exposé à tous : navigateur, clients API, rappels webhook).
- **Ressources** : `mem_limit: 768m`.
- **Healthcheck** : **oui** — `GET http://localhost:8000/health` (intervalle 15 s, timeout 5 s, 5 essais, *start period* 40 s).
- **Restart policy** : `unless-stopped`.
- **Volumes** : `./gateway/app:/app/app` (code en *bind mount*) et `gateway_logs:/app/logs` (journaux). `depends_on` : `gateway-db` (healthy), `redis` (healthy), `qdrant` (started).
- **Entrée** : `uvicorn app.main:app --host 0.0.0.0 --port 8000` (Dockerfile) ; le *bind mount* du code permet le rechargement en développement.

### 3.2 React Frontend
- **Rôle** : UI d'administration (SPA), proxy `/api → :8000`.
- **Version / image** : construite localement (`build: ./gateway/frontend`), servie par **nginx**.
- **Port** : `3000 → :80`.
- **Ressources** : aucune `mem_limit` déclarée.
- **Healthcheck** : non.
- **Restart policy** : `unless-stopped`. `depends_on` : `gateway` (healthy).
- **Données persistées** : aucune (contenu statique reconstruit à l'image).

### 3.3 MidPoint IAM Server
- **Rôle** : **hub IAM central** — dépôt d'identités, propagation vers les *Resources* (LDAP/Odoo/SQL), réconciliation. Piloté par la gateway via `/ws/rest/*` en **HTTP Basic**.
- **Version / image** : `evolveum/midpoint:4.4`.
- **Port** : `8080` (exposé).
- **Ressources** : `mem_limit: 3g` (`MP_MEM_MAX=2048m`, `MP_MEM_INIT=1024m`).
- **Healthcheck** : non défini sur le service MidPoint lui-même (sa base `midpoint-postgres` en possède un).
- **Restart policy** : `unless-stopped`. `depends_on` : `midpoint-postgres` (healthy).
- **Données persistées** : `midpoint_home:/opt/midpoint/var` (keystore, configuration).

### 3.4 Keycloak (SSO / OIDC)
- **Rôle** : fournisseur d'identité OIDC pour le SSO. **Provisionné depuis MidPoint** via le webhook de la gateway (`KeycloakProvisioner`).
- **Version / image** : `quay.io/keycloak/keycloak:23.0`, lancé en `start-dev`.
- **Port** : `8081 → :8080`.
- **Ressources** : `mem_limit: 1g`.
- **Healthcheck** : non (sa base `keycloak-db` en possède un).
- **Restart policy** : `unless-stopped`. `depends_on` : `keycloak-db` (healthy).
- **Données persistées** : aucune en propre — état stocké dans `keycloak-db`.

### 3.5 OpenLDAP + phpLDAPadmin
- **Rôle** : annuaire d'entrées `inetOrgPerson` et groupes sous `dc=example,dc=com` — **système cible** de provisionnement. phpLDAPadmin est l'UI d'inspection.
- **Version / image** : `osixia/openldap:1.5.0` ; `osixia/phpldapadmin:0.9.0`.
- **Ports** : OpenLDAP `127.0.0.1:10389→389` (clair) et `127.0.0.1:10636→636` (LDAPS) ; phpLDAPadmin `8088→80`.
- **Ressources** : aucune `mem_limit`.
- **Healthcheck** : non. **Restart policy** : `unless-stopped`. phpLDAPadmin `depends_on: openldap`.
- **Données persistées** : `openldap_data:/var/lib/ldap`, `openldap_config:/etc/ldap/slapd.d`.

### 3.6 Odoo ERP
- **Rôle** : **source RH** (employés, départements, contrats) **et système cible**. Piloté en XML-RPC.
- **Version / image** : `odoo:17`.
- **Port** : `8069` (exposé).
- **Ressources** : `mem_limit: 1g`.
- **Healthcheck** : non (sa base `odoo-db` en possède un). **Restart policy** : `unless-stopped`. `depends_on` : `odoo-db` (healthy).
- **Données persistées** : `odoo_data:/var/lib/odoo`, `odoo_addons:/mnt/extra-addons`.

### 3.7 PostgreSQL `gateway-db`
- **Rôle** : store durable de la gateway — opérations, logs d'audit, jobs de réconciliation, workflows, configs de connecteurs, utilisateurs (`gateway_users`).
- **Version / image** : `postgres:15`.
- **Port** : `127.0.0.1:5434→5432` (lié à l'hôte local uniquement).
- **Ressources** : aucune `mem_limit`.
- **Healthcheck** : **oui** — `pg_isready -U gateway` (10 s / 5 s / 5 essais).
- **Restart policy** : `unless-stopped`.
- **Données persistées** : `gateway_db_data:/var/lib/postgresql/data`.

### 3.8 PostgreSQL `midpoint-postgres`
- **Rôle** : dépôt (repository) propre à MidPoint.
- **Version / image** : `postgres:15`.
- **Port** : `127.0.0.1:5433→5432`.
- **Healthcheck** : **oui** — `pg_isready -U midpoint`. **Restart policy** : `unless-stopped`.
- **Données persistées** : `midpoint_postgres_data:/var/lib/postgresql/data`.

### 3.9 PostgreSQL `odoo-db`
- **Rôle** : base de données backing d'Odoo.
- **Version / image** : `postgres:15`.
- **Port** : **interne** (aucune publication sur l'hôte).
- **Healthcheck** : **oui** — `pg_isready -U odoo`. **Restart policy** : `unless-stopped`.
- **Données persistées** : `odoo_db_data:/var/lib/postgresql/data`.

> **Les deux autres instances PostgreSQL** : `intranet-db` (cible SQL « intranet », `127.0.0.1:55432→5432`, volume `intranet_db_data` + script d'init `infrastructure/sql/init-intranet.sql`, healthcheck `pg_isready -U intranet`) et `keycloak-db` (backing de Keycloak, **interne**, volume `keycloak_db_data`, healthcheck `pg_isready -U keycloak`). Soit **5 instances PostgreSQL 15** au total.

### 3.10 Redis
- **Rôle** : **blacklist de révocation JWT** (`blacklist:{jti}`) et **rate-limiting** atomique du login. Sert aussi de cache de sessions et de tokens de workflow.
- **Version / image** : `redis:7-alpine`.
- **Port** : `127.0.0.1:6379→6379`.
- **Ressources** : aucune `mem_limit`.
- **Healthcheck** : **oui** — `redis-cli ping` (10 s / 5 s / 5 essais).
- **Restart policy** : `unless-stopped`.
- **Données persistées** : `redis_data:/data`.

### 3.11 Qdrant (base vectorielle)
- **Rôle** : store de vecteurs — chaque log d'audit y est indexé pour une **recherche sémantique**. Dégrade gracieusement si indisponible.
- **Version / image** : `qdrant/qdrant:v1.12.4`.
- **Ports** : `127.0.0.1:6333` (REST) et `127.0.0.1:6334` (gRPC).
- **Ressources** : `mem_limit: 1g`.
- **Healthcheck** : non. **Restart policy** : `unless-stopped`.
- **Données persistées** : `qdrant_data:/qdrant/storage`.

### 3.12 MongoDB
- **Absent.** Aucun service MongoDB n'est déclaré dans `docker-compose.yml` et aucun pilote Mongo ne figure dans `requirements.txt`. La persistance documentaire/vectorielle est assurée par **PostgreSQL** (relationnel) et **Qdrant** (vecteurs). Ce composant est donc **sans objet** pour cette architecture.

### 3.13 Ordre de démarrage et dépendances (`depends_on`)

Compose ordonne le démarrage via des `depends_on` conditionnés par les *healthchecks*, garantissant qu'un service ne démarre qu'une fois ses dépendances prêtes :

| Service | Attend (condition) |
|---|---|
| `midpoint` | `midpoint-postgres` (service_healthy) |
| `gateway` | `gateway-db` (healthy), `redis` (healthy), `qdrant` (started) |
| `gateway-frontend` | `gateway` (healthy) |
| `odoo` | `odoo-db` (healthy) |
| `keycloak` | `keycloak-db` (healthy) |
| `phpldapadmin` | `openldap` (démarré) |

Le lanceur étagé `start.sh` reproduit cet ordre (bases de données → services IAM → gateway → frontend) avec ses propres sondes, ce qui évite les démarrages prématurés et les *races* d'initialisation.

---

## 4. Architecture interne du Gateway FastAPI

Application en couches sous `gateway/app/` : `api → services → connectors → systèmes externes`, avec `core` et `models` transverses. Au démarrage (`main.py`, *lifespan*) : logs → `init_db()` → chargement du cache `MemoryStore` → Redis → Qdrant → APScheduler. Un middleware `request_context_middleware` attribue un `X-Request-ID`, le lie aux logs et convertit toute exception non gérée en `500` générique.

### 4.1 `app/api/` — Couche routeurs (14 fichiers, 149 endpoints)

Comptes exacts (décorateurs `@router.<méthode>`) ; préfixe défini dans `main.py` ; colonne *Auth* : `JWT` = `get_current_user`, `RBAC` = `require_role([...])`, `HMAC` = signature webhook.

| Routeur | Endpoints | Préfixe | Auth dominante | Rôles pour les écritures |
|---|---:|---|---|---|
| `admin.py` | 11 | `/api/v1/admin` | Public (`/token`) + JWT | `admin` (emergency-stop, resume, config) |
| `provision.py` | 13 | `/api/v1/provision` | JWT (lecture) | `admin`, `iam_engineer` ; `admin` pour DELETE |
| `midpoint.py` | 14 | `/api/v1` | JWT (lecture) | `admin`, `iam_engineer` ; `admin` pour DELETE/rôles |
| `rules.py` | 11 | `/api/v1/rules` | JWT (lecture) | `admin`, `iam_engineer` ; `admin` pour DELETE |
| `workflow.py` | 13 | `/api/v1/workflow` | JWT + contrôle objet | `admin` (cancel) ; approbation par objet/token |
| `reconcile.py` | 7 | `/api/v1/reconcile` | JWT (lecture) | `admin`, `iam_engineer` ; `admin` (sync-cache) |
| `connectors.py` | 16 | `/api/v1/connectors` | JWT (lecture) | `admin` (CRUD, test-preview, sync MidPoint) |
| `scheduler.py` | 14 | `/api/v1/scheduler` | JWT (lecture) | `admin`, `iam_engineer` ; `admin` (DELETE) |
| `users.py` | 9 | `/api/v1/users` | `admin` (la plupart) | `admin` ; `admin,iam_engineer` (lectures ciblées) |
| `permissions.py` | 6 | `/api/v1/permissions` | JWT (lecture) | `admin`, `iam_engineer` (assign) |
| `live_comparison.py` | 17 | `/api/v1/live` | JWT (lecture) | `admin`, `iam_engineer` ; `admin,it_admin` (exec) |
| `ldap_groups.py` | 6 | `/api/v1` | JWT (lecture) | `admin`, `iam_engineer` (membres) |
| `ai_assistant.py` | 9 | `/api/v1/ai` | JWT | `admin` (config du fournisseur) |
| `webhooks.py` | 3 | `/api/v1/webhooks` | **HMAC** + Public (`/health`) | `admin` (sync-all) |

**Rôle de chaque routeur :**
- `admin` — authentification (`/token`), profil (`/me`), déconnexion, statut système (DB/Redis/LDAP/MidPoint), **arrêt d'urgence**/reprise, recherche d'audit, configuration, métriques.
- `provision` — opérations de provisionnement (hub ou direct), statut, **rollback**, et orchestration MidPoint (users/roles/resources).
- `midpoint` — gestion directe des objets MidPoint : users (CRUD, enable/disable), rôles, resources, shadows, santé.
- `rules` — CRUD des règles de mapping, test sur données d'exemple, versions et restauration, politiques.
- `workflow` — configs et instances de workflow, approbations en attente, approve/reject (contrôle au niveau objet), historique, **approbation par email**.
- `reconcile` — démarrage de jobs de réconciliation, statut, divergences, résolution, rafraîchissement du cache d'état.
- `connectors` — CRUD des connecteurs dynamiques, test (stocké ou *preview*), bascule, santé, et synchronisation vers une *Resource* MidPoint.
- `scheduler` — jobs APScheduler (daily/interval/cron), presets (workday/nightly/hourly), historique, contrôle des contrats.
- `users` — administration des utilisateurs gateway, rôles, emails par rôle, chaîne d'approbation.
- `permissions` — niveaux de droits 1–5, attribution, statistiques, vérification.
- `live_comparison` — vue temps réel inter-systèmes et synchronisation Odoo→MidPoint (avec/sans approbation), contrats expirés/expirants.
- `ldap_groups` — lecture des groupes LDAP et des appartenances, ajout/retrait de membres.
- `ai_assistant` — assistant optionnel (suggestion de mappings, génération de connecteur, analyse d'erreur, explication de règle).
- `webhooks` — réception des notifications MidPoint (HMAC) et déclenchement de synchronisation manuelle.

### 4.2 `app/services/` — Couche logique métier

| Service | Responsabilité |
|---|---|
| `midpoint_provision_service.py` | Provisionnement **mode hub** : crée l'enregistrement d'opération, mappe cibles→rôles, pilote `MidPointConnector`. |
| `provision_service.py` | Provisionnement **mode direct** + rollback + `continue_after_approval` (essaie MidPoint puis bascule en direct). |
| `midpoint_client.py` / `midpoint_resource_service.py` | Client bas niveau REST MidPoint ; gestion des *Resources*. |
| `rule_engine.py` | Moteur de règles d'attributs Jinja2 *sandboxé* (filtres `normalize_name`, `generate_login`, `slugify`), exécutées par priorité décroissante. |
| `workflow_service.py` | Workflows d'approbation **multi-niveaux** (Manager → RH → IT), tokens approve/reject, notifications email, auto-approbation sur timeout. |
| `reconciliation_service.py` | Jobs de réconciliation, détection/résolution des divergences. |
| `scheduler_service.py` | APScheduler : sync Odoo→MidPoint, rôles par département, contrôle d'expiration des contrats. |
| `audit_service.py` | Journalisation d'audit, métriques, état système (emergency-stop), indexation Qdrant. |
| `connector_management_service.py` | CRUD des configurations de connecteurs dynamiques. |
| `user_service.py` | Utilisateurs de la gateway (`gateway_users`), emails par rôle, chaînes d'approbation. |
| `email_service.py` | Emails d'approbation (SMTP ; journalisés en `DEV_MODE`). |
| `ai_agent.py` | Appels au fournisseur LLM (OpenAI/DeepSeek) pour l'assistant. |

### 4.3 `app/connectors/` — Couche adaptateurs

Interface commune `BaseConnector` (ABC, CRUD asynchrone). Valeurs exactes relevées dans le code :

| Connecteur | Protocole | Bibliothèque Python | Timeouts (valeurs du code) | Stratégie de *retry* |
|---|---|---|---|---|
| **MidPoint** (`midpoint_connector.py`) | REST HTTP/JSON (+ XML pour l'assignation de rôle en 4.4), Basic Auth | `httpx.AsyncClient` (client réutilisé) | `timeout = 60.0 s` ; TLS vérifié si `MIDPOINT_VERIFY_SSL` | `httpx.AsyncHTTPTransport(retries=2)` — 2 retentatives sur échec de connexion transitoire |
| **LDAP** (`ldap_connector.py`) | LDAP (389 clair / 636 TLS) | `ldap3` (synchrone) | `connect_timeout = 10 s` (Server), `receive_timeout = 10 s` (Connection) | `_get_connection` retente le *bind* **2 fois** (`range(2)`) ; motif *connect-use-unbind* |
| **Odoo** (`odoo_connector.py`) | XML-RPC (sur HTTP :8069) | `xmlrpc.client` + `_TimeoutTransport` | `timeout = 15.0 s` (socket) | `_execute` : **2 tentatives**, réauthentifie en réinitialisant l'`uid` mis en cache |
| **Keycloak** (`KeycloakProvisioner`, dans `webhooks.py`) | REST admin API (token `admin-cli`, *password grant*) | `httpx.AsyncClient` | `timeout = 10.0 s` par appel | Pas de *retry* explicite ; re-récupère un token admin à chaque opération |
| **Fabrique** (`connector_factory.py`) | — | — | — | `ConnectorFactory` met en cache par cible ; `invalidate_cache()` après modif. |

**Contrat commun (`BaseConnector`).** Chaque connecteur statique implémente la même interface asynchrone : `test_connection`, `create_account`, `update_account`, `delete_account`, `disable_account`, `enable_account`, `get_account`, `list_accounts`, ainsi que la gestion des appartenances (`add_to_group`/`remove_from_group`/`get_groups` pour LDAP et Odoo ; `assign_role`/`remove_role` pour MidPoint). Cette uniformité permet à `ConnectorFactory` et aux services de manipuler n'importe quelle cible de manière interchangeable, et de basculer du mode hub au mode direct sans changer la couche service.

**Détails de la fabrique.** `ConnectorFactory.get_connector(target)` résout d'abord un **connecteur dynamique** (config chargée de la table `connector_configurations`) puis retombe sur un **connecteur statique** : `MIDPOINT`, `LDAP`/`AD`, `SQL`, `ODOO`. `GLPI`, `KEYCLOAK`, `FIREBASE` lèvent `NotImplementedError` en statique (à ajouter via la page Connecteurs). Le `DynamicConnector` dispatche selon `connector_type` (`sql`/`ldap`/`rest`/`erp`). **Garde anti-injection** : `_safe_sql_identifier` valide chaque nom de colonne contre l'allowlist `^[A-Za-z_][A-Za-z0-9_]*$` avant toute interpolation dans une requête SQL dynamique.

### 4.4 `app/models/` — Couche modèles de données

- **Modèles SQLModel / SQLAlchemy (tables)** : définis dans `provision.py`, `connector.py`, `rules.py`, `workflow.py`, `audit.py`. `init_db()` exécute `SQLModel.metadata.create_all` au démarrage, mais la **source de vérité du schéma** reste `db/migrations.py` (SQL idempotent) — les deux sont maintenus à la main et peuvent diverger.
- **Modèles Pydantic (contrats d'API)** : requêtes/réponses validées (Pydantic v2), p. ex. `Token`, `UserCreate`, `SystemStatusResponse` (`admin.py`), `ProvisioningRequest`, ou `UserChangeEvent` (`webhooks.py`).
- **Modèles IAM typés (`iam.py`)** — 10 classes reflétant les objets MidPoint :
  - `ActivationStatus` (Enum : `enabled` / `disabled` / `archived`)
  - `ObjectRef` (targetRef/resourceRef : `oid`, `type`, `name`)
  - `Assignment` (rôle via `targetRef` **ou** compte cible via `resourceRef` + `kind`/`intent`)
  - `MidpointShadow` (projection dans une *Resource*)
  - `MidpointUser` (identité simplifiée : `oid`, `name`, `fullName`, `email`, `roles[]`, `shadows[]`…)
  - `MidpointRole`, `MidpointResource`
  - `MidpointUserList`, `MidpointRoleList`, `MidpointResourceList` (enveloppes `total` + liste)
  - Tous en `extra="ignore"` : sur-ensemble tolérant des formes renvoyées par les connecteurs.

**Tables principales** (référencées dans `memory_store.py`, `connector_factory.py` et les services) : `provisioning_operations`, `audit_logs`, `reconciliation_jobs`, `workflows`, `connector_configurations`, `gateway_users`.

### 4.5 `app/core/` — Infrastructure transversale

- **`config.py`** — `Settings(BaseSettings)` *pydantic-settings* (~50 variables, fichier `.env`, `case_sensitive`). Validateur `@model_validator` **fail-fast** : hors `DEBUG`, un `SECRET_KEY`/`JWT_SECRET_KEY` manquant, *placeholder* connu ou < 32 caractères lève `RuntimeError` au démarrage ; en `DEBUG`, un secret éphémère est généré.
- **`security.py`** — JWT : `create_access_token` (HS256 ; claims `sub`, `roles`, `exp` 60 min, `iss`, `aud`, `jti` UUID v4) ; `decode_token` vérifie **signature + expiration + audience + émetteur** (rejette les jetons forgés et l'algorithme `none`). `get_current_user` rejette tout `jti` blacklisté (Redis). `require_role([...])` → **403** si aucun rôle ne correspond. bcrypt **synchrone et asynchrone** (`asyncio.to_thread`) pour sortir le hachage de la boucle d'événements.
- **`redis_client.py`** — singleton. Blacklist (`setex blacklist:{jti}`), cache de sessions et de tokens de workflow. **Rate-limiting** par **script Lua atomique** : `INCR` puis `EXPIRE` en une seule opération (évite la fenêtre non atomique laissant des clés sans TTL). `check_rate_limit` **dégrade *open*** si Redis est indisponible (disponibilité > défense-en-profondeur).
- **`logging.py`** — `structlog` en **JSON** ; `merge_contextvars` propage le `request_id` ; `TimeStamper(iso)` ; niveau piloté par `LOG_LEVEL`. Format propice à ELK / Loki.
- **`database.py`** — `create_async_engine` (asyncpg) avec `echo = settings.DEBUG`, **`pool_pre_ping=True`**, **`pool_recycle=1800`** (30 min), **`pool_size=10`**, **`max_overflow=20`**. `get_session()` (dépendance FastAPI) effectue un `rollback` sur exception non gérée.

### 4.6 Séquence de démarrage, middleware et gestion d'erreurs

Le *lifespan* de `main.py` initialise les services **dans un ordre strict** : configuration des logs → `init_db()` (`SQLModel.metadata.create_all`) → chargement du cache `MemoryStore` depuis PostgreSQL → connexion **Redis** → connexion **Qdrant** → démarrage **APScheduler**. Redis et Qdrant **dégradent gracieusement** : une connexion échouée est journalisée (`status="unavailable"`) sans interrompre le démarrage. À l'arrêt, l'ordre est inversé (scheduler puis Redis).

Trois mécanismes transverses encadrent chaque requête :
- **Middleware `request_context_middleware`** : génère ou propage un `X-Request-ID`, le lie au contexte structlog (`bind_contextvars`), mesure la latence et journalise méthode/chemin/statut/durée. Toute exception non interceptée est convertie en réponse **500 générique** (`{"detail": "Internal server error", "request_id": …}`) — aucun détail interne n'est divulgué.
- **Handler `StarletteHTTPException`** : réponse cohérente `{"detail", "request_id"}` en conservant le code HTTP d'origine.
- **Handler `RequestValidationError`** : réponse **422** structurée avec le détail des erreurs Pydantic.

### 4.7 MemoryStore — le cache hybride (chemin de lecture)

`MemoryStore` (`core/memory_store.py`) est un **singleton thread-safe** qui constitue le **chemin de lecture** des opérations, logs d'audit, jobs de réconciliation et workflows. Au démarrage, `ensure_cache_loaded()` charge en masse les lignes récentes de PostgreSQL (p. ex. les **500 dernières opérations**, triées par date décroissante) dans des dictionnaires/listes en mémoire. Conséquences architecturales :
- **Lectures** : servies depuis le cache, **sans requête SQL** — latence minimale côté API.
- **Écritures** : le cache est mis à jour **immédiatement**, puis persisté en PostgreSQL de façon **asynchrone (*fire-and-forget*)** ; les erreurs DB sont journalisées sans interrompre la requête HTTP. Des **références fortes** aux tâches en cours (`_pending_tasks`) évitent leur ramassage prématuré par le ramasse-miettes (correctif `6cf898d`).
- Il réutilise l'`engine`/`async_session` de `database.py` et emploie du **SQL brut** (`text()`) avec des listes de colonnes explicites — qui doivent rester alignées avec `db/migrations.py`.
- *Corollaire* : une lecture d'API peut être en léger décalage avec une écriture asynchrone ayant échoué.

### 4.8 Moteur de règles et ordonnanceur

- **Moteur de règles (`rule_engine.py`)** : mappe les attributs source vers chaque système cible via **Jinja2 *sandboxé*** (`SafeJinjaEnvironment`, un `SandboxedEnvironment` doté de filtres métier `normalize_name`, `generate_login`, `slugify`). Les règles s'exécutent **par priorité décroissante**, la sortie de chaque règle alimentant le contexte des suivantes. *Réserve* : plusieurs méthodes de persistance renvoient encore des règles par défaut (mocks) — la table `rules` existe et est *seedée*, mais le câblage complet reste un travail en cours (à vérifier avant de supposer qu'une édition de règle persiste).
- **Ordonnanceur (`scheduler_service.py`)** : un `AsyncIOScheduler` (APScheduler, *job store* en mémoire) pilote les **synchronisations Odoo→MidPoint**, l'**auto-attribution de rôles par département** (`DEPARTMENT_ROLE_MAPPING`) et le **traitement des contrats expirés** (désactivation du *leaver*). Les jobs sont créables en `daily`/`interval`/`cron` ou via des *presets* (workday/nightly/hourly).

---

## 5. Flux de données détaillés

### 5.1 Flux 1 — Provisionnement d'un nouvel employé (Odoo → MidPoint → cibles → Keycloak)

```
Scheduler/API   Gateway              MidPoint            Cibles (LDAP/Odoo/SQL)   Keycloak
     │             │                    │                        │                  │
 (1) │ list_employees (XML-RPC search_read hr.employee)          │                  │
     │────────────▶│                    │                        │                  │
 (2) │ (option) workflow d'approbation Manager→RH→IT (tokens email)                  │
     │             │                    │                        │                  │
 (3) │ provision() → POST /ws/rest/users (UserType JSON)         │                  │
     │             │───────────────────▶│                        │                  │
 (4) │             │ assign_role(oid, "ldap-user"/"odoo-user"…) (XML objectModification)
     │             │───────────────────▶│                        │                  │
 (5) │             │                    │ propage via ses connecteurs ──▶ shadows    │
     │             │                    │───────────────────────▶│                  │
 (6) │             │                    │ notif. user-change (HMAC) ─────────────────▶ create_user
     │             │                    │                        │     (mdp temp aléatoire)
 (7) │ audit + MemoryStore (status SUCCESS) + index Qdrant       │                  │
```

Détail, étape par étape :
1. **Source (Odoo).** `ScheduledSyncService` (job planifié) ou `POST /api/v1/live/sync/odoo-to-midpoint` appelle `OdooConnector.list_employees()` → `execute_kw('hr.employee','search_read', …)` via XML-RPC.
2. **(Optionnel) Approbation.** Pour la variante `…/with-approval`, `WorkflowService.create_multi_level_approval_workflow()` crée une instance en `pending`, génère des tokens approve/reject par niveau (Manager 48 h → RH 48 h → IT 24 h *auto-approve*), envoie l'email, et **n'écrit rien dans MidPoint** tant que l'approbation finale n'est pas obtenue. À l'approbation complète, `_execute_odoo_sync()` poursuit la création.
3. **Hub (MidPoint).** `MidPointProvisionService.provision()` enregistre l'opération dans le `MemoryStore` (id `op_<horodatage>_<account_id>`, statut `IN_PROGRESS`, persistée *fire-and-forget* dans `gateway-db`), puis `MidPointConnector.create_account()` → `POST /ws/rest/users` avec un `UserType` (`name`, `givenName`, `familyName`, `emailAddress`, `employeeNumber`, `organizationalUnit`, `activation/administrativeStatus=enabled`). L'**OID** est extrait de la réponse ou de l'en-tête `Location`.
4. **Rôles.** `_map_targets_to_roles` traduit chaque cible en rôle MidPoint (`LDAP→ldap-user`, `ODOO→odoo-user`, `SQL→intranet-user`, `KEYCLOAK→keycloak-user`). Pour chaque rôle, `assign_role(oid, role)` poste un `objectModification` **XML** (ajout d'un `assignment` → `targetRef` `RoleType`) — format requis par MidPoint 4.4.
5. **Propagation (LDAP/Odoo/SQL).** Ce sont **les connecteurs propres à MidPoint** qui créent les projections (`uid=…,ou=users,dc=example,dc=com` ; `res.partner`+`res.users`+`hr.employee` ; ligne SQL `intranet`). L'utilisateur dispose alors de comptes **shadow**, consultables via `GET /ws/rest/users/{oid}/shadows`.
6. **Keycloak.** MidPoint émet une notification `user-change` → `POST /api/v1/webhooks/midpoint/user-change` (HMAC vérifiée) → `KeycloakProvisioner.create_user()` (mot de passe temporaire **aléatoire** `secrets.token_urlsafe(24)`, `temporary=True`, `emailVerified=True`).
7. **Audit.** L'opération passe à `SUCCESS` dans le `MemoryStore` (et en base) ; `AuditService` journalise et **Qdrant** indexe l'entrée pour la recherche sémantique.

> **Variante mode direct.** Si `MIDPOINT_ENABLED=False`, `ProvisionService.execute_provisioning()` écrit séquentiellement sur chaque cible via `ConnectorFactory` et **empile une `RollbackAction` par succès**. À la première erreur, les actions déjà effectuées sont annulées (rollback du succès partiel), ce qui préserve l'atomicité de l'opération multi-cibles — propriété que MidPoint assure nativement en mode hub.

### 5.2 Flux 2 — Authentification et autorisation

```
Client                 Gateway (FastAPI)               Redis            gateway-db
  │  POST /admin/token       │                            │                  │
  │─────────────────────────▶│ check_rate_limit (Lua)     │                  │
  │                          │───────────────────────────▶│ INCR+EXPIRE      │
  │                          │ get_user_by_username ──────────────────────────▶│
  │                          │ verify_password_async (bcrypt via to_thread)    │
  │   200 {access_token} ◀───│ create_access_token (HS256, jti, iss, aud)      │
  │                          │                            │                  │
  │  GET /… : Bearer <jwt>   │ decode_token (signature/exp/iss/aud)            │
  │─────────────────────────▶│ is_token_blacklisted(jti) ─▶│                  │
  │  200 / 401 / 403   ◀──────│ require_role([...])        │                  │
```

**À l'appel de `POST /api/v1/admin/token` :**
1. **Rate-limiting (Redis, Lua).** `redis_client.check_rate_limit("login:{ip}:{username}", max_requests=10, window_seconds=300)` : compteur atomique `INCR`+`EXPIRE`. Au-delà de **10 tentatives en 5 minutes** → **429**. Si Redis est indisponible, l'accès est autorisé (dégradation *open*).
2. **Résolution de l'utilisateur.** `UserService(session).get_user_by_username()` interroge `gateway_users` ; si le compte est actif et possède un `password_hash`, ses rôles sont chargés. **Sinon, et uniquement si `DEBUG=true`**, la fixture `TEMP_USERS` (`admin`/`operator`, hachée à la volée) est utilisée — jamais en production.
3. **Vérification du mot de passe.** `verify_password_async()` (bcrypt via `asyncio.to_thread`, hors *event loop*). Échec → **401** `Incorrect username or password`.
4. **Émission du JWT.** `create_access_token({"sub": username, "roles": roles})` → JWT **HS256** signé, avec `exp` (60 min), `iss`, `aud`, `jti`. Réponse `{access_token, token_type: "bearer"}`.

**À chaque requête authentifiée suivante (`Authorization: Bearer <token>`) :**
1. `oauth2_scheme` extrait le token.
2. `get_current_user` → `decode_token` : `jwt.decode` vérifie la **signature** (clé secrète), l'**expiration**, l'**audience** (`aud`) et l'**émetteur** (`iss`) ; échec → **401**. (L'algorithme est borné à `[HS256]`, donc `none` est rejeté.)
3. **Blacklist.** Si le `jti` figure dans `blacklist:{jti}` (Redis) → **401** *Token has been revoked*.
4. **RBAC.** `require_role([...])` évalue les rôles : si aucun rôle requis n'est présent → **403** *Insufficient permissions* ; sinon la requête se poursuit.
   - *Déconnexion* : `POST /api/v1/admin/logout` ajoute le `jti` à la blacklist avec un TTL = `JWT_EXPIRE_MINUTES × 60` s.

### 5.3 Flux 3 — Webhook MidPoint → Keycloak

```
MidPoint              Gateway /webhooks                      Keycloak
  │  POST user-change      │                                    │
  │  + X-MidPoint-Sig ────▶│ verify_midpoint_signature           │
  │                        │  HMAC-SHA256(body) == sig ?         │
  │   401 si invalide  ◀───│  (503 si aucun secret en prod)      │
  │   200 {accepted}   ◀───│ BackgroundTasks.add_task            │
  │                        │ └─ process_user_change ─▶ get_token (admin-cli) ─▶│
  │                        │                          create / update / delete ▶│
```

**À l'appel de `POST /api/v1/webhooks/midpoint/user-change` :**
1. **Vérification HMAC-SHA256** (dépendance `verify_midpoint_signature`, **avant** tout traitement). Le **corps brut** est lu une fois ; `expected = HMAC_SHA256(MIDPOINT_WEBHOOK_SECRET, body)` ; comparaison en **temps constant** (`hmac.compare_digest`) avec l'en-tête `X-MidPoint-Signature` (préfixe `sha256=` retiré). Mismatch → **401**. Si le secret n'est pas configuré : **bypass en `DEBUG`**, sinon **503** (fail-closed).
2. **Parsing.** Le handler lit le JSON → `UserChangeEvent(event, operation, user)`.
3. **Réponse immédiate.** La tâche est déléguée à `BackgroundTasks` (`process_user_change`) et l'API répond `{"status": "accepted"}` sans attendre — pour ne pas bloquer MidPoint.
4. **Provisionnement Keycloak.** `KeycloakProvisioner.provision_user(user, operation)` : obtient un token admin (`admin-cli`, *password grant* sur le realm `master`), vérifie l'existence (`user_exists`), puis selon l'opération :
   - `add`/`create` → `create_user` (ou `update_user` si déjà présent) avec **mot de passe temporaire aléatoire** ;
   - `modify`/`update` → `update_user` (ou création si absent) ;
   - `delete` → `delete_user`.
   Les comptes système (`administrator`, `midpoint`) sont **ignorés**.

> **Propriétés transversales aux trois flux.** Chaque opération est tracée (`request-id` + audit), **idempotente** côté Keycloak (création ou mise à jour selon l'existence) comme côté MidPoint (résolution par OID ou par nom), et tolère la panne des composants non critiques (Redis, Qdrant) par **dégradation contrôlée** plutôt que par échec dur.

---

## 6. Sécurité de l'architecture

La sécurité applicative repose sur quelques principes directeurs : **défense en profondeur** (authentification + RBAC + échappement + rate-limit), **moindre privilège** (RBAC granulaire — lectures en JWT, écritures réservées à des rôles dédiés), **fail-closed** sur les frontières sensibles (webhook rejeté en l'absence de secret en production) mais **fail-open** maîtrisé là où la disponibilité prime (rate-limit non bloquant si Redis tombe), et **aucun secret dans le code ni dans l'historique Git**.

### 6.1 Modèle de menaces et contrôles

Synthèse des contrôles introduits par la branche `security-hardening` (13 commits de sécurité), rattachés à leur commit d'origine.

| Menace | Vecteur | Contrôle mis en place | Commit |
|---|---|---|---|
| Forge de JWT | Secret faible/par défaut connu | Validation *fail-fast* des secrets (≥ 32 car., hors placeholders) | `d68adfb` |
| Exposition de données | Logs/echo SQL trop verbeux, secrets journalisés | `echo = DEBUG` uniquement ; arrêt de la journalisation des secrets | `d68adfb` |
| Indisponibilité (DB) | Connexions *stale* après redémarrage PG | `pool_pre_ping` + `pool_recycle=1800` + pooling | `d68adfb` |
| Secrets en clair dans le code | Identifiants admin *inline* | Suppression des identifiants codés en dur (+ fix crash `MIDPOINT_USERNAME`) | `8d3ac36` |
| Élévation de privilèges | RBAC incomplet sur les écritures | `require_role([...])` sur **tout** endpoint mutant | `0483e05` |
| Usurpation de webhook | Webhook MidPoint non authentifié | **HMAC-SHA256** en temps constant, *fail-closed* en prod | `7b834c0` |
| Compte Keycloak faible | Mot de passe temporaire prévisible | Mot de passe temporaire **aléatoire** (`token_urlsafe(24)`) | `7b834c0` |
| Injection LDAP | Filtre/DN non échappé | `escape_filter_chars()` + `escape_rdn()` | `2876c1d` |
| Injection SQL | Clés JSON utilisées comme colonnes | Allowlist regex `_safe_sql_identifier` | `2876c1d` |
| Déni de service (CPU) | bcrypt bloquant l'*event loop* | Hachage déporté via `asyncio.to_thread` | `65b2e6d` |
| Confusion d'audience JWT | Jeton réutilisé hors contexte | Claims + vérification `iss`/`aud` | `65b2e6d` |
| Blocage I/O (event loop) | Tests connecteurs / SMTP synchrones | Déport hors boucle d'événements | `9296a3b` |
| Perte d'intégrité d'audit | Tâches d'arrière-plan ramassées par le GC | Conservation de **références fortes** aux tâches | `6cf898d` |
| Fuite d'info via erreurs | *Stack traces* renvoyées au client | `request-id` + gestion centralisée (500 générique) | `e2fb262` |
| Force brute | Endpoint de login non limité | **Rate limit 10 / 5 min** (Lua Redis) | `5a46ddf` |
| Compromission conteneur/hôte | Conteneur root, images flottantes, ports exposés | Non-root **UID 10001**, healthcheck, images figées, liaison `127.0.0.1` | `97d284c` |
| Régressions de sécurité | Absence de tests/CI | Suite **pytest** + pipeline **GitHub Actions** | `8f93b6b` |
| SSRF | `connectors/test-preview` (config arbitraire) | Restreint au rôle **admin** uniquement | `088de77` |
| Intégrité d'authentification | Login basé sur un store mémoire seul | Login **adossé à `gateway_users`** (fixture en `DEBUG`) | `088de77` |

### 6.2 Architecture réseau sécurisée

- **Datastores liés à `127.0.0.1`** : `gateway-db` (5434), `midpoint-postgres` (5433), `intranet-db` (55432), `redis` (6379), `qdrant` (6333/6334), `openldap` (10389/10636) ne sont **pas exposés publiquement** ; `odoo-db` et `keycloak-db` n'ont **aucune** publication sur l'hôte.
- **Seuls les ports applicatifs** sont ouverts plus largement : gateway `:8000`, frontend `:3000`, MidPoint `:8080`, Keycloak `:8081`, Odoo `:8069`, phpLDAPadmin `:8088`.
- **CORS restreint** : `main.py` n'autorise que les origines de `settings.CORS_ORIGINS`, avec une liste explicite de méthodes (`GET/POST/PUT/PATCH/DELETE/OPTIONS`) et d'en-têtes (`Authorization`, `Content-Type`, `X-Request-ID`).
- **Conteneur non-root** : l'image de la gateway s'exécute en `appuser` (**UID 10001**) avec un healthcheck applicatif sur `/health`.
- **Réseau unique `iam-network`** (bridge) : tous les services communiquent par leur nom de service interne ; l'isolation réseau vis-à-vis de l'hôte repose sur les liaisons `127.0.0.1` ci-dessus.

**Exposition des ports (synthèse) :**

| Exposé largement (applicatif) | Lié à `127.0.0.1` (datastore) | Interne (aucun port hôte) |
|---|---|---|
| gateway `8000`, frontend `3000`, MidPoint `8080`, Keycloak `8081`, Odoo `8069`, phpLDAPadmin `8088` | gateway-db `5434`, midpoint-postgres `5433`, intranet-db `55432`, redis `6379`, qdrant `6333/6334`, openldap `10389/10636` | odoo-db, keycloak-db |

### 6.3 Cycle de vie et révocation des jetons JWT

- **Émission** : à la connexion, un JWT **HS256** est signé avec une durée de vie de **60 minutes** (`JWT_EXPIRE_MINUTES`) et porte un `jti` (UUID v4) unique, plus `iss` et `aud`.
- **Vérification** : chaque requête revalide signature, expiration, `iss` et `aud` ; l'algorithme étant borné à `[HS256]`, l'attaque `alg=none` est neutralisée.
- **Révocation** : la déconnexion inscrit le `jti` dans `blacklist:{jti}` (Redis) avec un TTL égal à la durée de vie résiduelle ; `get_current_user` rejette tout `jti` blacklisté. La révocation est ainsi **immédiate**, sans état serveur au-delà de Redis.
- **Anti-brute-force** : `POST /admin/token` est plafonné à **10 tentatives / 5 min** par couple IP + *username* (compteur Lua atomique), avec dégradation *open* si Redis est hors service.
- **Stockage des secrets** : les clés de signature sont obligatoires et fortes en production (validateur *fail-fast*), jamais journalisées, et absentes du dépôt (`.env` ignoré).

### 6.4 Hiérarchie des rôles (RBAC)

Les rôles sont stockés par utilisateur (`gateway_users.roles`) et vérifiés par `require_role([...])`.

| Catégorie | Rôles | Capacité type |
|---|---|---|
| **Accès** | `admin` | Contrôle total : utilisateurs, connecteurs, règles, arrêt d'urgence, suppressions, octroi de rôles. |
| | `iam_engineer` | Provisionnement, règles, scheduler, groupes LDAP, synchronisations. |
| | `director` / `viewer` | Orientés lecture. |
| **Approbation** | `manager`, `rh_manager`, `it_admin`, `security_officer` | Niveaux d'approbation des workflows. |
| **Legacy/dev** | `operator` | Fixture en code, réservée au mode `DEBUG`. |

Règle générale : les **lectures** exigent un JWT valide ; les endpoints **mutants** exigent un rôle — `admin` pour les suppressions et la gestion des rôles, `admin,iam_engineer` pour la plupart des autres écritures.

---

## 7. Justification des choix techniques

- **FastAPI plutôt que Flask.** *Async natif* (essentiel pour un orchestrateur qui multiplie les appels réseau — MidPoint, LDAP, Odoo, Keycloak, Redis), **validation automatique** via Pydantic v2 (contrats d'API typés, erreurs 422 cohérentes), et **OpenAPI/Swagger généré** automatiquement (`/docs`) — utile pour une UI et des clients API. Le système de **dépendances** (`Depends`) rend l'auth/RBAC déclaratifs et testables.
- **MidPoint plutôt qu'un développement *custom*.** MidPoint apporte des **connecteurs Java matures** (ConnId) et les fonctions d'IGA difficiles à réimplémenter : modèle de **rôles**, **recertification**, réconciliation, gestion des *shadows* et des projections. La gateway se concentre alors sur l'orchestration, les règles et l'expérience utilisateur, sans réinventer le moteur d'identités.
- **Redis pour le rate-limiting et la révocation.** L'**atomicité** via script **Lua** (`INCR`+`EXPIRE` indivisibles) garantit un compteur correct même en concurrence — impossible à obtenir proprement avec deux commandes séparées. Redis sert aussi de **blacklist de `jti`** à TTL, mécanisme naturel pour révoquer des JWT sans état serveur lourd.
- **Qdrant pour la recherche sémantique.** L'audit étant volumineux et interrogé en langage naturel (assistant IA), une **base vectorielle** permet la recherche par **similarité sémantique** plutôt que par mots-clés exacts. Qdrant **dégrade gracieusement** : son indisponibilité n'interrompt pas le provisionnement (l'audit relationnel reste dans PostgreSQL).
- **Docker Compose pour l'orchestration.** Un stack IAM réaliste suppose une dizaine de services interdépendants ; Compose en décrit l'**infrastructure as code** (versions figées, réseau, volumes, *healthchecks*, `depends_on`) et permet de lever localement, de façon reproductible, un environnement complet — essentiel dans un contexte pédagogique et d'évaluation.
- **`MemoryStore` (cache hybride) pour le chemin de lecture.** Servir les lectures depuis la mémoire (et persister en asynchrone) évite une requête SQL par appel d'API et garde l'interface réactive, au prix d'une cohérence *eventually consistent* acceptable pour des données d'opérations/d'audit.
- **Connecteurs dynamiques + règles Jinja2 *sandboxées*.** Plutôt que de coder en dur chaque cible, le `DynamicConnector` et le moteur de règles permettent d'ajouter une cible et de définir son mapping d'attributs **depuis l'UI**, sans redéploiement — répondant à l'objectif *no-code* du projet, tout en confinant l'exécution des templates dans un environnement Jinja2 restreint.
- **structlog en JSON.** Des logs structurés et corrélés par `request_id` sont directement exploitables par une chaîne d'observabilité (ELK, Grafana Loki), contrairement à des logs texte libres.
- **APScheduler embarqué.** Un ordonnanceur *in-process* suffit aux synchronisations périodiques (Odoo→MidPoint, contrats) sans dépendance à un *broker* externe (Celery/RabbitMQ), ce qui allège le déploiement de la plateforme.
- **bcrypt + JWT HS256.** bcrypt (coût configurable) protège les mots de passe au repos ; HS256 offre une signature symétrique simple à opérer pour un service unique, complétée par le couple `jti`/blacklist Redis pour la révocation immédiate.

---

## 8. Limites connues et perspectives

L'architecture est fonctionnelle mais comporte des points d'amélioration identifiés (cf. `ARCHITECTURE.md` §10) :
- **Source unique du schéma** : `SQLModel.metadata.create_all` (au démarrage) et `db/migrations.py` (SQL idempotent) coexistent et peuvent diverger ; l'adoption d'**Alembic** et l'alignement de la casse des enums sont à prévoir.
- **Persistance incomplète** : le moteur de règles et certaines configurations de workflow/provisionnement renvoient encore des mocks/no-ops, à câbler à la base.
- **Offload asynchrone complet** des connecteurs LDAP/Odoo (synchrones) : les timeouts sont posés, le déport en *thread* reste à finaliser.
- **JWT en cookie `HttpOnly` + rotation de *refresh token*** : les jetons sont aujourd'hui stockés côté client (`localStorage`) ; les claims `iss`/`aud` sont déjà en place.
- **Production** : terminaison TLS / reverse-proxy, gestionnaire de secrets externe, immuabilité de la piste d'audit, et outillage de sauvegarde/restauration des bases.
- **Assistant IA** : corriger le décalage de modèle requête/réponse de `/ai/suggest-mappings` et `/ai/generate-connector` (fonction optionnelle, désactivée par défaut).

Ces limites n'affectent pas le cœur du provisionnement (mode hub) mais cadrent l'industrialisation future de la plateforme.

---

## 9. Glossaire

| Sigle | Signification |
|---|---|
| **IAM** | *Identity and Access Management* — gestion des identités et des accès. |
| **IGA** | *Identity Governance and Administration* — gouvernance (rôles, recertification, workflows) ; domaine de MidPoint. |
| **JML** | *Joiner / Mover / Leaver* — cycle de vie d'une identité : arrivée, mobilité, départ. |
| **RBAC** | *Role-Based Access Control* — contrôle d'accès basé sur les rôles. |
| **JWT** | *JSON Web Token* — jeton signé porteur des *claims* d'authentification. |
| **HMAC** | *Hash-based Message Authentication Code* — signature à clé partagée (ici SHA-256) authentifiant le webhook. |
| **OIDC / SSO** | *OpenID Connect* / *Single Sign-On* — rôle assuré par Keycloak. |
| **SPA** | *Single-Page Application* — l'UI React servie par nginx. |
| **OID** | *Object Identifier* — identifiant unique d'un objet MidPoint (format UUID). |
| **Shadow** | Projection d'une identité MidPoint dans une *Resource* (le compte réel côté LDAP/Odoo/SQL). |
| **Resource** | (MidPoint) Système cible connecté au hub. |
| **CORS** | *Cross-Origin Resource Sharing* — politique d'origines autorisées côté navigateur. |
| **TTL** | *Time To Live* — durée de vie d'une clé (Redis). |

---

*Document généré dans le cadre du Projet 3 — IAM Gateway (SAE S5/S6, UPEC). Co-auteur référencé : `achibani@gmail.com`. Toutes les valeurs (ports, versions, timeouts, tailles de pool, limites mémoire) sont issues du code et de `docker-compose.yml` à la révision `50d2bc6`.*
