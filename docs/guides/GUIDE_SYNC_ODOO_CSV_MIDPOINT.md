# Guide : Synchronisation Odoo → CSV → MidPoint

## Introduction

Ce guide explique comment synchroniser les employés d'Odoo vers MidPoint en utilisant un fichier CSV comme intermédiaire. Cette architecture permet d'importer automatiquement les données RH dans le système IAM.

## Architecture de Synchronisation

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        FLUX DE SYNCHRONISATION                               │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────┐         ┌─────────────┐         ┌─────────────┐
│    ODOO     │         │     CSV     │         │  MIDPOINT   │
│   (Source)  │         │  (Transit)  │         │   (Hub)     │
│             │         │             │         │             │
│ ┌─────────┐ │  XML-   │ ┌─────────┐ │  CSV    │ ┌─────────┐ │
│ │   HR    │ │  RPC    │ │  File   │ │Connector│ │  Users  │ │
│ │Employee │ ├────────►│ │hr_sample│ ├────────►│ │         │ │
│ └─────────┘ │         │ │  .csv   │ │         │ └─────────┘ │
└─────────────┘         └─────────────┘         └─────────────┘
                              │
                    Script Python
                 odoo_to_midpoint_sync.py
```

## Prérequis

### Services Docker
```bash
# Vérifier que les services sont actifs
docker ps | grep -E "odoo|midpoint"

# Services requis :
# - odoo (port 8069)
# - midpoint-core (port 8080)
```

### Accès aux systèmes
| Système | URL | Identifiants |
|---------|-----|--------------|
| Odoo | http://localhost:8069 | admin / admin |
| MidPoint | http://localhost:8080/midpoint | administrator / 5ecr3t |

## Partie 1 : Configuration Odoo

### 1.1 Accéder au module Employés

1. Connectez-vous à Odoo : http://localhost:8069
2. Menu **Employés** (ou **Employees**)
3. Vous voyez la liste des employés existants

### 1.2 Créer un nouvel employé

1. Cliquez sur **Créer** (ou **Create**)
2. Remplissez les champs :
   - **Nom** : Prénom Nom (ex: Jean Dupont)
   - **Email professionnel** : email@example.com
   - **Département** : Sélectionnez ou créez
   - **Poste** : Titre du poste
   - **N° d'identification** : ID unique (optionnel)
3. Cliquez **Sauvegarder**

### 1.3 Structure des données Odoo

| Champ Odoo | Description | Exemple |
|------------|-------------|---------|
| `name` | Nom complet | Jean Dupont |
| `work_email` | Email professionnel | jean.dupont@example.com |
| `department_id` | Département | IT, RH, Finance |
| `job_title` | Poste | Développeur |
| `identification_id` | N° d'identification | EMP001 |

## Partie 2 : Script de Synchronisation

### 2.1 Emplacement du script

```
/home/vboxuser/Desktop/Project3/scripts/odoo_to_midpoint_sync.py
```

### 2.2 Configuration du script

Le script utilise des variables d'environnement (avec valeurs par défaut) :

```python
# Configuration Odoo
ODOO_URL = "http://localhost:8069"
ODOO_DB = "odoo"
ODOO_USER = "admin"
ODOO_PASSWORD = "admin"

# Configuration MidPoint
MIDPOINT_URL = "http://localhost:8080/midpoint"
MIDPOINT_USER = "administrator"
MIDPOINT_PASSWORD = "5ecr3t"

# Chemins des fichiers
CSV_PATH = "/home/vboxuser/Desktop/Project3/datasets/hr_employees.csv"
MIDPOINT_CSV_PATH = "/opt/midpoint/var/import/hr_sample.csv"
```

### 2.3 Fonctionnement du script

```
┌────────────────────────────────────────────────────────────────┐
│                    ÉTAPES DU SCRIPT                            │
└────────────────────────────────────────────────────────────────┘

1. CONNEXION ODOO
   ├── Connexion XML-RPC à Odoo
   └── Authentification avec uid

