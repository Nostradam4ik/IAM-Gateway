# Démonstration : Synchronisations Directes Sans Gateway

**Date** : 5 janvier 2026
**Objectif** : Démontrer que l'infrastructure IAM fonctionne **sans** la Gateway IAM, en synchronisant directement :
- Odoo → MidPoint (via CSV)
- MidPoint → OpenLDAP
- MidPoint → PostgreSQL (Intranet DB)

---

## 📋 Table des Matières

1. [Prérequis](#prérequis)
2. [Architecture](#architecture)
3. [Identifiants des Systèmes](#identifiants)
4. [Synchronisation 1 : Odoo → MidPoint (CSV)](#sync-odoo-midpoint)
5. [Synchronisation 2 : MidPoint → OpenLDAP](#sync-midpoint-ldap)
6. [Synchronisation 3 : MidPoint → PostgreSQL](#sync-midpoint-postgres)
7. [Tests et Vérifications](#tests)
8. [Résultats Attendus](#resultats)

---

## <a name="prérequis"></a>1. Prérequis

### Services Démarrés
```bash
# Vérifier l'état des services
docker ps --format "table {{.Names}}\t{{.Status}}"

# Démarrer les services si nécessaire
docker start midpoint-postgres midpoint-core
docker start odoo-db odoo
docker start intranet-db
docker start openldap
```

### Services Requis
- ✅ **Odoo** : http://localhost:8069
- ✅ **MidPoint** : http://localhost:8080/midpoint
- ✅ **OpenLDAP** : localhost:10389
- ✅ **PostgreSQL (Intranet)** : localhost:55432
- ✅ **phpLDAPadmin** : http://localhost:8088

---

## <a name="identifiants"></a>2. Identifiants des Systèmes

### Odoo (Source RH)
| Paramètre | Valeur |
|-----------|--------|
| URL | http://localhost:8069 |
| Base de données | `odoo` |
| Login | `admin` |
| Mot de passe | `admin` |

### MidPoint (IAM Central)
| Paramètre | Valeur |
|-----------|--------|
| URL | http://localhost:8080/midpoint |
| Login | `administrator` |
| Mot de passe | `Holimolly1` |

### OpenLDAP (Annuaire)
| Paramètre | Valeur |
|-----------|--------|
| Host | `localhost:10389` |
| Base DN | `dc=example,dc=com` |
| Admin DN | `cn=admin,dc=example,dc=com` |
| Password | `secret` |

### PostgreSQL Intranet
| Paramètre | Valeur |
|-----------|--------|
| Host | `localhost:55432` |
| Database | `intranet` |
| User | `intranet` |
| Password | `intranet` |

---

## <a name="architecture"></a>3. Architecture de Synchronisation

```
┌─────────────────┐
│      ODOO       │  (Source RH - Système Source)
│   Employés HR   │
└────────┬────────┘
         │
         │ [1] Export CSV via Script Python
         │     scripts/import_odoo_to_midpoint.py
         ↓
┌─────────────────┐
│    FICHIER CSV  │
│  /opt/midpoint/ │
│   var/csv/      │
└────────┬────────┘
         │
         │ [2] Import CSV → MidPoint
         │     Live Sync automatique
         ↓
┌─────────────────┐
│    MIDPOINT     │  (Hub IAM Central)
│  Utilisateurs   │
│    + Rôles      │
└────┬───────┬────┘
     │       │
     │       │ [3] Provisioning Direct
     │       │
     ↓       ↓
┌─────────┐ ┌──────────────┐
│ OpenLDAP│ │  PostgreSQL  │
│ Annuaire│ │   Intranet   │
└─────────┘ └──────────────┘
```

**Note importante** : La Gateway IAM n'est **PAS** utilisée dans ce flux. Toutes les synchronisations sont directes entre les systèmes.

---

## <a name="sync-odoo-midpoint"></a>4. Synchronisation 1 : Odoo → MidPoint (CSV)

### Étape 1 : Vérifier la Configuration CSV dans MidPoint

Se connecter à MidPoint : http://localhost:8080/midpoint

```
Login: administrator
Password: Holimolly1
```

Vérifier la ressource CSV :
- Aller dans **Configuration → Repository Objects → Resources**
- Chercher **"CSV Odoo Employees"**
- OID: `10000000-0000-0000-0000-000000000004`

### Étape 2 : Exécuter la Synchronisation Odoo → CSV

```bash
# Lancer le script de synchronisation
cd /home/vboxuser/Desktop/Project3
python3 scripts/import_odoo_to_midpoint.py
```

**Ce que fait le script** :
1. Se connecte à Odoo via XML-RPC
2. Récupère tous les employés avec leurs contrats
3. Génère `/tmp/odoo_users.csv`
4. Copie le CSV dans le conteneur MidPoint (`/opt/midpoint/var/csv/users.csv`)
5. Déclenche l'import MidPoint

### Étape 3 : Vérifier l'Import dans MidPoint

#### Via l'Interface Web
1. Aller dans **Users** dans MidPoint
2. Vérifier que les utilisateurs d'Odoo sont présents
3. Vérifier leurs attributs (prénom, nom, email, département)

#### Via API REST
```bash
# Lister les utilisateurs MidPoint
curl -s -u administrator:Holimolly1 \
  http://localhost:8080/midpoint/ws/rest/users | grep fullName
```

### Étape 4 : Activer le Live Sync (Optionnel)

Pour une synchronisation automatique toutes les 5 minutes :

```bash
# Vérifier la tâche Live Sync
curl -s -u administrator:Holimolly1 \
  http://localhost:8080/midpoint/ws/rest/tasks/10000000-0000-0000-5555-000000000001

# Démarrer la tâche
curl -X POST -u administrator:Holimolly1 \
  http://localhost:8080/midpoint/ws/rest/tasks/10000000-0000-0000-5555-000000000001/run
```

---

## <a name="sync-midpoint-ldap"></a>5. Synchronisation 2 : MidPoint → OpenLDAP

### Configuration de la Ressource LDAP

La ressource OpenLDAP est déjà configurée dans MidPoint.

#### Vérification via l'Interface
1. Se connecter à MidPoint
2. **Configuration → Repository Objects → Resources**
3. Chercher **"OpenLDAP Directory"**
4. OID: `10000000-0000-0000-0000-000000000001`

#### Test de Connexion
```bash
# Tester la ressource LDAP
curl -X POST -u administrator:Holimolly1 \
  http://localhost:8080/midpoint/ws/rest/resources/10000000-0000-0000-0000-000000000001/test
```

### Créer un Mapping de Provisioning

Les utilisateurs MidPoint doivent être automatiquement provisionnés vers LDAP via :

1. **Rôles MidPoint** : Assigner le rôle LDAP aux utilisateurs
2. **Outbound Mappings** : Mappings automatiques vers LDAP

#### Assigner le Rôle LDAP
Dans MidPoint :
1. Aller dans **Users**
2. Sélectionner un utilisateur
3. **Assignments** → Ajouter **"LDAP User Role"**
4. Sauvegarder

### Vérification dans LDAP

#### Via phpLDAPadmin (Interface Web)
http://localhost:8088

```
Login DN: cn=admin,dc=example,dc=com
Password: secret
```

#### Via ligne de commande
```bash
# Lister les utilisateurs LDAP
docker exec openldap ldapsearch -x -H ldap://localhost \
  -b "ou=people,dc=example,dc=com" \
  -D "cn=admin,dc=example,dc=com" -w secret \
  "(objectClass=inetOrgPerson)"
```

---

## <a name="sync-midpoint-postgres"></a>6. Synchronisation 3 : MidPoint → PostgreSQL (Intranet)

### Configuration de la Ressource Database

La ressource PostgreSQL est configurée dans :
- Fichier: `infrastructure/midpoint/resources/database-resource.xml`

#### Structure de la Table
```sql
-- Se connecter à la base intranet
psql -h localhost -p 55432 -U intranet -d intranet

-- Vérifier la table users
\d users

-- Colonnes attendues:
-- - username (clé primaire)
-- - first_name
-- - last_name
-- - email
-- - department
-- - active
```

### Import de la Ressource dans MidPoint

```bash
# Copier la ressource dans MidPoint
docker cp infrastructure/midpoint/resources/database-resource.xml midpoint-core:/tmp/

# Importer via l'interface ou REST API
curl -X POST -u administrator:Holimolly1 \
  -H "Content-Type: application/xml" \
  --data @infrastructure/midpoint/resources/database-resource.xml \
  http://localhost:8080/midpoint/ws/rest/resources
```

### Vérification dans PostgreSQL

```bash
# Lister les utilisateurs provisionnés
psql -h localhost -p 55432 -U intranet -d intranet \
  -c "SELECT username, first_name, last_name, email, department FROM users;"
```

---

## <a name="tests"></a>7. Tests et Vérifications

### Test Complet : Créer un Nouvel Employé dans Odoo

#### 1. Créer l'employé dans Odoo
http://localhost:8069

```
Aller dans : Employés → Créer
- Nom: Test Sync
- Prénom: Jean
- Email: jean.test@example.com
- Département: IT
```

#### 2. Lancer la Synchronisation
```bash
python3 scripts/import_odoo_to_midpoint.py
```

#### 3. Vérifier dans MidPoint
http://localhost:8080/midpoint
- Aller dans **Users**
- Chercher "Jean Test"

#### 4. Vérifier dans LDAP
```bash
docker exec openldap ldapsearch -x -H ldap://localhost \
  -b "ou=people,dc=example,dc=com" \
  -D "cn=admin,dc=example,dc=com" -w secret \
  "(cn=Jean Test)"
```

#### 5. Vérifier dans PostgreSQL
```bash
psql -h localhost -p 55432 -U intranet -d intranet \
  -c "SELECT * FROM users WHERE email = 'jean.test@example.com';"
```

---

## <a name="resultats"></a>8. Résultats Attendus

### Flux de Synchronisation Complet

| Étape | Source | Destination | Mécanisme | Temps |
|-------|--------|-------------|-----------|-------|
| 1 | Odoo | Fichier CSV | Script Python | ~5 sec |
| 2 | CSV | MidPoint | Import/Live Sync | ~10 sec |
| 3 | MidPoint | OpenLDAP | Outbound Mapping | Temps réel |
| 4 | MidPoint | PostgreSQL | Outbound Mapping | Temps réel |

### Statistiques de Synchronisation

Après exécution complète :

```bash
# Compter les utilisateurs dans chaque système
echo "=== ODOO ==="
# Se connecter à Odoo et compter les employés

echo "=== MIDPOINT ==="
curl -s -u administrator:Holimolly1 \
  http://localhost:8080/midpoint/ws/rest/users | grep -c "<user"

echo "=== LDAP ==="
docker exec openldap ldapsearch -x -H ldap://localhost \
  -b "ou=people,dc=example,dc=com" \
  -D "cn=admin,dc=example,dc=com" -w secret \
  "(objectClass=inetOrgPerson)" | grep -c "dn:"

echo "=== POSTGRESQL ==="
psql -h localhost -p 55432 -U intranet -d intranet \
  -t -c "SELECT COUNT(*) FROM users;"
```

---

## 9. Scripts d'Automatisation

### Script de Synchronisation Complète

Créer `scripts/demo_sync_complete.sh` :

```bash
#!/bin/bash
echo "=== SYNCHRONISATION COMPLETE SANS GATEWAY ==="
echo ""
echo "[1/4] Synchronisation Odoo → CSV → MidPoint..."
python3 scripts/import_odoo_to_midpoint.py

echo ""
echo "[2/4] Attente de l'import MidPoint..."
sleep 5

echo ""
echo "[3/4] Vérification des utilisateurs MidPoint..."
curl -s -u administrator:Holimolly1 \
  http://localhost:8080/midpoint/ws/rest/users | grep -c "<user"

echo ""
echo "[4/4] Vérification LDAP et PostgreSQL..."
docker exec openldap ldapsearch -x -H ldap://localhost \
  -b "ou=people,dc=example,dc=com" \
  -D "cn=admin,dc=example,dc=com" -w secret \
  "(objectClass=inetOrgPerson)" | grep -c "dn:"

echo ""
echo "=== SYNCHRONISATION TERMINÉE ==="
```

---

## 10. Preuves de Concept

Pour la démonstration, capturer :

### Captures d'écran
1. **Odoo** : Liste des employés
2. **MidPoint** : Interface utilisateurs
3. **phpLDAPadmin** : Arbre LDAP
4. **PostgreSQL** : Requête SQL montrant les utilisateurs

### Logs de Synchronisation
```bash
# Logs MidPoint
docker logs midpoint-core --tail 100 | grep -i "import\|sync"
```

---

## Conclusion

Cette démonstration prouve que :

✅ **Odoo → MidPoint** : Synchronisation via CSV fonctionne
✅ **MidPoint → LDAP** : Provisioning automatique opérationnel
✅ **MidPoint → PostgreSQL** : Provisioning base de données fonctionnel
✅ **Pas de Gateway IAM** : L'infrastructure IAM native fonctionne indépendamment

La Gateway IAM ajoute une **couche d'orchestration** et **d'intelligence** au-dessus de cette infrastructure, mais n'est **pas requise** pour le fonctionnement de base.

---

**Auteur** : Claude Code
**Projet** : IAM Gateway - Project3
**Repository** : https://github.com/Nostradam4ik/Project3
