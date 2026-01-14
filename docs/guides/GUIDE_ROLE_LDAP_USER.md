# Guide : Création du Rôle LDAP User dans MidPoint

## Introduction

Ce guide explique comment créer et utiliser le rôle "LDAP User" dans MidPoint pour automatiser le provisioning des comptes vers OpenLDAP.

## Concept RBAC dans MidPoint

MidPoint utilise le modèle **RBAC (Role-Based Access Control)** :

```
┌─────────────────────────────────────────────────────────────────┐
│                         MidPoint                                │
│                                                                 │
│   ┌──────────┐      ┌─────────────┐      ┌─────────────────┐   │
│   │   User   │ ───► │    Role     │ ───► │   Resource      │   │
│   │          │      │  LDAP User  │      │   (OpenLDAP)    │   │
│   └──────────┘      └─────────────┘      └─────────────────┘   │
│                            │                      │             │
│                     inducement              provisioning        │
│                     (construction)          automatique         │
└─────────────────────────────────────────────────────────────────┘
                                                    │
                                                    ▼
                                          ┌─────────────────┐
                                          │    OpenLDAP     │
                                          │  (compte créé)  │
                                          └─────────────────┘
```

## Fonctionnement du Rôle

| Étape | Action | Résultat |
|-------|--------|----------|
| 1 | Utilisateur existe dans MidPoint | Aucun compte LDAP |
| 2 | Assigner rôle "LDAP User" | MidPoint lit l'inducement |
| 3 | MidPoint exécute la construction | Compte LDAP créé automatiquement |
| 4 | Retirer le rôle | Compte LDAP supprimé automatiquement |

## Définition XML du Rôle

```xml
<?xml version="1.0" encoding="UTF-8"?>
<role xmlns="http://midpoint.evolveum.com/xml/ns/public/common/common-3"
      oid="12345678-1234-1234-1234-000000000001">
    <name>LDAP User</name>
    <description>Role that provisions user account to OpenLDAP</description>
    <inducement>
        <construction>
            <resourceRef oid="10000000-0000-0000-0000-000000000001" type="ResourceType"/>
            <kind>account</kind>
            <intent>default</intent>
        </construction>
    </inducement>
</role>
```

### Explication des éléments

| Élément | Description |
|---------|-------------|
| `oid` | Identifiant unique du rôle dans MidPoint |
| `name` | Nom affiché dans l'interface MidPoint |
| `description` | Description du rôle |
| `inducement` | Définit ce qui se passe quand le rôle est assigné |
| `construction` | Instruction pour créer un compte sur une ressource |
| `resourceRef` | Référence à la ressource cible (OpenLDAP) via son OID |
| `kind` | Type d'objet à créer (`account` = compte utilisateur) |
| `intent` | Configuration à utiliser (`default` = configuration standard) |

## Méthode 1 : Création via l'Interface MidPoint

### Étape 1 : Accéder aux Rôles
1. Connectez-vous à MidPoint : http://localhost:8080/midpoint
2. Identifiants : `administrator` / `5ecr3t`
3. Menu **Roles** → **All roles**

### Étape 2 : Créer un nouveau rôle
1. Cliquez sur **New role** (bouton +)
2. Onglet **Basic** :
   - **Name** : `LDAP User`
   - **Description** : `Role that provisions user account to OpenLDAP`

### Étape 3 : Configurer l'Inducement
1. Allez dans l'onglet **Inducements**
2. Cliquez sur **+** (Add inducement)
3. Sélectionnez **Construction**
4. Configurez :
   - **Resource** : `OpenLDAP Directory`
   - **Kind** : `account`
   - **Intent** : `default`

### Étape 4 : Sauvegarder
1. Cliquez sur **Save**
2. Le rôle est maintenant disponible pour assignation

## Méthode 2 : Création via l'API REST

### Commande cURL

```bash
curl -X POST "http://localhost:8080/midpoint/ws/rest/roles" \
  -u administrator:5ecr3t \
  -H "Content-Type: application/xml" \
  -d '<?xml version="1.0" encoding="UTF-8"?>
<role xmlns="http://midpoint.evolveum.com/xml/ns/public/common/common-3"
      oid="12345678-1234-1234-1234-000000000001">
    <name>LDAP User</name>
    <description>Role that provisions user account to OpenLDAP</description>
    <inducement>
        <construction>
            <resourceRef oid="10000000-0000-0000-0000-000000000001" type="ResourceType"/>
            <kind>account</kind>
            <intent>default</intent>
        </construction>
    </inducement>
</role>'
```

### Réponse attendue
- **HTTP 201 Created** : Rôle créé avec succès
- **HTTP 409 Conflict** : Rôle existe déjà

## Méthode 3 : Import via fichier XML

### Étape 1 : Créer le fichier XML
Sauvegardez le XML dans un fichier : `ldap-user-role.xml`

