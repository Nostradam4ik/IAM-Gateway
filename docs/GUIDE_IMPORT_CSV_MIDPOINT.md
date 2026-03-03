# Guide d'import CSV vers MidPoint via API REST

> **Contexte** : L'interface graphique MidPoint (menu "Tâches définies") était instable —
> le menu restait vide après configuration. Ce guide décrit la méthode fiable :
> passer directement par l'**API REST MidPoint** avec des commandes `curl`.

---

## Prérequis

- Docker en cours d'exécution (`./start.sh` depuis la racine du projet)
- MidPoint accessible sur `http://localhost:8080`
- `curl` installé sur votre machine
- Les fichiers du dépôt à jour (`git pull`)

Vérifier que MidPoint est prêt :

```bash
curl -s -u administrator:5ecr3t \
  http://localhost:8080/midpoint/ws/rest/users \
  -H "Accept: application/json" | python3 -m json.tool | head -5
```

Si vous obtenez du JSON → MidPoint est opérationnel. Sinon, attendez 2-3 minutes
(MidPoint met du temps à démarrer).

---

## Vue d'ensemble du flux

```
hr_employees.csv
      |
      | (1) Copier le CSV dans le container MidPoint
      v
/opt/midpoint/var/import/hr_employees.csv
      |
      | (2) Importer la ressource CSV (XML) via API
      v
MidPoint : Ressource "HR CSV Resource"
      |
      | (3) Lancer la tâche d'import via API
      v
MidPoint : Utilisateurs créés depuis le CSV
      |
      | (4) Rôle Employee assigné automatiquement
      v
LDAP + Odoo + Keycloak provisionnés
```

---

## Étape 1 — Copier le fichier CSV dans le container MidPoint

MidPoint lit le CSV depuis **l'intérieur** du container Docker, pas depuis votre machine.
Il faut donc copier le fichier dans le container.

```bash
# Depuis la racine du projet
docker cp datasets/hr_employees.csv midpoint-core:/opt/midpoint/var/import/hr_employees.csv
```

Vérifier que le fichier est bien là :

```bash
docker exec midpoint-core ls -lh /opt/midpoint/var/import/
```

Résultat attendu :
```
-rw-r--r-- 1 root root 1.2K ... hr_employees.csv
```

> **Structure du CSV** (séparateur `;`) :
> ```
> uid;givenName;familyName;email;department
> u1001;Abigail;Peterson;abigail.peterson39@example.com;Management / Professional Services
> u1002;Anita;Oliver;anita.oliver32@example.com;Management / R&D
> ...
> ```

---

## Étape 2 — Importer la ressource CSV dans MidPoint

La ressource CSV indique à MidPoint **où lire le fichier** et **comment mapper les colonnes**
vers les attributs utilisateur.

Le fichier XML de la ressource est :
```
infrastructure/midpoint/resources/hr-csv.xml
```

### Importer via API REST

```bash
curl -v -X POST http://localhost:8080/midpoint/ws/rest/resources \
  -u administrator:5ecr3t \
  -H "Content-Type: application/xml" \
  -H "Accept: application/xml" \
  --data-binary @infrastructure/midpoint/resources/hr-csv.xml
```

**Réponse attendue** :
- Code HTTP `201 Created` → ressource créée
- Code HTTP `409 Conflict` → la ressource existe déjà (c'est OK, passez à l'étape suivante)

En cas de `409`, vous pouvez mettre à jour la ressource existante avec son OID
(`8a8b9c1d-0002-0000-0000-000000000001`) :

```bash
curl -v -X PUT \
  http://localhost:8080/midpoint/ws/rest/resources/8a8b9c1d-0002-0000-0000-000000000001 \
  -u administrator:5ecr3t \
  -H "Content-Type: application/xml" \
  -H "Accept: application/xml" \
  --data-binary @infrastructure/midpoint/resources/hr-csv.xml
```

### Vérifier que la ressource est bien importée

```bash
curl -s -u administrator:5ecr3t \
  http://localhost:8080/midpoint/ws/rest/resources/8a8b9c1d-0002-0000-0000-000000000001 \
  -H "Accept: application/json" | python3 -c "
import json, sys
d = json.load(sys.stdin)
r = d.get('resource', d)
print('Nom     :', r.get('name', '?'))
print('OID     :', r.get('oid', '?'))
"
```

