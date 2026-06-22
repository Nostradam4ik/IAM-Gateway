# Fiche de déploiement Docker — IAM Gateway

> **Document** : Description de l'architecture de conteneurisation et guide de déploiement (livrable DevOps/SRE)
> **Projet** : *Projet 3 — Passerelle de provisionnement IAM intelligente* (SAE S5/S6, BUT Informatique — UPEC, laboratoire LISSI)
> **Dépôt** : <https://github.com/Nostradam4ik/IAM-Gateway>
> **Co-auteur** (métadonnées, conformément au `README.md`) : `achibani@gmail.com` (Abdelghani Chibani)
> **Sources** : `docker-compose.yml`, `gateway/Dockerfile`, `gateway/frontend/Dockerfile`, `gateway/frontend/nginx.conf`, les deux `.dockerignore`, `.env.example`, `core/config.py`

---

## 1. Vue d'ensemble de la stack Docker

| Indicateur | Valeur |
|---|---|
| **Format Docker Compose** | version `"3.9"` |
| **Nombre total de services** | **14** |
| **Réseaux Docker définis** | **1** (`iam-network`, driver `bridge`) |
| **Volumes nommés** | **13** |
| **Services avec `mem_limit`** | 5 (sur 14) |
| **Total `mem_limit` alloué** | **6 912 Mio ≈ 6,75 Gio** (midpoint 3 g + gateway 768 m + qdrant 1 g + odoo 1 g + keycloak 1 g) |

**Philosophie.** L'architecture est **micro-services** : chaque composant fonctionnel (hub IAM, gateway, frontend, annuaire, ERP, SSO, caches, bases) tourne dans **son propre conteneur**, avec son image, son cycle de vie et ses ressources. Les services communiquent par leur **nom de service** sur un réseau Docker partagé, et la persistance est externalisée dans des **volumes nommés**. Cette séparation permet de versionner, redémarrer et limiter chaque brique indépendamment.

> La clé `version: "3.9"` est conservée pour compatibilité ; Docker Compose v2 l'ignore désormais (le format est déduit du schéma), mais elle documente l'intention de format.

> Aucun service **MongoDB** n'est défini dans `docker-compose.yml` : la stack repose sur PostgreSQL (×5), Redis et Qdrant. Un lanceur étagé `start.sh` (bash/WSL2) reproduit l'ordre de démarrage avec des sondes de santé, en complément de `docker compose up`.

---

## 2. Tableau complet des services

Toutes les valeurs proviennent de `docker-compose.yml`. `Restart` = `unless-stopped` et `Réseau` = `iam-network` pour **tous** les services. Notation des ports : `hôte→conteneur` ; le préfixe `127.0.0.1:` signifie « lié à l'hôte local uniquement », son absence signifie une exposition sur `0.0.0.0`.

| Service | Image:Tag | Ports | Mem limit | Healthcheck | Dépend de |
|---|---|---|---|---|---|
| `gateway` | *build* `./gateway` (`python:3.11-slim`) | `8000→8000` | **768m** | ✅ `GET /health` | gateway-db (h), redis (h), qdrant (s) |
| `gateway-frontend` | *build* `./gateway/frontend` (`nginx:alpine`) | `3000→80` | — | ❌ | gateway (**healthy**) |
| `gateway-db` | `postgres:15` | `127.0.0.1:5434→5432` | — | ✅ `pg_isready -U gateway` | — |
| `midpoint` | `evolveum/midpoint:4.4` | `8080→8080` | **3g** | ❌ | midpoint-postgres (h) |
| `midpoint-postgres` | `postgres:15` | `127.0.0.1:5433→5432` | — | ✅ `pg_isready -U midpoint` | — |
| `keycloak` | `quay.io/keycloak/keycloak:23.0` | `8081→8080` | **1g** | ❌ | keycloak-db (h) |
| `keycloak-db` | `postgres:15` | *(interne)* | — | ✅ `pg_isready -U keycloak` | — |
| `openldap` | `osixia/openldap:1.5.0` | `127.0.0.1:10389→389`, `127.0.0.1:10636→636` | — | ❌ | — |
| `phpldapadmin` | `osixia/phpldapadmin:0.9.0` | `8088→80` | — | ❌ | openldap |
| `odoo` | `odoo:17` | `8069→8069` | **1g** | ❌ | odoo-db (h) |
| `odoo-db` | `postgres:15` | *(interne)* | — | ✅ `pg_isready -U odoo` | — |
| `intranet-db` | `postgres:15` | `127.0.0.1:55432→5432` | — | ✅ `pg_isready -U intranet` | — |
| `redis` | `redis:7-alpine` | `127.0.0.1:6379→6379` | — | ✅ `redis-cli ping` | — |
| `qdrant` | `qdrant/qdrant:v1.12.4` | `127.0.0.1:6333→6333`, `127.0.0.1:6334→6334` | **1g** | ❌ | — |

