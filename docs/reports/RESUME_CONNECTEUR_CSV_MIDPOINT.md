# Résumé : Configuration du Connecteur CSV MidPoint

**Date** : 19 décembre 2024
**Projet** : IAM Gateway - Intégration Odoo/MidPoint

---

## 1. Identifiants du Projet

### Odoo (ERP)
| Paramètre | Valeur |
|-----------|--------|
| URL | http://localhost:8069 |
| Base de données | `odoo` |
| Login | `admin` |
| Mot de passe | `admin` |

### MidPoint (IAM)
| Paramètre | Valeur |
|-----------|--------|
| URL | http://localhost:8080/midpoint |
| Login | `administrator` |
| Mot de passe | `Holimolly1` |

### OpenLDAP
| Paramètre | Valeur |
|-----------|--------|
| Host | `localhost:10389` |
| Base DN | `dc=example,dc=com` |
| Admin DN | `cn=admin,dc=example,dc=com` |
| Password | `secret` |

---

## 2. Connecteur CSV - Configuration

### Ressource MidPoint
- **Nom** : CSV Odoo Employees
- **OID** : `10000000-0000-0000-0000-000000000004`
- **Fichier** : `/opt/midpoint/var/csv/users.csv`
- **Connecteur** : `connector-csv-2.6.jar`

### Colonnes du fichier CSV
| Colonne | Description | Mapping MidPoint |
|---------|-------------|------------------|
| `uid` | Identifiant unique | `name` |
| `firstname` | Prénom | `givenName` |
| `lastname` | Nom | `familyName` |
| `email` | Email | `emailAddress` |
| `phone` | Téléphone | `telephoneNumber` |
| `department` | Département | `organizationalUnit` |
| `job_title` | Poste | `title` |
| `manager` | Manager | - |
| `start_date` | Date début contrat | `activation/validFrom` |
| `end_date` | Date fin contrat | `activation/validTo` |
| `active` | Statut actif | `activation/administrativeStatus` |

---

## 3. Scripts Créés

### import_odoo_to_midpoint.py
Script Python principal qui :
1. Se connecte à Odoo via XML-RPC
2. Récupère tous les employés avec leurs contrats
3. Extrait les dates de début/fin de contrat
4. Génère un fichier CSV formaté
5. Copie le CSV dans le conteneur MidPoint
6. Lance une tâche d'import

**Utilisation** :
```bash
python3 scripts/import_odoo_to_midpoint.py
```

### sync_odoo_to_midpoint.sh
Script shell pour synchronisation rapide :
```bash
./scripts/sync_odoo_to_midpoint.sh
```

### import_csv_to_midpoint.sh
Script complet avec vérifications :
```bash
./scripts/import_csv_to_midpoint.sh
```

---

## 4. Live Sync - Synchronisation Automatique

### Tâche configurée
- **Nom** : Live Sync: CSV Odoo Employees
- **OID** : `10000000-0000-0000-5555-000000000001`
- **Intervalle** : 300 secondes (5 minutes)
- **État** : `runnable`

### Fonctionnement
Le Live Sync surveille automatiquement le fichier CSV et :
- Crée les nouveaux utilisateurs
- Met à jour les utilisateurs existants
- Désactive les utilisateurs supprimés

---

## 5. Flux de Synchronisation

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   ODOO      │ --> │   Script    │ --> │    CSV      │ --> │  MidPoint   │
│  Employés   │     │   Python    │     │   File      │     │  Live Sync  │
│  + Contrats │     │             │     │             │     │             │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
```

---

## 6. Résultats

### Import réussi
- **21 employés** importés depuis Odoo
- **8 contrats** avec dates récupérés
- **27 utilisateurs** total dans MidPoint

### Exemples de données importées
| Employé | Département | Date début | Date fin |
|---------|-------------|------------|----------|
| Mitchell Admin | Management | 2025-12-16 | 2025-12-31 |
| Audrey Peterson | Professional Services | 2015-01-01 | 2017-12-01 |
| Ronnie Hart | R&D | 2025-01-01 | - |
| Keith Byrd | R&D | 2015-01-01 | 2025-12-19 |

---

## 7. Connecteur LDAP

### État
- **Ressource** : OpenLDAP Directory
- **OID** : `10000000-0000-0000-0000-000000000001`
- **Status** : ✅ UP
- **Utilisateurs LDAP** : 127 entrées

---

## 8. Structure du Projet

```
Project3/
├── docs/
│   ├── guides/           # Documentation
│   └── reports/          # Rapports
├── gateway/
│   └── app/
│       ├── connectors/   # Connecteurs Python
│       └── services/     # Services
├── infrastructure/
│   ├── midpoint/
│   │   ├── resources/    # Configurations XML
│   │   ├── roles/        # Rôles MidPoint
│   │   └── tasks/        # Tâches planifiées
│   └── sql/              # Scripts SQL
└── scripts/
    ├── demo/             # Scripts de démo
    ├── tests/            # Tests
    ├── import_odoo_to_midpoint.py
    ├── sync_odoo_to_midpoint.sh
    └── import_csv_to_midpoint.sh
```

---

## 9. Commandes Utiles

### Synchroniser Odoo → MidPoint
```bash
python3 scripts/import_odoo_to_midpoint.py
```

### Forcer le Live Sync
```bash
curl -X POST "http://localhost:8080/midpoint/ws/rest/tasks/10000000-0000-0000-5555-000000000001/run" \
  -u administrator:Holimolly1
```

### Tester la ressource CSV
```bash
curl -X POST "http://localhost:8080/midpoint/ws/rest/resources/10000000-0000-0000-0000-000000000004/test" \
  -u administrator:Holimolly1
```

### Voir le contenu du CSV
```bash
docker exec midpoint-core cat /opt/midpoint/var/csv/users.csv
```

---

## 10. Automatisation (Cron)

Pour synchroniser automatiquement toutes les 5 minutes :
```bash
crontab -e
# Ajouter :
*/5 * * * * /home/vboxuser/Desktop/Project3/scripts/sync_odoo_to_midpoint.sh
```

---

**Auteur** : Claude Code
**Repository** : https://github.com/Nostradam4ik/Project3
