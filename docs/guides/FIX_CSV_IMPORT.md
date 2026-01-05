# 🔧 Guide de correction - Import CSV dans MidPoint

## Problème rencontré
L'import de la ressource CSV ne crée pas les utilisateurs dans MidPoint.

## ✅ Solution complète en 7 étapes

---

### Étape 1 : Supprimer la ressource CSV existante

**Dans MidPoint :**

1. Menu : **Resources** → **All resources**
2. **Cocher la case** à côté de "HR CSV Resource"
3. Cliquer sur le bouton **Delete** en haut de la liste
4. Confirmer la suppression
5. ✅ Vérifier qu'elle n'apparaît plus dans la liste

---

### Étape 2 : Importer la version minimale

1. Menu : **Configuration** → **Import object**
2. Cliquer sur **Choose File**
3. Sélectionner : `infrastructure/midpoint/resources/hr-csv-minimal.xml`
4. Cliquer sur **Import object**
5. ✅ Vous devriez voir : "Object imported successfully"

---

### Étape 3 : Tester la connexion

1. Menu : **Resources** → **All resources**
2. Cliquer sur "HR CSV Resource"
3. Onglet **Configuration**
4. Cliquer sur le bouton **Test connection**
5. ✅ Résultat attendu : "Success" (vert)

---

### Étape 4 : Créer une tâche de réconciliation

**IMPORTANT** : Utilisez "Reconciliation task" au lieu de "Import task"

1. Menu : **Server tasks** → **New task**
2. Dans la liste, choisir : **"Reconciliation task"**
3. Configurer :
   - **Name** : `Reconcile HR CSV`
   - **Resource** : Sélectionner "HR CSV Resource"
   - **Object class** : Sélectionner "AccountObjectClass"
4. Cliquer sur **Save**

---

### Étape 5 : Configurer la synchronisation

**Option A : Via l'interface (recommandé)**

1. Menu : **Resources** → **All resources**
2. Cliquer sur "HR CSV Resource"
3. Chercher un onglet **"Synchronization"** ou **"Mappings"**
4. S'il existe, cliquer sur **"Add object synchronization"**
5. Configurer :
   - **Enabled** : ✓ Coché
   - **Object class** : AccountObjectClass
   - **Focus type** : User
   - **Kind** : account
   - **Intent** : default

6. Dans **Reactions** :
   - Chercher "unmatched" → Sélectionner : **"Add focus"** ou **"Create user"**
   - Chercher "matched" → Sélectionner : **"Synchronize"**

7. Cliquer sur **Save**

**Option B : Via l'import du fichier complet (si Option A ne fonctionne pas)**

1. Menu : **Resources** → **All resources**
2. **Supprimer** "HR CSV Resource"
3. Menu : **Configuration** → **Import object**
4. Importer : `infrastructure/midpoint/resources/hr-csv.xml` (fichier complet)
5. Si erreur "attribute uid not found" : ignorer et continuer à l'étape 6

---

### Étape 6 : Exécuter la réconciliation

1. Menu : **Server tasks** → **All tasks**
2. Trouver "Reconcile HR CSV" dans la liste
3. Cliquer dessus
4. Cliquer sur le bouton **Run now**
5. Attendre 10-15 secondes
6. Appuyer sur **F5** pour rafraîchir
7. ✅ Vérifier : Status = "Closed" ou "Success"
8. ✅ Vérifier : Progress = 3 objets traités

---

### Étape 7 : Vérifier les utilisateurs créés

1. Menu : **Users** → **All users**
2. ✅ Vous devriez voir **4 utilisateurs au total** :
   - `administrator` (déjà existant)
   - `u1001` - Alice Dupont
   - `u1002` - Bob Martin
   - `u1003` - Carla Nguyen

3. Cliquer sur "u1001" pour vérifier les détails :
   - Given name : Alice
   - Family name : Dupont
   - Email : alice.dupont@example.com
   - Organizational unit : Engineering

---

## 🎯 Si ça ne fonctionne toujours pas

### Solution alternative : Import manuel

1. Menu : **Users** → **New user**
2. Créer manuellement chaque utilisateur :

**Utilisateur 1 :**
- Name : u1001
- Given name : Alice
- Family name : Dupont
- Email : alice.dupont@example.com
- Organizational unit : Engineering

**Utilisateur 2 :**
- Name : u1002
- Given name : Bob
- Family name : Martin
- Email : bob.martin@example.com
- Organizational unit : Sales

**Utilisateur 3 :**
- Name : u1003
- Given name : Carla
- Family name : Nguyen
- Email : carla.nguyen@example.com
- Organizational unit : HR

---

## 📸 N'oubliez pas les captures d'écran !

Après avoir réussi :

1. **Capture de la tâche** : `media/midpoint/task-import.png`
2. **Capture de la liste des utilisateurs** : `media/midpoint/users.png`

---

## 🔍 Vérification des logs (si problème)

Si vous avez toujours des erreurs :

```bash
# Voir les logs du conteneur MidPoint
docker logs midpoint-core --tail 100

# Voir les logs en temps réel
docker logs -f midpoint-core
```

Cherchez des messages d'erreur contenant :
- "correlation"
- "synchronization"
- "unmatched"
- "addFocus"

---

_Co-auteurs : <votre nom>, achibani@gmail.com_