*(h) = `condition: service_healthy`, (s) = `condition: service_started`.* Les healthchecks PostgreSQL utilisent `pg_isready` (intervalle 10 s, timeout 5 s, 5 essais) ; le service `midpoint` ajoute `MP_MEM_MAX=2048m` / `MP_MEM_INIT=1024m` sous sa limite de 3 g ; `keycloak` est lancé en `command: start-dev`. Les cadences de sonde diffèrent : **10 s** pour les bases (`pg_isready` / `redis-cli ping`), **15 s** pour la gateway, avec **40 s de *start period*** laissés à l'initialisation de FastAPI.

**Rôle de chaque service :**
- `gateway` — API FastAPI, plan de contrôle (auth, règles, workflows, connecteurs).
- `gateway-frontend` — SPA React servie par nginx, proxy `/api` vers la gateway.
- `gateway-db` — PostgreSQL applicatif (opérations, audit, workflows, utilisateurs).
- `midpoint` / `midpoint-postgres` — hub IAM central et son dépôt.
- `keycloak` / `keycloak-db` — fournisseur OIDC (SSO) et sa base.
- `openldap` / `phpldapadmin` — annuaire cible et son UI d'inspection.
- `odoo` / `odoo-db` — ERP (source RH + cible) et sa base.
- `intranet-db` — base cible « intranet » (provisioning SQL).
- `redis` — blacklist JWT, rate-limiting, cache.
- `qdrant` — index vectoriel pour la recherche d'audit.

**Images construites vs tirées.** Deux images sont **construites localement** (`gateway` et `gateway-frontend`, via leurs `Dockerfile`) ; les **12 autres** sont **tirées** de registres publics (Docker Hub, quay.io).

**Cinq instances PostgreSQL, par autonomie de service.** Chaque produit possède sa propre base — `gateway-db`, `midpoint-postgres`, `odoo-db`, `keycloak-db`, `intranet-db` — afin que schémas, montées de version et sauvegardes restent **indépendants**. `odoo-db` et `keycloak-db` ne publient **aucun port** (accès strictement interne au réseau Docker).

---

## 3. Analyse détaillée du service `gateway`

### 3.1 Dockerfile backend (`gateway/Dockerfile`)

| Instruction | Rôle / justification |
|---|---|
| `FROM python:3.11-slim` | Image de base **minimale** (variante *slim* sans outils superflus) ; Python 3.11 est la version cible du projet — surface d'attaque et taille réduites. |
| `WORKDIR /app` | Répertoire de travail de l'application. |
| `RUN apt-get install gcc libpq-dev libldap2-dev libsasl2-dev` puis `rm -rf /var/lib/apt/lists/*` | Dépendances système de **compilation** des paquets natifs (`psycopg2`, `ldap3`/SASL) ; le nettoyage du cache APT dans la **même couche** réduit la taille de l'image. |
| `COPY requirements.txt .` **avant** le code | Optimise le **cache de couches** Docker : tant que `requirements.txt` ne change pas, la couche d'installation `pip` est réutilisée — un changement de code seul n'invalide pas l'installation des dépendances. |
| `RUN pip install --no-cache-dir -r requirements.txt` | `--no-cache-dir` empêche `pip` de conserver son cache de téléchargement → **image plus légère**. |
| `COPY app/ ./app/` | Copie du code applicatif (après les dépendances, cf. ci-dessus). |
| `RUN useradd --create-home --uid 10001 appuser && mkdir -p /app/logs && chown -R appuser:appuser /app` | Création d'un **utilisateur non privilégié** `appuser` ; le dossier de logs est créé et la propriété transférée. |
| `USER appuser` | Bascule en utilisateur non-root pour l'exécution du processus. |
| `EXPOSE 8000` | Documente le port applicatif. |
| `HEALTHCHECK …` | Sonde de santé interne (voir §3.3). |
| `CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]` | Démarre l'API. `--host 0.0.0.0` est **nécessaire dans un conteneur** pour écouter sur l'interface réseau du conteneur (et non `127.0.0.1` interne). |

