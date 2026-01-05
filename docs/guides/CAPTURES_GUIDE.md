# 📸 Guide des captures d'écran - Étape par étape

## 🎯 Objectif
Vous devez prendre 14 captures d'écran pour documenter votre configuration MidPoint.

## 🖥️ Comment faire une capture d'écran sur Linux ?

### Méthode rapide (recommandée)
1. Appuyez sur `Print Screen` (PrtSc) sur votre clavier
2. Une fenêtre s'ouvre pour sauvegarder l'image
3. Nommez le fichier selon le nom indiqué ci-dessous
4. Sauvegardez dans le bon dossier

### Ou installez Flameshot (plus pratique)
```bash
sudo apt install flameshot
flameshot gui
```

---

## 📋 LISTE DES CAPTURES À PRENDRE (dans l'ordre)

### ÉTAPE 1 : Première connexion

#### 📸 Capture 1 : `media/midpoint/login.png`
**QUAND ?** Maintenant, avant de vous connecter
**QUOI FAIRE ?**
1. Ouvrir le navigateur
2. Aller sur : http://localhost:8080/midpoint
3. Vous voyez la page de connexion
4. ⚠️ NE PAS ENCORE SE CONNECTER
5. Appuyer sur Print Screen
6. Sauvegarder comme : `media/midpoint/login.png`

**Ce qu'on doit voir :**
- Le logo MidPoint
- Champs "Username" et "Password"
- Bouton "Log in"

---

#### 📸 Capture 2 : `media/midpoint/dashboard.png`
**QUAND ?** Après vous être connecté
**QUOI FAIRE ?**
1. Se connecter avec : administrator / admin
2. Changer le mot de passe quand demandé
3. Vous arrivez sur le dashboard (tableau de bord)
4. Appuyer sur Print Screen
5. Sauvegarder comme : `media/midpoint/dashboard.png`

**Ce qu'on doit voir :**
- Le menu principal à gauche
- Les widgets du dashboard (statistiques)
- Le nom "Administrator" en haut à droite

---

### ÉTAPE 2 : Import des ressources

#### 📸 Capture 3 : `media/midpoint/resource-ldap.png`
**QUAND ?** Après avoir importé ldap-resource.xml
**QUOI FAIRE ?**
1. Menu : Configuration → Import object
2. Importer le fichier : `infrastructure/midpoint/resources/ldap-resource.xml`
3. Aller dans : Resources → All resources
4. Cliquer sur "ApacheDS LDAP Resource"
5. Onglet "Configuration"
6. Cliquer sur le bouton "Test connection"
7. ✅ Attendre que le message "Success" s'affiche
8. Appuyer sur Print Screen
9. Sauvegarder comme : `media/midpoint/resource-ldap.png`

**Ce qu'on doit voir :**
- Le nom de la ressource "ApacheDS LDAP Resource"
- Le bouton "Test connection"
- Le message de succès (vert) "Success"
- Les paramètres de connexion (host: apacheds, port: 389)

---

#### 📸 Capture 4 : `media/midpoint/resource-csv.png`
**QUAND ?** Après avoir importé hr-csv.xml
**QUOI FAIRE ?**
1. Menu : Configuration → Import object
2. Importer le fichier : `infrastructure/midpoint/resources/hr-csv.xml`
3. Aller dans : Resources → All resources
4. Cliquer sur "HR CSV Resource"
5. Onglet "Configuration"
6. Cliquer sur "Test connection"
7. ✅ Attendre le message "Success"
8. Appuyer sur Print Screen
9. Sauvegarder comme : `media/midpoint/resource-csv.png`

**Ce qu'on doit voir :**
- Le nom "HR CSV Resource"
- Le message "Success"
- Le chemin du fichier CSV

---

### ÉTAPE 3 : Import des utilisateurs

#### 📸 Capture 5 : `media/midpoint/task-import.png`
**QUAND ?** Après avoir créé et exécuté la tâche d'import
**QUOI FAIRE ?**
1. Menu : Server tasks → New task
2. Créer une tâche d'import :
   - Name: "Import HR CSV"
   - Type: Import from resource
   - Resource: HR CSV Resource
   - Object class: AccountObjectClass
3. Cliquer sur "Save"
4. Cliquer sur "Run now"
5. Attendre quelques secondes
6. Rafraîchir la page (F5)
7. La tâche doit afficher "Success"
8. Appuyer sur Print Screen
9. Sauvegarder comme : `media/midpoint/task-import.png`

**Ce qu'on doit voir :**
- Le nom de la tâche "Import HR CSV"
- Statut : "Success" ou "Closed"
- Nombre d'objets traités : 3

---

#### 📸 Capture 6 : `media/midpoint/users.png`
**QUAND ?** Après l'import CSV
**QUOI FAIRE ?**
1. Menu : Users → All users
2. Vous devez voir 4 utilisateurs :
   - administrator
   - u1001 (Alice Dupont)
   - u1002 (Bob Martin)
   - u1003 (Carla Nguyen)
3. Appuyer sur Print Screen
4. Sauvegarder comme : `media/midpoint/users.png`

**Ce qu'on doit voir :**
- La liste des 4 utilisateurs
- Les noms complets (Alice Dupont, Bob Martin, Carla Nguyen)

---

### ÉTAPE 4 : Import des rôles

#### 📸 Capture 7 : `media/midpoint/role-ldap.png`
**QUAND ?** Après avoir importé role-ldap-basic.xml
**QUOI FAIRE ?**
1. Menu : Configuration → Import object
2. Importer : `infrastructure/midpoint/roles/role-ldap-basic.xml`
3. Menu : Roles → All roles
4. Cliquer sur "LDAP Basic User"
5. Regarder les détails du rôle
6. Appuyer sur Print Screen
7. Sauvegarder comme : `media/midpoint/role-ldap.png`