### Étape 2 : Importer dans MidPoint
1. Menu **Resources** → **Import resource definition**
2. Ou via Repository Objects → Import object
3. Sélectionnez le fichier XML
4. Cliquez **Import**

## Utilisation du Rôle

### Assigner le rôle à un utilisateur (Interface)

1. Menu **Users** → **All users**
2. Cliquez sur l'utilisateur souhaité
3. Onglet **Assignments**
4. Cliquez sur **+** → **Role**
5. Recherchez **LDAP User**
6. Sélectionnez et cliquez **Add**
7. Cliquez **Save**

### Assigner le rôle via API REST

```bash
# Récupérer l'OID de l'utilisateur
USER_OID="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"

# Assigner le rôle
curl -X PATCH "http://localhost:8080/midpoint/ws/rest/users/${USER_OID}" \
  -u administrator:5ecr3t \
  -H "Content-Type: application/xml" \
  -d '<?xml version="1.0"?>
<objectModification xmlns="http://midpoint.evolveum.com/xml/ns/public/common/api-types-3">
    <itemDelta>
        <modificationType>add</modificationType>
        <path>assignment</path>
        <value>
            <targetRef oid="12345678-1234-1234-1234-000000000001" type="RoleType"/>
        </value>
    </itemDelta>
</objectModification>'
```

## Vérification du Provisioning

### Vérifier dans MidPoint
1. Ouvrez l'utilisateur
2. Onglet **Projections**
3. Vous devez voir : **OpenLDAP Directory** - inetOrgPerson

### Vérifier dans LDAP

```bash
# Via ligne de commande
docker exec openldap ldapsearch -x -H ldap://localhost:389 \
  -D "cn=admin,dc=example,dc=com" -w secret \
  -b "ou=users,dc=example,dc=com" \
  "(uid=USERNAME)" dn cn mail

# Via phpLDAPadmin
# URL : http://localhost:8088
# Login : cn=admin,dc=example,dc=com
# Password : secret
```

## Mappings LDAP

Le rôle utilise les mappings définis dans la ressource OpenLDAP :

| Attribut MidPoint | Attribut LDAP | Description |
|-------------------|---------------|-------------|
| `name` | `uid` | Identifiant unique |
| `givenName` | `givenName` | Prénom |
| `familyName` | `sn` | Nom de famille |
| `fullName` | `cn` | Nom complet |
| `emailAddress` | `mail` | Adresse email |

## Flux Complet de Provisioning

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│    Odoo     │     │     CSV     │     │  MidPoint   │     │   OpenLDAP  │
│  (source)   │     │   (export)  │     │   (hub)     │     │   (cible)   │
└──────┬──────┘     └──────┬──────┘     └──────┬──────┘     └──────┬──────┘
       │                   │                   │                   │
       │  1. Créer         │                   │                   │
       │  employé          │                   │                   │
       ├──────────────────►│                   │                   │
       │                   │  2. Script        │                   │
       │                   │  sync.py          │                   │
       │                   ├──────────────────►│                   │
       │                   │                   │  3. Assigner      │
       │                   │                   │  rôle LDAP User   │
       │                   │                   ├──────────────────►│
       │                   │                   │                   │
       │                   │                   │  4. Compte créé   │
       │                   │                   │  automatiquement  │
       │                   │                   │◄──────────────────┤
       │                   │                   │                   │
```

## Dépannage

### Le compte LDAP n'est pas créé

1. **Vérifier que le rôle est assigné**
   - Onglet Assignments → Role doit montrer "LDAP User"

2. **Vérifier les attributs obligatoires**
   - L'utilisateur doit avoir `fullName` (pour l'attribut `cn` LDAP)
   - L'utilisateur doit avoir `familyName` (pour l'attribut `sn` LDAP)

3. **Vérifier la connexion à LDAP**
   - Resources → OpenLDAP Directory → Test connection

4. **Consulter les logs MidPoint**
   ```bash
   docker logs midpoint-core --tail 100
   ```

### Erreur "object class 'inetOrgPerson' requires attribute 'cn'"

L'utilisateur n'a pas de `fullName`. Ajoutez-le :
1. Éditez l'utilisateur dans MidPoint
2. Onglet Basic → Full name
3. Entrez le nom complet
4. Save

## Ressources Associées

- **OID Ressource OpenLDAP** : `10000000-0000-0000-0000-000000000001`
- **OID Rôle LDAP User** : `12345678-1234-1234-1234-000000000001`

## Bonnes Pratiques

1. **Nommage des rôles** : Utilisez des noms descriptifs (ex: "LDAP User", "Database Admin")
2. **Documentation** : Ajoutez toujours une description au rôle
3. **Test** : Testez le rôle avec un utilisateur de test avant déploiement
4. **Audit** : Consultez l'onglet History pour suivre les assignations

---

*Documentation créée pour le projet IAM Gateway - Synchronisation Odoo → MidPoint → LDAP*
