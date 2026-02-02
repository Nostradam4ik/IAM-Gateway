# Presentation PowerPoint - Plateforme No-Code & Gateway IAM
## UPEC - Département Informatique - BUT 3ème année
### Zhmuryk Andrii & Aydin Ibrahim

---

# SLIDE 1: PAGE DE TITRE

**Plateforme No-Code & Gateway IAM**
*Orchestration intelligente des identités multi-systèmes*

- **Étudiants**: Zhmuryk Andrii & Aydin Ibrahim
- **Formation**: BUT Informatique 3ème année
- **Université**: UPEC - Université Paris-Est Créteil
- **Département**: Informatique
- **Date**: Janvier 2026

[Logo UPEC] [Logo Département Informatique]

---

# SLIDE 2: PROBLÉMATIQUE

## Le problème de la gestion des identités en entreprise

### Situation actuelle dans les entreprises:

**Multiplication des systèmes**
- Active Directory / LDAP (authentification)
- ERP (Odoo, SAP) - gestion RH
- Applications métier (bases SQL)
- Services Cloud (Keycloak, OAuth)

**Problèmes rencontrés:**
- Un employé = 5 à 10 comptes différents
- Création manuelle = erreurs + temps perdu
- Départ d'un employé = comptes oubliés (failles de sécurité)
- Aucune traçabilité des modifications

**Statistiques:**
- 30% des violations de données liées aux comptes orphelins
- 4h en moyenne pour créer tous les accès d'un nouvel employé

---

# SLIDE 3: NOTRE SOLUTION - INNOVATION

## Gateway IAM: Orchestration Intelligente

### Ce que nous apportons:

**1. Interface No-Code**
- MidPoint est puissant MAIS complexe (XML, concepts techniques)
- Notre interface = simple, visuelle, accessible aux non-techniciens
- Un administrateur RH peut gérer les accès sans connaissance technique

**2. Automatisation Intelligente**
- Règles dynamiques en YAML (pas de code Java)
- Moteur de calcul automatique (login, email, groupes)
- Workflows d'approbation multi-niveaux

**3. Centralisation**
- Un seul point d'entrée pour tous les systèmes
- Vue temps réel de l'état de synchronisation
- Réconciliation automatique des écarts

**Innovation clé**: Rendre l'IAM accessible à tous, pas seulement aux experts MidPoint

---

# SLIDE 4: BACKLOG - FONCTIONNALITÉS INITIALES (1/2)

## Epic 1: Gestion des Utilisateurs
| User Story | Priorité | Points |
|------------|----------|--------|
| Créer un utilisateur dans tous les systèmes | Must | 8 |
| Modifier les attributs d'un utilisateur | Must | 5 |
| Désactiver/supprimer un compte | Must | 5 |
| Voir l'historique des modifications | Should | 3 |

## Epic 2: Moteur de Règles
| User Story | Priorité | Points |
|------------|----------|--------|
| Définir des règles de mapping d'attributs | Must | 8 |
| Tester une règle avec des données fictives | Must | 5 |
| Versionner les règles | Should | 3 |

## Epic 3: Workflows d'Approbation
| User Story | Priorité | Points |
|------------|----------|--------|
| Configurer des workflows multi-niveaux | Must | 8 |
| Approuver/rejeter une demande | Must | 5 |
| Notifications par email | Should | 5 |

---

# SLIDE 5: BACKLOG - FONCTIONNALITÉS INITIALES (2/2)

## Epic 4: Connecteurs Systèmes
| User Story | Priorité | Points |
|------------|----------|--------|
| Connecteur LDAP (OpenLDAP, AD) | Must | 8 |
| Connecteur Odoo (ERP) | Must | 8 |
| Connecteur SQL (PostgreSQL) | Must | 5 |
| Connecteur MidPoint (REST API) | Must | 13 |
| Connecteur Keycloak (OIDC) | Should | 8 |

## Epic 5: Réconciliation & Audit
| User Story | Priorité | Points |
|------------|----------|--------|
| Comparer l'état des systèmes | Must | 8 |
| Détecter les écarts (orphelins, drift) | Must | 5 |
| Recherche sémantique dans les logs | Should | 8 |
| Export des rapports d'audit | Should | 3 |

## Epic 6: Intelligence Artificielle
| User Story | Priorité | Points |
|------------|----------|--------|
| Assistant IA pour aide à la configuration | Could | 8 |
| Suggestions de règles automatiques | Could | 5 |

