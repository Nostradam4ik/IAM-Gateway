# Présentation IAM Gateway - Projet #3
## Passerelle IAM Intelligente avec MidPoint

---

# SLIDE 1: Page de Titre

## **Projet #3 - Passerelle IAM Intelligente**
### Gateway de Provisioning Multi-Cibles avec MidPoint

**Équipe**: [Votre Nom]
**Date**: Janvier 2026
**Version**: 1.0

---

# SLIDE 2: Sommaire

1. **Rappel du Projet**
2. **Architecture Mise en Place**
3. **Fonctionnalités Implémentées**
4. **Nouveautés Récentes**
5. **Démonstration**
6. **Ce qui Reste à Faire**
7. **Difficultés Rencontrées**
8. **Conclusion**

---

# SLIDE 3: Rappel du Projet

## **Objectif Principal**

Développer une **passerelle IAM intelligente** capable de:

- ✅ Centraliser la gestion des identités via **MidPoint**
- ✅ Provisionner automatiquement vers plusieurs systèmes cibles
- ✅ Appliquer des règles métier dynamiques
- ✅ Gérer des workflows d'approbation
- ✅ Fournir un assistant IA pour les opérations

### **Systèmes Intégrés**
| Source | Hub IAM | Cibles |
|--------|---------|--------|
| Odoo (RH) | MidPoint | OpenLDAP, PostgreSQL, Keycloak |

---

# SLIDE 4: Architecture Globale

```
┌─────────────────────────────────────────────────────────────┐
│                        FRONTEND                              │
│                    React + TypeScript                        │
│                     (Port 3000)                              │
└─────────────────────────┬───────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────┐
│                     GATEWAY IAM                              │
│                    FastAPI (Python)                          │
│                     (Port 8000)                              │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐         │
│  │ Rules   │  │Workflows│  │  Audit  │  │   AI    │         │
│  │ Engine  │  │ Manager │  │ Service │  │Assistant│         │
│  └─────────┘  └─────────┘  └─────────┘  └─────────┘         │
└─────────────────────────┬───────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────┐
│                      MIDPOINT                                │
│                   Hub IAM Central                            │
│                     (Port 8080)                              │
│           Rôles | Mappings | Synchronisation                 │
└──────────┬─────────────────────────────┬────────────────────┘
           │                             │
    ┌──────▼──────┐              ┌───────▼───────┐
    │  OpenLDAP   │              │  PostgreSQL   │
    │   :10389    │              │    :55432     │
    └─────────────┘              └───────────────┘
```

---

# SLIDE 5: Fonctionnalités Implémentées (1/2)

## **1. Provisioning Multi-Cibles** ✅

- Création, modification, suppression d'utilisateurs
- Support de 7 types de systèmes cibles
- Transactions atomiques avec rollback

## **2. Moteur de Règles Dynamique** ✅

- Règles en YAML/JSON avec Jinja2
- Calcul automatique d'attributs (login, email, etc.)
- Environnement sandbox sécurisé

## **3. Gestion des Workflows** ✅

