# Guide d'installation et de déploiement — IAM-Gateway

**Plateforme IAM multi-cibles · Docker Compose · Linux**

| | |
|---|---|
| **Projet** | IAM-Gateway — SAÉ « Projet 3 » |
| **Formation** | BUT Informatique, 3ᵉ année — UPEC |
| **Type de document** | Guide d'installation, d'exploitation et de déploiement |
| **Public visé** | Développeur Linux disposant des bases de Docker |
| **Auteurs** | Zhmuryk Andrii · Aydin Ibrahim |
| **Co-auteur (livrables générés)** | achibani@gmail.com |

> ⚠️ **À lire avant de commencer.** Ce guide décrit le déploiement réel tel que défini dans le `docker-compose.yml` du dépôt. Quelques valeurs affichées par le script `start.sh` sont **erronées** (port phpLDAPadmin, identifiants Gateway) ; ce guide indique les **valeurs correctes** et le signale par des encadrés. L'image MidPoint utilisée est `evolveum/midpoint:4.4`.

---

## Table des matières

1. [Prérequis système](#1-prérequis-système)
2. [Cloner et configurer le projet](#2-cloner-et-configurer-le-projet)
3. [Premier démarrage (l'ordre compte)](#3-premier-démarrage-lordre-compte)
4. [Initialisation des bases de données](#4-initialisation-des-bases-de-données)
5. [Configuration post-démarrage](#5-configuration-post-démarrage)
6. [Commandes utiles au quotidien](#6-commandes-utiles-au-quotidien)
7. [Résolution des problèmes courants](#7-résolution-des-problèmes-courants)
8. [Déploiement en production](#8-déploiement-en-production)
9. [Architecture réseau Docker](#9-architecture-réseau-docker)

---

# 1. Prérequis système

## 1.1 Système d'exploitation

IAM-Gateway est conçu pour tourner sur **Linux** avec Docker. Distributions recommandées et testées :

| OS | Version | Statut |
|---|---|---|
| Ubuntu | 22.04 LTS / 24.04 LTS | ✅ Recommandé |
| Debian | 12 (Bookworm) | ✅ Recommandé |
| Autres (Rocky, Alma, Fedora) | récentes | ⚙️ Compatible (adapter les commandes `apt`) |

> ℹ️ Le développement sous Windows/macOS est possible via Docker Desktop, mais ce guide cible un déploiement Linux (serveur dédié ou VM).

## 1.2 Ressources matérielles

La pile complète démarre **15 conteneurs**, dont plusieurs gros consommateurs (MidPoint sur JVM, Keycloak, Odoo, 5 instances PostgreSQL). Les limites mémoire déclarées dans `docker-compose.yml` totalisent à elles seules ~6 Go (MidPoint 3 Go, Odoo 1 Go, Keycloak 1 Go, Qdrant 1 Go, Gateway 768 Mo), auxquelles s'ajoutent les bases et le cache.

| Ressource | Minimum | Recommandé |
|---|---|---|
| **RAM** | 8 Go | 12–16 Go |
| **CPU** | 4 vCPU | 6–8 vCPU |
| **Disque** | 30 Go libres (SSD) | 50 Go+ (SSD) |
| **Réseau** | Accès Internet (pull images, Let's Encrypt) | — |

> ⚠️ **Avec moins de 8 Go de RAM, MidPoint sera tué par l'OOM-killer** au démarrage (voir [§7](#7-résolution-des-problèmes-courants)). Sur une VM 8 Go, fermez les autres applications et prévoyez du swap.

## 1.3 Docker Engine et Docker Compose

| Composant | Version minimale | Vérification |
|---|---|---|
| Docker Engine | **24.x** (20.10+ accepté) | `docker --version` |
| Docker Compose | **v2** (plugin `docker compose`) | `docker compose version` |

> ⚠️ Ce projet utilise la syntaxe **`docker compose`** (plugin v2, avec espace), **pas** l'ancien `docker-compose` (binaire v1). Vérifiez que `docker compose version` répond bien `v2.x`.

## 1.4 Installation de Docker sur Ubuntu / Debian

Installation depuis le dépôt officiel Docker (recommandée plutôt que le paquet de la distribution) :

```bash
# 1. Mettre à jour l'index des paquets et installer les prérequis
sudo apt-get update
sudo apt-get install -y ca-certificates curl gnupg

# 2. Ajouter la clé GPG officielle de Docker
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | \
  sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

# 3. Ajouter le dépôt Docker aux sources APT
#    (Pour Debian, remplacer "ubuntu" par "debian" dans l'URL ci-dessous)
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
  https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# 4. Installer Docker Engine + plugin Compose v2
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io \
  docker-buildx-plugin docker-compose-plugin

# 5. Permettre à votre utilisateur de lancer docker sans sudo
sudo usermod -aG docker "$USER"
newgrp docker   # ou se déconnecter/reconnecter
```

✅ **Vérification :**

```bash
docker --version            # Docker version 24.x ou +
docker compose version      # Docker Compose version v2.x
docker run --rm hello-world # doit afficher "Hello from Docker!"
```

## 1.5 Ports à ouvrir (firewall)

En déploiement sur serveur, **seuls les ports réellement publics doivent être ouverts**. Beaucoup de services sont volontairement liés à `127.0.0.1` dans le `docker-compose.yml` (voir [§9](#9-architecture-réseau-docker)) et ne nécessitent **aucune** règle firewall.

| Port | Service | Exposition compose | À ouvrir publiquement ? |
|---|---|---|---|
| 3000 | Frontend React (Nginx) | `0.0.0.0` | Oui (ou via reverse proxy) |
| 8000 | Gateway API (FastAPI) | `0.0.0.0` | Oui (ou via reverse proxy) |
| 8080 | MidPoint | `0.0.0.0` | Admin uniquement / reverse proxy |
| 8069 | Odoo | `0.0.0.0` | Selon besoin |
| 8081 | Keycloak | `0.0.0.0` | Oui si SSO public |
| 8088 | phpLDAPadmin | `0.0.0.0` | ❌ Non (admin interne) |
| 5433/5434/55432 | PostgreSQL | `127.0.0.1` | ❌ Jamais |
| 6379 | Redis | `127.0.0.1` | ❌ Jamais |
| 6333/6334 | Qdrant | `127.0.0.1` | ❌ Jamais |
| 10389/10636 | OpenLDAP | `127.0.0.1` | ❌ Jamais |

Configuration **UFW** typique pour un serveur exposant Gateway + Keycloak derrière un reverse proxy (voir [§8](#8-déploiement-en-production)) :

```bash
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp      # SSH (adaptez si port personnalisé)
sudo ufw allow 80/tcp      # HTTP (redirige vers HTTPS)
sudo ufw allow 443/tcp     # HTTPS (reverse proxy Nginx)
sudo ufw enable
sudo ufw status verbose
```

> ⚠️ En production, n'exposez **pas** directement les ports 3000/8000/8080/8069/8081. Placez-les derrière Nginx + TLS (voir [§8.3](#83-reverse-proxy-nginx)) et ne laissez ouverts que 80/443.

---

# 2. Cloner et configurer le projet

## 2.1 Récupérer le code

```bash
# Cloner le dépôt
git clone <URL_DU_DEPOT> iam-gateway
cd iam-gateway

# Vérifier la présence des fichiers clés
ls docker-compose.yml .env.example start.sh
```

## 2.2 Créer le fichier `.env`

Le fichier `.env.example` sert de modèle. Copiez-le en `.env` (jamais commité) :

```bash
cp .env.example .env
```

> ⚠️ **Comportement de sécurité au démarrage.** Lorsque `DEBUG=false` (mode production), l'application **refuse de démarrer** si `SECRET_KEY` ou `JWT_SECRET_KEY` est absent ou trop faible. En `DEBUG=true`, un secret jetable est généré automatiquement pour le développement local.

## 2.3 Générer les secrets

Générez une valeur forte et unique pour **chaque** secret :

```bash
# Générer un secret (à répéter pour chaque variable)
python3 -c "import secrets; print(secrets.token_urlsafe(48))"

# Astuce : injecter directement dans .env (exemple pour SECRET_KEY)
echo "SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_urlsafe(48))')" >> .env
```

Secrets **obligatoires** à renseigner :

| Variable | Rôle |
|---|---|
| `SECRET_KEY` | Clé de signature générale de l'application |
| `JWT_SECRET_KEY` | Signature des tokens JWT (HS256) |
| `MIDPOINT_WEBHOOK_SECRET` | Secret HMAC-SHA256 partagé pour signer/valider les webhooks MidPoint entrants |
| `MIDPOINT_PASSWORD` | Mot de passe du compte `administrator` MidPoint |
| `LDAP_BIND_PASSWORD` | Mot de passe du compte bind LDAP |
| `KEYCLOAK_CLIENT_SECRET` | Secret du client OIDC `gateway-client` (récupéré après config Keycloak, voir [§5.2](#52-keycloak--realm-et-client-oidc)) |

## 2.4 Variables d'environnement importantes

Le `.env.example` est organisé en sections. Voici les variables structurantes :

### Mode d'exécution

| Variable | Défaut (`.env.example`) | Description |
|---|---|---|
| `DEBUG` | `false` | `true` = mode dev (secrets auto, logs verbeux). **Mettre `false` en production.** |
| `DEV_MODE` | `false` | Active des facilités de développement. |
| `LOG_LEVEL` | `INFO` | Niveau de log (`DEBUG`/`INFO`/`WARNING`/`ERROR`). |

### Crypto / JWT

| Variable | Défaut | Description |
|---|---|---|
| `JWT_ALGORITHM` | `HS256` | Algorithme de signature JWT. |
| `JWT_EXPIRE_MINUTES` | `60` | Durée de validité d'un token. |
| `JWT_ISSUER` / `JWT_AUDIENCE` | `iam-gateway` | Émetteur / audience validés à chaque requête. |
| `BCRYPT_ROUNDS` | `12` | Coût bcrypt du hachage des mots de passe. |

### Datastores (noms DNS internes Docker)

| Variable | Valeur | Description |
|---|---|---|
| `DATABASE_URL` | `postgresql+asyncpg://gateway:gateway@gateway-db:5432/gateway` | Base `gateway` (driver async). |
| `REDIS_URL` | `redis://redis:6379/0` | Cache / blacklist JWT. |
| `QDRANT_HOST` / `QDRANT_PORT` | `qdrant` / `6333` | Base vectorielle d'audit. |

### Hub MidPoint et cibles

| Variable | Valeur | Description |
|---|---|---|
| `MIDPOINT_URL` | `http://midpoint-core:8080/midpoint` | URL interne du hub IGA. |
| `MIDPOINT_ENABLED` | `true` | Active le mode hub (`false` = provisionnement direct). |
| `LDAP_HOST` / `LDAP_PORT` / `LDAP_BASE_DN` | `openldap` / `389` / `dc=example,dc=com` | Annuaire cible. |
| `ODOO_URL` / `ODOO_DB` / `ODOO_USER` | `http://odoo:8069` / `odoo` / `admin` | ERP cible. |
| `INTRANET_DB_URL` | `postgresql://intranet:intranet@intranet-db:5432/intranet` | Base RH simulée. |
| `KEYCLOAK_URL` / `KEYCLOAK_REALM` / `KEYCLOAK_CLIENT_ID` | `http://keycloak:8080` / `gateway` / `gateway-client` | SSO/OIDC. |

### Intégrations optionnelles

| Variable | Description |
|---|---|
| `OPENAI_API_KEY` / `OPENAI_MODEL` / `DEEPSEEK_API_KEY` | Assistant IA (la plateforme fonctionne sans). |
| `SMTP_HOST` / `SMTP_PORT` / `SMTP_USER` / `SMTP_PASSWORD` / `FROM_EMAIL` | Envoi des emails d'approbation de workflow. |
| `BASE_URL` | URL publique de la Gateway (liens dans les emails). |
| `CORS_ORIGINS` | Tableau JSON des origines autorisées (ex. `["http://localhost:3000"]`). |

> ⚠️ **Limite connue du `docker-compose.yml` actuel.** Plusieurs mots de passe de bases (`gateway`, `midpoint`, `odoo`, `intranet`, `keycloak`) et l'admin MidPoint/Keycloak sont **codés en dur** dans `docker-compose.yml`, et les variables `POSTGRES_*_PASSWORD` du `.env.example` ne sont pas encore câblées dans le compose. En production, modifiez **directement** ces valeurs dans `docker-compose.yml` (voir [§8.2](#82-changer-tous-les-mots-de-passe-par-défaut)) en plus de remplir le `.env`.

---

# 3. Premier démarrage (l'ordre compte)

## 3.1 Pourquoi l'ordre est important

Le `docker-compose.yml` déclare des dépendances `depends_on` avec `condition: service_healthy`. Concrètement :

- La **Gateway** attend que `gateway-db` et `redis` soient *healthy* et que `qdrant` soit *démarré*.
- **MidPoint**, **Odoo** et **Keycloak** attendent que leur base PostgreSQL respective soit *healthy*.
- Le **frontend** attend que la **Gateway** soit *healthy*.

De plus, **MidPoint est très long à démarrer** (≈ 3 à 5 minutes : initialisation JVM + création/upgrade du schéma SQL). Démarrer tout d'un coup fonctionne grâce aux healthchecks, mais un démarrage **par étapes** évite les pics de charge et facilite le diagnostic.

## 3.2 Méthode A — script automatisé (recommandé)

Le script `start.sh` orchestre le démarrage en 4 étapes (bases → services IAM → Gateway → frontend) avec attentes et vérifications :

```bash
chmod +x start.sh
./start.sh                # démarrage standard
./start.sh --reset        # recrée les conteneurs (conserve les volumes)
./start.sh --logs         # suit les logs de la Gateway après démarrage
```

> ⚠️ Le récapitulatif final du script affiche des valeurs **inexactes** : phpLDAPadmin sur `8443` (réellement **8088**) et « Gateway admin/admin » (réellement **admin/admin123** côté API). Fiez-vous au présent guide.

## 3.3 Méthode B — démarrage manuel par étapes

Pour comprendre / déboguer, reproduisez les étapes à la main :

```bash
# --- Étape 1 : bases de données d'abord ---
docker compose up -d gateway-db midpoint-postgres odoo-db keycloak-db intranet-db

# Attendre que toutes les bases soient "healthy"
watch -n 3 'docker compose ps'   # Ctrl+C quand les 5 bases sont healthy

# --- Étape 2 : services IAM (MidPoint est le plus lent) ---
docker compose up -d openldap phpldapadmin keycloak odoo midpoint

# Suivre la montée en charge de MidPoint (3-5 min)
docker compose logs -f midpoint   # attendre "Started..." / écoute sur 8080

# --- Étape 3 : cache, vecteurs, puis la Gateway ---
docker compose up -d redis qdrant gateway

# --- Étape 4 : frontend ---
docker compose up -d gateway-frontend
```

✅ **Vérification du démarrage complet :**

```bash
# Tous les conteneurs doivent être "running" / "healthy"
docker compose ps

# La Gateway doit répondre 200
curl -s http://localhost:8000/health
# → {"status":"healthy","version":"1.0.0","service":"Gateway IAM"}
```

> ℹ️ Le premier `docker compose up` télécharge et **construit** les images `gateway` et `gateway-frontend` (Dockerfile local). Comptez quelques minutes supplémentaires la première fois.

---

# 4. Initialisation des bases de données

Trois mécanismes d'initialisation coexistent, dont **un seul est manuel**.

## 4.1 Base `intranet` — automatique

La base RH simulée est initialisée **automatiquement** au tout premier démarrage du conteneur `intranet-db`, grâce au montage du script SQL dans le répertoire d'init de l'image PostgreSQL :

```yaml
# docker-compose.yml (extrait)
volumes:
  - ./infrastructure/sql/init-intranet.sql:/docker-entrypoint-initdb.d/init.sql:ro
```

> ℹ️ PostgreSQL n'exécute les scripts de `/docker-entrypoint-initdb.d/` **que si le volume de données est vide** (premier boot). Pour rejouer le script, il faut supprimer le volume `intranet_db_data` (voir [§7.5](#75-réinitialiser-une-base)).

✅ **Vérification :**

```bash
docker compose exec intranet-db psql -U intranet -d intranet -c "\dt"
# → doit lister : users, permissions, groups, user_groups, ...
```

## 4.2 Schéma MidPoint — automatique

MidPoint crée/migre son propre schéma à son premier démarrage, piloté par ces variables du compose :

```yaml
- MP_SET_midpoint_repository_missingSchemaAction=create     # crée le schéma s'il manque
- MP_SET_midpoint_repository_upgradeableSchemaAction=upgrade # migre si nécessaire
```

✅ **Vérification que MidPoint a créé ses tables :**

```bash
docker compose exec midpoint-postgres psql -U midpoint -d midpoint \
  -c "SELECT count(*) FROM information_schema.tables WHERE table_name LIKE 'm_%';"
# → un nombre > 0 (tables m_user, m_role, m_resource, m_shadow, ...)
```

## 4.3 Base `gateway` — migration manuelle (à lancer une fois)

⚠️ **La base `gateway` n'est PAS initialisée automatiquement.** Après le premier démarrage, exécutez les migrations (création des 22 tables + enums + seed) :

```bash
# Méthode A : script fourni
./scripts/init-db.sh

# Méthode B : équivalent direct
docker compose exec -T gateway python -m app.db.migrations
```

✅ **Vérification des tables `gateway` :**

```bash
docker compose exec gateway-db psql -U gateway -d gateway -c "\dt"
# → provisioning_operations, audit_logs, workflows, rules,
#   connector_configurations, gateway_users, ...
```

✅ **Vérification de l'utilisateur d'API seedé :**

```bash
docker compose exec gateway-db psql -U gateway -d gateway \
  -c "SELECT username, role FROM gateway_users;"
# → admin
```

---

# 5. Configuration post-démarrage

Une fois la pile démarrée et la base `gateway` migrée, configurez les composants externes.

## 5.1 MidPoint (http://localhost:8080)

1. Connectez-vous avec les identifiants par défaut :
   - **Utilisateur :** `administrator`
   - **Mot de passe :** `5ecr3t`

   > ⚠️ **Changez immédiatement ce mot de passe** (par défaut public d'Evolveum). Mettez à jour `MIDPOINT_PASSWORD` dans `.env` en conséquence puis redémarrez la Gateway. Un script utilitaire existe : `scripts/change-midpoint-password.py`.

2. Importez les ressources cibles (LDAP, Odoo, Intranet) depuis les définitions XML du dépôt :
   - Via l'UI : **Configuration → Import object**, puis chargez les fichiers de `infrastructure/midpoint/`.
   - Ou via le script : `scripts/import-midpoint-config.sh`.

✅ Les ressources importées apparaissent dans **Resources → All resources**, à l'état « Up ».

## 5.2 Keycloak — realm et client OIDC (http://localhost:8081)

1. Connectez-vous à la console d'administration : **`admin` / `admin`** (défaut du compose, en mode `start-dev`).

   > ⚠️ À changer en production (`KEYCLOAK_ADMIN` / `KEYCLOAK_ADMIN_PASSWORD`).

2. **Créer le realm** : menu déroulant en haut à gauche → *Create realm* → nom **`gateway`** (doit correspondre à `KEYCLOAK_REALM`).

3. **Créer le client** : *Clients → Create client*
   - *Client ID* : **`gateway-client`** (doit correspondre à `KEYCLOAK_CLIENT_ID`)
   - *Client authentication* : **On** (client confidentiel)
   - *Valid redirect URIs* : l'URL de votre Gateway (ex. `http://localhost:8000/*`)

4. **Récupérer le secret** : onglet *Credentials* du client → copier *Client secret*.

5. Renseignez-le dans `.env` :

```bash
# .env
KEYCLOAK_CLIENT_SECRET=<le-secret-copié-depuis-keycloak>
```

6. Redémarrez la Gateway pour prise en compte :

```bash
docker compose up -d --force-recreate gateway
```

## 5.3 Gateway API (http://localhost:8000/docs)

1. Ouvrez la documentation interactive **Swagger UI** : <http://localhost:8000/docs>.
2. Authentifiez-vous via `POST /api/v1/admin/token` :
   - **Utilisateur :** `admin`
   - **Mot de passe :** `admin123`

   > ⚠️ Identifiant d'API correct = **`admin` / `admin123`** (et non `admin/admin` affiché par `start.sh`).

3. Testez l'endpoint de santé :

```bash
curl -s http://localhost:8000/health
# ✅ {"status":"healthy","version":"1.0.0","service":"Gateway IAM"}
```

## 5.4 Autres interfaces

| Service | URL | Identifiants par défaut | Note |
|---|---|---|---|
| **Frontend React** | http://localhost:3000 | `admin` / `admin123` | Console d'administration. |
| **phpLDAPadmin** | http://localhost:8088 | `cn=admin,dc=example,dc=com` / `secret` | HTTP (pas HTTPS). |
| **Odoo** | http://localhost:8069 | `admin` / `admin` | Création de la base au 1ᵉʳ accès. |
| **MidPoint** | http://localhost:8080 | `administrator` / `5ecr3t` | À sécuriser. |
| **Keycloak** | http://localhost:8081 | `admin` / `admin` | À sécuriser. |

> ⚠️ Le DN d'admin LDAP est **`cn=admin,dc=example,dc=com`** avec le mot de passe **`secret`** (valeurs du `docker-compose.yml`), et **non** `dc=example,dc=org` / `admin` comme l'affiche `start.sh`.

---

# 6. Commandes utiles au quotidien

## 6.1 Cycle de vie des services

```bash
# Démarrer / arrêter toute la pile
docker compose up -d
docker compose stop                  # stoppe sans supprimer les conteneurs
docker compose down                  # supprime les conteneurs (garde les volumes)
docker compose down --remove-orphans # + supprime les conteneurs orphelins

# Redémarrer UN service sans toucher au reste
docker compose restart gateway
docker compose up -d --force-recreate gateway   # recrée (prend en compte .env modifié)
```

> ⚠️ **`docker compose down -v` supprime les volumes** → perte de TOUTES les données (bases, MidPoint, LDAP). À n'utiliser qu'en connaissance de cause.

## 6.2 Logs

```bash
# Logs de tous les services (suivi en direct)
docker compose logs -f

# Logs d'un service précis (100 dernières lignes puis suivi)
docker compose logs -f --tail=100 gateway
docker compose logs -f midpoint     # utile pour suivre le long démarrage

# Logs depuis un horodatage
docker compose logs --since 10m gateway
```

## 6.3 Statut et santé

```bash
# Vue d'ensemble (statut + santé de chaque conteneur)
docker compose ps

# Statut de santé détaillé d'un conteneur
docker inspect --format '{{.State.Health.Status}}' gateway-iam

# Ressources consommées en temps réel
docker stats --no-stream
```

## 6.4 Accès aux bases PostgreSQL (CLI)

```bash
# Base gateway
docker compose exec gateway-db psql -U gateway -d gateway

# Base MidPoint
docker compose exec midpoint-postgres psql -U midpoint -d midpoint

# Base intranet (RH simulée)
docker compose exec intranet-db psql -U intranet -d intranet

# Exemple de requête directe (sans session interactive)
docker compose exec gateway-db psql -U gateway -d gateway \
  -c "SELECT id, status FROM provisioning_operations ORDER BY created_at DESC LIMIT 5;"
```

## 6.5 Redis

```bash
# Ouvrir une session redis-cli
docker compose exec redis redis-cli

# Vider tout le cache Redis (sessions + blacklist JWT)
docker compose exec redis redis-cli FLUSHALL

# Inspecter les clés
docker compose exec redis redis-cli KEYS '*'
```

> ⚠️ `FLUSHALL` invalide la blacklist des tokens révoqués et toutes les sessions : tous les utilisateurs devront se reconnecter.

## 6.6 Exécuter une commande dans un conteneur

```bash
# Shell dans la Gateway
docker compose exec gateway bash

# Relancer les migrations de la base gateway
docker compose exec -T gateway python -m app.db.migrations
```

---

# 7. Résolution des problèmes courants

## 7.1 MidPoint ne démarre pas (OOM / base non prête)

**Symptômes :** le conteneur `midpoint-core` redémarre en boucle, ou les logs s'arrêtent brutalement (`Killed`).

```bash
docker compose logs --tail=80 midpoint
docker inspect midpoint-core --format '{{.State.OOMKilled}}'   # → true = manque de RAM
```

**Causes & solutions :**
- **Manque de RAM** (OOM-killed) : MidPoint a une `mem_limit: 3g` et une JVM jusqu'à 2 Go (`MP_MEM_MAX=2048m`). Libérez de la RAM, ajoutez du swap, ou réduisez `MP_MEM_MAX`/`mem_limit` (au prix de la stabilité).
- **Base pas encore prête** : MidPoint dépend de `midpoint-postgres` *healthy*. Vérifiez la base d'abord :

```bash
docker compose ps midpoint-postgres
docker compose logs midpoint-postgres
```

- **Démarrage simplement long** : patientez 3 à 5 minutes. MidPoint n'a **pas** de healthcheck déclaré — surveillez les logs jusqu'à l'écoute sur `:8080`.

## 7.2 Port déjà utilisé

**Symptôme :** `Error ... bind: address already in use`.

```bash
# Identifier le processus occupant le port (ex. 8080)
sudo ss -ltnp | grep ':8080'

# Soit libérer le port, soit changer le mapping dans docker-compose.yml :
#   ports: ["8082:8080"]   # exposer MidPoint sur 8082 côté hôte
```

## 7.3 La Gateway échoue au healthcheck

**Symptôme :** `gateway-iam` reste `unhealthy` ; le frontend ne démarre pas (il dépend de la Gateway *healthy*).

```bash
docker compose logs --tail=100 gateway

# Tester le endpoint manuellement
docker compose exec gateway python -c \
  "import urllib.request; print(urllib.request.urlopen('http://localhost:8000/health').getcode())"
```

**Causes fréquentes :**
- Migrations non exécutées → lancez `./scripts/init-db.sh`.
- `gateway-db` ou `redis` indisponibles → `docker compose ps`.
- `DEBUG=false` avec `SECRET_KEY`/`JWT_SECRET_KEY` manquants → l'app refuse de démarrer (voir logs). Renseignez les secrets dans `.env`.

> ℹ️ La Gateway bénéficie d'un `start_period: 40s` : elle n'est pas marquée *unhealthy* pendant les 40 premières secondes.

## 7.4 Keycloak ne se connecte pas à sa base

**Symptôme :** `keycloak` redémarre, logs `Failed to connect to keycloak-db`.

```bash
docker compose ps keycloak-db
docker compose logs keycloak-db
docker compose logs --tail=50 keycloak
```

**Solution :** s'assurer que `keycloak-db` est *healthy* (Keycloak en dépend). En cas de corruption du volume, réinitialiser la base (voir §7.5). Vérifier la cohérence `KC_DB_URL` / `KC_DB_USERNAME` / `KC_DB_PASSWORD`.

## 7.5 Réinitialiser une base

Pour rejouer l'init (`intranet`) ou repartir propre sur une base corrompue, supprimez son volume :

```bash
# Exemple : réinitialiser l'intranet
docker compose stop intranet-db
docker compose rm -f intranet-db
docker volume rm iam-gateway_intranet_db_data   # nom = <projet>_<volume>
docker compose up -d intranet-db                 # rejoue init-intranet.sql
```

```bash
# Lister les volumes du projet pour trouver le nom exact
docker volume ls | grep -i intranet
```

> ⚠️ Cette opération **détruit les données** de la base concernée. À réserver au dev / à un incident.

## 7.6 Problèmes de permissions sur les volumes

**Symptôme :** un service (souvent Odoo ou un PostgreSQL) échoue avec `Permission denied` sur `/var/lib/...`.

```bash
# Inspecter le point de montage et le propriétaire
docker compose exec odoo ls -la /var/lib/odoo

# Solution générale : laisser Docker gérer les volumes nommés (déjà le cas ici).
# Pour le bind-mount ./gateway/app, s'assurer qu'il est lisible :
ls -la gateway/app
```

Pour les volumes nommés (cas par défaut de ce projet), Docker gère les permissions ; évitez de bind-monter des dossiers hôte avec un propriétaire incompatible.

---

# 8. Déploiement en production

## 8.1 Différences clés avec le dev local

| Aspect | Dev local | Production |
|---|---|---|
| `DEBUG` / `DEV_MODE` | `true` | **`false`** |
| Secrets | auto-générés si absents | **obligatoires et forts** |
| Code Gateway | bind-mount `./gateway/app` (live reload) | **image figée** (retirer le bind-mount) |
| Exposition réseau | ports en clair sur l'hôte | **reverse proxy + TLS**, ports applicatifs non publics |
| Mots de passe | valeurs par défaut | **tous changés** |
| Sauvegardes | aucune | **pg_dump planifié** |

> ⚠️ En production, retirez le montage `./gateway/app:/app/app` du service `gateway` dans `docker-compose.yml` (ou utilisez un fichier `docker-compose.prod.yml` en *override*). Ce bind-mount sert au rechargement de code en développement et écrase le code de l'image.

## 8.2 Changer TOUS les mots de passe par défaut

Le `docker-compose.yml` contient de nombreuses valeurs par défaut **publiques** à remplacer impérativement :

| Emplacement | Valeur par défaut | Action |
|---|---|---|
| `gateway-db` | `gateway` / `gateway` | Changer `POSTGRES_PASSWORD` **et** `DATABASE_URL` (compose + `.env`). |
| `midpoint-postgres` | `midpoint` / `midpoint` | Changer + `MP_SET_..._jdbcPassword`. |
| `odoo-db` / `odoo` | `odoo` / `odoo` | Changer + `ODOO_PASSWORD`. |
| `intranet-db` | `intranet` / `intranet` | Changer + `INTRANET_DB_URL`. |
| `keycloak-db` | `keycloak` / `keycloak` | Changer + `KC_DB_PASSWORD`. |
| MidPoint admin | `administrator` / `5ecr3t` | Changer dans l'UI MidPoint + `MIDPOINT_PASSWORD`. |
| Keycloak admin | `admin` / `admin` | `KEYCLOAK_ADMIN_PASSWORD`. |
| OpenLDAP admin | `cn=admin...` / `secret` | `LDAP_ADMIN_PASSWORD` + `LDAP_BIND_PASSWORD`. |
| MidPoint keystore | `changeit` | `MP_SET_midpoint_keystore_keyStorePassword`. |
| Compte API Gateway | `admin` / `admin123` | Changer le mot de passe dans `gateway_users`. |

> ⚠️ **Cohérence indispensable :** un mot de passe de base apparaît à **deux endroits** (la variable `POSTGRES_PASSWORD` du conteneur de base **et** l'URL de connexion du client). Les deux doivent correspondre, sinon le service ne se connecte plus.

Idéalement, paramétrez ces valeurs via des variables `.env` (en complétant `docker-compose.yml` pour lire `${POSTGRES_GATEWAY_PASSWORD}` etc.) afin de ne plus stocker de secret en clair dans le compose.

## 8.3 Reverse proxy Nginx

Placez un Nginx (sur l'hôte ou en conteneur) devant les services applicatifs. N'exposez publiquement que 80/443.

```nginx
# /etc/nginx/sites-available/iam-gateway.conf

# Frontend + API Gateway
server {
    listen 443 ssl http2;
    server_name iam.example.com;

    ssl_certificate     /etc/letsencrypt/live/iam.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/iam.example.com/privkey.pem;

    # API → conteneur gateway (port hôte 8000)
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host              $host;
        proxy_set_header X-Real-IP         $remote_addr;
        proxy_set_header X-Forwarded-For   $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Frontend React → conteneur gateway-frontend (port hôte 3000)
    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_set_header Host $host;
    }
}

# Keycloak (sous-domaine dédié)
server {
    listen 443 ssl http2;
    server_name auth.example.com;

    ssl_certificate     /etc/letsencrypt/live/auth.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/auth.example.com/privkey.pem;

    location / {
        proxy_pass http://127.0.0.1:8081;
        proxy_set_header Host              $host;
        proxy_set_header X-Forwarded-For   $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;   # requis par KC_PROXY=edge
    }
}
```

```bash
# Activer le site et recharger Nginx
sudo ln -s /etc/nginx/sites-available/iam-gateway.conf /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

> ℹ️ Pensez à mettre à jour `BASE_URL`, `CORS_ORIGINS` et les *Valid redirect URIs* Keycloak avec les URLs HTTPS publiques. Keycloak est déjà en `KC_PROXY=edge`, adapté à la terminaison TLS par Nginx.

## 8.4 SSL/TLS avec Let's Encrypt

```bash
# Installer certbot
sudo apt-get install -y certbot python3-certbot-nginx

# Obtenir et installer les certificats (Nginx déjà configuré)
sudo certbot --nginx -d iam.example.com -d auth.example.com

# Le renouvellement automatique est installé via un timer systemd ; tester :
sudo certbot renew --dry-run
```

✅ Après émission, `https://iam.example.com` et `https://auth.example.com` répondent en TLS, et le renouvellement est automatique.

## 8.5 Sauvegardes automatiques des bases PostgreSQL

Script de sauvegarde des 5 bases via `pg_dump` dans les conteneurs :

```bash
#!/bin/bash
# /opt/iam-gateway/backup.sh — sauvegarde des bases IAM-Gateway
set -euo pipefail

BACKUP_DIR="/var/backups/iam-gateway"
STAMP="$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

# Format : "conteneur:utilisateur:base"
DBS=(
  "gateway-db:gateway:gateway"
  "midpoint-postgres:midpoint:midpoint"
  "odoo-db:odoo:odoo"
  "intranet-db:intranet:intranet"
  "keycloak-db:keycloak:keycloak"
)

for entry in "${DBS[@]}"; do
  IFS=':' read -r container user db <<< "$entry"
  out="$BACKUP_DIR/${db}_${STAMP}.sql.gz"
  echo "Sauvegarde $db → $out"
  docker exec "$container" pg_dump -U "$user" "$db" | gzip > "$out"
done

# Rétention : supprimer les sauvegardes de plus de 14 jours
find "$BACKUP_DIR" -name '*.sql.gz' -mtime +14 -delete
echo "Sauvegarde terminée : $STAMP"
```

Planification via **cron** (sauvegarde quotidienne à 2 h du matin) :

```bash
sudo chmod +x /opt/iam-gateway/backup.sh
sudo crontab -e
# Ajouter la ligne :
0 2 * * * /opt/iam-gateway/backup.sh >> /var/log/iam-backup.log 2>&1
```

**Restauration** d'une base à partir d'un dump :

```bash
gunzip -c /var/backups/iam-gateway/gateway_20260625_020000.sql.gz | \
  docker exec -i gateway-db psql -U gateway -d gateway
```

> ⚠️ Pensez aussi à sauvegarder le volume `midpoint_home` (keystore `keystore.jceks` et configuration) : sans lui, MidPoint ne pourra pas déchiffrer ses secrets même après restauration de la base.

```bash
# Sauvegarde du volume midpoint_home
docker run --rm -v iam-gateway_midpoint_home:/data -v /var/backups/iam-gateway:/backup \
  alpine tar czf /backup/midpoint_home_$(date +%Y%m%d).tar.gz -C /data .
```

## 8.6 Monitoring basique

```bash
# Consommation CPU/RAM/IO en continu
docker stats

# Snapshot ponctuel (scriptable)
docker stats --no-stream --format \
  "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}"

# Surveiller la santé des conteneurs
watch -n 5 'docker compose ps'
```

> ℹ️ Pour un monitoring durable, branchez un stack Prometheus + Grafana via `cAdvisor` et `node-exporter`, et exploitez l'endpoint `/health` de la Gateway dans une sonde externe (Uptime Kuma, etc.).

---

# 9. Architecture réseau Docker

## 9.1 Le réseau `iam-network`

Tous les conteneurs sont rattachés à un unique réseau bridge nommé **`iam-network`**. À l'intérieur de ce réseau, Docker fournit une **résolution DNS interne** : chaque service est joignable par son **nom de service** (ou `container_name`). C'est pourquoi les variables d'environnement utilisent des hôtes comme `gateway-db`, `redis`, `midpoint-core`, `openldap` plutôt que des adresses IP.

```
┌──────────────────────────────────────────────────────────────────────────┐
│                         Réseau Docker : iam-network (bridge)               │
│                                                                            │
│   ┌────────────┐     ┌──────────────┐      ┌──────────────────┐           │
│   │  frontend  │────▶│   gateway    │─────▶│  midpoint-core   │           │
│   │ (Nginx :80)│     │ (FastAPI     │      │  (:8080)         │           │
│   └────────────┘     │   :8000)     │      └────────┬─────────┘           │
│                      └───┬───┬───┬──┘               │                      │
│           ┌──────────────┘   │   └──────────┐       │ (rôles → cibles)     │
│           ▼                  ▼              ▼        ▼                      │
│     ┌──────────┐      ┌──────────┐   ┌──────────┐  ┌──────────┐           │
│     │gateway-db│      │  redis   │   │  qdrant  │  │ openldap │           │
│     │  :5432   │      │  :6379   │   │  :6333   │  │  :389    │           │
│     └──────────┘      └──────────┘   └──────────┘  └──────────┘           │
│                                                                            │
│     ┌──────────┐  ┌──────────┐  ┌────────────┐  ┌──────────┐  ┌─────────┐ │
│     │   odoo   │  │ odoo-db  │  │ intranet-db│  │ keycloak │  │keycloak-│ │
│     │  :8069   │  │  :5432   │  │   :5432    │  │  :8080   │  │  db     │ │
│     └──────────┘  └──────────┘  └────────────┘  └──────────┘  └─────────┘ │
│     ┌──────────────┐  ┌──────────────────┐                                │
│     │midpoint-     │  │   phpldapadmin   │                                │
│     │postgres :5432│  │      :80         │                                │
│     └──────────────┘  └──────────────────┘                                │
└──────────────────────────────────────────────────────────────────────────┘
        │ ports publiés vers l'hôte (voir tableau ci-dessous)
        ▼
   Hôte Linux  ── (firewall UFW) ──▶  Internet
```

## 9.2 Ports exposés et politique d'exposition

Le `docker-compose.yml` distingue deux types de publication de ports :

- **`0.0.0.0:<port>`** (implicite quand on écrit `"8000:8000"`) : le port est accessible depuis **n'importe quelle interface réseau** de l'hôte → potentiellement depuis Internet.
- **`127.0.0.1:<port>`** : le port n'est accessible que depuis **l'hôte lui-même** (loopback) → invisible de l'extérieur, même sans firewall.

| Service | Mapping (hôte → conteneur) | Liaison | Justification |
|---|---|---|---|
| `gateway-frontend` | 3000 → 80 | `0.0.0.0` | Interface utilisateur, doit être accessible. |
| `gateway` | 8000 → 8000 | `0.0.0.0` | API consommée par le frontend / clients. |
| `midpoint` | 8080 → 8080 | `0.0.0.0` | Console d'admin IGA. |
| `odoo` | 8069 → 8069 | `0.0.0.0` | ERP. |
| `keycloak` | 8081 → 8080 | `0.0.0.0` | SSO/OIDC. |
| `phpldapadmin` | 8088 → 80 | `0.0.0.0` | Admin LDAP (à ne PAS publier en prod). |
| `gateway-db` | 5434 → 5432 | **`127.0.0.1`** | Base interne : aucun accès externe nécessaire. |
| `midpoint-postgres` | 5433 → 5432 | **`127.0.0.1`** | Base interne. |
| `intranet-db` | 55432 → 5432 | **`127.0.0.1`** | Base interne. |
| `redis` | 6379 → 6379 | **`127.0.0.1`** | Cache : ne jamais exposer (pas d'auth par défaut). |
| `qdrant` | 6333/6334 | **`127.0.0.1`** | Base vectorielle interne. |
| `openldap` | 10389/10636 | **`127.0.0.1`** | Annuaire : accès via la Gateway/MidPoint uniquement. |
| `odoo-db` / `keycloak-db` | — | non publié | Accessibles **uniquement** dans `iam-network`. |

> ✅ **Bonne pratique appliquée :** les bases de données, Redis, Qdrant et LDAP sont liés à `127.0.0.1` (ou non publiés). Ils communiquent avec les applications **via le réseau interne `iam-network`**, sans jamais être exposés sur le réseau public. C'est une mesure de défense en profondeur : même une mauvaise configuration de firewall ne les rendra pas accessibles depuis Internet.

## 9.3 Communication inter-services (résolution DNS)

Exemples de noms DNS internes utilisés dans la configuration :

| Depuis | Vers | Adresse interne utilisée |
|---|---|---|
| Gateway | Base `gateway` | `gateway-db:5432` |
| Gateway | Redis | `redis:6379` |
| Gateway | Qdrant | `qdrant:6333` |
| Gateway | MidPoint | `midpoint-core:8080` |
| Gateway | LDAP | `openldap:389` |
| Gateway | Odoo | `odoo:8069` |
| Gateway | Intranet | `intranet-db:5432` |
| Gateway | Keycloak | `keycloak:8080` |
| MidPoint | Sa base | `midpoint-postgres:5432` |
| Keycloak | Sa base | `keycloak-db:5432` |

> ℹ️ Le port **interne** d'un PostgreSQL est toujours `5432`, quel que soit le port publié côté hôte (5433/5434/55432). De même, Keycloak écoute en interne sur `8080` bien qu'il soit publié sur `8081`. Ne confondez pas port interne (DNS Docker) et port publié (hôte).

---

*Document généré dans le cadre de la SAÉ Projet 3 — BUT Informatique 3ᵉ année, UPEC.*
*Auteurs : Zhmuryk Andrii, Aydin Ibrahim. Co-auteur des livrables : achibani@gmail.com.*