**Total initial: ~120 points** (sprints de 2 semaines)

---

# SLIDE 6: ARCHITECTURE GLOBALE - SCHÉMA

```
┌────────────────────────────────────────────────────────────────────┐
│                         UTILISATEUR                                 │
│                    (Navigateur Web)                                 │
└─────────────────────────┬──────────────────────────────────────────┘
                          │ HTTPS (Port 3000)
                          ▼
┌────────────────────────────────────────────────────────────────────┐
│                    FRONTEND REACT                                   │
│            TypeScript + Tailwind CSS + Vite                        │
│     ┌─────────┬─────────┬─────────┬─────────┬─────────┐           │
│     │Dashboard│ Users   │ Rules   │Workflows│  Audit  │           │
│     └─────────┴─────────┴─────────┴─────────┴─────────┘           │
└─────────────────────────┬──────────────────────────────────────────┘
                          │ REST API (Port 8000)
                          ▼
┌────────────────────────────────────────────────────────────────────┐
│                    GATEWAY API (FastAPI)                            │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐               │
│  │ Rule Engine  │ │ Workflow Mgr │ │ AI Assistant │               │
│  │  (Jinja2)    │ │ (Approvals)  │ │  (OpenAI)    │               │
│  └──────────────┘ └──────────────┘ └──────────────┘               │
│  ┌──────────────────────────────────────────────────┐             │
│  │              CONNECTOR LAYER                      │             │
│  │  MidPoint │ LDAP │ Odoo │ SQL │ Keycloak        │             │
│  └──────────────────────────────────────────────────┘             │
└───────┬───────────────┬───────────────┬───────────────┬───────────┘
        │               │               │               │
        ▼               ▼               ▼               ▼
   ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐
   │MidPoint │    │OpenLDAP │    │  Odoo   │    │Keycloak │
   │  (IAM)  │    │(Annuaire│    │  (ERP)  │    │ (OIDC)  │
   └─────────┘    └─────────┘    └─────────┘    └─────────┘
```

---

# SLIDE 7: ARCHITECTURE TECHNIQUE DÉTAILLÉE

## 15 Services Docker

| Service | Technologie | Port | Rôle |
|---------|------------|------|------|
| **gateway** | FastAPI/Python 3.11 | 8000 | API principale |
| **gateway-frontend** | React 18/TypeScript | 3000 | Interface utilisateur |
| **gateway-db** | PostgreSQL 15 | 5434 | Base Gateway |
| **redis** | Redis 7 | 6379 | Cache & sessions |
| **qdrant** | Qdrant | 6333 | Recherche sémantique |
| **midpoint** | MidPoint 4.4 | 8080 | Hub d'identité |
| **midpoint-postgres** | PostgreSQL 15 | 5433 | Base MidPoint |
| **openldap** | OpenLDAP 1.5 | 10389 | Annuaire LDAP |
| **phpldapadmin** | phpLDAPadmin | 8088 | Admin LDAP |
| **odoo** | Odoo 17 | 8069 | ERP/RH |
| **odoo-db** | PostgreSQL 15 | - | Base Odoo |
| **keycloak** | Keycloak 23 | 8081 | OAuth/OIDC |
| **keycloak-db** | PostgreSQL 15 | - | Base Keycloak |
| **intranet-db** | PostgreSQL 15 | 55432 | App métier |

**Réseau**: `iam-network` (bridge Docker)

---

# SLIDE 8: STACK TECHNOLOGIQUE

## Backend (Python)
- **Framework**: FastAPI 0.109 + Uvicorn
- **ORM**: SQLModel (SQLAlchemy + Pydantic)
- **Auth**: JWT + OAuth2 (python-jose, passlib)
- **LDAP**: ldap3 (Python library)
- **Scheduler**: APScheduler
- **Logging**: structlog (JSON structuré)
- **AI**: OpenAI API (GPT-4)

## Frontend (TypeScript)
- **Framework**: React 18 + Vite
- **Routing**: React Router v6
- **State**: Zustand
- **Styling**: Tailwind CSS
- **Icons**: Lucide React
- **HTTP**: Axios

## Infrastructure
- **Conteneurisation**: Docker + Docker Compose
- **Bases de données**: PostgreSQL 15 (x5 instances)
- **Cache**: Redis 7
- **Vector Store**: Qdrant
- **IAM Core**: MidPoint 4.4

---

# SLIDE 9: FONCTIONNALITÉS IMPLÉMENTÉES - DASHBOARD

