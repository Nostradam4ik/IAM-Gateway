# Rapport de Maintenance Logicielle - IAM Gateway

**Projet:** IAM Gateway - Identity & Access Management Platform
**Organisation:** NEXUS-AI-Innovation-lab
**Repository:** https://github.com/NEXUS-AI-Innovation-lab/IAM-Gateway
**Auteur:** Nostradam4ik
**Date de debut du projet:** 24 novembre 2025
**Debut de la phase de maintenance:** 11 fevrier 2026

---

## Table des matieres

1. [Introduction](#1-introduction)
2. [Types de Maintenance](#2-types-de-maintenance)
3. [Journal de Maintenance - Phase 1 (Developpement)](#3-journal-de-maintenance---phase-1-developpement)
4. [Journal de Maintenance - Phase 2 (Maintenance)](#4-journal-de-maintenance---phase-2-maintenance)
5. [Statistiques](#5-statistiques)
6. [Annexes](#6-annexes)

---

## 1. Introduction

Ce rapport documente toutes les operations de maintenance effectuees sur le projet IAM Gateway. Chaque modification est classee selon les quatre types de maintenance logicielle :

- **Corrective** : Correction de bugs et defauts
- **Preventive** : Actions pour eviter des problemes futurs
- **Perfective** : Ameliorations fonctionnelles et de performance
- **Adaptive** : Adaptation a de nouveaux environnements ou exigences

---

## 2. Types de Maintenance

| Type | Description | Exemples |
|------|-------------|----------|
| **Corrective** | Correction de defauts detectes | Fix bugs SQL, fix erreurs de validation, fix crash |
| **Preventive** | Prevenir les problemes futurs | Ajout de logs, refactoring, securisation |
| **Perfective** | Ameliorer les fonctionnalites | Nouvelles features, amelioration UX, i18n |
| **Adaptive** | Adapter aux changements d'environnement | Compatibilite Docker, nouveaux connecteurs |

---

## 3. Journal de Maintenance - Phase 1 (Developpement)

> Modifications effectuees avant le debut officiel de la phase de maintenance.

### 3.1 Corrections effectuees durant le developpement

| # | Date | Heure | Type | Description | Fichiers concernes | Commit |
|---|------|-------|------|-------------|-------------------|--------|
| 001 | 2026-01-14 | 15:12 | Corrective | Fix reference OID de ressource CSV LiveSync dans la tache MidPoint | `infrastructure/midpoint/` | 535e920 |
| 002 | 2026-02-06 | 15:34 | Corrective | Fix requete SQL pour la chaine d'approbation - `cast(:role_json as jsonb)` au lieu de `::jsonb` qui interferait avec asyncpg | `gateway/app/services/user_service.py` | 37836ef |
| 003 | 2026-02-06 | 15:34 | Corrective | Fix type mismatch `id` (int vers str) dans ConnectorListResponse | `gateway/app/services/connector_management_service.py` | 37836ef |
| 004 | 2026-02-06 | 15:34 | Corrective | Fix erreur `'iga' is not a valid ConnectorSubtype` - ajout des sous-types IGA/MidPoint manquants | `gateway/app/models/connector.py` | 37836ef |

### 3.2 Ameliorations effectuees durant le developpement

| # | Date | Heure | Type | Description | Fichiers concernes | Commit |
|---|------|-------|------|-------------|-------------------|--------|
| 005 | 2026-02-06 | 15:34 | Perfective | Ajout support multi-langues (FR, EN, UK) avec i18next | `gateway/frontend/src/i18n/`, `main.tsx`, `Layout.tsx` | 37836ef |
| 006 | 2026-02-06 | 15:34 | Perfective | Ajout composant LanguageSelector dans le header | `gateway/frontend/src/components/LanguageSelector.tsx` | 37836ef |
| 007 | 2026-02-06 | 15:34 | Perfective | Suppression onglet "Systeme" des categories de roles MidPoint | `gateway/frontend/src/pages/MidpointUsers.tsx` | 37836ef |
| 008 | 2026-02-06 | 15:34 | Perfective | Separation roles d'acces et roles d'approbation avec categories | `gateway/app/services/user_service.py`, `gateway/app/api/users.py`, `Users.tsx` | 37836ef |
| 009 | 2026-02-06 | 15:34 | Perfective | Amelioration UI gestion utilisateurs Gateway avec groupement par categorie | `gateway/frontend/src/pages/Users.tsx` | 37836ef |
| 010 | 2026-02-06 | 15:34 | Adaptive | Ajout types de connecteurs IGA (MidPoint, SailPoint, Saviynt) | `gateway/app/models/connector.py` | 37836ef |
| 011 | 2026-02-02 | 09:32 | Perfective | Ajout groupes LDAP, comparaison live, ameliorations MidPoint | Multiple fichiers | a52a32a |
| 012 | 2026-01-14 | 13:37 | Perfective | Ajout script d'import configuration MidPoint | `scripts/` | 9d6e8ae |
| 013 | 2026-01-14 | 13:05 | Adaptive | Integration Keycloak et provisioning par webhooks | `gateway/app/api/webhooks.py`, `docker-compose.yml` | 5c47736 |

---

## 4. Journal de Maintenance - Phase 2 (Maintenance)

> A partir du 11 fevrier 2026 - Toutes les modifications sont documentees en temps reel.

### 4.1 Maintenance Corrective

| # | Date | Heure | Severite | Description | Cause racine | Solution | Fichiers modifies | Statut |
|---|------|-------|----------|-------------|--------------|----------|-------------------|--------|
| M-C001 | 2026-02-11 | 10:20 | Critique | Backend `gateway-iam` en boucle de redemarrage | Bases de donnees PostgreSQL arretees (gateway-db, odoo-db, midpoint-postgres, keycloak-db) | Demarrage des conteneurs DB avant le backend : `docker start gateway-db odoo-db midpoint-postgres keycloak-db` | Aucun fichier modifie (operation infrastructure) | Resolu |
| M-C002 | 2026-02-11 | 10:20 | Haute | Keycloak en boucle de redemarrage | Conteneur `keycloak-db` arrete | Demarrage de keycloak-db puis restart keycloak | Aucun fichier modifie (operation infrastructure) | Resolu |
| M-C003 | 2026-02-11 | 10:21 | Moyenne | phpLDAPadmin inaccessible sur port 8088 | Conteneur phpldapadmin arrete | `docker start phpldapadmin` | Aucun fichier modifie (operation infrastructure) | Resolu |
| M-C004 | 2026-02-14 | 14:00 | Critique | Schema DB (migrations.py) desynchronise avec memory_store.py - colonnes manquantes, enums absents | migrations.py utilisait des noms de colonnes differents de ceux attendus par memory_store.py | Reecriture complete de migrations.py : ajout enums PostgreSQL (operationtype, operationstatus, auditeventtype, auditseverity), alignement colonnes (correlation_id, target_systems, account_id, input_attributes, created_at, severity), ajout table workflows, ALTER TABLE pour compatibilite | `gateway/app/db/migrations.py` | Resolu |
| M-C005 | 2026-02-14 | 14:10 | Haute | Doublon API provision_via_midpoint.py avec endpoints identiques a midpoint.py + asyncio.sleep(2) bloquant | Refactoring incomplet - deux fichiers service et deux routers API pour la meme fonctionnalite | Suppression de `provision_via_midpoint.py` (API), `midpoint_provision_service_updated.py` (service doublon), retrait import et router dans main.py | `gateway/app/api/provision_via_midpoint.py` (supprime), `gateway/app/services/midpoint_provision_service_updated.py` (supprime), `gateway/app/main.py` | Resolu |
| M-C006 | 2026-02-14 | 14:15 | Moyenne | database_store.py inutilise - doublon de memory_store.py | Fichier orphelin non importe dans le projet | Suppression du fichier | `gateway/app/core/database_store.py` (supprime) | Resolu |
| M-C007 | 2026-02-14 | 14:20 | Haute | Permissions utilisateurs non persistees en DB - donnees demo en memoire perdues au redemarrage | API permissions.py utilisait un cache in-memory avec des donnees demo hardcodees | Reecriture de permissions.py pour lire/ecrire depuis gateway_users.permission_level via SQLAlchemy | `gateway/app/api/permissions.py` | Resolu |
| M-C008 | 2026-02-14 | 14:25 | Basse | memory_store.py creait son propre engine DB au lieu de reutiliser celui de database.py | Double connexion a PostgreSQL inutile | Remplacement par import de engine/async_session depuis database.py | `gateway/app/core/memory_store.py` | Resolu |
| M-C009 | 2026-02-14 | 14:30 | Basse | Dependance passlib[bcrypt] inutilisee - tout le code utilise bcrypt directement | Dependance residuelle non nettoyee | Remplacement par `bcrypt` dans requirements.txt | `gateway/requirements.txt` | Resolu |
| M-C010 | 2026-02-14 | 16:00 | Haute | Comparaison Live - recherche utilisateur echoue ("Utilisateur non trouve") | Chaque connecteur ne cherchait que sur un seul champ exact (LDAP: uid, SQL: id, Odoo: login) | Ajout recherche multi-champs : LDAP (uid, cn, mail, givenName, sn avec wildcards), SQL (id, username, email, first_name, last_name avec ILIKE), Odoo (login, name, email avec ilike) | `gateway/app/connectors/ldap_connector.py`, `gateway/app/connectors/sql_connector.py`, `gateway/app/connectors/odoo_connector.py` | Resolu |
| M-C011 | 2026-02-16 | 11:00 | Critique | Page Connecteurs non fonctionnelle - table connector_configurations avec schema incorrect (id integer au lieu de varchar, colonnes manquantes) | Table creee par SQLModel auto-create au lieu de migrations.py - id auto-increment incompatible avec IDs `conn-{uuid}` du service, colonnes `last_health_error` et `created_by` absentes | Suppression et recreation de la table avec le schema correct (id VARCHAR(100), toutes colonnes presentes). Pre-creation des 4 connecteurs existants (OpenLDAP, Odoo, PostgreSQL, MidPoint) avec test de connexion valide | Table `connector_configurations` (PostgreSQL) | Resolu |
| M-C012 | 2026-02-17 | 10:15 | Haute | Page Regles - boutons "Nouvelle regle" et "Modifier" non fonctionnels (pas de onClick handler) | Formulaire de creation/edition jamais implemente - seuls supprimer et tester fonctionnaient | Ajout modal creation/edition avec champs (nom, type, systeme cible, expression Jinja2 avec exemples cliquables, attributs source/cible, priorite slider, description). Branchement sur API POST/PUT /rules/ | `gateway/frontend/src/pages/Rules.tsx` | Resolu |
| M-C013 | 2026-02-17 | 10:15 | Moyenne | Bouton "Arret d'urgence" du header (Layout.tsx) non fonctionnel - pas de onClick | Bouton present visuellement mais jamais branche a l'API emergencyStop() | Ajout onClick avec confirmation + appel API emergencyStop() | `gateway/frontend/src/components/Layout.tsx` | Resolu |
| M-C014 | 2026-02-17 | 10:15 | Moyenne | Endpoint /admin/status retourne ldap et midpoint "healthy" en dur sans verifier | Valeurs hardcodees dans le code au lieu de tester les connexions reelles | Remplacement par tests reels : LDAP via LDAPConnector.test_connection(), MidPoint via requete HTTP /ws/rest/self | `gateway/app/api/admin.py` | Resolu |
| M-C015 | 2026-02-17 | 10:15 | Basse | Page Parametres - section "Configuration" avec valeurs hardcodees fausses (URL MidPoint localhost, etc.) | Valeurs hardcodees dans le JSX ne correspondant pas aux vrais parametres du systeme | Suppression de la section Configuration hardcodee | `gateway/frontend/src/pages/Settings.tsx` | Resolu |

### 4.2 Maintenance Preventive

| # | Date | Heure | Description | Justification | Fichiers modifies | Statut |
|---|------|-------|-------------|---------------|-------------------|--------|
| M-V001 | 2026-02-14 | 14:35 | Ajout JTI (JWT Token ID) unique dans les tokens JWT | Permet la revocation de tokens individuels via Redis blacklist - securisation des sessions | `gateway/app/core/security.py` | Resolu |
| M-V002 | 2026-02-14 | 14:35 | Verification blacklist Redis dans get_current_user() | Prevention des attaques par rejeu de tokens revoques | `gateway/app/core/security.py` | Resolu |

### 4.3 Maintenance Perfective

| # | Date | Heure | Description | Impact utilisateur | Fichiers modifies | Statut |
|---|------|-------|-------------|-------------------|-------------------|--------|
| M-P001 | 2026-02-13 | 13:20 | Suppression de l'onglet "Groupes LDAP" de la navigation Gateway | Simplification de l'interface - fonctionnalite non necessaire dans Gateway | `Layout.tsx` (suppression nav entry + import ShieldCheck), `App.tsx` (suppression route + import LDAPGroups) | Resolu |
| M-P002 | 2026-02-14 | 14:40 | Integration Redis : client cache, sessions, blacklist tokens, rate limiting, endpoint logout | Utilisation effective du service Redis (gateway-redis) declare dans docker-compose mais jamais utilise | `gateway/app/core/redis_client.py` (nouveau), `gateway/app/main.py`, `gateway/app/core/security.py`, `gateway/app/api/admin.py` | Resolu |
| M-P003 | 2026-02-14 | 14:50 | Integration Qdrant : indexation audit logs, recherche semantique vectorielle | Utilisation effective du service Qdrant (gateway-qdrant) declare dans docker-compose mais jamais utilise | `gateway/app/core/qdrant_store.py` (nouveau), `gateway/app/main.py`, `gateway/app/core/memory_store.py`, `gateway/app/services/audit_service.py` | Resolu |
| M-P004 | 2026-02-14 | 16:10 | Suppression des onglets "Statistiques" et "Comparaison" de la page Comparaison Live | Donnees non exploitables (SQL deconnecte = 0% sync, divergences faussees) - simplification UX | `gateway/frontend/src/pages/LiveComparison.tsx` | Resolu |
| M-P005 | 2026-02-16 | 11:30 | Refonte du Dashboard : affichage des connecteurs configures avec statut sante, suppression des cartes statistiques Operations/Taux/Approbations/Erreurs | Les statistiques affichaient toujours 0 (non connectees) - remplacement par vue des connecteurs reels avec indicateur de sante | `gateway/frontend/src/pages/Dashboard.tsx` | Resolu |
| M-P006 | 2026-02-17 | 10:15 | Suppression section "Actions rapides" du Dashboard | Section non essentielle, simplification interface | `gateway/frontend/src/pages/Dashboard.tsx` | Resolu |

### 4.4 Maintenance Adaptive

| # | Date | Heure | Description | Raison | Fichiers modifies | Statut |
|---|------|-------|-------------|--------|-------------------|--------|
| M-A001 | 2026-02-11 | 10:25 | Depot du projet sur l'organisation GitHub NEXUS-AI-Innovation-lab | Migration vers repository organisationnel | `.git/config` (ajout remote nexus) | Resolu |
| | | | | | | |

---

## 5. Statistiques

### 5.1 Resume Phase 1 (Developpement)

| Type de maintenance | Nombre d'interventions |
|--------------------|-----------------------|
| Corrective | 4 |
| Preventive | 0 |
| Perfective | 9 |
| Adaptive | 2 |
| **Total** | **15** |

### 5.2 Resume Phase 2 (Maintenance) - Mis a jour en temps reel

| Type de maintenance | Nombre d'interventions |
|--------------------|-----------------------|
| Corrective | 15 |
| Preventive | 2 |
| Perfective | 6 |
| Adaptive | 1 |
| **Total** | **24** |

### 5.3 Repartition Globale

```
Corrective  : ██████████████████████████████  19  (48.7%)
Preventive  : ████  2  (5.1%)
Perfective  : ████████████████████████████  15  (38.5%)
Adaptive    : ██████  3  (7.7%)
Total       :              39
```

---

## 6. Annexes

### 6.1 Architecture du Projet

```
IAM Gateway
├── gateway/                  # Application principale
│   ├── app/                  # Backend FastAPI (Python)
│   │   ├── api/              # Endpoints API REST
│   │   ├── connectors/       # Connecteurs (LDAP, Odoo, MidPoint, SQL)
│   │   ├── core/             # Configuration, securite, base de donnees
│   │   ├── models/           # Modeles de donnees (Pydantic)
│   │   ├── services/         # Services metier
│   │   └── db/               # Migrations base de donnees
│   └── frontend/             # Interface React + TypeScript + Tailwind
│       ├── src/components/   # Composants reutilisables
│       ├── src/pages/        # Pages de l'application
│       ├── src/i18n/         # Traductions (FR, EN, UK)
│       └── src/lib/          # API client, utilitaires
├── infrastructure/           # Configuration MidPoint, LDAP
├── scripts/                  # Scripts d'import et utilitaires
├── docs/                     # Documentation et rapports
└── docker-compose.yml        # Orchestration des services
```

### 6.2 Services Docker

| Service | Image | Port | Role |
|---------|-------|------|------|
| gateway-frontend | nginx (build custom) | 3000 | Interface web React |
| gateway-iam | python:3.11 (build custom) | 8000 | Backend API FastAPI |
| gateway-db | postgres:15 | 5434 | Base de donnees Gateway |
| midpoint-core | evolveum/midpoint:4.4 | 8080 | Serveur IAM MidPoint |
| midpoint-postgres | postgres:15 | 5433 | Base de donnees MidPoint |
| openldap | osixia/openldap:1.5.0 | 10389 | Annuaire LDAP |
| phpldapadmin | osixia/phpldapadmin | 8088 | Interface web LDAP |
| keycloak | quay.io/keycloak/keycloak:23.0 | 8081 | SSO / Authentification |
| keycloak-db | postgres:15 | - | Base de donnees Keycloak |
| odoo | odoo:17 | 8069 | ERP / Gestion RH |
| odoo-db | postgres:15 | - | Base de donnees Odoo |
| gateway-redis | redis:7-alpine | 6379 | Cache / Sessions |
| gateway-qdrant | qdrant/qdrant | 6333 | Base vectorielle (IA) |

### 6.3 Credentials de Reference

| Service | URL | Identifiant | Mot de passe |
|---------|-----|-------------|--------------|
| Gateway Frontend | http://localhost:3000 | admin | admin123 |
| MidPoint | http://localhost:8080/midpoint | administrator | 5ecr3t |
| Odoo | http://localhost:8069 | admin | admin |
| Keycloak | http://localhost:8081 | admin | admin |
| phpLDAPadmin | http://localhost:8088 | cn=admin,dc=example,dc=com | secret |
| OpenLDAP | ldap://localhost:10389 | cn=admin,dc=example,dc=com | secret |

---

*Rapport genere le 11 fevrier 2026. Derniere mise a jour: 17 fevrier 2026.*