2. EXPORT EMPLOYÉS
   ├── Recherche tous les employés (hr.employee)
   └── Récupère : name, work_email, department_id, job_title, identification_id

3. CRÉATION CSV
   ├── Format : uid;givenName;familyName;email;department
   ├── Séparateur : point-virgule (;)
   └── Encodage : UTF-8

4. COPIE VERS MIDPOINT
   ├── docker cp vers le container midpoint-core
   └── Destination : /opt/midpoint/var/import/hr_sample.csv

5. DÉCLENCHEMENT IMPORT
   ├── Test de connexion à la ressource CSV
   └── Création d'une tâche d'import dans MidPoint
```

### 2.4 Exécution du script

```bash
# Exécution standard (avec export Odoo)
python3 /home/vboxuser/Desktop/Project3/scripts/odoo_to_midpoint_sync.py

# Utiliser le CSV existant (sans connexion Odoo)
python3 /home/vboxuser/Desktop/Project3/scripts/odoo_to_midpoint_sync.py --skip-odoo

# Lister les utilisateurs MidPoint
python3 /home/vboxuser/Desktop/Project3/scripts/odoo_to_midpoint_sync.py --list-users
```

### 2.5 Exemple de sortie

```
============================================================
  SYNCHRONISATION ODOO → CSV → MIDPOINT
============================================================
  Date: 2025-01-12 14:30:00
============================================================
[INFO] Connexion à Odoo: http://localhost:8069
[OK] Connecté à Odoo (uid: 2)
[INFO] Export des employés depuis Odoo...
[OK] 21 employés trouvés
[INFO] Création du fichier CSV: /home/vboxuser/Desktop/Project3/datasets/hr_employees.csv
  - Jean Dupont (jean.dupont@example.com)
  - Marie Martin (marie.martin@example.com)
  - Jean Dark (jeandark@example.com)
[OK] Fichier CSV créé avec 21 entrées
[INFO] Copie du CSV vers MidPoint...
[OK] CSV copié vers /opt/midpoint/var/import/hr_sample.csv
[INFO] Déclenchement de l'import MidPoint...
[OK] Tâche d'import créée dans MidPoint

[INFO] Utilisateurs dans MidPoint:
  - administrator (OID: 00000000...)
  - jean.dupont (OID: 4420cc05...)
  - jean.dark (OID: 8a8b9c1d...)
[OK] Total: 22 utilisateurs

============================================================
  SYNCHRONISATION TERMINÉE
============================================================
```

## Partie 3 : Format du Fichier CSV

### 3.1 Structure du CSV

```csv
uid;givenName;familyName;email;department
u1001;Jean;Dupont;jean.dupont@example.com;IT
u1002;Marie;Martin;marie.martin@example.com;RH
u1003;Pierre;Bernard;pierre.bernard@example.com;Finance
```

### 3.2 Description des colonnes

| Colonne | Description | Obligatoire | Exemple |
|---------|-------------|-------------|---------|
| `uid` | Identifiant unique | Oui | u1001 |
| `givenName` | Prénom | Oui | Jean |
| `familyName` | Nom de famille | Oui | Dupont |
| `email` | Adresse email | Oui | jean.dupont@example.com |
| `department` | Département | Non | IT |

### 3.3 Règles de formatage

- **Séparateur** : Point-virgule (`;`)
- **Encodage** : UTF-8
- **En-tête** : Première ligne obligatoire
- **Guillemets** : Non requis sauf si valeur contient `;`

## Partie 4 : Configuration MidPoint - Ressource CSV

### 4.1 Définition de la ressource

Fichier : `/home/vboxuser/Desktop/Project3/infrastructure/midpoint/resources/hr-csv-complete.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<resource xmlns="http://midpoint.evolveum.com/xml/ns/public/common/common-3"
          xmlns:q="http://prism.evolveum.com/xml/ns/public/query-3"
          xmlns:icfc="http://midpoint.evolveum.com/xml/ns/public/connector/icf-1/connector-schema-3"
          xmlns:ri="http://midpoint.evolveum.com/xml/ns/public/resource/instance-3"
          oid="8a8b9c1d-0002-0000-0000-000000000001">

  <name>HR CSV Resource</name>
  <description>CSV resource for HR employees from Odoo</description>

  <!-- Référence au connecteur CSV -->
  <connectorRef type="ConnectorType">
    <filter>
      <q:equal>
        <q:path>connectorType</q:path>
        <q:value>com.evolveum.polygon.connector.csv.CsvConnector</q:value>
      </q:equal>
    </filter>
  </connectorRef>

  <!-- Configuration du connecteur -->
  <connectorConfiguration>
    <icfc:configurationProperties>
      <icfccsv:filePath>/opt/midpoint/var/import/hr_sample.csv</icfccsv:filePath>
      <icfccsv:encoding>UTF-8</icfccsv:encoding>
      <icfccsv:fieldDelimiter>;</icfccsv:fieldDelimiter>
      <icfccsv:uniqueAttribute>uid</icfccsv:uniqueAttribute>
      <icfccsv:nameAttribute>uid</icfccsv:nameAttribute>
    </icfc:configurationProperties>
  </connectorConfiguration>

  <!-- ... schemaHandling et synchronization ... -->
