# Synchronisation Directe Sans Gateway IAM

## 🎯 Objectif

Ce guide démontre que votre infrastructure IAM peut fonctionner **sans la Gateway IAM**, en utilisant uniquement les connecteurs natifs et des scripts de synchronisation directe.

---

## 📁 Fichiers de Démonstration

| Fichier | Description |
|---------|-------------|
| [DEMONSTRATION_SYNC_DIRECTE.md](./DEMONSTRATION_SYNC_DIRECTE.md) | Guide complet avec MidPoint |
| [GUIDE_DEMONSTRATION_RAPIDE.md](./GUIDE_DEMONSTRATION_RAPIDE.md) | Guide rapide avec solutions alternatives |
| [scripts/demo_sync_direct.py](../../scripts/demo_sync_direct.py) | Script Python de synchronisation |
| [scripts/demo_sync_complete.sh](../../scripts/demo_sync_complete.sh) | Script Bash complet |

---

## 🚀 Démarrage Rapide

### Option 1 : Script Python (Recommandé)

```bash
# Installer les dépendances si nécessaire
pip3 install psycopg2-binary

# Lancer la synchronisation
python3 scripts/demo_sync_direct.py
```

**Ce que fait ce script:**
1. ✅ Se connecte à Odoo et récupère tous les employés
2. ✅ Génère un fichier LDIF pour OpenLDAP
3. ✅ Synchronise directement vers PostgreSQL (Intranet DB)
4. ✅ Affiche les statistiques complètes

### Option 2 : Script Bash Complet

```bash
# Lancer la démonstration complète
./scripts/demo_sync_complete.sh
```

---

## 📊 Architecture de Synchronisation

```
┌─────────────────┐
│      ODOO       │  ← Source RH (Système Source)
│   Employés HR   │     http://localhost:8069
└────────┬────────┘     admin / admin
         │
         │ Scripts de Synchronisation Directe
         │ • demo_sync_direct.py
         │ • import_odoo_to_midpoint.py
         ↓
    ┌────────────┐
    │   LDIF     │  Fichier intermédiaire
    │    CSV     │  /tmp/odoo_sync_*.ldif
    └──┬─────┬───┘
       │     │
       ↓     ↓
┌──────────┐ ┌──────────────┐
│ OpenLDAP │ │  PostgreSQL  │
│ Annuaire │ │   Intranet   │
└──────────┘ └──────────────┘
   :10389       :55432
```

### ⚠️ Note Importante

**MidPoint n'est PAS utilisé** dans cette démonstration simplifiée, car il a des problèmes de configuration. Les scripts contournent MidPoint et synchronisent directement.

---

## 🔧 Services Requis

### Vérifier les Services

```bash
docker ps --format "table {{.Names}}\t{{.Status}}"
```

### Démarrer les Services Nécessaires

```bash
# PostgreSQL Intranet
docker start intranet-db

# Odoo
docker start odoo-db odoo

# OpenLDAP
docker start openldap
```

### Accès aux Services

| Service | URL/Host | Identifiants |
|---------|----------|--------------|
| **Odoo** | http://localhost:8069 | admin / admin |
| **phpLDAPadmin** | http://localhost:8088 | cn=admin,dc=example,dc=com / secret |
| **PostgreSQL** | localhost:55432 | intranet / intranet |
| **OpenLDAP** | localhost:10389 | cn=admin,dc=example,dc=com / secret |

---

## 📝 Étapes de Démonstration

### 1. Lancer la Synchronisation

```bash
python3 scripts/demo_sync_direct.py
```

### 2. Importer le Fichier LDIF dans OpenLDAP

```bash
docker exec -i openldap ldapadd -x -H ldap://localhost \
  -D "cn=admin,dc=example,dc=com" -w secret \
  < /tmp/odoo_sync_to_ldap.ldif
```

### 3. Vérifier dans LDAP (Interface Web)

1. Ouvrir http://localhost:8088
2. Login: `cn=admin,dc=example,dc=com` / `secret`
3. Naviguer dans `dc=example,dc=com` → `ou=people`
4. Vérifier que les utilisateurs sont présents

### 4. Vérifier dans PostgreSQL

```bash
# Compter les utilisateurs
docker exec intranet-db psql -U intranet -d intranet \
  -c "SELECT COUNT(*) FROM users;"

# Voir les derniers utilisateurs
docker exec intranet-db psql -U intranet -d intranet \
  -c "SELECT username, email, department, created_at FROM users ORDER BY created_at DESC LIMIT 10;"
```

---

## 🎬 Scénario de Test Complet

### Ajouter un Nouvel Employé dans Odoo

**1. Créer dans Odoo**
```
Aller sur http://localhost:8069
→ Employés → Créer
→ Nom: Test Synchronisation
→ Email: test.sync@example.com
→ Département: IT
→ Sauvegarder
```

