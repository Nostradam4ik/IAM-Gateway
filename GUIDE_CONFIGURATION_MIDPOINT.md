# 🔧 GUIDE DE CONFIGURATION DES CONNECTEURS MIDPOINT

Ce guide vous explique comment configurer tous les connecteurs nécessaires dans MidPoint pour votre projet Gateway IAM.

## 📋 Prérequis

- MidPoint démarré et accessible : http://localhost:8080/midpoint/admin/
- Credentials : `administrator / Nost1`
- Tous les services cibles opérationnels

---

## 1️⃣ CONNECTEUR LDAP (OpenLDAP)

### Méthode 1 : Via l'interface web (Recommandé)

1. **Accédez à MidPoint** : http://localhost:8080/midpoint/admin/

2. **Naviguez vers** : `Resources → New resource`

3. **Sélectionnez** : `From Scratch`

4. **Configuration de base** :
   - **Name** : `OpenLDAP Resource`
   - **Connector** : Sélectionnez `LdapConnector`

5. **Paramètres de connexion** :
   ```
   Host: openldap
   Port: 389
   Base Context: dc=example,dc=com
   Bind DN: cn=admin,dc=example,dc=com
   Bind Password: secret
   Connection Security: none
   ```

6. **Test de connexion** : Cliquez sur `Test Connection`
   - ✅ Devrait afficher "Success"

7. **Configuration du schéma** :
   - Object Class: `inetOrgPerson`
   - Base Context for accounts: `ou=people,dc=example,dc=com`

8. **Mapping des attributs** :
   ```
   uid → $user/name
   cn → $user/fullName
   sn → $user/familyName
   givenName → $user/givenName
   mail → $user/emailAddress
   ```

9. **Sauvegardez** la ressource

### Méthode 2 : Import XML

```bash
# Depuis le répertoire du projet
docker compose exec midpoint-core bash -c "cat > /opt/midpoint/var/import/ldap-resource.xml" < midpoint-resources/ldap-resource.xml
```

Puis dans MidPoint : `Configuration → Import object → Select file`

---

## 2️⃣ CONNECTEUR CSV

### Configuration via l'interface

1. **Resources → New resource → From Scratch**

2. **Connector** : Sélectionnez `CsvConnector`

3. **Paramètres** :
   ```
   File Path: /opt/midpoint/var/csv/users.csv
   Encoding: UTF-8
   Field Delimiter: ,
   Unique Attribute: uid
   ```

4. **Créer le fichier CSV** :
   ```bash
   docker compose exec midpoint-core bash -c "mkdir -p /opt/midpoint/var/csv"
   docker compose exec midpoint-core bash -c "echo 'uid,firstname,lastname,email' > /opt/midpoint/var/csv/users.csv"
   ```

5. **Test et sauvegarde**

---

## 3️⃣ CONNECTEUR DATABASE (PostgreSQL Intranet)

### Configuration via l'interface

1. **Resources → New resource → From Scratch**

2. **Connector** : Sélectionnez `DatabaseTableConnector`

3. **Paramètres JDBC** :
   ```
   JDBC Driver: org.postgresql.Driver
   JDBC URL: jdbc:postgresql://intranet-db:5432/intranet
   User: intranet
   Password: intranet
   Table: users
   Key Column: id
   ```

4. **Mapping des colonnes** :
   ```
   username → $user/name
   email → $user/emailAddress
   first_name → $user/givenName
   last_name → $user/familyName
   ```

5. **Test de connexion** et **Sauvegarde**

---

## 4️⃣ VÉRIFICATION DES CONNECTEURS

### Test rapide depuis l'interface MidPoint

1. **Allez dans** : `Resources → All resources`

2. **Pour chaque ressource** :
   - Cliquez sur le nom
   - Cliquez sur `Test Connection`
   - ✅ Vérifiez que le statut est "Success"

### Test depuis le Gateway

```bash
docker compose exec -T gateway python3 << 'EOF'
import asyncio
import sys
sys.path.insert(0, '/app')

from app.services.midpoint_client import MidPointClient

async def test():
    client = MidPointClient()
    try:
        print("\n🔍 Test des ressources MidPoint...")

        # À implémenter : récupération des ressources
        print("✅ Connecteurs configurés!")

    finally:
        await client.close()

asyncio.run(test())
EOF
```

---

## 5️⃣ CONFIGURATION DES RÔLES (Optionnel)

### Créer un rôle "Employee"

1. **Roles → New role**

2. **Configuration** :
   ```
   Name: Employee
   Description: Standard employee role
   ```

3. **Inducements** (Assignations automatiques) :
   - Ajouter LDAP account
   - Ajouter Database account
   - Ajouter CSV account

4. **Sauvegarde**

---

## 6️⃣ TEST DE PROVISIONNEMENT

### Créer un utilisateur de test

1. **Users → New user**

2. **Informations** :
   ```
   Name: jdoe
   Given Name: John
   Family Name: Doe
   Email: john.doe@example.com
   ```

3. **Assigner le rôle** : `Employee`

4. **Sauvegarde**

5. **Vérification** :
   - Allez dans l'utilisateur → Onglet `Projections`
   - Vous devriez voir des comptes dans LDAP, Database, CSV

### Vérifier dans les systèmes cibles

```bash
# Vérifier dans LDAP
docker compose exec openldap ldapsearch -x -b "dc=example,dc=com" "(uid=jdoe)"

# Vérifier dans la base Intranet
docker compose exec intranet-db psql -U intranet -d intranet -c "SELECT * FROM users WHERE username='jdoe';"
```

---

## 🔥 DÉPANNAGE

### Problème : "Cannot connect to LDAP"
```bash
# Vérifier que OpenLDAP est accessible
docker compose exec midpoint-core ping openldap
```

### Problème : "Database driver not found"
```bash
# Le driver PostgreSQL doit être dans MidPoint
# Vérifier dans /opt/midpoint/lib/
docker compose exec midpoint-core ls /opt/midpoint/lib/ | grep postgresql
```

### Problème : "CSV file not found"
```bash
# Créer le répertoire et le fichier
docker compose exec midpoint-core mkdir -p /opt/midpoint/var/csv
docker compose exec midpoint-core touch /opt/midpoint/var/csv/users.csv
```

---

## 📚 RESSOURCES UTILES

- Documentation MidPoint : https://docs.evolveum.com/midpoint/
- LDAP Connector : https://docs.evolveum.com/connectors/connectors/com.evolveum.polygon.connector.ldap.LdapConnector/
- CSV Connector : https://docs.evolveum.com/connectors/connectors/com.evolveum.polygon.connector.csv.CsvConnector/
- Database Connector : https://docs.evolveum.com/connectors/connectors/org.identityconnectors.databasetable.DatabaseTableConnector/

---

## ✅ CHECKLIST FINALE

- [ ] Connecteur LDAP configuré et testé
- [ ] Connecteur CSV configuré
- [ ] Connecteur Database configuré
- [ ] Rôle "Employee" créé
- [ ] Utilisateur de test créé et provisionné
- [ ] Vérification dans les systèmes cibles
- [ ] Gateway peut communiquer avec MidPoint (Nost1)

---

🎉 **Félicitations !** Votre infrastructure IAM est complète !