</resource>
```

### 4.2 Configuration du connecteur

| Paramètre | Valeur | Description |
|-----------|--------|-------------|
| `filePath` | `/opt/midpoint/var/import/hr_sample.csv` | Chemin du fichier dans le container |
| `encoding` | `UTF-8` | Encodage du fichier |
| `fieldDelimiter` | `;` | Séparateur de champs |
| `uniqueAttribute` | `uid` | Colonne identifiant unique |
| `nameAttribute` | `uid` | Colonne pour le nom |

### 4.3 Mappings Inbound (CSV → MidPoint)

Les mappings définissent comment les colonnes CSV sont transformées en attributs MidPoint :

```xml
<schemaHandling>
  <objectType>
    <kind>account</kind>
    <intent>default</intent>
    <displayName>HR Employee</displayName>
    <default>true</default>
    <objectClass>ri:AccountObjectClass</objectClass>

    <!-- uid → name (identifiant MidPoint) -->
    <attribute>
      <ref>ri:uid</ref>
      <displayName>Employee ID</displayName>
      <inbound>
        <strength>strong</strength>
        <target>
          <path>name</path>
        </target>
      </inbound>
    </attribute>

    <!-- givenName → givenName -->
    <attribute>
      <ref>ri:givenName</ref>
      <displayName>First Name</displayName>
      <inbound>
        <target>
          <path>givenName</path>
        </target>
      </inbound>
    </attribute>

    <!-- familyName → familyName -->
    <attribute>
      <ref>ri:familyName</ref>
      <displayName>Last Name</displayName>
      <inbound>
        <target>
          <path>familyName</path>
        </target>
      </inbound>
    </attribute>

    <!-- email → emailAddress -->
    <attribute>
      <ref>ri:email</ref>
      <displayName>Email</displayName>
      <inbound>
        <target>
          <path>emailAddress</path>
        </target>
      </inbound>
    </attribute>

    <!-- department → organizationalUnit -->
    <attribute>
      <ref>ri:department</ref>
      <displayName>Department</displayName>
      <inbound>
        <target>
          <path>organizationalUnit</path>
        </target>
      </inbound>
    </attribute>

  </objectType>