## Dashboard Principal (100%)

**Fonctionnalités:**
- Vue d'ensemble en temps réel
- Statistiques clés (utilisateurs, opérations, erreurs)
- État de santé des connecteurs
- Graphiques de performance
- Alertes et notifications

**Captures d'écran:**
[Image: Dashboard avec métriques]

**Endpoints API:**
- `GET /api/v1/admin/status` - État système
- `GET /api/v1/admin/metrics` - Métriques détaillées
- `GET /api/v1/connectors/health` - Santé connecteurs

---

# SLIDE 10: FONCTIONNALITÉS IMPLÉMENTÉES - PROVISIONING

## Gestion des Opérations (100%)

**Fonctionnalités:**
- Création d'utilisateur multi-système
- Modification des attributs
- Suppression/désactivation
- Rollback des opérations
- Suivi du statut en temps réel

**Workflow type:**
1. Création demande → 2. Validation règles → 3. Workflow approbation → 4. Exécution → 5. Audit

**Endpoints API:**
- `POST /api/v1/provision/` - Créer opération
- `GET /api/v1/provision/{id}` - Détails opération
- `POST /api/v1/provision/{id}/rollback` - Annuler

**Systèmes cibles supportés:**
- LDAP (comptes + groupes)
- Odoo (res.users, res.partner)
- PostgreSQL (tables custom)
- MidPoint (utilisateurs, rôles)

---

# SLIDE 11: FONCTIONNALITÉS IMPLÉMENTÉES - RÈGLES

## Moteur de Règles Dynamique (100%)

**Fonctionnalités:**
- Définition en YAML/JSON
- Expressions Jinja2 sandboxées
- Filtres intégrés (normalize_name, slugify, etc.)
- Test avec données fictives
- Versionnage (in-memory)

**Exemple de règle:**
```yaml
target_system: LDAP
rule_type: MAPPING
definition: |
  {%- set login = (firstname ~ '.' ~ lastname) | normalize_name -%}
  {
    "uid": "{{ login }}",
    "mail": "{{ login }}@example.com",
    "cn": "{{ firstname }} {{ lastname }}"
  }
```

**Cas d'usage:**
- Génération automatique de login
- Calcul de l'email selon le département
- Attribution de groupes selon le poste

---

# SLIDE 12: FONCTIONNALITÉS IMPLÉMENTÉES - WORKFLOWS

## Workflows d'Approbation (100%)

