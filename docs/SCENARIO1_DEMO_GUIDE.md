# Scénario 1 - Guide Détaillé des Vidéos de Démonstration

---

# PRÉPARATION

## Services requis

```bash
cd /home/vboxuser/Desktop/Project3-clean
docker-compose up -d
```

## Credentials

| Service | URL | Login | Password |
|---------|-----|-------|----------|
| Odoo | http://localhost:8069 | admin | admin |
| MidPoint | http://localhost:8080/midpoint | administrator | Test5ecr3t |
| phpLDAPadmin | http://localhost:8081 | cn=admin,dc=example,dc=com | secret |

---

# VIDÉO 1 : Configuration du connecteur de synchronisation

## Étape 1.1 - Ouvrir MidPoint
- Navigateur → `http://localhost:8080/midpoint`
- Entrer : `administrator`
- Entrer : `Test5ecr3t`
- Cliquer **Sign in**

## Étape 1.2 - Aller aux ressources
- Menu gauche → **Resources**
- Cliquer → **All resources**

## Étape 1.3 - Ouvrir ressource Odoo
- Cliquer sur `Odoo ERP`

## Étape 1.4 - Montrer la configuration
- Onglet **Configuration**
- Montrer :
  - Host : `odoo-db`
  - Port : `5432`
  - Database : `odoo`
  - Table : `res_partner`

## Étape 1.5 - Montrer le mapping
- Onglet **Schema handling**
- Déplier **account/contact**
- Montrer les attributs mappés

## Étape 1.6 - Tester la connexion
- Bouton **Test connection**
- Vérifier : tous les ✅ verts
- Cliquer **OK**

---

# VIDÉO 2 : Création de l'employée dans Odoo

## Étape 2.1 - Ouvrir Odoo
- Navigateur → `http://localhost:8069`
- Entrer : `admin`
- Entrer : `admin`
- Cliquer **Log in**

## Étape 2.2 - Aller aux employés
- Menu grille (haut gauche)
- Cliquer **Employees**

## Étape 2.3 - Créer employé
- Bouton **Create**

## Étape 2.4 - Remplir le formulaire
- **Name** : `Alice Doe`
- **Work Email** : `alice.doe@example.com`
- **Work Phone** : `+33 1 23 45 67 89`
- **Department** : `IT` (créer si nécessaire)
- **Job Position** : `Software Developer`

## Étape 2.5 - Sauvegarder
- Bouton **Save**
- Montrer la fiche créée

## Étape 2.6 - Créer le contrat (optionnel)
- Onglet **Contracts**
- Bouton **Create**
- **Start Date** : aujourd'hui
- **Status** : Running
- Bouton **Save**

---

# VIDÉO 3 : Import de l'identité dans MidPoint

## Étape 3.1 - Ouvrir MidPoint
- Navigateur → `http://localhost:8080/midpoint`
- Se connecter

## Étape 3.2 - Créer utilisateur
- Menu → **Users**
- Bouton **New user**

## Étape 3.3 - Onglet Basic
- **Name** : `alice.doe`
- **Given name** : `Alice`
- **Family name** : `Doe`
- **Full name** : `Alice Doe`
- **Email** : `alice.doe@example.com`
- **Telephone** : `+33 1 23 45 67 89`

## Étape 3.4 - Onglet Activation
- Cliquer onglet **Activation**
- **Administrative status** : `Enabled`
- **Valid from** : date du jour

## Étape 3.5 - Onglet Password
- Cliquer onglet **Password**
- Bouton **Set password**
- Entrer : `Welcome123!`
- Confirmer : `Welcome123!`
- Bouton **Set**

## Étape 3.6 - Sauvegarder
- Bouton **Save**
- Vérifier message succès

## Étape 3.7 - Vérifier
- Menu → **Users** → **List users**
- Rechercher `alice.doe`
- Vérifier statut **Enabled**

---

# VIDÉO 4 : Configuration du connecteur LDAP

## Étape 4.1 - Ouvrir ressource LDAP
- MidPoint → **Resources** → **All resources**
- Cliquer `OpenLDAP Directory`

## Étape 4.2 - Montrer configuration
- Onglet **Configuration**
- Montrer :
  - Host : `openldap`
  - Port : `389`
  - Base DN : `dc=example,dc=com`
  - Bind DN : `cn=admin,dc=example,dc=com`

## Étape 4.3 - Montrer schema comptes
- Onglet **Schema handling**
- Déplier **account/default**
- Montrer :
  - Object class : `inetOrgPerson`
  - Attributs : uid, cn, sn, mail

## Étape 4.4 - Montrer schema groupes
- Déplier **entitlement/ldapGroup**
- Montrer :
  - Object class : `groupOfUniqueNames`

## Étape 4.5 - Tester connexion
- Bouton **Test connection**
- Vérifier tous ✅ verts

## Étape 4.6 - Ouvrir phpLDAPadmin
- Navigateur → `http://localhost:8081`
- Login DN : `cn=admin,dc=example,dc=com`
- Password : `secret`
- Cliquer **Authenticate**

## Étape 4.7 - Montrer les groupes
- Arbre gauche → `dc=example,dc=com`
- Cliquer → `ou=groups`
- Montrer les 4 groupes :
  - `cn=Employee`
  - `cn=Internet`
  - `cn=Printer`
  - `cn=Public_Share_Folder_SharePoint`