Extrait des instructions finales du `Dockerfile` :
```dockerfile
RUN useradd --create-home --uid 10001 appuser \
    && mkdir -p /app/logs && chown -R appuser:appuser /app
USER appuser
EXPOSE 8000
HEALTHCHECK --interval=15s --timeout=5s --start-period=40s --retries=5 \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://localhost:8000/health').getcode()==200 else 1)"
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Pourquoi l'UID `10001` ?** Les UID inférieurs à 1000 sont réservés aux comptes système et ceux autour de 1000 aux premiers utilisateurs de l'hôte. Choisir un **UID élevé (10001)** évite toute **collision** avec un utilisateur existant de l'hôte si un volume est monté, tout en restant clairement non privilégié. *Précision de fidélité* : le Dockerfile utilise `useradd --create-home --uid 10001` (compte avec répertoire personnel), et **non** `-r` (compte système) ; et `uvicorn` est lancé en **processus unique** (aucun `--workers` n'est spécifié).

### 3.2 `gateway/.dockerignore`

| Exclusion | Pourquoi cela compte |
|---|---|
| `.env`, `.env.*` (sauf `!.env.example`) | **Ne jamais cuire de secrets dans l'image** : un `.env` embarqué fuiterait des clés/mots de passe. |
| `__pycache__/`, `*.py[cod]`, `*.egg-info/` | Bytecode et artefacts Python inutiles, régénérés à l'exécution. |
| `.venv/`, `venv/` | Environnement virtuel local (dépendant de la plateforme hôte). |
| `.pytest_cache/`, `.ruff_cache/`, `.mypy_cache/` | Caches d'outils de dev sans valeur en production. |
| `tests/` | La suite de tests n'a **pas sa place dans l'image d'exécution** (taille + surface). |
| `*.log`, `logs/` | Journaux locaux. |
| `.git/`, `.gitignore` | Métadonnées de gestion de versions (taille + fuite d'historique). |
| `frontend/node_modules/`, `frontend/dist/` | Le frontend a son **propre contexte de build** ; ces dossiers (mauvaise plateforme/volumineux) ne doivent jamais transiter par l'image backend. |

### 3.3 Configuration du healthcheck

Identique dans le `Dockerfile` (instruction `HEALTHCHECK`) et dans `docker-compose.yml` :

| Paramètre | Valeur |
|---|---|
| Test | `python -c "… urllib.request.urlopen('http://localhost:8000/health') … 200"` |
| `interval` | `15s` |
| `timeout` | `5s` |
| `retries` | `5` |
| `start_period` | `40s` (délai de grâce au démarrage) |

L'endpoint **`/health`** renvoie `{"status": "healthy", …}`. Le service `gateway-frontend` déclare `depends_on: gateway: condition: service_healthy` : nginx **n'est démarré qu'une fois la sonde du backend passée au vert**, évitant de servir l'UI avant que l'API ne réponde. Le test utilise **Python (`urllib`)** plutôt que `curl` — ce dernier est absent de l'image *slim*, ce qui évite d'installer une dépendance supplémentaire juste pour la sonde.

### 3.4 Dockerfile frontend (`gateway/frontend/Dockerfile`) — build multi-étapes

Une **construction multi-stage** sépare la compilation de l'exécution :
1. **Étape `builder`** (`node:20-alpine`) : `COPY package*.json` → `npm install` → `COPY . .` → `npm run build` (produit `dist/`).
2. **Étape finale** (`nginx:alpine`) : copie `nginx.conf` vers `/etc/nginx/conf.d/default.conf` et les assets compilés `--from=builder /app/dist` vers `/usr/share/nginx/html`. `EXPOSE 80`, puis `nginx -g "daemon off;"`.

L'image finale **ne contient ni Node ni `node_modules`** (seulement nginx + les fichiers statiques) → image légère et surface réduite. Le `nginx.conf` configure la **compression gzip**, le **proxy `/api → http://gateway:8000`**, le **routage SPA** (`try_files … /index.html`), le **cache long** des assets statiques (`expires 1y`), et des **en-têtes de sécurité** (`X-Frame-Options: SAMEORIGIN`, `X-Content-Type-Options: nosniff`, `X-XSS-Protection`). Son `.dockerignore` exclut `node_modules/`, `dist/`, `.env`, `.env.*`, `*.log`, `.git/`, `.vscode/`.

### 3.5 Variables d'environnement injectées dans `gateway`

La configuration du service `gateway` est fournie **par variables d'environnement** (jamais cuite dans l'image) ; les secrets sont **substitués depuis le `.env`** via la syntaxe Compose `${VAR:-défaut}`. Principales clés (de `docker-compose.yml`) :