**Ce qu'on doit voir :**
- Le nom "LDAP Basic User"
- La description du rôle
- Les détails de configuration

---

#### 📸 Capture 8 : `media/midpoint/role-crm.png`
**QUAND ?** Après avoir importé role-crm-agent.xml
**QUOI FAIRE ?**
1. Menu : Configuration → Import object
2. Importer : `infrastructure/midpoint/roles/role-crm-agent.xml`
3. Menu : Roles → All roles
4. Cliquer sur "Agent Commercial CRM"
5. Appuyer sur Print Screen
6. Sauvegarder comme : `media/midpoint/role-crm.png`

**Ce qu'on doit voir :**
- Le nom "Agent Commercial CRM"
- La description

---

#### 📸 Capture 9 : `media/midpoint/user-projections.png`
**QUAND ?** Après avoir assigné un rôle à un utilisateur
**QUOI FAIRE ?**
1. Menu : Users → All users
2. Cliquer sur "Bob Martin" (u1002)
3. Onglet "Assignments"
4. Cliquer sur "Assign" → "Assign role"
5. Sélectionner "LDAP Basic User"
6. Cliquer sur "Assign"
7. Cliquer sur "Save" (en haut)
8. Aller dans l'onglet "Projections"
9. Vous devez voir un compte LDAP créé
10. Appuyer sur Print Screen
11. Sauvegarder comme : `media/midpoint/user-projections.png`

**Ce qu'on doit voir :**
- L'onglet "Projections"
- Un compte LDAP pour Bob Martin
- Le DN du compte (uid=u1002,ou=people,dc=example,dc=com)

---

### ÉTAPE 5 : ApacheDS (Optionnel mais recommandé)

#### 📸 Capture 10 : `media/apacheds/tree.png`
**QUAND ?** Après avoir installé Apache Directory Studio
**QUOI FAIRE ?**
1. Télécharger Apache Directory Studio : https://directory.apache.org/studio/
2. Créer une connexion LDAP :
   - Host: localhost
   - Port: 10389
   - Bind DN: cn=admin,dc=example,dc=com
   - Password: secret
3. Se connecter
4. Explorer l'arborescence : dc=example,dc=com
5. Appuyer sur Print Screen
6. Sauvegarder comme : `media/apacheds/tree.png`

**Ce qu'on doit voir :**
- L'arborescence LDAP complète
- dc=example,dc=com
- ou=people (si des comptes ont été créés)

---

#### 📸 Capture 11 : `media/apacheds/group.png`
**QUAND ?** Si vous créez un groupe dans LDAP
**QUOI FAIRE ?**
1. Dans Apache Directory Studio
2. Créer un groupe : cn=Finance,dc=example,dc=com
3. Appuyer sur Print Screen
4. Sauvegarder comme : `media/apacheds/group.png`

---

#### 📸 Capture 12 : `media/apacheds/user-bob.png`
**QUAND ?** Après avoir assigné le rôle LDAP à Bob
**QUOI FAIRE ?**
1. Dans Apache Directory Studio
2. Naviguer vers : ou=people,dc=example,dc=com
3. Chercher l'utilisateur Bob Martin (uid=u1002)
4. Appuyer sur Print Screen
5. Sauvegarder comme : `media/apacheds/user-bob.png`

**Ce qu'on doit voir :**
- Le compte LDAP de Bob Martin
- Ses attributs (cn, sn, givenName, mail)

---

### ÉTAPE 6 : Odoo (À faire plus tard)

#### 📸 Capture 13 : `media/odoo/hr.png`
**QUAND ?** Après avoir configuré Odoo
**QUOI FAIRE ?**
1. Ouvrir : http://localhost:8069
2. Se connecter : admin / admin
3. Créer une base de données
4. Activer le module RH
5. Ajouter quelques employés
6. Appuyer sur Print Screen
7. Sauvegarder comme : `media/odoo/hr.png`

---

#### �� Capture 14 : `media/odoo/crm.png`
**QUAND ?** Après avoir configuré Odoo CRM
**QUOI FAIRE ?**
1. Dans Odoo
2. Activer le module CRM
3. Créer quelques opportunités commerciales
4. Appuyer sur Print Screen
5. Sauvegarder comme : `media/odoo/crm.png`

---

## ✅ Checklist rapide

Cochez au fur et à mesure :

**MidPoint (9 captures) :**
- [ ] login.png - Page de connexion
- [ ] dashboard.png - Dashboard
- [ ] resource-ldap.png - LDAP testé OK
- [ ] resource-csv.png - CSV testé OK
- [ ] task-import.png - Tâche exécutée
- [ ] users.png - 3 utilisateurs importés
- [ ] role-ldap.png - Rôle LDAP
- [ ] role-crm.png - Rôle CRM
- [ ] user-projections.png - Projection LDAP

**ApacheDS (3 captures) :**
- [ ] tree.png - Arborescence LDAP
- [ ] group.png - Groupe créé
- [ ] user-bob.png - Compte Bob dans LDAP

**Odoo (2 captures) :**
- [ ] hr.png - Module RH
- [ ] crm.png - Module CRM

---

## 💡 Conseil

**Prenez les captures AU FUR ET À MESURE que vous suivez le guide de configuration !**

Ne faites pas toute la configuration d'abord, sinon vous devrez tout refaire pour prendre les captures.

---

_Co-auteurs : <votre nom>, achibani@gmail.com_
