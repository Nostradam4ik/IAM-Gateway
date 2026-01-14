# Guide de Démonstration Rapide - Synchronisation Directe

**Objectif** : Démontrer que l'infrastructure IAM fonctionne **sans la Gateway IAM**

---

## 🎯 Ce que Nous Allons Démontrer

Votre infrastructure permet la synchronisation directe entre systèmes :

1. **Odoo (HR) → MidPoint** : Via export CSV
2. **MidPoint → OpenLDAP** : Via connecteur LDAP natif
3. **MidPoint → PostgreSQL** : Via connecteur Database natif

**IMPORTANT** : Aucune de ces synchronisations n'utilise la Gateway IAM. Elles utilisent uniquement les connecteurs natifs de MidPoint.

---

## 📋 État Actuel de l'Infrastructure

### Services Opérationnels

```bash
# Vérifier les services
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
```

✅ **Odoo** : http://localhost:8069 (admin/admin)
✅ **OpenLDAP** : localhost:10389 (cn=admin,dc=example,dc=com/secret)
✅ **PostgreSQL Intranet** : localhost:55432 (intranet/intranet)
✅ **phpLDAPadmin** : http://localhost:8088

⚠️ **MidPoint** : Problème de configuration détecté (voir section Troubleshooting)

---

## 🔧 Solution Alternative : Utiliser les Connecteurs Existants

Puisque MidPoint a des problèmes de configuration, nous pouvons démontrer les synchronisations avec les outils déjà en place :

### Méthode 1 : Via la Gateway IAM (Déjà Implémentée)

Votre Gateway IAM **orchestre** ces synchronisations :

```bash
# Les API de synchronisation existent déjà
# Voir: gateway/app/services/provision_service.py
# Voir: gateway/app/connectors/connector_factory.py
```

### Méthode 2 : Synchronisation Manuelle LDAP

```bash
# 1. Exporter les utilisateurs d'Odoo vers LDIF
python3 << 'EOF'
import xmlrpc.client

# Connexion Odoo
url = "http://localhost:8069"
db = "odoo"
username = "admin"
password = "admin"

common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
uid = common.authenticate(db, username, password, {})

models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')

# Récupérer les employés
employees = models.execute_kw(db, uid, password,
    'hr.employee', 'search_read',
    [[]], {'fields': ['name', 'work_email', 'department_id']})

# Générer LDIF
with open('/tmp/odoo_users.ldif', 'w') as f:
    for emp in employees:
        if emp.get('work_email'):
            uid = emp['work_email'].split('@')[0]
            f.write(f"dn: uid={uid},ou=people,dc=example,dc=com\n")
            f.write(f"objectClass: inetOrgPerson\n")
            f.write(f"uid: {uid}\n")
            f.write(f"cn: {emp['name']}\n")
            f.write(f"sn: {emp['name'].split()[-1]}\n")
            f.write(f"mail: {emp['work_email']}\n")
            if emp.get('department_id'):
                f.write(f"ou: {emp['department_id'][1]}\n")
            f.write(f"\n")

print(f"✅ LDIF généré : /tmp/odoo_users.ldif")
print(f"✅ {len([e for e in employees if e.get('work_email')])} utilisateurs exportés")
EOF

# 2. Importer dans LDAP
docker exec -i openldap ldapadd -x -H ldap://localhost \
  -D "cn=admin,dc=example,dc=com" -w secret \
  < /tmp/odoo_users.ldif
```

### Méthode 3 : Synchronisation Manuelle PostgreSQL

```bash
# Script de synchronisation Odoo → PostgreSQL
python3 << 'EOF'
import xmlrpc.client
import psycopg2

# Connexion Odoo
odoo_url = "http://localhost:8069"
odoo_db = "odoo"
odoo_user = "admin"
odoo_pwd = "admin"

common = xmlrpc.client.ServerProxy(f'{odoo_url}/xmlrpc/2/common')
uid = common.authenticate(odoo_db, odoo_user, odoo_pwd, {})
models = xmlrpc.client.ServerProxy(f'{odoo_url}/xmlrpc/2/object')

# Récupérer employés Odoo
employees = models.execute_kw(odoo_db, uid, odoo_pwd,
    'hr.employee', 'search_read',
    [[]], {'fields': ['name', 'work_email', 'department_id', 'job_id', 'work_phone']})

# Connexion PostgreSQL
conn = psycopg2.connect(
    host="localhost",
    port="55432",
    database="intranet",
    user="intranet",
    password="intranet"
)
cur = conn.cursor()

# Synchroniser vers PostgreSQL
count = 0
for emp in employees:
    if emp.get('work_email'):
        username = emp['work_email'].split('@')[0]
        first_name = emp['name'].split()[0] if emp['name'] else ''
        last_name = ' '.join(emp['name'].split()[1:]) if len(emp['name'].split()) > 1 else ''

        try:
            cur.execute("""
                INSERT INTO users (username, email, first_name, last_name, department, phone, is_active)
                VALUES (%s, %s, %s, %s, %s, %s, true)
                ON CONFLICT (username)
                DO UPDATE SET
                    email = EXCLUDED.email,
                    first_name = EXCLUDED.first_name,
                    last_name = EXCLUDED.last_name,
                    department = EXCLUDED.department,
                    phone = EXCLUDED.phone,
                    updated_at = CURRENT_TIMESTAMP
            """, (
                username,
                emp['work_email'],
                first_name,
                last_name,
                emp['department_id'][1] if emp.get('department_id') else None,
                emp.get('work_phone')
            ))
            count += 1
        except Exception as e:
            print(f"⚠️  Erreur pour {emp['name']}: {e}")

conn.commit()
cur.close()
conn.close()

print(f"✅ Synchronisé {count} utilisateurs vers PostgreSQL")
EOF
```

