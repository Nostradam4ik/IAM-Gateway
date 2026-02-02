# Vidéo : Synchronisation Odoo → MidPoint

## Objectif
Démontrer l'import des identités depuis Odoo (SI RH) vers MidPoint.

Vous avez **2 options** :
- **Cas 1** : Export CSV + Import dans MidPoint
- **Cas 2** : Import direct depuis la DB Odoo (Script Python)

---

# CAS 1 : Export CSV et Import dans MidPoint

## Prérequis
- Alice Doe créée dans Odoo (Vidéo 2)
- Services Docker démarrés

## Script à utiliser
```bash
cd /home/vboxuser/Desktop/Project3-clean
./scripts/demo/export_odoo_csv_demo.sh
```

## Étapes détaillées

### Étape 1 - Ouvrir un terminal
- Ouvrir un terminal
- Naviguer vers le projet :
```bash
cd /home/vboxuser/Desktop/Project3-clean
```

### Étape 2 - Lancer le script d'export
```bash
./scripts/demo/export_odoo_csv_demo.sh
```

### Étape 3 - Observer l'export
Le script affiche :
```
======================================================================
   SYNCHRONISATION ODOO → MIDPOINT VIA CSV
   CAS 1 : Export CSV et Import dans MidPoint
======================================================================

ÉTAPE 1 : Export des employés Odoo vers CSV
----------------------------------------------------------------------
   Connexion à Odoo...
   ✅ Connecté à Odoo (UID: 2)
   ✅ 1 employé(s) trouvé(s)
   • Alice Doe → alice.doe

   ✅ Fichier CSV créé : /tmp/odoo_employees.csv
```

### Étape 4 - Voir le contenu CSV
Appuyer sur Entrée pour voir :
```
   Contenu :
   ---------
   uid;givenName;familyName;fullName;email;phone;department
   alice.doe;Alice;Doe;Alice Doe;alice.doe@example.com;+33 1 23 45 67 89;IT
```

### Étape 5 - Copier vers MidPoint
Appuyer sur Entrée :
```
   ✅ Fichier CSV copié avec succès
```

### Étape 6 - Importer dans MidPoint (Interface)
1. Ouvrir MidPoint : `http://localhost:8080/midpoint`
2. Menu → **Resources** → **All resources**
3. Cliquer sur **HR CSV Resource** (si configuré)
4. Onglet **Accounts**
5. Bouton **Import**

---

# CAS 2 : Import direct depuis Odoo (Recommandé)

## Prérequis
- Alice Doe créée dans Odoo (Vidéo 2)
- Services Docker démarrés

## Script à utiliser
```bash
cd /home/vboxuser/Desktop/Project3-clean
python scripts/demo/sync_odoo_to_midpoint_demo.py
```

## Étapes détaillées

### Étape 1 - Ouvrir un terminal
- Ouvrir un terminal
- Naviguer vers le projet :
```bash
cd /home/vboxuser/Desktop/Project3-clean
```

### Étape 2 - Lancer le script de synchronisation
```bash
python scripts/demo/sync_odoo_to_midpoint_demo.py
```

### Étape 3 - Observer la connexion Odoo
```
======================================================================
   SYNCHRONISATION ODOO → MIDPOINT
   CAS 2 : Import direct depuis la base de données Odoo
======================================================================
   Date : 2025-01-26 14:30:00
   Odoo : http://localhost:8069
   MidPoint : http://localhost:8080/midpoint
======================================================================

----------------------------------------------------------------------
ÉTAPE 1 : Connexion à Odoo via XML-RPC
----------------------------------------------------------------------

   URL : http://localhost:8069
   Base de données : odoo
   Utilisateur : admin

   ✅ Connecté à Odoo (UID: 2)

   Appuyez sur Entrée pour continuer vers l'étape 2...
```

**→ Appuyer sur Entrée**

### Étape 4 - Observer la récupération des employés
```
----------------------------------------------------------------------
ÉTAPE 2 : Récupération des employés depuis Odoo
----------------------------------------------------------------------

   ✅ 1 employé(s) trouvé(s) dans Odoo

   Liste des employés :
   --------------------------------------------------
   • Alice Doe
     Email : alice.doe@example.com
     Département : IT

   Appuyez sur Entrée pour continuer vers l'étape 3...
```

**→ Appuyer sur Entrée**

### Étape 5 - Observer la création dans MidPoint
```
----------------------------------------------------------------------
ÉTAPE 3 : Création des utilisateurs dans MidPoint
----------------------------------------------------------------------

   → Traitement : Alice Doe (alice.doe)
     ✅ Créé avec succès

   Appuyez sur Entrée pour continuer vers l'étape 4...
```

**→ Appuyer sur Entrée**

### Étape 6 - Observer la vérification
```
----------------------------------------------------------------------
ÉTAPE 4 : Vérification des utilisateurs dans MidPoint
----------------------------------------------------------------------

   ✅ 2 utilisateur(s) dans MidPoint

   Liste des utilisateurs :
   --------------------------------------------------
   • administrator - Administrator (N/A)
   • alice.doe - Alice Doe (alice.doe@example.com)

======================================================================
   RÉSUMÉ DE LA SYNCHRONISATION
======================================================================

   ✅ Créés     : 1
   ⚠️  Ignorés   : 0
   ❌ Erreurs   : 0

======================================================================
   SYNCHRONISATION TERMINÉE
======================================================================
```

### Étape 7 - Vérifier dans MidPoint (Interface)
1. Ouvrir MidPoint : `http://localhost:8080/midpoint`
2. Menu → **Users** → **List users**
3. Rechercher `alice.doe`
4. Vérifier :
   - ✅ Name : alice.doe
   - ✅ Full name : Alice Doe
   - ✅ Email : alice.doe@example.com
   - ✅ Status : Enabled

---

# Résumé de la vidéo

| Cas | Méthode | Commande |
|-----|---------|----------|
| 1 | CSV | `./scripts/demo/export_odoo_csv_demo.sh` |
| 2 | Direct DB | `python scripts/demo/sync_odoo_to_midpoint_demo.py` |

## Résultat attendu

| Avant | Après |
|-------|-------|
| Alice dans Odoo uniquement | Alice dans Odoo + MidPoint |
| MidPoint : 1 user (admin) | MidPoint : 2 users (admin + alice.doe) |

## Points à montrer dans la vidéo

1. **Connexion** : Le script se connecte à Odoo via XML-RPC
2. **Lecture** : Les employés sont lus depuis la base Odoo
3. **Transformation** : Les données sont transformées (nom → login)
4. **Création** : L'utilisateur est créé dans MidPoint via API REST
5. **Vérification** : L'utilisateur apparaît dans MidPoint

---

# Durée estimée : 3-5 minutes
