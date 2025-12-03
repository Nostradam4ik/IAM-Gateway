# 🐍 Script Python d'import CSV → MidPoint

Ce script lit le fichier CSV et crée automatiquement les utilisateurs dans MidPoint via l'API REST.

## 📋 Prérequis

1. **Python 3** installé
2. **MidPoint** accessible sur http://localhost:8080
3. **Mot de passe administrator** de MidPoint

## 🚀 Installation

### Étape 1 : Installer les dépendances Python

```bash
cd /home/vboxuser/Desktop/Project3

# Installer la bibliothèque requests
pip3 install -r infrastructure/scripts/requirements.txt
```

Ou directement :
```bash
pip3 install requests
```

## ▶️ Exécution du script

### Méthode 1 : Depuis la racine du projet

```bash
cd /home/vboxuser/Desktop/Project3
python3 infrastructure/scripts/import_csv_users.py
```

### Méthode 2 : Depuis le dossier scripts

```bash
cd /home/vboxuser/Desktop/Project3/infrastructure/scripts
python3 import_csv_users.py
```

## 📝 Ce que fait le script

1. ✅ Lit le fichier `datasets/hr_sample.csv`
2. ✅ Se connecte à MidPoint avec vos identifiants
3. ✅ Vérifie si chaque utilisateur existe déjà
4. ✅ Crée les utilisateurs manquants via l'API REST
5. ✅ Affiche un résumé des opérations

## 🎬 Exemple d'exécution

```
============================================================
🚀 Import des utilisateurs CSV dans MidPoint
============================================================

Enter MidPoint administrator password: ********

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

📋 Prochaines étapes :
1. Vérifier dans MidPoint : Users → All users
2. Vous devriez voir : u1001, u1002, u1003
```

## ✅ Vérification après import

1. Ouvrir MidPoint : http://localhost:8080/midpoint
2. Menu : **Users** → **All users**
3. Vous devriez voir :
   - administrator
   - u1001 (Alice Dupont)
   - u1002 (Bob Martin)
   - u1003 (Carla Nguyen)

## 🔧 Dépannage

### Erreur : "pip3: command not found"

Installer pip :
```bash
sudo apt update
sudo apt install python3-pip
```

### Erreur : "Module requests not found"

```bash
pip3 install requests
```

### Erreur : "Connexion refusée"

Vérifier que MidPoint est démarré :
```bash
docker ps | grep midpoint-core
```

Si non démarré :
```bash
bash infrastructure/scripts/setup_midpoint.sh
```

### Erreur : "Authentication failed"

Le mot de passe administrator est incorrect.

**Rappel** : Vous avez changé le mot de passe lors de la première connexion à MidPoint.

### Erreur : "User already exists"

C'est normal ! Le script détecte les utilisateurs existants et les ignore.

## 📚 Structure du CSV attendue

Le script attend un CSV avec ces colonnes (séparées par `;`) :

```csv
uid;givenName;familyName;email;department
u1001;Alice;Dupont;alice.dupont@example.com;Engineering
u1002;Bob;Martin;bob.martin@example.com;Sales
u1003;Carla;Nguyen;carla.nguyen@example.com;HR
```

## 🔍 Détails techniques

Le script utilise l'API REST de MidPoint :
- **Endpoint** : `http://localhost:8080/midpoint/ws/rest/users`
- **Méthode** : POST
- **Authentication** : Basic Auth (administrator/password)
- **Format** : JSON (UserType object)

## 📖 Documentation MidPoint REST API

https://docs.evolveum.com/midpoint/reference/interfaces/rest/

---

_Co-auteurs : <votre nom>, achibani@gmail.com_
