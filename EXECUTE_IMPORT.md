# 🚀 Comment exécuter le script d'import

## ✅ Script prêt à utiliser (sans installation)

J'ai créé **2 versions** du script :

### Version 1 : `import_csv_users_simple.py` ⭐ RECOMMANDÉ
**Avantage** : Pas besoin d'installer de dépendances ! Utilise uniquement les bibliothèques standard Python.

### Version 2 : `import_csv_users.py`
**Avantage** : Plus moderne, utilise la bibliothèque `requests`.
**Inconvénient** : Nécessite `pip3 install requests`

---

## 🎬 Exécution du script (Version simple)

### Étape 1 : Ouvrir un terminal

Appuyez sur `Ctrl + Alt + T`

### Étape 2 : Aller dans le dossier du projet

```bash
cd /home/vboxuser/Desktop/Project3
```

### Étape 3 : Exécuter le script

```bash
python3 infrastructure/scripts/import_csv_users_simple.py
```

### Étape 4 : Entrer le mot de passe

Le script vous demandera :
```
Enter MidPoint administrator password:
```

Tapez le mot de passe que vous avez défini pour l'administrateur MidPoint.

⚠️ **Le mot de passe ne s'affichera pas quand vous tapez** (c'est normal pour la sécurité)

### Étape 5 : Regarder le script travailler

Vous verrez :
```
============================================================
🚀 Import des utilisateurs CSV dans MidPoint
============================================================

📖 Lecture du fichier CSV : datasets/hr_sample.csv
✅ 3 utilisateurs trouvés dans le CSV

🔌 Test de connexion à MidPoint...
✅ Connexion à MidPoint OK

👥 Création des 3 utilisateurs...
------------------------------------------------------------
🔄 Création de l'utilisateur u1001...
✅ Utilisateur u1001 créé avec succès !

🔄 Création de l'utilisateur u1002...
✅ Utilisateur u1002 créé avec succès !

🔄 Création de l'utilisateur u1003...
✅ Utilisateur u1003 créé avec succès !

============================================================
📊 RÉSUMÉ
============================================================
✅ Utilisateurs créés : 3
❌ Échecs : 0

🎉 Import terminé avec succès !
```

---

## ✅ Vérification

### Dans MidPoint :

1. Ouvrir le navigateur : http://localhost:8080/midpoint
2. Menu : **Users** → **All users**
3. Vous devriez voir **4 utilisateurs** :
   - administrator
   - u1001 (Alice Dupont)
   - u1002 (Bob Martin)
   - u1003 (Carla Nguyen)

📸 **Prendre une capture d'écran** : `media/midpoint/users.png`

---

## 🔧 Si vous avez une erreur

### Erreur : "File not found: datasets/hr_sample.csv"

Vous n'êtes pas dans le bon dossier.

**Solution** :
```bash
cd /home/vboxuser/Desktop/Project3
python3 infrastructure/scripts/import_csv_users_simple.py
```

### Erreur : "Connexion refused" ou "Connection error"

MidPoint n'est pas démarré.

**Solution** :
```bash
docker ps | grep midpoint
```

Si rien ne s'affiche, démarrez MidPoint :
```bash
bash infrastructure/scripts/setup_midpoint.sh
```

### Erreur : "Authentication failed" ou "Status 401"

Le mot de passe est incorrect.

**Solution** : Vérifiez que vous utilisez le bon mot de passe administrator.

### Les utilisateurs existent déjà

Si vous voyez :
```
⚠️  Utilisateur u1001 existe déjà, ignoré
```

C'est normal ! Ça veut dire que l'import précédent a fonctionné ou que vous les avez créés manuellement.

**Solution** : Vérifiez dans MidPoint → Users → All users

---

## 🎯 Après l'import réussi

### Prochaines étapes :

1. ✅ **Importer les rôles**
   ```
   Configuration → Import object
   - role-ldap-basic.xml
   - role-crm-agent.xml
   - role-intranet-user.xml
   ```

2. ✅ **Assigner un rôle à Bob Martin**
   - Users → u1002 (Bob Martin)
   - Onglet Assignments → Assign role
   - Sélectionner "LDAP Basic User"
   - Save

3. ✅ **Vérifier la projection LDAP**
   - Onglet Projections
   - Vous devriez voir un compte LDAP créé

4. ✅ **Prendre les captures manquantes**
   - media/midpoint/user-projections.png
   - media/odoo/hr.png
   - media/odoo/crm.png

---

## 💻 Commande complète (copier-coller)

```bash
cd /home/vboxuser/Desktop/Project3 && python3 infrastructure/scripts/import_csv_users_simple.py
```

Puis entrez votre mot de passe administrator quand demandé.

---

_Co-auteurs : <votre nom>, achibani@gmail.com_