## Étape 4.8 - Montrer un groupe
- Cliquer `cn=Employee`
- Montrer attributs :
  - objectClass : groupOfUniqueNames
  - cn : Employee
  - uniqueMember : (liste)

---

# VIDÉO 5 : Attribution des droits LDAP

## Étape 5.1 - Montrer les rôles
- MidPoint → **Roles** → **All roles**
- Montrer `Employee-Full-Access`

## Étape 5.2 - Examiner le rôle
- Cliquer `Employee-Full-Access`
- Onglet **Inducement**
- Montrer : 4 associations aux groupes LDAP

## Étape 5.3 - Ouvrir Alice
- Menu → **Users** → **List users**
- Rechercher `alice.doe`
- Cliquer sur l'utilisateur

## Étape 5.4 - Vérifier projections vides
- Onglet **Projections**
- Constater : liste vide

## Étape 5.5 - Attribuer le rôle
- Onglet **Assignments**
- Bouton **Assign**
- Sélectionner **Assign role**

## Étape 5.6 - Sélectionner Employee-Full-Access
- Rechercher `Employee-Full-Access`
- Cocher le rôle
- Bouton **Assign**

## Étape 5.7 - Sauvegarder
- Bouton **Save**
- Attendre traitement

## Étape 5.8 - Vérifier projection LDAP
- Onglet **Projections**
- Voir nouvelle projection :
  - Resource : OpenLDAP Directory
  - Name : uid=alice.doe,ou=users,dc=example,dc=com

## Étape 5.9 - Vérifier dans phpLDAPadmin
- Navigateur → `http://localhost:8081`
- Arbre → `ou=users`
- Trouver `uid=alice.doe`
- Cliquer pour voir attributs

## Étape 5.10 - Vérifier groupes
- Arbre → `ou=groups`
- Cliquer `cn=Employee`
- Vérifier uniqueMember contient `uid=alice.doe,ou=users,dc=example,dc=com`
- Répéter pour :
  - `cn=Internet` ✅
  - `cn=Printer` ✅
  - `cn=Public_Share_Folder_SharePoint` ✅

---

# VIDÉO 6 : Configuration du connecteur Odoo

## Étape 6.1 - Ouvrir ressource Odoo
- MidPoint → **Resources** → **All resources**
- Cliquer `Odoo ERP`

## Étape 6.2 - Montrer configuration
- Onglet **Configuration**
- Montrer :
  - Connector : DatabaseTableConnector
  - Host : `odoo-db`
  - Database : `odoo`
  - Table : `res_partner`

## Étape 6.3 - Montrer schema
- Onglet **Schema handling**
- Déplier **account/contact**
- Montrer mapping :
  - fullName → name
  - emailAddress → email
  - telephoneNumber → phone

## Étape 6.4 - Montrer rôles Odoo
- Menu → **Roles** → **All roles**
- Montrer :
  - `Odoo_User` (standard)
  - `Odoo_Finance` (finance)
  - `Odoo_Admin` (critique ⚠️)

## Étape 6.5 - Examiner Odoo_Admin
- Cliquer `Odoo_Admin`
- Montrer **Risk level** : critical

---

# VIDÉO 7 : Attribution des droits Odoo

## Étape 7.1 - Ouvrir Alice
- MidPoint → **Users** → **List users**
- Rechercher `alice.doe`
- Cliquer sur l'utilisateur

## Étape 7.2 - Vérifier assignments
- Onglet **Assignments**
- Voir : `Employee-Full-Access` déjà présent

## Étape 7.3 - Attribuer Odoo_User
- Bouton **Assign**
- Sélectionner **Assign role**
- Rechercher `Odoo_User`
- Cocher le rôle
- Bouton **Assign**

## Étape 7.4 - Sauvegarder
- Bouton **Save**
- Attendre traitement

## Étape 7.5 - Vérifier projections
- Onglet **Projections**
- Voir 2 projections :
  - OpenLDAP Directory
  - Odoo ERP

## Étape 7.6 - Vérifier dans Odoo
- Navigateur → `http://localhost:8069`
- Se connecter admin/admin
- Menu → **Contacts**
- Rechercher `Alice Doe`
- Ouvrir le contact
- Vérifier :
  - Nom : Alice Doe ✅
  - Email : alice.doe@example.com ✅
  - Type employé : Oui ✅

---

# RÉSUMÉ FINAL

| Vidéo | Contenu | Durée |
|-------|---------|-------|
| 1 | Config connecteur sync | 3-5 min |
| 2 | Création employé Odoo | 4-6 min |
| 3 | Import MidPoint | 5-7 min |
| 4 | Config connecteur LDAP | 4-6 min |
| 5 | Attribution droits LDAP | 5-7 min |
| 6 | Config connecteur Odoo | 3-5 min |
| 7 | Attribution droits Odoo | 4-6 min |

## Résultat final pour Alice Doe

| Système | Compte | Droits |
|---------|--------|--------|
| Odoo RH | Employée | - |
| MidPoint | alice.doe | Active |
| LDAP | uid=alice.doe | Employee, Internet, Printer, SharePoint |
| Odoo Contact | Alice Doe | User |

## Script automatisé

```bash
python scripts/demo/scenario1_alice_doe.py
```
