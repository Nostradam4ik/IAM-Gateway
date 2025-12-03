## Guide d’installation MidPoint / ApacheDS / Odoo

### 1. Pré-requis
- Docker Engine + Docker Compose.
- 8 Go RAM dédiés, 4 vCPU recommandés.
- Ports libres : 8080 (MidPoint), 10389 (LDAP), 8069 (Odoo), 5433/55432 (PostgreSQL).

### 2. Démarrage de l’environnement
1. Cloner le dépôt puis exécuter :
   - Windows : `powershell -ExecutionPolicy Bypass -File infrastructure/scripts/setup_midpoint.ps1`.
   - Linux/macOS : `bash infrastructure/scripts/setup_midpoint.sh`.
2. Le script lance `docker-compose.midpoint.yml` avec les services :
   - `midpoint` + `postgres` (repository).
   - `apacheds` (LDAP).
   - `odoo` + `odoo-db`.
   - `intranet-db` (PostgreSQL applicatif).
3. Vérifier l’état : `docker compose -f infrastructure/docker/docker-compose.midpoint.yml ps`.

### 3. Accès et captures à réaliser
| Composant | URL / Outil | Identifiants démo | Captures à déposer dans `media/` |
| --- | --- | --- | --- |
| MidPoint UI | `http://localhost:8080/midpoint` | `administrator` / `admin` | `media/midpoint/login.png`, `media/midpoint/dashboard.png`, `media/midpoint/resource-ldap.png`, `media/midpoint/task-import.png`, `media/midpoint/role-crm.png` |
| ApacheDS | Apache Directory Studio (`ldap://localhost:10389`) | `cn=admin,dc=example,dc=com` / `secret` | `media/apacheds/tree.png`, `media/apacheds/group.png` |
| Odoo | `http://localhost:8069` | `admin` / `admin` (création base démo) | `media/odoo/hr.png`, `media/odoo/crm.png` |

### 4. MidPoint – Configuration initiale
1. Se connecter à l’UI, changer le mot de passe admin.
2. Importer le schéma HR CSV :
   - Menu **Resources** → **Import** → sélectionner `infrastructure/midpoint/resources/hr-csv.xml` (à produire).
   - Créer un **Task** `Import HR CSV`.
3. Déployer la ressource LDAP :
   - Importer `infrastructure/midpoint/resources/ldap-resource.xml`.
   - Tester la connectivité vers `apacheds`.
4. Créer un rôle de test :
   - **Roles → Add** : `Role - LDAP Basic`.
   - Affecter un mapping vers un groupe LDAP.

### 5. ApacheDS
1. Ouvrir Apache Directory Studio, ajouter une connexion vers `localhost:10389`.
2. Explorer le DIT : `dc=example,dc=com`.
3. Créer un groupe `cn=Finance`.
4. Capturer les écrans structure + groupe pour `media/apacheds`.

### 6. Odoo
1. À la première connexion, créer la base `demo`.
2. Activer modules RH/CRM.
3. Exporter la liste des employés (CSV) → stocker dans `datasets/hr_export.csv`.
4. Capturer les vues RH et CRM.

### 7. Arrêt et nettoyage
- `docker compose -f infrastructure/docker/docker-compose.midpoint.yml down`.
- Pour supprimer les volumes : `docker compose -f ... down -v`.

### 8. Checklist livrables
- Scripts `setup_midpoint.ps1` / `.sh`.
- Fichier Compose.
- Captures d’écran dans `media/`.
- Exports CSV/Excel dans `datasets/`.
- Configs MidPoint exportées (`infrastructure/midpoint/resources/*.xml`).

_Co-auteurs : <votre nom>, achibani@gmail.com_

