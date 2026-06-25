# IAM-Gateway

### Plateforme open-source d'orchestration IAM multi-systèmes

![Python](https://img.shields.io/badge/Python-3.11-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.1-009688)
![React](https://img.shields.io/badge/React-18-61DAFB)
![TypeScript](https://img.shields.io/badge/TypeScript-5-3178C6)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-336791)
![MidPoint](https://img.shields.io/badge/MidPoint-IGA-orange)
![Keycloak](https://img.shields.io/badge/Keycloak-23-4D4D4D)
![Qdrant](https://img.shields.io/badge/Qdrant-Vector_Search-DC244C)
![License](https://img.shields.io/badge/License-MIT-green)

> **Un projet de recherche appliquée du Laboratoire LISSI (UPEC)** — SAÉ BUT Informatique 3ᵉ année · 2025-2026

🔗 **Dépôt GitHub :** <https://github.com/Nostradam4ik/IAM-Gateway>
🎓 **Cadre :** SAÉ « Projet 3 » — BUT Informatique, Université Paris-Est Créteil (UPEC)
🔬 **Laboratoire :** LISSI (Laboratoire Images, Signaux et Systèmes Intelligents)

---

## 1. Résumé exécutif

**La problématique.** Dans toute organisation, l'arrivée, le changement de poste ou le départ d'un collaborateur impliquent de créer, modifier ou supprimer ses comptes dans une multitude de systèmes hétérogènes (annuaire, ERP, SSO, bases RH). Réalisées manuellement, ces opérations sont **lentes, sources d'erreurs et difficiles à auditer** — un enjeu majeur de sécurité et de conformité.

**La solution.** IAM-Gateway est une **passerelle intelligente de provisionnement multi-cibles** qui centralise et automatise l'orchestration des identités numériques. À partir d'une seule demande, elle propage les changements vers l'ensemble des systèmes connectés (MidPoint, Keycloak, OpenLDAP, Odoo, bases SQL), en appliquant des **règles de transformation dynamiques**, des **workflows d'approbation multi-niveaux** et une **réconciliation automatique** des écarts. Une couche d'**intelligence artificielle** enrichit le journal d'audit d'une recherche sémantique.

**La valeur ajoutée.** La plateforme réduit drastiquement le temps de provisionnement, fiabilise les accès, garantit une **traçabilité complète** à des fins de conformité, et s'étend à de nouveaux systèmes sans développement grâce à ses **connecteurs dynamiques**. Construite sur une architecture moderne (FastAPI, React, Docker), elle illustre une approche de recherche appliquée à l'**Identity Governance & Administration**.

> 💬 *« Une seule demande, tous les systèmes provisionnés — avec validation hiérarchique et audit intégral. »*

---

## 2. Architecture en une image

```
                       ┌───────────────────────────┐
                       │     Frontend React         │
                       │  (Console d'administration)│
                       └─────────────┬─────────────┘
                                     │ HTTPS / REST
                       ┌─────────────▼─────────────┐
                       │      API Gateway FastAPI   │
                       │  Règles · Workflows · Audit│
                       │  Réconciliation · IA       │
                       └───┬───────┬───────┬────────┘
              ┌────────────┘       │       └────────────┐
              ▼                    ▼                    ▼
     ┌─────────────┐      ┌────────────────┐    ┌──────────────┐
     │ PostgreSQL  │      │     Redis       │    │    Qdrant    │
     │ (gateway DB)│      │ (cache / JWT)   │    │ (IA vectoriel)│
     └─────────────┘      └────────────────┘    └──────────────┘
                                     │
                       ┌─────────────▼─────────────┐
                       │   MidPoint (Hub IGA)       │
                       │  Référentiel d'identités   │
                       └───┬───────┬───────┬────────┘
                           │       │       │  (propagation par rôles)
              ┌────────────┘       │       └────────────┐
              ▼                    ▼                    ▼
       ┌───────────┐        ┌───────────┐        ┌────────────┐
       │ OpenLDAP  │        │ Odoo ERP  │        │ Intranet   │
       │ (annuaire)│        │           │        │ (base RH)  │
       └───────────┘        └───────────┘        └────────────┘
                           ┌───────────┐
                           │ Keycloak  │  ← SSO / OIDC
                           └───────────┘
```

**Flux simplifié :** une demande émise depuis le frontend est traitée par l'API → soumise à un workflow d'approbation si nécessaire → exécutée via MidPoint (hub central) qui propage aux systèmes cibles selon les rôles → tracée dans le journal d'audit (indexé pour la recherche IA).

---

## 3. Fonctionnalités clés

- 🔄 **Provisionnement multi-cibles** — Crée, met à jour et désactive les comptes sur plusieurs systèmes simultanément à partir d'une seule demande.
- ✅ **Workflows d'approbation multi-niveaux** — Circuit de validation Manager → RH → IT Admin, avec notifications et approbation par email.
- 🔍 **Réconciliation automatique** — Détecte et résout les écarts entre le référentiel central et les systèmes cibles.
- 🔌 **Connecteurs dynamiques** — Intègre de nouveaux systèmes (SQL, LDAP, REST, ERP, IGA) à chaud, sans redéploiement.
- 🧠 **Audit augmenté par IA** — Recherche sémantique en langage naturel dans les journaux d'audit (vector search).
- 🖥️ **Console web d'administration** — Interface React complète : utilisateurs, règles, connecteurs, audit, supervision.
- ⚙️ **Moteur de règles dynamiques** — Transformation des attributs via des templates Jinja2 sécurisés, versionnés et testables.
- 🔐 **Sécurité by design** — Authentification JWT révocable, contrôle d'accès par rôles (RBAC), hachage bcrypt.

---

## 4. Stack technique

| Couche | Technologies |
|---|---|
| **Backend** | Python 3.11 · FastAPI · SQLModel / SQLAlchemy (async) · Jinja2 (sandbox) · JWT (HS256) · bcrypt |
| **Frontend** | React 18 · TypeScript · Vite · TailwindCSS · Radix UI · TanStack Query · Zustand · Monaco Editor · i18n (FR/EN/UK) |
| **Bases de données** | PostgreSQL 15 (instances dédiées : gateway, MidPoint, Odoo, intranet, Keycloak) |
| **IAM / IGA** | Evolveum MidPoint 4.4 (hub IGA) · Keycloak 23 (SSO/OIDC) · OpenLDAP (annuaire) |
| **Systèmes cibles** | Odoo 17 (ERP) · base SQL « intranet » (RH simulée) |
| **Infrastructure** | Docker · Docker Compose · Nginx · Redis 7 (cache & blacklist JWT) |
| **Intelligence artificielle** | Qdrant (recherche vectorielle) · OpenAI (assistant & embeddings) |

---

## 5. Comment démarrer (Quick Start)

```bash
# 1. Cloner le dépôt
git clone https://github.com/Nostradam4ik/IAM-Gateway.git
cd IAM-Gateway

# 2. Configurer l'environnement (générer les secrets)
cp .env.example .env
#   → renseigner SECRET_KEY, JWT_SECRET_KEY, mots de passe...

# 3. Démarrer toute la pile (bases → services IAM → API → frontend)
./start.sh

# 4. Initialiser la base de la gateway (une seule fois)
./scripts/init-db.sh
```

Une fois démarré :
- 🖥️ **Console d'administration** : <http://localhost:3000>
- 📚 **API & documentation (Swagger)** : <http://localhost:8000/docs>

> 📖 **Guide complet :** consultez [`docs/GUIDE_INSTALLATION_DEPLOIEMENT.md`](GUIDE_INSTALLATION_DEPLOIEMENT.md) pour les prérequis, la configuration détaillée et le déploiement en production.

---

## 6. L'équipe

### 👤 Zhmuryk Andrii

> 📸 **[PLACEHOLDER_PHOTO_ANDRII]** — *insérer ici une photo carrée (recommandé : 400×400 px). À défaut : pastille ronde avec les initiales « ZA ».*

**Rôle sur le projet :** Développeur principal Full-Stack · Architecture technique · DevOps
**Formation :** BUT Informatique, 3ᵉ année — UPEC (diplôme prévu juin 2026)

Développeur full-stack passionné par l'ingénierie logicielle et la gestion des identités, Andrii a conçu l'architecture technique d'IAM-Gateway et piloté son développement de bout en bout — du moteur de provisionnement et des connecteurs à l'interface React, en passant par l'orchestration Docker. Il a affûté son expertise IAM lors d'un stage au **Laboratoire LISSI (UPEC)** sur MidPoint et l'infrastructure cloud, puis renforcé ses compétences full-stack et produit lors d'un stage aux **Aéroports de Paris** (application FastAPI + React + PostgreSQL avec paiement Stripe et intégration d'IA de vision). Certifié **Oracle Cloud Infrastructure AI Foundations**, il s'intéresse particulièrement à l'intégration de l'IA dans les systèmes d'entreprise.

**Compétences :**
`Python` · `FastAPI` · `React` · `TypeScript` · `PostgreSQL` · `Docker` · `IAM / MidPoint` · `API Design` · `Cloud (Hetzner)` · `Stripe` · `IA (Claude, Groq)`

**Expériences :**
- **Stage Développeur Full-Stack — Aéroports de Paris** (avr.–juin 2025) : application FastAPI + React + PostgreSQL + Stripe + intégration d'IA de vision.
- **Stage IAM / Gateway Developer — Laboratoire LISSI, UPEC** (juil.–août 2024) : MidPoint 4.x, Docker, infrastructure cloud, IAM.

**Certification :** Oracle Cloud Infrastructure AI Foundations
**Langues :** Ukrainien (natif) · Français (courant) · Anglais (courant)
**GitHub :** <https://github.com/Nostradam4ik>
**LinkedIn :** *[À COMPLÉTER]*

---

### 👤 Aydin Ibrahim

> 📸 **[PLACEHOLDER_PHOTO_IBRAHIM]** — *insérer ici une photo carrée (recommandé : 400×400 px). À défaut : pastille ronde avec les initiales « AI ».*

**Rôle sur le projet :** Développeur · Intégration des connecteurs · Tests
**Formation :** BUT Informatique, 3ᵉ année — UPEC (diplôme prévu juin 2026)

Ibrahim a contribué à l'intégration des connecteurs vers les systèmes cibles et à la démarche de tests/validation de la plateforme.

> ✏️ **Section à compléter par Ibrahim :**
> - **Bio courte (5-6 lignes) :** *[À COMPLÉTER]*
> - **Compétences :** *[À COMPLÉTER — ex. Python, LDAP, tests, …]*
> - **Expériences / stages :** *[À COMPLÉTER]*
> - **Certifications :** *[À COMPLÉTER]*
> - **Langues :** *[À COMPLÉTER]*

**GitHub :** *[À COMPLÉTER]*
**LinkedIn :** *[À COMPLÉTER]*

---

## 7. Contexte académique

| | |
|---|---|
| **Type de projet** | SAÉ (Situation d'Apprentissage et d'Évaluation) — « Projet 3 » |
| **Formation** | BUT Informatique, 3ᵉ année |
| **Établissement** | Université Paris-Est Créteil (UPEC) |
| **Laboratoire de rattachement** | LISSI — Laboratoire Images, Signaux et Systèmes Intelligents |
| **Année universitaire** | 2025-2026 |
| **Encadrant(s)** | *[À COMPLÉTER]* |

> 🔬 **Recherche appliquée.** IAM-Gateway s'inscrit dans une démarche de **recherche appliquée** menée au sein du Laboratoire LISSI de l'UPEC. Le projet confronte les standards de l'Identity Governance & Administration (MidPoint, Keycloak) à une couche d'orchestration intelligente et d'IA, dans une perspective à la fois pédagogique et expérimentale.

---

## 8. Licence et contribution

### Licence

> ⚠️ **[À CONFIRMER]** — Aucun fichier `LICENSE` n'est présent dans le dépôt à ce jour. La licence **MIT** est **recommandée** pour ce projet open-source académique. Pour l'officialiser, ajoutez un fichier `LICENSE` à la racine :

```text
MIT License — Copyright (c) 2025-2026 Zhmuryk Andrii, Aydin Ibrahim — Laboratoire LISSI, UPEC
```

### Comment contribuer

Les contributions sont les bienvenues ! Pour proposer une amélioration :

```bash
# 1. Forkez le dépôt et créez une branche
git checkout -b feature/ma-fonctionnalite

# 2. Validez vos changements
git commit -m "feat: description de la fonctionnalité"

# 3. Poussez et ouvrez une Pull Request
git push origin feature/ma-fonctionnalite
```

1. **Issues** — Signalez bugs et idées via l'onglet *Issues* du dépôt GitHub.
2. **Pull Requests** — Décrivez clairement le changement et son intérêt.
3. **Documentation** — Le dossier [`docs/`](.) regroupe le rapport technique, les guides d'installation, de packaging et d'utilisation.

---

<div align="center">

**IAM-Gateway** · Projet SAÉ BUT Informatique 3ᵉ année · UPEC · Laboratoire LISSI · 2025-2026

Réalisé par **Zhmuryk Andrii** et **Aydin Ibrahim**

🔗 [github.com/Nostradam4ik/IAM-Gateway](https://github.com/Nostradam4ik/IAM-Gateway)

</div>

<!--
═══════════════════════════════════════════════════════════════════════════
  CONVERSION EN .DOCX
  Ce document Markdown peut être converti en Word via Pandoc :

      pandoc PRESENTATION_NEXUS_AI.md -o IAM-Gateway-presentation.docx

  Avant publication :
    1. Remplacer [PLACEHOLDER_PHOTO_ANDRII] et [PLACEHOLDER_PHOTO_IBRAHIM]
       par les vraies photos.
    2. Compléter tous les champs [À COMPLÉTER] (infos d'Ibrahim, encadrant,
       LinkedIn).
    3. Confirmer la licence et ajouter le fichier LICENSE à la racine.
═══════════════════════════════════════════════════════════════════════════
-->
