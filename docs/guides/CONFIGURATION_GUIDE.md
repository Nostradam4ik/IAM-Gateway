# Guide de configuration MidPoint - Étapes détaillées

## ✅ Prérequis (Complétés)

- [x] Environnement Docker démarré
- [x] Fichier CSV copié dans le conteneur
- [x] Fichiers XML de ressources et rôles créés

## 📝 Configuration MidPoint UI

### Étape 1 : Première connexion et changement de mot de passe

1. Ouvrir le navigateur : **http://localhost:8080/midpoint**
2. Se connecter avec :
   - Username : `administrator`
   - Password : `admin`
3. MidPoint vous demandera de changer le mot de passe
4. **IMPORTANT** : Notez le nouveau mot de passe !

**Capture d'écran** : `media/midpoint/login.png`

---

### Étape 2 : Vérifier le Dashboard

1. Après connexion, vous êtes sur le dashboard
2. Vérifier que MidPoint fonctionne correctement

**Capture d'écran** : `media/midpoint/dashboard.png`

---

### Étape 3 : Importer la ressource LDAP

1. Menu : **Configuration** → **Import object**
2. Cliquer sur **Choose File**
3. Sélectionner : `infrastructure/midpoint/resources/ldap-resource.xml`
4. Cliquer sur **Import object**
5. Vérifier le message de succès

6. Aller dans : **Resources** → **All resources**
7. Cliquer sur "ApacheDS LDAP Resource"
8. Onglet **Configuration** → bouton **Test connection**
9. Devrait afficher : ✅ **Success**

**Capture d'écran** : `media/midpoint/resource-ldap.png`

---

### Étape 4 : Importer la ressource CSV

1. Menu : **Configuration** → **Import object**
2. Cliquer sur **Choose File**
3. Sélectionner : `infrastructure/midpoint/resources/hr-csv.xml`
4. Cliquer sur **Import object**
5. Vérifier le message de succès

6. Aller dans : **Resources** → **All resources**
7. Cliquer sur "HR CSV Resource"
8. Onglet **Configuration** → bouton **Test connection**
9. Devrait afficher : ✅ **Success**

---

### Étape 5 : Créer une tâche d'import CSV

1. Menu : **Server tasks** → **New task**

2. Configuration de base :
   - **Name** : `Import HR CSV`
   - **Handler URI** : Sélectionner "Import from resource"

3. Onglet **Resource** :
   - **Resource** : Sélectionner "HR CSV Resource"
   - **Object class** : `AccountObjectClass`

4. Onglet **Scheduling** :
   - Laisser "Run now" (exécution manuelle)

5. Cliquer sur **Save**
6. Cliquer sur **Run now**

7. Attendre quelques secondes, puis rafraîchir la page
8. Vérifier que le statut est "Success"
9. Vérifier le nombre d'objets importés (devrait être 3)

**Capture d'écran** : `media/midpoint/task-import.png`

---

### Étape 6 : Vérifier les utilisateurs importés

1. Menu : **Users** → **All users**
2. Vous devriez voir 4 utilisateurs :
   - `administrator` (utilisateur système)
   - `u1001` - Alice Dupont (Engineering)
   - `u1002` - Bob Martin (Sales)
   - `u1003` - Carla Nguyen (HR)

3. Cliquer sur un utilisateur pour voir les détails :
   - Given Name, Family Name
   - Email Address
   - Organizational Unit (département)

**Capture d'écran** : `media/midpoint/users.png`

---

### Étape 7 : Importer les rôles

#### 7.1 Rôle LDAP Basic

1. Menu : **Configuration** → **Import object**
2. Sélectionner : `infrastructure/midpoint/roles/role-ldap-basic.xml`
3. Cliquer sur **Import object**

#### 7.2 Rôle Agent Commercial CRM

1. Menu : **Configuration** → **Import object**
2. Sélectionner : `infrastructure/midpoint/roles/role-crm-agent.xml`
3. Cliquer sur **Import object**

#### 7.3 Rôle Intranet User

1. Menu : **Configuration** → **Import object**
2. Sélectionner : `infrastructure/midpoint/roles/role-intranet-user.xml`
3. Cliquer sur **Import object**

