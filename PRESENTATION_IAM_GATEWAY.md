# Gateway IAM - Passerelle de Provisionnement Multi-Cibles

## Presentation du Projet

---

# 1. Introduction

## Qu'est-ce que la Gateway IAM ?

Une **passerelle intelligente** pour la gestion centralisee des identites numeriques.

**Probleme resolu :**
- Les entreprises ont plusieurs systemes (LDAP, ERP, bases de donnees...)
- Creer un utilisateur = le creer dans 5-10 systemes differents
- Risque d'erreurs, incoherences, perte de temps

**Notre solution :**
- Un point d'entree unique pour gerer toutes les identites
- Provisionnement automatique vers tous les systemes cibles
- Reconciliation et synchronisation en temps reel

---

# 2. Architecture Technique

## Stack Technologique

| Composant | Technologie |
|-----------|-------------|
| Backend | FastAPI (Python) |
| Frontend | React + TypeScript + Vite |
| Base de donnees | PostgreSQL |
| Cache | Redis |
| Recherche vectorielle | Qdrant |
| Conteneurisation | Docker Compose |

## Systemes Cibles Integres

- **LDAP/Active Directory** - Annuaire d'entreprise
- **PostgreSQL (Intranet)** - Base utilisateurs interne
- **Odoo** - ERP (contacts, utilisateurs)
- **MidPoint** - Solution IAM open-source
- **Keycloak** - Gestion des identites et SSO

---

# 3. Fonctionnalites Principales

## 3.1 Provisionnement Multi-Cibles

**Flux de creation d'utilisateur :**
1. Requete via API ou interface web
2. Application des regles metier
3. Workflow d'approbation (si requis)
4. Provisionnement simultane vers tous les systemes
5. Audit et tracabilite

## 3.2 Workflows d'Approbation

- Validation multi-niveaux (manager, RH, IT...)
- Delai d'expiration configurable
- Notifications automatiques
- Historique complet

## 3.3 Reconciliation

- Detection des incoherences entre systemes
- Comparaison en temps reel
- Resolution automatique ou manuelle
- Rapports de divergences

## 3.4 Regles Dynamiques

- Calcul automatique d'attributs (email, login...)
- Regles YAML/JSON editables
- Transformation de donnees
- Validation metier

---

# 4. Demonstration - Interfaces

## 4.1 Dashboard Principal
- Vue d'ensemble des operations
- Statistiques en temps reel
- Alertes et notifications

## 4.2 Operations de Provisionnement
- Liste des operations (succes, echec, en cours)
- Details de chaque operation
- Rollback si necessaire

## 4.3 Workflows
- Approbations en attente
- Historique des validations
- Actions rapides (approuver/rejeter)

## 4.4 Reconciliation
- Lancement de reconciliation
- Historique des jobs
- Divergences detectees

## 4.5 Comparaison Live (NOUVEAU)
- Statistiques temps reel de tous les systemes
- Comparaison croisee LDAP/SQL/Odoo
- Recherche d'utilisateur multi-systemes
- Vue detaillee Odoo

## 4.6 Niveaux de Droits (NOUVEAU)
- Gestion hierarchique des permissions (niveaux 1-5)
- Visualisation des droits par utilisateur
- Filtrage par departement
- Attribution et modification des niveaux

---

# 5. Systeme de Niveaux de Droits

## Hierarchie des Permissions (1-5)

| Niveau | Role | Description | Exemples |
|--------|------|-------------|----------|
| **1** | Visiteur | Acces minimal - Consultation uniquement | Stagiaire, Visiteur externe |
| **2** | Utilisateur | Acces standard - Actions basiques | Employe, Technicien |
| **3** | Operateur | Acces etendu - Gestion operations | Chef d'equipe, Superviseur |
| **4** | Manager | Acces avance - Validation equipe | Manager, Responsable RH |
| **5** | Chef Departement | Acces maximum (non-admin) | Directeur, VP |

## Permissions par Niveau

**Niveau 1 (Visiteur):**
- Voir le dashboard
- Voir son profil

**Niveau 2 (Utilisateur):**
- + Voir les operations
- + Creer des demandes
- + Voir ses propres demandes

**Niveau 3 (Operateur):**
- + Voir toutes les demandes
- + Approuver niveau 1
- + Exporter des donnees

**Niveau 4 (Manager):**
- + Approuver niveau 2
- + Gerer son equipe
- + Voir les logs d'audit
- + Configurer les regles

**Niveau 5 (Chef Departement):**
- + Approuver niveau 3
- + Gerer le departement
- + Voir tous les departements
- + Decisions strategiques

---

# 6. Donnees de Demo

## Volumes de Donnees

| Systeme | Utilisateurs/Contacts |
|---------|----------------------|
| LDAP | 118 utilisateurs |
| Odoo | 113 contacts + 7 users |
| Intranet SQL | ~143 utilisateurs |

## Operations Demo
- 10 operations de provisionnement
- 4 workflows en attente d'approbation
- 4 jobs de reconciliation
- 8 entrees d'audit

---

# 6. API REST

## Endpoints Principaux

```
POST /api/v1/provision/          - Creer un utilisateur
GET  /api/v1/provision/          - Lister les operations
GET  /api/v1/workflow/instances  - Lister les workflows
POST /api/v1/reconcile/start     - Lancer reconciliation
GET  /api/v1/live/stats          - Stats temps reel
GET  /api/v1/live/compare        - Comparaison systemes
GET  /api/v1/admin/audit/recent  - Logs d'audit
```

## Authentification
- JWT Token
- Roles: admin, iam_engineer, manager

---

# 7. Points Forts

## Innovation
- **Comparaison temps reel** entre tous les systemes
- **Recherche unifiee** d'utilisateurs
- **Reconciliation automatique** avec MidPoint

## Securite
- Authentification JWT
- Controle d'acces par roles
- Audit complet de toutes les actions
- Arret d'urgence

## Scalabilite
- Architecture microservices
- Conteneurisation Docker
- Cache Redis pour performances
- Base vectorielle pour recherche semantique

---

# 8. URLs d'Acces

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| API Backend | http://localhost:8000 |
| API Docs (Swagger) | http://localhost:8000/docs |
| Odoo | http://localhost:8069 |
| phpLDAPadmin | http://localhost:8088 |
| MidPoint | http://localhost:8080/midpoint |
| Keycloak | http://localhost:8081 |

## Identifiants Demo

**Frontend/API:**
- Username: `admin`
- Password: `admin123`

**Odoo:**
- Username: `admin`
- Password: `admin`

---

# 9. Conclusion

## Benefices

1. **Gain de temps** - Provisionnement automatise
2. **Reduction des erreurs** - Un seul point d'entree
3. **Conformite** - Audit et tracabilite complete
4. **Flexibilite** - Regles metier configurables
5. **Visibilite** - Dashboard et rapports temps reel

## Evolutions Futures

- Integration avec plus de systemes (ServiceNow, SAP...)
- Assistant IA pour mapping automatique
- Self-service utilisateur
- Notifications multi-canaux (email, Slack...)

---

# Merci !

## Questions ?

**Projet Gateway IAM**
- 14 services Docker
- 10+ pages frontend
- API REST complete
- Donnees de demo massives