- Approbations multi-niveaux (jusqu'à 5)
- Timeout configurable (72h par défaut)
- Historique des décisions

---

# SLIDE 6: Fonctionnalités Implémentées (2/2)

## **4. Comparaison Live** ✅

- Statistiques temps réel de tous les systèmes
- Détection des écarts entre systèmes
- Synchronisation manuelle possible

## **5. Audit Complet** ✅

- Traçabilité de toutes les opérations
- Recherche sémantique (Qdrant)
- Logs structurés

## **6. Interface Utilisateur** ✅

- Dashboard avec métriques
- 10+ pages fonctionnelles
- Gestion des connecteurs

---

# SLIDE 7: Connecteurs Implémentés

| Connecteur | Description | Status |
|------------|-------------|--------|
| **OdooConnector** | Connexion XML-RPC à Odoo ERP | ✅ Fonctionnel |
| **LDAPConnector** | Provisioning vers OpenLDAP | ✅ Fonctionnel |
| **SQLConnector** | Base PostgreSQL Intranet | ✅ Fonctionnel |
| **MidPointConnector** | Intégration REST API MidPoint | ✅ Fonctionnel |
| **KeycloakConnector** | Gestion des utilisateurs Keycloak | 🔄 Partiel |
| **CSVConnector** | Import/Export CSV | ✅ Fonctionnel |

### **Pattern Factory**
```python
connector = ConnectorFactory.get_connector("LDAP")
connector.create_account(user_data)
```

---

# SLIDE 8: Nouveautés Récentes

## **Ce qui a été fait dernièrement**

### 1. **Architecture via MidPoint** 🆕
- Tout passe maintenant par MidPoint
- Plus de connexion directe aux systèmes cibles
- `POST /api/v1/provision-midpoint/users`

### 2. **Connecteur CSV pour Odoo** 🆕
- Synchronisation Odoo → MidPoint via fichier CSV
- Live Sync toutes les 5 minutes
- Documentation complète

### 3. **Gestion des Permissions** 🆕
- Niveaux de droits configurables
- API `/api/v1/permissions/*`
- Interface UI dédiée

### 4. **Documentation Technique** 🆕
- 15+ guides de configuration
- Architecture détaillée
- Scripts de démonstration

---

# SLIDE 9: Démonstration - Flux Complet

## **Scénario: Nouvel Employé**

```
1️⃣ RH crée l'employé dans ODOO
   └─> Jean Dupont, IT Department

2️⃣ Gateway IAM détecte le changement
   └─> Validation des données
   └─> Application des règles (génération login: jdupont)

3️⃣ Gateway envoie à MidPoint
   └─> POST /midpoint/ws/rest/users
   └─> Assignation des rôles

4️⃣ MidPoint provisionne automatiquement
   └─> LDAP: uid=jdupont,ou=people,dc=example,dc=com
   └─> PostgreSQL: INSERT INTO users...

5️⃣ Vérification et audit
   └─> Statuts collectés
   └─> Log enregistré
```

---

# SLIDE 10: Démonstration - Captures

## **1. Interface Odoo** (Source RH)
- URL: http://localhost:8069
- Créer un employé avec email et département

## **2. Dashboard Gateway**
- URL: http://localhost:3000
- Voir les opérations de provisioning

## **3. MidPoint** (Hub IAM)
- URL: http://localhost:8080/midpoint
- Voir l'utilisateur créé et ses rôles

## **4. Vérification LDAP**
```bash
docker exec openldap ldapsearch -x \
  -b "ou=people,dc=example,dc=com" "(uid=jdupont)"
```

---

# SLIDE 11: Ce qui Reste à Faire

## **Phase 2: Configuration MidPoint** 🔜

| Tâche | Priorité | Status |
|-------|----------|--------|
| Configurer connecteur LDAP dans MidPoint UI | Haute | 🔄 En cours |
| Configurer connecteur PostgreSQL dans MidPoint UI | Haute | 🔄 En cours |
| Créer les rôles avec inducements | Haute | ⏳ À faire |
| Tester le Live Sync CSV | Moyenne | ⏳ À faire |

## **Phase 3: Tests d'Intégration** 🔜

| Tâche | Priorité | Status |
|-------|----------|--------|
| Test création utilisateur bout en bout | Haute | ⏳ À faire |
| Test modification et propagation | Haute | ⏳ À faire |
| Test suppression et nettoyage | Moyenne | ⏳ À faire |
| Test workflows d'approbation | Moyenne | ⏳ À faire |

---

# SLIDE 12: Ce qui Reste à Faire (Suite)

## **Phase 4: Fonctionnalités Avancées** 🔜

| Tâche | Priorité | Status |
|-------|----------|--------|
| Configurer Assistant IA (clé OpenAI) | Basse | ⏳ À faire |
| Intégration Keycloak complète | Moyenne | ⏳ À faire |
| Réconciliation automatique | Basse | ⏳ À faire |

## **Phase 5: Production** 🔜

| Tâche | Priorité | Status |
|-------|----------|--------|
| Tests de charge | Moyenne | ⏳ À faire |
| Sécurisation (HTTPS, secrets) | Haute | ⏳ À faire |
| Documentation utilisateur finale | Moyenne | ⏳ À faire |

---

# SLIDE 13: Ce qu'on n'a pas pu faire

## **Contraintes de Temps**

### 1. **Configuration complète MidPoint UI** ❌
- Les connecteurs sont codés mais pas tous configurés via l'interface MidPoint
- Raison: Problèmes de démarrage de MidPoint (driver PostgreSQL)

### 2. **Assistant IA fonctionnel** ❌
- L'API est prête mais nécessite une clé OpenAI payante
- Raison: Coût de l'API externe

### 3. **Tests automatisés complets** ❌
- Tests unitaires partiels
- Raison: Priorité donnée aux fonctionnalités

### 4. **Intégration Keycloak** ❌
- Connecteur basique seulement
- Raison: Complexité de la configuration OIDC

---

# SLIDE 14: Difficultés Rencontrées

## **1. MidPoint - Problèmes de Driver**
- **Problème**: Conflit entre drivers H2 et PostgreSQL
- **Impact**: MidPoint ne démarre pas correctement
- **Solution**: Utilisation de la version 4.4 avec H2 embedded

## **2. Docker Networking**
- **Problème**: Communication entre conteneurs
- **Impact**: Connexions timeout
- **Solution**: Configuration réseau `iam-network`

## **3. Permissions Volume**
- **Problème**: Fichiers créés par Docker avec mauvaises permissions
- **Impact**: Impossible de modifier certains fichiers
- **Solution**: Utilisation de volumes nommés Docker

## **4. Synchronisation Asynchrone**
- **Problème**: Timing entre création et vérification
- **Impact**: Faux négatifs lors des vérifications
- **Solution**: Ajout de délais et retry

---

# SLIDE 15: Points Forts du Projet

## **Architecture Solide** ✅
- Séparation claire des responsabilités
- Pattern Factory pour les connecteurs
- Services modulaires et testables

## **Code Propre** ✅
- ~13,000 lignes de code Python
- Typage avec Pydantic
- Logging structuré (structlog)

## **Documentation Complète** ✅
- 20+ fichiers de documentation
- Guides pas à pas
- Architecture technique détaillée

## **Extensibilité** ✅
- Nouveaux connecteurs faciles à ajouter
- Règles configurables sans code
- API REST standard

---

# SLIDE 16: Statistiques du Projet

## **Code**

| Composant | Fichiers | Lignes (approx) |
|-----------|----------|-----------------|
| Backend Python | 48 | ~13,000 |
| Frontend React | 15+ | ~5,000 |
| Configuration | 20+ | ~2,000 |
| Documentation | 25+ | ~3,000 |

## **Infrastructure**

| Service | Image | Port |
|---------|-------|------|
| Gateway API | FastAPI | 8000 |
| Frontend | React/Nginx | 3000 |
| MidPoint | Evolveum | 8080 |
| OpenLDAP | Osixia | 10389 |
| PostgreSQL | Postgres:15 | 55432 |
| Redis | Redis:7 | 6379 |

---

# SLIDE 17: Prochaines Étapes Recommandées

## **Court Terme (1-2 semaines)**

1. ✅ Finaliser la configuration MidPoint
2. ✅ Tester le flux complet Odoo → MidPoint → LDAP
3. ✅ Documenter les tests effectués

## **Moyen Terme (1 mois)**

1. 🔄 Ajouter des tests automatisés
2. 🔄 Configurer l'Assistant IA
3. 🔄 Intégrer Keycloak complètement

## **Long Terme**

1. 📅 Mise en production
2. 📅 Monitoring et alerting
3. 📅 Formation utilisateurs

---

# SLIDE 18: Conclusion

## **Bilan du Projet**

### ✅ **Réussites**
- Architecture IAM complète et fonctionnelle
- Gateway intelligente avec règles et workflows
- Intégration MidPoint comme hub central
- Interface utilisateur moderne

### 🔄 **En Cours**
- Configuration finale des connecteurs MidPoint
- Tests d'intégration

### ⏳ **À Compléter**
- Assistant IA
- Tests automatisés
- Documentation utilisateur

---

# SLIDE 19: Questions ?

## **Merci de votre attention!**

### **Ressources**

- **Repository**: github.com/Nostradam4ik/Project3
- **Documentation**: `/docs/guides/`
- **API**: http://localhost:8000/docs

### **Contact**
- Email: [votre.email@example.com]

---

# SLIDE 20: Annexes - Identifiants

## **Accès aux Systèmes**

| Système | URL | Login | Password |
|---------|-----|-------|----------|
| Odoo | localhost:8069 | admin | admin |
| MidPoint | localhost:8080/midpoint | administrator | 5ecr3t |
| Gateway | localhost:8000 | admin | admin123 |
| phpLDAPadmin | localhost:8088 | cn=admin,dc=example,dc=com | secret |
| PostgreSQL | localhost:55432 | intranet | intranet |

---

# SLIDE 21: Annexes - Commandes Utiles

```bash
# Démarrer tous les services
docker compose up -d

# Vérifier les services
docker ps --format "table {{.Names}}\t{{.Status}}"

# Logs MidPoint
docker logs midpoint-core -f

# Test LDAP
docker exec openldap ldapsearch -x \
  -b "dc=example,dc=com" \
  -D "cn=admin,dc=example,dc=com" -w secret

# Test PostgreSQL
docker exec intranet-db psql -U intranet -d intranet \
  -c "SELECT COUNT(*) FROM users;"

# Générer token Gateway
curl -X POST http://localhost:8000/api/v1/admin/token \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'
```