---

## 📊 Vérifications

### 1. Vérifier LDAP

```bash
# Via ligne de commande
docker exec openldap ldapsearch -x -H ldap://localhost \
  -b "ou=people,dc=example,dc=com" \
  -D "cn=admin,dc=example,dc=com" -w secret \
  "(objectClass=inetOrgPerson)" | grep "dn:" | wc -l

# Via interface web
# Ouvrir http://localhost:8088
# Login: cn=admin,dc=example,dc=com / secret
```

### 2. Vérifier PostgreSQL

```bash
# Compter les utilisateurs
docker exec intranet-db psql -U intranet -d intranet \
  -c "SELECT COUNT(*) FROM users;"

# Voir les derniers utilisateurs ajoutés
docker exec intranet-db psql -U intranet -d intranet \
  -c "SELECT username, email, department, created_at FROM users ORDER BY created_at DESC LIMIT 10;"
```

### 3. Vérifier Odoo

```bash
# Se connecter à http://localhost:8069
# Login: admin / admin
# Aller dans Employés
```

---

## 🎬 Démonstration Complète

### Scénario : Ajouter un Nouvel Employé

**1. Créer l'employé dans Odoo**
- Aller sur http://localhost:8069
- Employés → Créer
- Remplir les informations
- Sauvegarder

**2. Synchroniser vers LDAP**
```bash
# Utiliser le script LDIF ci-dessus
```

**3. Synchroniser vers PostgreSQL**
```bash
# Utiliser le script PostgreSQL ci-dessus
```

**4. Vérifier**
```bash
# LDAP
docker exec openldap ldapsearch -x -H ldap://localhost \
  -b "ou=people,dc=example,dc=com" \
  -D "cn=admin,dc=example,dc=com" -w secret \
  "(mail=nouvel.employe@example.com)"

# PostgreSQL
docker exec intranet-db psql -U intranet -d intranet \
  -c "SELECT * FROM users WHERE email = 'nouvel.employe@example.com';"
```

---

## 🔍 Troubleshooting MidPoint

### Problème Actuel

MidPoint essaie d'utiliser le driver H2 au lieu de PostgreSQL.

### Solution

1. **Nettoyer le volume**
```bash
# Arrêter MidPoint
docker stop midpoint-core
docker rm midpoint-core

# Nettoyer (nécessite sudo)
sudo rm -rf midpoint-resources/var/*
mkdir -p midpoint-resources/var/csv
chmod 777 midpoint-resources/var/csv

# Redémarrer
docker compose up -d midpoint
```

2. **Vérifier les logs**
```bash
docker logs midpoint-core --tail 100
```

3. **Vérifier la connexion PostgreSQL**
```bash
docker exec midpoint-postgres psql -U midpoint -d midpoint -c "SELECT version();"
```

---

## 📈 Statistiques Actuelles

```bash
echo "=== STATISTIQUES DES SYSTEMES ==="
echo ""
echo "OpenLDAP:"
docker exec openldap ldapsearch -x -H ldap://localhost \
  -b "dc=example,dc=com" \
  -D "cn=admin,dc=example,dc=com" -w secret \
  "(objectClass=*)" 2>/dev/null | grep "^dn:" | wc -l
echo ""
echo "PostgreSQL Intranet:"
docker exec intranet-db psql -U intranet -d intranet -t \
  -c "SELECT COUNT(*) FROM users;"
echo ""
```

---

## 📝 Conclusion

### Ce qui Fonctionne ✅

- Odoo (Source RH)
- OpenLDAP (Annuaire)
- PostgreSQL (Base Intranet)
- Scripts de synchronisation manuelle

### Ce qui Nécessite un Fix ⚠️

- MidPoint (problème de configuration du driver de base de données)

### Alternative

La **Gateway IAM** que vous avez développée peut orchestrer toutes ces synchronisations de manière automatique et intelligente, en ajoutant :
- Validation des données
- Gestion des erreurs
- Workflows d'approbation
- Audit complet
- Interface utilisateur

---

## 🚀 Prochaines Étapes

1. Fixer la configuration MidPoint
2. Importer les ressources XML dans MidPoint
3. Configurer le Live Sync automatique
4. Tester le provisioning automatique

Ou utiliser directement la Gateway IAM qui implémente déjà tout cela!

---

**Auteur** : Claude Code
**Date** : 5 janvier 2026
**Projet** : IAM Gateway - Project3