---

## Étape 3 — Tester la connexion à la ressource CSV

Avant de lancer l'import, vérifier que MidPoint peut lire le CSV :

```bash
curl -s -X POST \
  http://localhost:8080/midpoint/ws/rest/resources/8a8b9c1d-0002-0000-0000-000000000001/test \
  -u administrator:5ecr3t \
  -H "Accept: application/xml" | grep -E "<status>|<message>"
```

**Résultat OK :**
```xml
<status>success</status>
```

**Si erreur `File not found`** → le CSV n'est pas au bon endroit dans le container.
Refaire l'étape 1.

---

## Étape 4 — Lancer la tâche d'import (Import Task)

C'est la commande qui **lit le CSV et crée les utilisateurs** dans MidPoint.

```bash
curl -v -X POST http://localhost:8080/midpoint/ws/rest/tasks \
  -u administrator:5ecr3t \
  -H "Content-Type: application/xml" \
  -H "Accept: application/xml" \
  -d '<?xml version="1.0" encoding="UTF-8"?>
<task xmlns="http://midpoint.evolveum.com/xml/ns/public/common/common-3"
      xmlns:ri="http://midpoint.evolveum.com/xml/ns/public/resource/instance-3">
    <name>Import CSV HR Employees</name>
    <executionState>runnable</executionState>
    <activity>
        <work>
            <import>
                <resourceObjects>
                    <resourceRef oid="8a8b9c1d-0002-0000-0000-000000000001"/>
                    <kind>account</kind>
                    <intent>default</intent>
                    <objectclass>ri:AccountObjectClass</objectclass>
                </resourceObjects>
            </import>
        </work>
    </activity>
</task>'
```

**Réponse attendue** : HTTP `201 Created` avec le XML de la tâche créée.

---

## Étape 5 — (Optionnel) Lancer la synchronisation Live Sync

La Live Sync surveille le CSV **en continu** (toutes les 5 minutes) et crée/met à jour
les utilisateurs à chaque modification du fichier.

```bash
curl -v -X POST http://localhost:8080/midpoint/ws/rest/tasks \
  -u administrator:5ecr3t \
  -H "Content-Type: application/xml" \
  -H "Accept: application/xml" \
  --data-binary @infrastructure/midpoint/tasks/csv-livesync-task.xml
```

---

## Étape 6 — Vérifier que les utilisateurs ont été créés

Attendre ~15 secondes puis vérifier :

```bash
# Compter les utilisateurs (hors administrator)
curl -s -u administrator:5ecr3t \
  "http://localhost:8080/midpoint/ws/rest/users" \
  -H "Accept: application/json" | python3 -c "
import json, sys
data = json.load(sys.stdin)
users = data.get('object', {}).get('object', [])
if isinstance(users, dict):
    users = [users]
print(f'Total utilisateurs dans MidPoint : {len(users)}')
for u in users[:5]:
    name = u.get('name', '?')
    fn   = u.get('givenName', '')
    ln   = u.get('familyName', '')
    print(f'  - {name} : {fn} {ln}')
print('  ...')
"
```

Résultat attendu avec 21 employés dans le CSV :
```
Total utilisateurs dans MidPoint : 22
  - administrator : ...
  - u1001 : Abigail Peterson
  - u1002 : Anita Oliver
  - u1003 : Audrey Peterson
  - u1004 : Beth Evans
  ...
```

---

## Étape 7 — Vérifier qu'un utilisateur est bien dans LDAP

Après l'import, le rôle `Employee` est assigné automatiquement (via l'object template),
ce qui provisionne le compte LDAP :

```bash
docker exec openldap ldapsearch \
  -x -H ldap://localhost \
  -D "cn=admin,dc=example,dc=com" \
  -w admin \
  -b "ou=people,dc=example,dc=com" \
  "(uid=u1001)" uid cn mail
```

Résultat attendu :
```
dn: uid=u1001,ou=people,dc=example,dc=com
uid: u1001
cn: Abigail Peterson
mail: abigail.peterson39@example.com
```

---

## Script tout-en-un

Pour exécuter toutes les étapes en une seule commande :

```bash
bash scripts/import_csv_to_midpoint.sh
```