**Note** : Les rôles CRM et Intranet nécessitent les ressources Odoo et PostgreSQL (à configurer ensuite)

---

### Étape 8 : Vérifier les rôles créés

1. Menu : **Roles** → **All roles**
2. Vous devriez voir :
   - LDAP Basic User
   - Agent Commercial CRM
   - Intranet Application User

3. Cliquer sur "LDAP Basic User"
4. Vérifier la configuration du rôle

**Capture d'écran** : `media/midpoint/role-crm.png`

---

### Étape 9 : Assigner un rôle à un utilisateur

1. Menu : **Users** → **All users**
2. Cliquer sur "Bob Martin" (u1002)
3. Onglet **Assignments**
4. Cliquer sur **Assign** → **Assign role**
5. Sélectionner "LDAP Basic User"
6. Cliquer sur **Assign**
7. Cliquer sur **Save** (en haut de la page)

8. MidPoint va créer automatiquement un compte LDAP pour Bob Martin
9. Aller dans l'onglet **Projections** pour voir le compte LDAP créé

---

### Étape 10 : Configurer ApacheDS (optionnel)

Pour vérifier que les comptes LDAP sont bien créés, utiliser Apache Directory Studio :

1. Télécharger Apache Directory Studio : https://directory.apache.org/studio/
2. Créer une nouvelle connexion :
   - **Host** : `localhost`
   - **Port** : `10389`
   - **Bind DN** : `cn=admin,dc=example,dc=com`
   - **Password** : `secret`

3. Explorer l'arborescence LDAP :
   - `dc=example,dc=com`
   - Chercher l'OU `ou=people`

**Captures d'écran** :
- `media/apacheds/tree.png` - Arborescence LDAP
- `media/apacheds/group.png` - Groupes LDAP

---

## 🎯 Prochaines étapes

### Ressources supplémentaires à créer :

1. **Ressource Odoo** (CRM/RH)
   - Connecteur REST personnalisé
   - Mappings vers utilisateurs Odoo

2. **Ressource PostgreSQL Intranet**
   - Connecteur DatabaseTable
   - Table `users` dans la base `intranet`

### Workflow d'approbation

1. Créer des policy rules pour approbation multi-niveaux
2. Configurer les notifications par email

### Tests de bout en bout

1. Créer un nouvel utilisateur dans le CSV
2. Relancer la tâche d'import
3. Vérifier que les rôles sont auto-assignés
4. Vérifier que les comptes LDAP sont créés automatiquement

---

## 📊 Checklist de validation

- [ ] MidPoint accessible et mot de passe changé
- [ ] Ressource LDAP importée et testée (connexion OK)
- [ ] Ressource CSV importée et testée (connexion OK)
- [ ] Tâche d'import CSV exécutée avec succès
- [ ] 3 utilisateurs importés depuis le CSV
- [ ] 3 rôles créés (LDAP Basic, CRM Agent, Intranet User)
- [ ] Au moins un rôle assigné à un utilisateur
- [ ] Compte LDAP créé automatiquement via le rôle
- [ ] Toutes les captures d'écran prises et sauvegardées
- [ ] ApacheDS vérifié avec Apache Directory Studio

---

## 🐛 Dépannage

### Problème : Test de connexion LDAP échoue

**Solution** :
```bash
# Vérifier que le conteneur apacheds fonctionne
docker ps | grep apacheds

# Vérifier les logs
docker logs apacheds
```

### Problème : CSV non trouvé

**Solution** :
```bash
# Vérifier que le fichier est bien copié
docker exec midpoint-core ls -lh /opt/midpoint/var/import/

# Re-copier si nécessaire
bash infrastructure/scripts/copy_csv_to_midpoint.sh
```

### Problème : Tâche d'import échoue

**Solution** :
1. Vérifier les logs de la tâche dans MidPoint
2. Vérifier le format du CSV (délimiteur `;`)
3. Vérifier les logs du conteneur :
   ```bash
   docker logs midpoint-core
   ```

---

_Co-auteurs : <votre nom>, achibani@gmail.com_
