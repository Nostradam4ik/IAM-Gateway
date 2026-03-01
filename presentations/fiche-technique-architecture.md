---
title: "Fiche Technique : Architecture Passerelle IAM Gateway"
author: "Andrii Zhmuryk, Aydin Ibrahim"
date: "1er mars 2026"
---

# Fiche Technique : Architecture Passerelle IAM Gateway

**Projet** : Passerelle de Provisionnement IAM Intelligente (SAE S5/S6)  
**Auteurs** : Andrii Zhmuryk, Aydin Ibrahim  
**Contact** : andrijzmurik@gmail.com | [GitHub](https://github.com/Nostradam4ik)

---

## 1. Contexte et Enjeux Métiers

La **Passerelle IAM Gateway** répond à un besoin critique des entreprises : automatiser et sécuriser le cycle de vie des identités à travers des systèmes hétérogènes. Historiquement complexe, le provisionnement "multi-cibles" (ex: créer simultanément un compte AD, un badge virtuel et un accès applicatif) génère des failles de sécurité et des coûts opérationnels. 

**Valeur ajoutée de la solution :**
- **Automatisation intelligente** : Intermédiation entre la source de vérité (MidPoint) et les cibles.
- **Fiabilité transactionnelle** : Mécanismes de Rollback garantissant la cohérence des données.
- **Sécurité et conformité** : Traçabilité complète et workflows d'approbation stricts.
- **Innovation IA** : Recherche sémantique d'incidents et aide au diagnostic.

## 2. Description des Composants Architecturaux

L'architecture repose sur une approche **Microservices et API-First**, conteneurisée via Docker pour garantir scalabilité et reproductibilité.

### 2.1. Couche d'Entrée et Orchestration (Core)
- **API Gateway (FastAPI / Python)** : Point d'entrée asynchrone ultra-performant. Gère les requêtes REST entrantes (depuis MidPoint), la validation JSON Schema, et l'orchestration des flux.
- **Moteur de Règles (YAML/Jinja2)** : Évalue dynamiquement les conditions de provisionnement. Sépare la logique métier du code technique, permettant des modifications à chaud.
- **Gestionnaire de Transactions** : Implémente le pattern "Saga". En cas d'échec sur un système cible, il déclenche les compensations (Rollback) sur les systèmes déjà provisionnés.

### 2.2. Couche Connecteurs (Interfaces Cibles)
Architecture modulaire (Design Pattern *Strategy*) permettant d'ajouter facilement de nouvelles cibles sans altérer le Core.
- **Annuaire** : Active Directory / OpenLDAP (via protocole LDAPS).
- **SSO & Auth** : Keycloak (Admin REST API) / Firebase (Admin SDK).
- **Applications Métiers** : Odoo (XML-RPC) / GLPI (REST API).

### 2.3. Couche Infrastructure et Données
- **Redis (Cache & Message Broker)** : Gère les files d'attente asynchrones pour le traitement en tâche de fond (Celery/RQ) et le caching des règles fréquentes.
- **PostgreSQL (Base de données relationnelle)** : Stockage persistent de l'audit trail, des statuts d'approbation et de l'historique de versionnement des règles.
- **Qdrant (Base de données Vectorielle)** : Innovation majeure du projet. Stocke les embeddings (vecteurs) des logs d'erreurs pour permettre la recherche sémantique intelligente ("Trouver les pannes similaires survenues le mois dernier").

### 2.4. Couche Sécurité
- **Keycloak** : Fournit l'authentification OIDC (OpenID Connect) pour l'interface d'administration et la sécurisation des endpoints API via tokens JWT.
- **Chiffrement** : Transport TLS systématique et hachage des identifiants de service.

## 3. Flux de Données Principal (Nominal)

1. **Déclenchement** : MidPoint détecte une embauche et envoie un payload utilisateur (JSON) à l'API FastAPI.
2. **Validation & Règles** : L'API valide la structure, interroge le moteur YAML pour identifier les systèmes cibles concernés selon les attributs (ex: *Département = IT*).
3. **Workflow (Optionnel)** : Si la règle l'exige, le traitement est suspendu (stocké dans Redis) en attente d'une validation humaine via l'interface web.
4. **Provisionnement Parallèle** : Les connecteurs exécutent les appels d'API/LDAP vers AD, GLPI et Keycloak simultanément.
5. **Validation Transactionnelle** : 
   - *Succès* : L'état validé est inscrit dans PostgreSQL.
   - *Échec partiel* : Le Rollback est ordonné pour annuler les créations partielles.
6. **Vectorisation** : Les logs détaillés de l'opération sont encodés et stockés dans Qdrant pour analyse IA future.

## 4. Choix Technologiques & Compétences Démontrées

Ce projet démontre une maîtrise "Full-Stack Ops" :

| Domaine | Technologies exploitées |
|---|---|
| **Développement Backend** | Python (FastAPI), Asynchronisme, Design Patterns |
| **Gestion des Identités (IAM)** | Protocole LDAP, OAuth2/OIDC, Keycloak, MidPoint |
| **DevOps & Infrastructure** | Docker, Docker-Compose, Redis, PostgreSQL |
| **Data & Intelligence Artificielle** | Qdrant (Vector DB), LLM (Embeddings / Assistant) |
| **Qualité & Sécurité** | Tests unitaires, Rollback transactionnel, Audit Trail |

## 5. Perspectives Professionnelles

Cette architecture a été conçue comme un produit d'entreprise *"Production-Ready"*. 

**Évolutions possibles à court terme :**
1. **Migration Kubernetes (K8s)** : Passage d'un déploiement Docker-Compose à un cluster orchestré avec Helm charts pour la haute disponibilité.
2. **Observabilité Avancée** : Intégration de la stack ELK (Elasticsearch, Logstash, Kibana) ou Prometheus/Grafana pour des dashboards temps réels.
3. **Pipeline CI/CD** : Automatisation complète des tests et du déploiement via GitHub Actions ou GitLab CI.

---
*Document conçu en appui du Poster "Architecture IAM Gateway". Pour toute démonstration technique ou accès au dépôt du code source, merci de me contacter directement.*