</schemaHandling>
```

### 4.4 Table des mappings

| Colonne CSV | Attribut MidPoint | Type de mapping |
|-------------|-------------------|-----------------|
| `uid` | `name` | inbound (strong) |
| `givenName` | `givenName` | inbound |
| `familyName` | `familyName` | inbound |
| `email` | `emailAddress` | inbound |
| `department` | `organizationalUnit` | inbound |

### 4.5 Configuration de la synchronisation

```xml
<synchronization>
  <objectSynchronization>
    <name>HR Employee Sync</name>
    <enabled>true</enabled>
    <focusType>UserType</focusType>
    <kind>account</kind>
    <intent>default</intent>

    <!-- Corrélation : comment trouver l'utilisateur existant -->
    <correlation>
      <q:equal>
        <q:path>name</q:path>
        <expression>
          <path>$projection/attributes/ri:uid</path>
        </expression>
      </q:equal>
    </correlation>

    <!-- Réactions selon la situation -->
    <reaction>
      <situation>unmatched</situation>
      <action>
        <handlerUri>http://midpoint.evolveum.com/xml/ns/public/model/action-3#addFocus</handlerUri>
      </action>
    </reaction>

    <reaction>
      <situation>linked</situation>
      <synchronize>true</synchronize>
    </reaction>

    <reaction>
      <situation>unlinked</situation>
      <action>
        <handlerUri>http://midpoint.evolveum.com/xml/ns/public/model/action-3#link</handlerUri>
      </action>
    </reaction>

  </objectSynchronization>
</synchronization>
```

### 4.6 Situations de synchronisation

| Situation | Description | Action |
|-----------|-------------|--------|
| `unmatched` | Compte CSV sans utilisateur MidPoint | Créer l'utilisateur (`addFocus`) |
| `linked` | Compte CSV lié à un utilisateur | Synchroniser les attributs |
| `unlinked` | Compte CSV avec utilisateur existant non lié | Lier les deux (`link`) |

## Partie 5 : Import dans MidPoint

### 5.1 Import via l'interface

1. Menu **Resources** → **All resources**
2. Cliquez sur **HR CSV Resource**
3. Onglet **Content** ou **Accounts**
4. Cliquez sur **Import** (icône flèche vers le bas)
5. Sélectionnez les options d'import
6. Cliquez **Import**

### 5.2 Import via tâche planifiée

1. Menu **Server tasks** → **New task**
2. Type : **Import task**
3. Configurez :
   - **Resource** : HR CSV Resource
   - **Object class** : AccountObjectClass
4. Exécutez la tâche

### 5.3 Import via API REST

```bash
# Créer une tâche d'import
curl -X POST "http://localhost:8080/midpoint/ws/rest/tasks" \
  -u administrator:5ecr3t \
  -H "Content-Type: application/xml" \
  -d '<?xml version="1.0" encoding="UTF-8"?>
<task xmlns="http://midpoint.evolveum.com/xml/ns/public/common/common-3">
    <name>Import HR CSV - Manual</name>
    <ownerRef oid="00000000-0000-0000-0000-000000000002" type="UserType"/>
    <executionState>runnable</executionState>
    <category>ImportingAccounts</category>
    <handlerUri>http://midpoint.evolveum.com/xml/ns/public/model/synchronization/task/import/handler-3</handlerUri>
    <objectRef oid="8a8b9c1d-0002-0000-0000-000000000001" type="ResourceType"/>
    <recurrence>single</recurrence>
</task>'
```

## Partie 6 : Vérification

### 6.1 Vérifier dans MidPoint

1. Menu **Users** → **All users**
2. Recherchez l'utilisateur importé
3. Vérifiez les attributs :
   - Name (uid)
   - Given name
   - Family name
   - Email
   - Organizational unit

### 6.2 Vérifier les projections

1. Ouvrez un utilisateur
2. Onglet **Projections**
3. Vous devez voir : **HR CSV Resource** - AccountObjectClass

### 6.3 Commandes de vérification

```bash
# Lister les utilisateurs MidPoint via API
curl -s -u administrator:5ecr3t \
  "http://localhost:8080/midpoint/ws/rest/users" \
  -H "Accept: application/json" | python3 -m json.tool