| Variable | Source / valeur |
|---|---|
| `DEBUG` / `DEV_MODE` | `${DEBUG:-true}` / `${DEV_MODE:-true}` |
| `SECRET_KEY` / `JWT_SECRET_KEY` | `${SECRET_KEY:-}` / `${JWT_SECRET_KEY:-}` (depuis `.env`) |
| `DATABASE_URL` | `postgresql+asyncpg://gateway:gateway@gateway-db:5432/gateway` |
| `REDIS_URL` | `redis://redis:6379/0` |
| `MIDPOINT_URL` / `MIDPOINT_USER` / `MIDPOINT_PASSWORD` | `http://midpoint-core:8080/midpoint` / `administrator` / `5ecr3t` |
| `LDAP_HOST` / `LDAP_PORT` / `LDAP_BIND_DN` | `openldap` / `389` / `cn=admin,dc=example,dc=com` |
| `ODOO_URL` / `ODOO_DB` / `ODOO_USER` | `http://odoo:8069` / `odoo` / `admin` |
| `KEYCLOAK_URL` / `KEYCLOAK_REALM` | `http://keycloak:8080` / `gateway` |
| `QDRANT_HOST` / `QDRANT_PORT` | `qdrant` / `6333` |
| `MIDPOINT_WEBHOOK_SECRET` | `${MIDPOINT_WEBHOOK_SECRET:-}` |
| `WORKFLOW_MAX_LEVELS` / `WORKFLOW_DEFAULT_TIMEOUT_HOURS` | `5` / `72` |
| `SMTP_*` / `FROM_EMAIL` | `${SMTP_*:-}` / `noreply@iam-gateway.local` |

Les hôtes (`gateway-db`, `redis`, `midpoint-core`, `openldap`, `odoo`, `keycloak`, `qdrant`) sont des **noms de service** résolus par le DNS interne de `iam-network`.

### 3.6 Optimisations de l'image

- **Image de base *slim*** (`python:3.11-slim`) et **multi-stage** côté frontend (le Node de build n'atterrit pas dans l'image finale) → empreinte réduite.
- **Ordre des `COPY`** : `requirements.txt` avant le code → le cache de la couche `pip install` survit aux changements de code.
- **`--no-cache-dir`** (pip) et **nettoyage du cache APT** dans la même couche `RUN` → pas de fichiers temporaires figés dans une couche.
- **`.dockerignore`** : le contexte de build exclut tests, caches, `.git`, `.env`, `node_modules` → build plus rapide et image plus sûre.

---

## 4. Réseaux Docker

Un **unique réseau** est défini :

```yaml
networks:
  iam-network:
    driver: bridge
    name: iam-network
```