Ce script effectue automatiquement :
1. Copie du CSV dans le container
2. Import/mise à jour de la ressource XML
3. Test de connexion à la ressource
4. Création et lancement de la tâche d'import
5. Attente et vérification du nombre d'utilisateurs créés

---

## Résolution des problèmes courants

### Problème : `File not found` lors du test de ressource

```
<message>CSV file not found: /opt/midpoint/var/import/hr_employees.csv</message>
```

**Solution** : Refaire l'étape 1 — copier le CSV dans le container.

```bash
docker cp datasets/hr_employees.csv midpoint-core:/opt/midpoint/var/import/hr_employees.csv
```

---

### Problème : `409 Conflict` à l'import de la ressource

La ressource existe déjà. Utiliser `PUT` au lieu de `POST` (voir Étape 2).

---

### Problème : Tâche créée mais 0 utilisateurs importés

Vérifier les logs de la tâche :

```bash
# Récupérer l'OID de la dernière tâche
TASK_OID=$(curl -s -u administrator:5ecr3t \
  "http://localhost:8080/midpoint/ws/rest/tasks" \
  -H "Accept: application/json" | python3 -c "
import json, sys
d = json.load(sys.stdin)
tasks = d.get('object', {}).get('object', [])
if isinstance(tasks, dict): tasks = [tasks]
for t in tasks:
    if 'Import CSV' in t.get('name',''):
        print(t.get('oid',''))
        break
")
echo "OID tâche : $TASK_OID"

# Voir le statut de la tâche
curl -s -u administrator:5ecr3t \
  "http://localhost:8080/midpoint/ws/rest/tasks/$TASK_OID" \
  -H "Accept: application/json" | python3 -c "
import json, sys
d = json.load(sys.stdin)
t = d.get('task', d)
print('Etat         :', t.get('executionState','?'))
print('Résultat     :', t.get('resultStatus','?'))
"
```

---

### Problème : MidPoint ne démarre pas (healthcheck failed)

MidPoint prend 2-5 minutes à démarrer. Vérifier :

```bash
docker logs midpoint-core --tail=20
```

Attendre que la ligne suivante apparaisse :
```
INFO  [main] com.evolveum.midpoint.web.boot.MidPointSpringApplication - Started
```

---

### Problème : Mot de passe `administrator` refusé

Le mot de passe par défaut est `5ecr3t`. S'il a été changé, utiliser le script :

```bash
python3 scripts/change-midpoint-password.py
```

---

## Prochaine étape : Ressource LDAP

Une fois l'import CSV maîtrisé, **appliquer la même logique** pour la ressource LDAP :

```bash
# 1. Importer la ressource LDAP
curl -v -X POST http://localhost:8080/midpoint/ws/rest/resources \
  -u administrator:5ecr3t \
  -H "Content-Type: application/xml" \
  --data-binary @infrastructure/midpoint/resources/openldap-resource.xml

# 2. Tester la ressource LDAP
curl -s -X POST \
  http://localhost:8080/midpoint/ws/rest/resources/<OID_LDAP>/test \
  -u administrator:5ecr3t \
  -H "Accept: application/xml"
```

Le fichier XML est dans :
```
infrastructure/midpoint/resources/openldap-resource.xml
```

---

## Résumé des commandes essentielles

| Action | Commande |
|--------|----------|
| Copier CSV dans container | `docker cp datasets/hr_employees.csv midpoint-core:/opt/midpoint/var/import/` |
| Importer ressource XML | `curl -X POST .../resources -d @hr-csv.xml` |
| Mettre à jour ressource | `curl -X PUT .../resources/<OID> -d @hr-csv.xml` |
| Tester la ressource | `curl -X POST .../resources/<OID>/test` |
| Lancer import (tâche) | `curl -X POST .../tasks -d '<task>...'` |
| Compter utilisateurs | `curl .../users` |
| Vérifier LDAP | `docker exec openldap ldapsearch ...` |
| Script tout-en-un | `bash scripts/import_csv_to_midpoint.sh` |

---

*Guide rédigé par Zhmuryk Andrii — Projet SAE IAM Gateway 2026*
*NEXUS AI Innovation Lab — IUT Créteil-Vitry — UPEC*
