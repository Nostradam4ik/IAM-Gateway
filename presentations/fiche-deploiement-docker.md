---
title: "Fiche de Déploiement : Packages Docker en Production"
author: "Andrii Zhmuryk"
date: "1er mars 2026"
---

# Fiche de Déploiement : Packages Docker
## Déploiement de l'Infrastructure IAM Gateway

**Projet** : SAE S5/S6 - Passerelle de Provisionnement IAM Intelligente  
**Auteurs** : Andrii Zhmuryk, Aydin Ibrahim, Abdelghani Chibani
**Contact** : andrijzmurik@gmail.com  
**Dépôt GitHub** : [https://github.com/Nostradam4ik/IAM-Gateway](https://github.com/Nostradam4ik/IAM-Gateway)  

*Note aux étudiants de 2ème année : Cette fiche technique documente la structure de l'infrastructure Docker du projet IAM-Gateway et vous guide pas-à-pas pour la déployer sur vos environnements locaux ou serveurs de test.*

---

## 1. Vue d'Ensemble de l'Infrastructure Docker

L'architecture s'appuie sur le paradigme des **Microservices** conteneurisés. Le fichier `docker-compose.yml` gère l'orchestration de l'ensemble de la stack technique répartie sur un réseau Docker privé isolé (`iam-network`).

### 1.1. Les 4 Piliers de la Stack

L'infrastructure déploie simultanément **13 conteneurs** répartis en quatre domaines :

1. **Le Cœur (Core IAM)**
   - `gateway` : L'API FastAPI développée en Python (le cerveau du projet).
   - `gateway-frontend` : L'interface web de gestion (React/Nginx).
   - `midpoint` : Evolveum MidPoint, le système source de vérité IAM.

2. **Bases de données & Cache (Stockage)**
   - `gateway-db` : PostgreSQL gérant l'audit trail et les transactions de la Gateway.
   - `midpoint-postgres` : PostgreSQL dédié au stockage natif de MidPoint.
   - `redis` : Gestionnaire de file d'attente asynchrone (Message Broker).
   - `qdrant` : Base de données vectorielle gérant la recherche sémantique des logs par l'IA.

3. **Sécurité & Authentification**
   - `keycloak` : Identity Provider (IdP) OIDC gérant l'authentification sécurisée des utilisateurs et admins.
   - `keycloak-db` : PostgreSQL stockant les configurations du Keycloak.

4. **Applications Cibles (Simulations pour les tests)**
   - `openldap` : Annuaire d'entreprise cible simulé.
   - `phpldapadmin` : Interface graphique pour visualiser l'annuaire LDAP.
   - `odoo` & `odoo-db` : ERP cible de provisionnement d'entreprise.
   - `intranet-db` : Base SQL applicative tierce.

---

## 2. Le fichier `Dockerfile` (L'Application Gateway)

Le fichier Dockerfile définit la recette de construction de notre application FastAPI. Il a été optimisé pour la production.

### 2.1. Explication du code source

```dockerfile
# Utilisation d'une image Python optimisée et légère
FROM python:3.11-slim

# Création d'un répertoire de travail
WORKDIR /app

# Sécurité : création d'un utilisateur non-root
RUN adduser --disabled-password --gecos '' gateway_user

# Installation des dépendances système nécessaires à certains packages Python
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    python3-dev \
    libldap2-dev \
    libsasl2-dev \
    && rm -rf /var/lib/apt/lists/*

# Copie exclusive du fichier des dépendances (optimisation du cache Docker)
COPY requirements.txt .

# Installation des paquets Python
RUN pip install --no-cache-dir -r requirements.txt

# Copie du code source complet
COPY . .

# Définition des permissions pour l'utilisateur non-root
RUN chown -R gateway_user:gateway_user /app
USER gateway_user

# Exposition du port
EXPOSE 8000

# Commande de lancement asynchrone Uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

### 2.2. Points Clés pour l'Étudiant

1. **Sécurité (User non-root)** : La directive `USER gateway_user` empêche l'application d'exécuter des commandes administrateur sur l'hôte en cas de compromission.
2. **Optimisation du cache (Layers)** : L'instruction `COPY requirements.txt` est volontairement séparée de `COPY . .`. Si vous modifiez un fichier Python sans modifier vos dépendances, Docker ne reconstruira pas l'image depuis zéro (gain de temps immense lors du développement).
3. **Serveur ASGI** : Uvicorn est lancé avec `--workers 4`, permettant de gérer de multiples requêtes simultanément.

---

## 3. Le fichier `docker-compose.yml`

C'est le chef d'orchestre. Voici la méthode de déclaration standard utilisée pour lier les applications.

### 3.1. Exemple de déclaration : Le service Gateway

```yaml
  gateway:
    build:
      context: ./gateway
      dockerfile: Dockerfile
    container_name: gateway-iam
    depends_on:
      gateway-db:
        condition: service_healthy
      redis:
        condition: service_healthy
      qdrant:
        condition: service_started
    environment:
      DEBUG: "false"
      DATABASE_URL: postgresql+asyncpg://gateway:gateway@gateway-db:5432/gateway
      REDIS_URL: redis://redis:6379/0
      # ... Configuration des API externes et secrets
    ports:
      - "8000:8000"
    volumes:
      - ./gateway/app:/app/app      # Hot-reload local
      - gateway_logs:/app/logs      # Persistance des logs
    networks:
      - iam-network
```

### 3.2. Mécanisme de `depends_on` et Healthchecks

Un point fondamental de cette architecture réside dans les `healthchecks`.
La Gateway FastAPI a besoin que la base de données PostgreSQL soit *réellement* prête à recevoir des connexions (et pas seulement démarrée).

C'est pourquoi `gateway-db` inclut un healthcheck natif :
```yaml
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U gateway"]
      interval: 10s
      timeout: 5s
```
Ce mécanisme évite les erreurs critiques de connexion au démarrage du cluster.

---

## 4. Tutoriel : Comment Déployer l'Application (Pas-à-pas)

Étudiants, suivez ces étapes avec rigueur pour déployer la plateforme sur votre machine.

### Prérequis
- Docker Engine installé et configuré (Version 20.10+ recommandée).
- Docker Compose installé.
- Git installé.
- 4 Go de RAM libres minimum (en raison des bases Odoo, Keycloak et Midpoint).

### Étape 1 : Récupérer le code source

```bash
git clone https://github.com/Nostradam4ik/IAM-Gateway.git
cd IAM-Gateway
```

### Étape 2 : Configurer l'environnement

Les données sensibles (clés d'API, mots de passe) ne doivent jamais être poussées sur GitHub. Le projet utilise des variables d'environnement.

```bash
# Créer le fichier .env à partir de l'exemple
cp gateway/.env.example gateway/.env
```
*Note : Pour vos tests locaux, les valeurs par défaut du fichier `.env` sont suffisantes.*

### Étape 3 : Démarrer l'infrastructure

L'option `-d` (detached) permet au processus de tourner en arrière-plan.
L'option `--build` force Docker à reconstruire votre image FastAPI et Frontend au cas où vous auriez fait des modifications.

```bash
docker-compose up -d --build
```

### Étape 4 : Vérifier le statut du déploiement

Le démarrage complet des 13 conteneurs prend généralement entre 30 et 60 secondes. Vérifiez l'état de santé :

```bash
docker-compose ps
```
Assurez-vous que l'état de la gateway indique `Up` et non `Restarting` ou `Exited`.

### Étape 5 : Accéder aux Services

Une fois l'infrastructure en ligne, accédez aux services depuis votre navigateur Web :

| Service | URL Localhost | Identifiants par défaut |
|---|---|---|
| **API Gateway (Swagger)** | http://localhost:8000/docs | Accès public |
| **Frontend Web** | http://localhost:3000 | admin / admin |
| **MidPoint UI** | http://localhost:8080/midpoint | administrator / 5ecr3t |
| **Keycloak Admin** | http://localhost:8081 | admin / admin |
| **Odoo ERP** | http://localhost:8069 | admin / admin |
| **phpLDAPadmin** | http://localhost:8088 | cn=admin,dc=example,dc=com / secret |

---

## 5. Dépannage (Troubleshooting)

Si l'application ne fonctionne pas comme prévu, voici vos premiers réflexes d'ingénieur.

### 5.1. Consulter les logs

Si un service (ex: l'API `gateway`) crash au démarrage :
```bash
docker-compose logs -f gateway
```
*Le flag `-f` permet de suivre les logs en temps réel (tail).*

### 5.2. Nettoyer et tout réinitialiser

Si vos bases de données sont corrompues par des tests erronés, vous pouvez détruire l'environnement de test et effacer les **volumes persistants** (supprime toutes les données).

```bash
# Stopper et détruire les conteneurs et les volumes (-v)
docker-compose down -v

# Relancer depuis une page blanche
docker-compose up -d
```

### 5.3. Interagir avec les bases de données

Pour inspecter la base de données principale (audit et transactions) :
```bash
# Se connecter en SSH au conteneur de base de données
docker exec -it gateway-db bash

# Lancer la console PostgreSQL
psql -U gateway -d gateway
```

---

*Fiche technique destinée au déploiement des paquets Docker du projet IAM-Gateway. Ce dépôt n'intègre pas d'application mobile APK (contrairement à l'intitulé standard attendu de certaines UEs).*