**Fonctionnalités:**
- Configuration multi-niveaux (jusqu'à 5)
- Approbation/rejet avec commentaires
- Timeout configurable (72h par défaut)
- Notifications email (partiel)
- Historique des décisions

**Niveaux type:**
1. Manager direct
2. Chef de département
3. Propriétaire application
4. RSSI (si sensible)

**Endpoints API:**
- `GET /api/v1/workflow/instances/pending` - En attente
- `POST /api/v1/workflow/instances/{id}/approve` - Approuver
- `POST /api/v1/workflow/instances/{id}/reject` - Rejeter

---

# SLIDE 13: FONCTIONNALITÉS IMPLÉMENTÉES - GROUPES LDAP

## Gestion des Groupes LDAP (100%)

**Fonctionnalités:**
- Liste de tous les groupes LDAP
- Visualisation des membres
- Ajout de membres (avec autocomplete)
- Suppression de membres
- Support groupOfUniqueNames et groupOfNames

**Interface:**
- Recherche d'utilisateurs en temps réel
- Autocomplétion intelligente
- Filtrage des OIDs MidPoint

**Endpoints API:**
- `GET /api/v1/ldap/groups` - Liste groupes
- `GET /api/v1/ldap/groups/{cn}` - Détails groupe
- `POST /api/v1/ldap/groups/{cn}/members` - Ajouter membre
- `DELETE /api/v1/ldap/groups/{cn}/members/{uid}` - Retirer

---

# SLIDE 14: FONCTIONNALITÉS IMPLÉMENTÉES - COMPARAISON LIVE

## Comparaison Temps Réel (100%)

**Fonctionnalités:**
- Statistiques live de chaque système
- Comparaison croisée des populations
- Détection des écarts
- Synchronisation Odoo → MidPoint
- Planification des syncs

**Métriques affichées:**
- Nombre d'utilisateurs par système
- Utilisateurs communs vs orphelins
- État de dernière synchronisation

**Endpoints API:**
- `GET /api/v1/live/stats` - Stats temps réel
- `GET /api/v1/live/compare` - Comparaison
- `POST /api/v1/live/sync/odoo-to-midpoint` - Sync manuel

---

# SLIDE 15: FONCTIONNALITÉS IMPLÉMENTÉES - AUDIT & IA

## Audit & Logs (100%)
- Logging structuré (JSON)
- Recherche full-text
- Recherche sémantique (Qdrant)
- Filtrage par date, type, utilisateur
- Export des rapports

## Assistant IA (100%)
- Chat avec GPT-4
- Suggestions de règles
- Aide au diagnostic d'erreurs
- Génération de code connecteur

**Endpoints:**
- `POST /api/v1/ai/query` - Question IA
- `POST /api/v1/admin/audit/search` - Recherche logs

---

# SLIDE 16: FONCTIONNALITÉS PARTIELLEMENT IMPLÉMENTÉES

| Fonctionnalité | Progression | Reste à faire |
|----------------|-------------|---------------|
| **Intégration Keycloak** | 70% | Synchronisation des groupes, mapping des rôles |
| **Notifications Email** | 50% | Templates HTML, personnalisation, retry logic |
| **Recherche Vectorielle** | 80% | Rafraîchissement auto des embeddings |
| **Rollback Complet** | 60% | Nettoyage des états intermédiaires |
| **Versionnage Git des Règles** | 40% | Intégration Git bare repo |
| **Multi-langue UI** | 10% | Traduction anglais, i18n React |

## Détails:

**Keycloak (70%)**
- Création utilisateur OK
- Token validation OK
- Sync groupes: en cours

**Email (50%)**
- SMTP configurable
- Templates hardcodés
- Besoin: moteur de templates

---

# SLIDE 17: FONCTIONNALITÉS À IMPLÉMENTER

## Priorité Haute (Should)
| Fonctionnalité | Estimation | Description |
|----------------|------------|-------------|
| Déploiement Kubernetes | 8 pts | Helm charts, auto-scaling |
| Masquage des données PII | 3 pts | RGPD compliance |
| Migration Alembic | 5 pts | Versionnage BDD automatique |

## Priorité Moyenne (Could)
| Fonctionnalité | Estimation | Description |
|----------------|------------|-------------|
| Connecteur Firebase | 8 pts | Support Firebase Auth |
| Connecteur GLPI | 5 pts | Gestion des assets |
| Détection SoD | 8 pts | Séparation des devoirs |
| App Mobile | 21 pts | Approbations sur mobile |

## Priorité Basse (Won't - cette version)
| Fonctionnalité | Description |
|----------------|-------------|
| Multi-tenancy | Support multi-organisations |
| MFA Biométrique | Authentification forte |
| Machine Learning | Détection d'anomalies |

---

# SLIDE 18: DIFFICULTÉS RENCONTRÉES (1/2)

## 1. Complexité de MidPoint
**Problème:** MidPoint utilise XML complexe et concepts avancés (shadows, projections)
**Solution:** Abstraction via notre API REST simplifiée
**Apprentissage:** Importance de l'encapsulation

## 2. Transactions Distribuées
**Problème:** Une opération = 4 systèmes différents. Que faire si un échoue?
**Solution:** Pattern Saga avec compensations (rollback partiel)
**Apprentissage:** ACID ne fonctionne pas en distribué

## 3. Sécurité du Moteur de Règles
**Problème:** Jinja2 peut exécuter du code arbitraire
**Solution:** SandboxedEnvironment avec whitelist de fonctions
**Apprentissage:** Ne jamais faire confiance aux entrées utilisateur

## 4. Synchronisation Temps Réel
**Problème:** Cohérence éventuelle entre systèmes
**Solution:** Cache invalidation + polling régulier
**Apprentissage:** CAP theorem en pratique

---

# SLIDE 19: DIFFICULTÉS RENCONTRÉES (2/2)

## 5. Mapping d'Attributs LDAP
**Problème:** Chaque LDAP a des schémas différents (uid vs sAMAccountName)
**Solution:** Configuration mappings par connecteur
**Apprentissage:** Standards ≠ implémentations

## 6. Coûts et Latence IA
**Problème:** Chaque requête OpenAI = $$ + 5-10 secondes
**Solution:** Cache des réponses fréquentes, rate limiting
**Apprentissage:** L'IA a un coût opérationnel

## 7. Gestion des Secrets
**Problème:** 20+ variables d'environnement sensibles
**Solution:** Fichier .env + validation au démarrage
**Apprentissage:** Configuration ≠ Code

## 8. Tests d'Intégration
**Problème:** Tester avec 15 services Docker = complexe
**Solution:** Mocks pour tests unitaires, environnement dédié pour intégration
**Apprentissage:** Pyramide des tests

---

# SLIDE 20: CE QUE NOUS AVONS APPRIS

## Compétences Techniques
- Architecture microservices
- API REST avec FastAPI
- React moderne (hooks, state management)
- Docker & orchestration
- Sécurité (JWT, RBAC, sandboxing)
- Bases de données (SQL, Vector DB)

## Compétences Projet
- Gestion de backlog Agile
- Travail en binôme (pair programming)
- Documentation technique
- Versionnage Git

## Concepts IAM
- Provisionnement d'identités
- Réconciliation
- Workflows d'approbation
- Audit et conformité

---

# SLIDE 21: DÉMONSTRATION VIDÉO

## Scénarios démontrés:

**Scénario 1: Création d'un employé (5 min)**
1. Création dans Odoo (RH)
2. Synchronisation vers MidPoint
3. Attribution du rôle "Employé Complet"
4. Vérification compte LDAP créé automatiquement
5. Ajout à un groupe LDAP

**Scénario 2: Gestion des règles (3 min)**
1. Visualisation des règles existantes
2. Test d'une règle avec données
3. Modification d'une règle

**Scénario 3: Workflow d'approbation (3 min)**
1. Demande de création compte sensible
2. Notification manager
3. Approbation avec commentaire
4. Exécution automatique

**Scénario 4: Réconciliation (2 min)**
1. Comparaison live des systèmes
2. Détection d'un compte orphelin
3. Résolution

---

# SLIDE 22: ROADMAP FUTURE

## Court terme (1-2 mois)
- Finaliser intégration Keycloak
- Templates email personnalisables
- Tests automatisés complets

## Moyen terme (3-6 mois)
- Déploiement Kubernetes
- Connecteurs supplémentaires (Azure AD, Google Workspace)
- Dashboard analytics avancé

## Long terme (6-12 mois)
- Application mobile
- Machine Learning pour détection d'anomalies
- Multi-tenancy pour SaaS

## Vision
Devenir une plateforme IAM No-Code complète, accessible aux PME qui n'ont pas les ressources pour des solutions entreprise comme SailPoint ou Saviynt.

---

# SLIDE 23: CONCLUSION

## Ce que nous avons réalisé

**Objectif initial:** Simplifier MidPoint avec une interface No-Code
**Résultat:** Plateforme complète avec 12+ fonctionnalités opérationnelles

## Chiffres clés
- **16,000+** lignes de code Python (Backend)
- **5,000+** lignes de code TypeScript (Frontend)
- **15** services Docker orchestrés
- **80+** endpoints API REST
- **6** connecteurs systèmes

## Points forts du projet
- Architecture moderne et scalable
- Interface utilisateur intuitive
- Automatisation intelligente (règles + IA)
- Sécurité intégrée (JWT, RBAC, audit)

## Merci de votre attention!

**Questions?**

---

# SLIDE 24: ANNEXES - LIENS & RESSOURCES

## Accès au projet
- **Code source:** [Repository Git]
- **Documentation:** /docs/
- **Vidéo démo:** [Lien vidéo]

## Technologies utilisées
- MidPoint: https://evolveum.com/midpoint/
- FastAPI: https://fastapi.tiangolo.com/
- React: https://react.dev/
- Docker: https://www.docker.com/

## Contact
- **Zhmuryk Andrii:** [email]
- **Aydin Ibrahim:** [email]

## Remerciements
- Professeur encadrant
- Département Informatique UPEC
- Communauté Open Source

---

# NOTES POUR LA PRÉSENTATION

## Timing suggéré (20 minutes)
- Slides 1-3: Introduction & Problématique (3 min)
- Slides 4-5: Backlog (2 min)
- Slides 6-8: Architecture (3 min)
- Slides 9-15: Fonctionnalités implémentées (5 min)
- Slides 16-17: Fonctionnalités partielles et futures (2 min)
- Slides 18-19: Difficultés (2 min)
- Slide 20: Apprentissages (1 min)
- Slide 21: Intro vidéo (30 sec)
- Slides 22-23: Roadmap & Conclusion (1 min 30)

## Conseils
- Préparer des réponses aux questions courantes
- Avoir la démo vidéo prête en backup
- Connaître les détails techniques de chaque fonctionnalité