- **Nom** : `iam-network` · **Driver** : `bridge` (réseau virtuel local à l'hôte).
- **Services connectés** : **les 14 services** y sont rattachés.

**Principe d'isolation réseau.** En théorie, des services placés sur des réseaux Docker **différents** ne peuvent pas communiquer directement, ce qui permet de cloisonner (p. ex. isoler les bases du frontend). **Dans cette stack, il n'existe qu'un seul réseau** : tous les conteneurs peuvent donc se joindre par leur nom de service (`gateway`, `midpoint-core`, `openldap`, …). **La frontière de sécurité n'est donc pas une segmentation inter-services, mais le binding des ports côté hôte** (§6.1) : ce qui n'est pas publié (ou publié sur `127.0.0.1`) reste inatteignable depuis l'extérieur de la machine.

```
                ┌──────────────────────── HÔTE (Docker) ────────────────────────┐
   0.0.0.0  ───▶│  :3000 frontend   :8000 gateway   :8080 midpoint   :8069 odoo  │
   (réseau) ───▶│  :8081 keycloak   :8088 phpldapadmin                            │
                │                                                                 │
 127.0.0.1 ───▶│  :5434 gateway-db  :5433 mp-pg  :55432 intranet-db              │
  (local) ────▶│  :6379 redis  :6333/6334 qdrant  :10389/10636 openldap          │
                │                                                                 │
                │   ┌──────────── réseau bridge « iam-network » ──────────────┐   │
                │   │ gateway ─ gateway-db ─ redis ─ qdrant ─ midpoint ─ …     │   │
                │   │ (tous les conteneurs communiquent par nom de service)   │   │
                │   │ odoo-db, keycloak-db : AUCUN port publié (purement int.) │   │
                │   └──────────────────────────────────────────────────────────┘ │
                └─────────────────────────────────────────────────────────────────┘
```

**Résolution par nom de service.** Sur `iam-network`, chaque conteneur en joint un autre par son **nom de service** (et son `container_name` quand il diffère) grâce au DNS interne de Docker, sans dépendre d'adresses IP : la gateway atteint `gateway-db:5432`, `redis:6379`, `qdrant:6333`, `openldap:389`, `odoo:8069`, `keycloak:8080`, et `midpoint-core:8080` (alias du service `midpoint`). nginx atteint la gateway via `http://gateway:8000`. Le driver **`bridge`** crée un réseau virtuel privé à l'hôte : les conteneurs y reçoivent une IP interne et un NAT les sépare de l'extérieur — seuls les ports explicitement publiés (`ports:`) franchissent vers l'hôte.

---

## 5. Volumes persistants

13 **volumes nommés** (gérés par Docker, indépendants du cycle de vie des conteneurs) :

| Volume | Service(s) | Données stockées | Survit à `down` | Survit à `down -v` |
|---|---|---|---|---|
| `gateway_db_data` | gateway-db | Base applicative (opérations, audit, users…) | ✅ | ❌ |
| `gateway_logs` | gateway | Journaux applicatifs | ✅ | ❌ |
| `midpoint_postgres_data` | midpoint-postgres | Dépôt MidPoint | ✅ | ❌ |
| `midpoint_home` | midpoint | `/opt/midpoint/var` (keystore, config) | ✅ | ❌ |
| `redis_data` | redis | Persistance Redis (blacklist, compteurs) | ✅ | ❌ |
| `qdrant_data` | qdrant | Collection vectorielle `audit_logs` | ✅ | ❌ |
| `openldap_data` | openldap | Annuaire LDAP (`/var/lib/ldap`) | ✅ | ❌ |
| `openldap_config` | openldap | Config slapd (`/etc/ldap/slapd.d`) | ✅ | ❌ |
| `odoo_db_data` | odoo-db | Base Odoo | ✅ | ❌ |
| `odoo_data` | odoo | Données Odoo (`/var/lib/odoo`) | ✅ | ❌ |
| `odoo_addons` | odoo | Modules additionnels | ✅ | ❌ |
| `intranet_db_data` | intranet-db | Base cible « intranet » | ✅ | ❌ |
| `keycloak_db_data` | keycloak-db | Base Keycloak | ✅ | ❌ |

**`docker compose down` vs `down -v` :**
- `docker compose down` — supprime conteneurs et réseau, **conserve les volumes** → aucune donnée perdue, redémarrage à l'identique.
- `docker compose down -v` — supprime **aussi les volumes** : **opération DESTRUCTIVE**. Toutes les bases, la blacklist Redis et la collection Qdrant sont vidées ; il faut relancer les migrations (`python -m app.db.migrations`) après le prochain démarrage.

### 5.1 Volumes nommés vs bind mounts

Outre les 13 **volumes nommés** (gérés par Docker, persistance abstraite), la stack utilise deux **bind mounts** (dossiers de l'hôte) :
- `./gateway/app:/app/app` — le **code** de la gateway monté en direct, pour le rechargement en développement (à figer dans l'image en production, cf. §9).
- `./infrastructure/sql/init-intranet.sql:/docker-entrypoint-initdb.d/init.sql:ro` — script d'**initialisation** de la base « intranet », monté en **lecture seule** (`:ro`), exécuté au premier démarrage du conteneur PostgreSQL.

**Différence clé** : un *volume nommé* est géré par Docker et survit indépendamment du chemin hôte ; un *bind mount* lie un dossier précis de la machine (pratique pour le dev, mais couple le conteneur à l'arborescence locale).

---

## 6. Sécurité Docker

Le durcissement empile plusieurs couches : **surface réduite** (images *slim* / multi-stage), **moindre privilège** (exécution non-root), **reproductibilité** (tags figés, pas de `:latest`), **cloisonnement des ressources** (`mem_limit`), **confinement réseau** (binding `127.0.0.1`) et **secrets hors image** (injectés depuis `.env`, jamais cuits — garanti par `.dockerignore`).

### 6.1 Binding des ports datastores à `127.0.0.1`

Les bases et caches sont publiés **uniquement sur la boucle locale** : `gateway-db` (5434), `midpoint-postgres` (5433), `intranet-db` (55432), `redis` (6379), `qdrant` (6333/6334), `openldap` (10389/10636). `odoo-db` et `keycloak-db` ne publient **aucun** port (accès purement interne au réseau Docker). **Pourquoi** : sans le préfixe `127.0.0.1:`, Docker publie sur `0.0.0.0`, rendant le port **accessible depuis le réseau local, voire Internet** si l'hôte n'est pas pare-feu. Lier à `127.0.0.1` réserve l'accès aux outils locaux (psql, redis-cli) sans exposer les données. *Scénario évité* : sans cette restriction, un `gateway-db` publié sur `0.0.0.0:5434` serait joignable par toute machine du réseau local ; un attaquant pourrait tenter une connexion PostgreSQL directe avec les identifiants par défaut, **contournant entièrement** l'authentification de la gateway.

### 6.2 Images non-root

L'image `gateway` s'exécute en **`appuser` (UID 10001)**, jamais en root. **Risque d'un conteneur root** : une faille applicative permettant l'exécution de code donnerait des privilèges root **dans le conteneur**, facilitant une évasion vers l'hôte (montages, capacités). L'exécution non privilégiée applique le **moindre privilège**.

### 6.3 Images taguées (pas `:latest`)

Aucune image n'utilise `:latest`. Versions **épinglées au correctif** : `qdrant/qdrant:v1.12.4`, `osixia/openldap:1.5.0`, `osixia/phpldapadmin:0.9.0`, `quay.io/keycloak/keycloak:23.0`. Versions **majeures/roulantes** : `postgres:15`, `redis:7-alpine`, `odoo:17`, `evolveum/midpoint:4.4`, `python:3.11-slim`, `node:20-alpine`, `nginx:alpine`. **Risque de `:latest`** : l'image peut changer sans préavis entre deux `pull`, cassant la reproductibilité (« ça marchait hier »). L'épinglage garantit des déploiements déterministes ; l'épinglage au correctif (voire au digest) est encore plus strict.

### 6.4 Limites mémoire (`mem_limit`)

| Service | Limite | Justification |
|---|---|---|
| `midpoint` | **3g** | JVM gourmande (`MP_MEM_MAX=2048m`) ; le hub IAM est le plus lourd. |
| `keycloak` | **1g** | JVM (serveur OIDC). |
| `odoo` | **1g** | Workers Python + ORM. |
| `qdrant` | **1g** | Index vectoriel en mémoire. |
| `gateway` | **768m** | API FastAPI async (empreinte modérée). |

**Conséquence** : sous `mem_limit`, un conteneur qui dépasse sa limite est **tué par l'OOM killer (OOM kill ciblé du conteneur)**, et redémarré par `restart: unless-stopped` — au lieu de provoquer un **OOM de l'hôte entier** qui ferait tomber *tous* les services. C'est une mesure de **résilience par cloisonnement des ressources**. On surveille la consommation réelle avec `docker stats` et on ajuste `mem_limit` dans `docker-compose.yml` si un service est régulièrement tué.

### 6.5 Healthchecks et démarrage ordonné

Les `depends_on` conditionnés par `service_healthy` (et non un simple ordre de lancement) garantissent qu'un service ne démarre qu'une fois sa dépendance **réellement prête** : `gateway` attend `gateway-db`/`redis` *healthy*, `gateway-frontend` attend `gateway` *healthy*, et `midpoint`/`odoo`/`keycloak` attendent leur base respective. Couplé à `restart: unless-stopped`, ce mécanisme rend le démarrage **résilient** aux *races* d'initialisation et aux redémarrages de l'hôte, et évite qu'un service serve du trafic avant que ses dépendances ne répondent.

---

## 7. Guide de déploiement complet

### 7.1 Prérequis système

| Élément | Recommandation |
|---|---|
| Docker Desktop | ≥ 4.x (Compose v2) — backend WSL2 sous Windows |
| OS supportés | Windows (WSL2), macOS, Linux |
| RAM — stack minimale | ~2 Go (`gateway` + `gateway-db` + `redis`) |
| RAM — stack complète | **16 Go recommandés** (8 Go minimum ; MidPoint à lui seul jusqu'à 3 Go) |
| Espace disque (estimé) | ~8–10 Go pour les images + volumes selon l'usage (Odoo et MidPoint dominent) |

**Profils de déploiement :**

| Profil | Services | RAM indicative | Usage |
|---|---|---|---|
| **Minimal (dev)** | `gateway`, `gateway-db`, `redis` (+ `qdrant` via `depends_on`) | ~2 Go | API, UI, auth, règles, workflows — les appels MidPoint échouent gracieusement |
| **Complet (démo)** | les 14 services | 8–16 Go | Provisionnement de bout en bout, réconciliation, sync Odoo→MidPoint, webhook Keycloak |

### 7.2 Configuration initiale

```bash
# 1. Cloner le dépôt
git clone https://github.com/Nostradam4ik/IAM-Gateway.git
cd IAM-Gateway

# 2. Créer le fichier .env
copy .env.example .env   # Windows PowerShell
cp .env.example .env      # Linux / macOS

# 3. Générer les secrets (OBLIGATOIRE hors DEBUG)
python -c "import secrets; print(secrets.token_hex(32))"
# → coller la valeur dans SECRET_KEY
python -c "import secrets; print(secrets.token_hex(32))"
# → coller la valeur dans JWT_SECRET_KEY
```

> En production (`DEBUG=false`), la gateway **refuse de démarrer** si `SECRET_KEY`/`JWT_SECRET_KEY` est vide, trop court (< 32 caractères) ou égal à un placeholder connu (validateur *fail-fast* de `config.py`). `token_hex(32)` produit 64 caractères, conforme.

### 7.3 Stack minimale (développement)

```bash
docker compose up gateway gateway-db redis --build
```
Démarre l'API (`gateway`), sa base et Redis. Comme `gateway` déclare `depends_on` pour `gateway-db`, `redis` **et** `qdrant`, Compose démarre aussi Qdrant. API disponible sur **http://localhost:8000** (Swagger `/docs`). En dev, `DEBUG` vaut `true` par défaut (un secret éphémère est généré si absent). Démarrage : ~1 minute.

### 7.4 Stack complète (démonstration)

```bash
docker compose up --build
# Initialiser le schéma + le seed (une seule fois) :
docker compose exec -T gateway python -m app.db.migrations
```
**Ordre de démarrage** (via `depends_on` + healthchecks) : les bases (`*-postgres`, `*-db`) et `redis`/`qdrant` d'abord → puis `midpoint`, `odoo`, `keycloak` (chacun attend sa base *healthy*) → puis `gateway` (attend gateway-db, redis, qdrant) → enfin `gateway-frontend` (attend `gateway` *healthy*). **Durée estimée** : ~10 minutes (MidPoint et Odoo initialisent leur schéma au premier boot). **Vérification**, dans l'ordre :
1. `docker compose ps` — tous les conteneurs en *Up*, ceux à healthcheck en *healthy*.
2. `curl http://localhost:8000/health` — doit renvoyer `{"status": "healthy", …}`.
3. `docker compose logs gateway | tail` — absence d'erreurs de connexion (DB/Redis).
4. Accès UI sur http://localhost:3000 et login `admin` / `admin123`.
5. MidPoint accessible sur http://localhost:8080/midpoint (peut prendre 1–2 min de plus que la gateway).

### 7.5 URLs et identifiants (valeurs de développement)

| Service | URL | Login | Mot de passe |
|---|---|---|---|
| Frontend | http://localhost:3000 | `admin` | `admin123` |
| API / Swagger | http://localhost:8000 · `/docs` | `admin` | `admin123` (→ JWT via `/api/v1/admin/token`) |
| MidPoint | http://localhost:8080/midpoint | `administrator` | `5ecr3t` |
| Keycloak | http://localhost:8081 | `admin` | `admin` |
| Odoo | http://localhost:8069 | `admin` | `admin` |
| phpLDAPadmin | http://localhost:8088 | `cn=admin,dc=example,dc=com` | `secret` |
| Qdrant (dashboard) | http://localhost:6333/dashboard | — | — |

> Ce sont des **valeurs de développement**. Avant tout déploiement non local : changer chaque identifiant, fournir un vrai `.env`, placer un reverse-proxy TLS devant la gateway.

### Référence rapide des ports

| Port hôte | Service | Exposition |
|---|---|---|
| `3000` | frontend (UI nginx) | `0.0.0.0` |
| `8000` | gateway (API) | `0.0.0.0` |
| `8080` | MidPoint | `0.0.0.0` |
| `8081` | Keycloak | `0.0.0.0` |
| `8069` | Odoo | `0.0.0.0` |
| `8088` | phpLDAPadmin | `0.0.0.0` |
| `5434` / `5433` / `55432` | gateway-db / midpoint-postgres / intranet-db | `127.0.0.1` |
| `6379` | Redis | `127.0.0.1` |
| `6333` / `6334` | Qdrant (REST / gRPC) | `127.0.0.1` |
| `10389` / `10636` | OpenLDAP (LDAP / LDAPS) | `127.0.0.1` |

### 7.6 Commandes de maintenance

```bash
# Voir les logs en temps réel
docker compose logs -f gateway

# Redémarrer un service
docker compose restart gateway

# Voir l'état des conteneurs (santé incluse)
docker compose ps

# Arrêter sans perdre les données (volumes conservés)
docker compose down

# Arrêter ET supprimer les données (DESTRUCTIF — volumes supprimés)
docker compose down -v

# Reconstruire après modification du code
docker compose up gateway --build
```

### 7.7 Dépannage courant

| Symptôme | Cause probable | Résolution |
|---|---|---|
| `gateway` ne démarre pas (`RuntimeError` secret) | `SECRET_KEY`/`JWT_SECRET_KEY` vide ou faible avec `DEBUG=false` | Générer des secrets (§7.2) ou rester en `DEBUG=true` en dev |
| `bind: address already in use` | Un process occupe déjà 8000/3000/8080… sur l'hôte | Libérer le port ou modifier le mapping dans `docker-compose.yml` |
| Conteneur tué/redémarré en boucle | Dépassement de `mem_limit` (OOM kill ciblé) | Augmenter la limite (ex. MidPoint) ou libérer de la RAM hôte |
| Erreurs « relation/table does not exist » | Migrations non exécutées | `docker compose exec -T gateway python -m app.db.migrations` |
| `gateway-frontend` ne démarre pas | `gateway` jamais *healthy* (sonde KO) | `docker compose logs gateway` puis vérifier `/health` |
| Données disparues après un arrêt | `docker compose down -v` exécuté | Restaurer depuis une sauvegarde de volume (§7.8) |

### 7.8 Sauvegarde et restauration des volumes

Les volumes nommés se sauvegardent à chaud via un conteneur éphémère :
```bash
# Sauvegarde de la base gateway
docker run --rm -v gateway_db_data:/data -v "$PWD":/backup alpine \
  tar czf /backup/gateway_db_data.tgz -C /data .

# Restauration
docker run --rm -v gateway_db_data:/data -v "$PWD":/backup alpine \
  tar xzf /backup/gateway_db_data.tgz -C /data
```
À répéter pour chaque volume critique (`midpoint_postgres_data`, `qdrant_data`, `openldap_data`, …). Pour PostgreSQL, `pg_dump` via `docker compose exec` est une alternative cohérente et plus portable que l'archivage brut du volume.

### 7.9 Mise à jour et cycle de vie

```bash
# Récupérer les dernières images tirées (selon les tags du compose)
docker compose pull

# Reconstruire les images locales après changement de Dockerfile / dépendances
docker compose build --no-cache gateway gateway-frontend

# Appliquer : recrée uniquement les conteneurs dont l'image/config a changé
docker compose up -d
```
Après une évolution du schéma, rejouer les migrations (`docker compose exec -T gateway python -m app.db.migrations`, idempotent). Les **volumes étant préservés** par `pull`/`build`/`up`, les données survivent aux mises à jour d'images.

---

## 8. Observabilité et exploitation

- **Journaux structurés** : la gateway émet des logs **JSON** (structlog) sur la sortie standard → consultables via `docker compose logs -f gateway` et agrégeables (ELK, Grafana Loki). Chaque ligne porte un `request_id` de corrélation.
- **État de santé** : `docker compose ps` affiche la colonne *health* (les services dotés d'un healthcheck remontent `healthy`/`unhealthy`) ; l'endpoint `/health` expose l'état applicatif de la gateway.
- **Ressources** : `docker stats` montre la consommation CPU/mémoire par conteneur, à rapprocher des `mem_limit` (§6.4) pour anticiper un OOM kill.
- **Inspection** : `docker compose exec gateway sh` ouvre un shell dans le conteneur ; `docker inspect <conteneur>` révèle la configuration effective (réseau, montages, état de santé).

Exemple de ligne de log JSON émise par la gateway :
```json
{"event": "request", "request_id": "a1b2c3d4-…", "method": "POST",
 "path": "/api/v1/admin/token", "status_code": 200, "duration_ms": 42.7,
 "level": "info", "timestamp": "2026-06-21T10:15:03Z"}
```

---

## 9. Bonnes pratiques et limites pour la production

La stack est optimisée pour la **démonstration pédagogique** ; un passage en production exigerait :
- **TLS / reverse-proxy** devant la gateway et le frontend (aujourd'hui en HTTP clair) : terminaison TLS et redirection HTTPS.
- **Gestion des secrets** par un coffre (Docker secrets, Vault) plutôt que par `.env`, et **rotation** des identifiants de démonstration (`admin123`, `5ecr3t`, `admin/admin`).
- **Keycloak hors `start-dev`** : ce mode est explicitement non destiné à la production (utiliser `start` avec `hostname`/HTTPS configurés).
- **Segmentation réseau** : un seul `iam-network` aujourd'hui ; isoler les bases sur un réseau « backend » sans accès depuis le frontend renforcerait le cloisonnement.
- **Limites de ressources sur les bases** : PostgreSQL et Redis n'ont pas de `mem_limit` — à borner pour qu'une base ne puisse pas épuiser la RAM de l'hôte.
- **Code figé dans l'image** : le bind-mount `./gateway/app` (pratique en dev) doit être supprimé en production au profit du code copié dans l'image.
- **Healthchecks complémentaires** sur `midpoint`, `keycloak`, `odoo`, `qdrant`, `openldap` : des sondes amélioreraient l'ordonnancement et la détection de panne.

---

*Document généré dans le cadre du Projet 3 — IAM Gateway (SAE S5/S6, UPEC). Co-auteur référencé : `achibani@gmail.com`. Toutes les valeurs (ports, `mem_limit`, versions d'images, volumes, healthchecks) sont issues de `docker-compose.yml`, des `Dockerfile` et des `.dockerignore` du dépôt.*