**2. Re-synchroniser**
```bash
python3 scripts/demo_sync_direct.py
```

**3. Importer dans LDAP**
```bash
docker exec -i openldap ldapadd -x -H ldap://localhost \
  -D "cn=admin,dc=example,dc=com" -w secret \
  < /tmp/odoo_sync_to_ldap.ldif
```

**4. Vérifier**
```bash
# LDAP
docker exec openldap ldapsearch -x -H ldap://localhost \
  -b "ou=people,dc=example,dc=com" \
  -D "cn=admin,dc=example,dc=com" -w secret \
  "(mail=test.sync@example.com)"

# PostgreSQL
docker exec intranet-db psql -U intranet -d intranet \
  -c "SELECT * FROM users WHERE email = 'test.sync@example.com';"
```

---

## 📈 Statistiques

### Compter les Utilisateurs dans Chaque Système

```bash
# Script de vérification rapide
echo "=== STATISTIQUES DES SYSTEMES ==="
echo ""

echo -n "Odoo: "
# (Connectez-vous à l'interface pour compter)

echo -n "LDAP: "
docker exec openldap ldapsearch -x -H ldap://localhost \
  -b "ou=people,dc=example,dc=com" \
  -D "cn=admin,dc=example,dc=com" -w secret \
  "(objectClass=inetOrgPerson)" 2>/dev/null | grep "^dn:" | wc -l

echo -n "PostgreSQL: "
docker exec intranet-db psql -U intranet -d intranet -t \
  -c "SELECT COUNT(*) FROM users;"
```

---

## 🔍 Troubleshooting

### Problème: Odoo Inaccessible

```bash
docker start odoo-db odoo
docker logs odoo --tail 50
```

### Problème: LDAP Inaccessible

```bash
docker start openldap
docker logs openldap --tail 50
```

### Problème: PostgreSQL Inaccessible

```bash
docker start intranet-db
docker exec intranet-db psql -U intranet -d intranet -c "SELECT version();"
```

### Problème: Import LDIF Échoue

```bash
# Vérifier que le fichier LDIF existe
cat /tmp/odoo_sync_to_ldap.ldif

# Vérifier la syntaxe LDIF
docker exec -i openldap slapcat -n 2 > /tmp/ldap_backup.ldif
```

---

## 🔄 Synchronisation Automatique (Optionnel)

### Via Cron

```bash
# Éditer le crontab
crontab -e

# Ajouter pour une synchronisation toutes les 10 minutes
*/10 * * * * /usr/bin/python3 /home/vboxuser/Desktop/Project3/scripts/demo_sync_direct.py >> /tmp/sync_log.txt 2>&1
```

---

## 💡 Avantages de la Gateway IAM

Cette démonstration montre qu'on **peut** synchroniser sans la Gateway, mais la Gateway IAM apporte:

### ✨ Avantages de la Gateway

1. **Orchestration Intelligente**
   - Workflows d'approbation
   - Validation automatique des données
   - Gestion des erreurs sophistiquée

2. **Audit Complet**
   - Traçabilité de toutes les opérations
   - Logs centralisés
   - Conformité RGPD

3. **Interface Utilisateur**
   - Dashboard de monitoring
   - Gestion visuelle des opérations
   - Rapports automatiques

4. **Intelligence Artificielle**
   - Assistant IA pour les décisions
   - Détection d'anomalies
   - Recommandations automatiques

5. **Scalabilité**
   - Cache Redis
   - File d'attente asynchrone
   - Performance optimisée

### 🎯 Conclusion

- **Sans Gateway** : Synchronisation manuelle possible mais basique
- **Avec Gateway** : Orchestration intelligente et automatisée

La Gateway IAM est une **surcouche d'intelligence** qui rend l'infrastructure IAM :
- Plus robuste
- Plus intelligente
- Plus facile à gérer
- Conforme et auditable

---

## 📚 Documentation Associée

- [RESUME_CONNECTEUR_CSV_MIDPOINT.md](../reports/RESUME_CONNECTEUR_CSV_MIDPOINT.md) - Configuration CSV MidPoint
- [DEMONSTRATION_SYNC_DIRECTE.md](./DEMONSTRATION_SYNC_DIRECTE.md) - Guide complet
- [GUIDE_DEMONSTRATION_RAPIDE.md](./GUIDE_DEMONSTRATION_RAPIDE.md) - Guide rapide

---

## 🤝 Support

Pour toute question ou problème :
1. Vérifiez les logs : `docker logs <container>`
2. Consultez les guides de troubleshooting
3. Vérifiez que tous les services sont démarrés

---

**Auteur** : Claude Code
**Date** : 5 janvier 2026
**Projet** : IAM Gateway - Project3
**Repository** : https://github.com/Nostradam4ik/Project3