# Vérifier le contenu du CSV dans MidPoint
docker exec midpoint-core cat /opt/midpoint/var/import/hr_sample.csv
```

## Partie 7 : Flux Complet - Démonstration

### Étape 1 : Créer un employé dans Odoo
```
Odoo → Employés → Créer
Nom : Test Demo
Email : test.demo@example.com
Département : IT
```

### Étape 2 : Exécuter le script de synchronisation
```bash
python3 /home/vboxuser/Desktop/Project3/scripts/odoo_to_midpoint_sync.py
```

### Étape 3 : Vérifier dans MidPoint
```
MidPoint → Users → All users
Rechercher : test.demo
```

### Étape 4 : Vérifier la projection CSV
```
Ouvrir l'utilisateur → Onglet Projections
Voir : HR CSV Resource
```

## Partie 8 : Dépannage

### Problème : "Connexion Odoo échouée"

**Causes possibles** :
- Odoo n'est pas démarré
- Mauvais identifiants
- Base de données incorrecte

**Solutions** :
```bash
# Vérifier que Odoo est actif
docker ps | grep odoo

# Vérifier les logs Odoo
docker logs odoo --tail 50

# Tester la connexion manuellement
curl http://localhost:8069/web/database/selector
```

### Problème : "Copie CSV échouée"

**Causes possibles** :
- Container MidPoint non accessible
- Permissions insuffisantes

**Solutions** :
```bash
# Vérifier le container MidPoint
docker ps | grep midpoint

# Copier manuellement
docker cp /chemin/local/hr_sample.csv midpoint-core:/opt/midpoint/var/import/

# Vérifier le fichier
docker exec midpoint-core ls -la /opt/midpoint/var/import/
```

### Problème : "Import avec erreurs"

**Causes possibles** :
- Format CSV incorrect
- Colonnes manquantes
- Encodage incorrect

**Solutions** :
```bash
# Vérifier le format du CSV
head -5 /home/vboxuser/Desktop/Project3/datasets/hr_employees.csv

# Vérifier l'encodage
file /home/vboxuser/Desktop/Project3/datasets/hr_employees.csv

# Vérifier dans MidPoint : Resources → HR CSV Resource → Content
```

### Problème : "Utilisateurs non créés (UNMATCHED)"

**Cause** : La synchronisation détecte les comptes mais ne crée pas les utilisateurs

**Solution** : Vérifier que la réaction `unmatched` → `addFocus` est configurée dans la ressource

## Partie 9 : Automatisation

### Cron job pour synchronisation périodique

```bash
# Éditer le crontab
crontab -e

# Ajouter une synchronisation toutes les heures
0 * * * * /usr/bin/python3 /home/vboxuser/Desktop/Project3/scripts/odoo_to_midpoint_sync.py >> /var/log/odoo_sync.log 2>&1
```

### Script wrapper avec logging

```bash
#!/bin/bash
# /home/vboxuser/Desktop/Project3/scripts/sync_with_log.sh

LOG_FILE="/home/vboxuser/Desktop/Project3/logs/sync_$(date +%Y%m%d_%H%M%S).log"
echo "=== Synchronisation démarrée: $(date) ===" >> $LOG_FILE
python3 /home/vboxuser/Desktop/Project3/scripts/odoo_to_midpoint_sync.py >> $LOG_FILE 2>&1
echo "=== Synchronisation terminée: $(date) ===" >> $LOG_FILE
```

## Ressources

### Fichiers clés

| Fichier | Description |
|---------|-------------|
| `scripts/odoo_to_midpoint_sync.py` | Script de synchronisation |
| `infrastructure/midpoint/resources/hr-csv-complete.xml` | Ressource CSV MidPoint |
| `datasets/hr_employees.csv` | Fichier CSV local |
| `/opt/midpoint/var/import/hr_sample.csv` | CSV dans container MidPoint |

### OIDs importants

| Objet | OID |
|-------|-----|
| HR CSV Resource | `8a8b9c1d-0002-0000-0000-000000000001` |
| Administrator | `00000000-0000-0000-0000-000000000002` |

---

*Documentation créée pour le projet IAM Gateway - Synchronisation Odoo → CSV → MidPoint*
