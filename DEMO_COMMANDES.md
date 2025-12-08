# Commandes de Démonstration - Gateway IAM

## 1. Obtenir le Token (à faire en premier)

```bash
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/admin/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123" | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
echo "Token: $TOKEN"
```

---

## 2. Vérifier les Connecteurs

```bash
curl -s http://localhost:8000/api/v1/admin/connectors/status \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
```

---

## 3. Afficher les Règles

```bash
curl -s http://localhost:8000/api/v1/rules/ \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
```

---

## 4. Créer un Utilisateur (LDAP + SQL)

```bash
curl -s -X POST http://localhost:8000/api/v1/provision/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "operation": "create",
    "account_id": "jdupont",
    "target_systems": ["LDAP", "SQL"],
    "attributes": {
      "firstname": "Jean",
      "lastname": "Dupont",
      "email": "jean.dupont@example.com",
      "department": "IT"
    }
  }' | python3 -m json.tool
```

---

## 5. Créer un Utilisateur Multi-Cibles (LDAP + SQL + ODOO)

```bash
curl -s -X POST http://localhost:8000/api/v1/provision/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "operation": "create",
    "account_id": "mmartin",
    "target_systems": ["LDAP", "SQL", "ODOO"],
    "attributes": {
      "firstname": "Marie",
      "lastname": "Martin",
      "email": "marie.martin@example.com",
      "department": "Finance"
    }
  }' | python3 -m json.tool
```

---

## 6. Créer un Manager (Haute Priorité)

```bash
curl -s -X POST http://localhost:8000/api/v1/provision/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "operation": "create",
    "account_id": "pdurand",
    "target_systems": ["LDAP", "SQL", "ODOO"],
    "attributes": {
      "firstname": "Pierre",
      "lastname": "Durand",
      "email": "pierre.durand@example.com",
      "department": "Direction",
      "title": "Directeur Technique"
    },
    "priority": "high"
  }' | python3 -m json.tool
```

---

## 7. Tester une Règle de Calcul

```bash
curl -s -X POST http://localhost:8000/api/v1/rules/test \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "expression": "{{ firstname | normalize_name }}.{{ lastname | normalize_name }}",
    "test_data": {
      "firstname": "François",
      "lastname": "Lefèvre"
    }
  }' | python3 -m json.tool
```

---

## 8. Lancer une Réconciliation

```bash
curl -s -X POST http://localhost:8000/api/v1/reconcile/start \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "target_systems": ["LDAP", "SQL"],
    "full_sync": false
  }' | python3 -m json.tool
```

---

## 9. Voir les Logs d'Audit

```bash
curl -s http://localhost:8000/api/v1/admin/audit/recent \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
```

---

## 10. État du Système

```bash
curl -s http://localhost:8000/api/v1/admin/status \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
```

---

## 11. Arrêt d'Urgence (ATTENTION!)

```bash
curl -s -X POST http://localhost:8000/api/v1/admin/emergency-stop \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
```

---

## 12. Reprendre après Arrêt d'Urgence

```bash
curl -s -X POST http://localhost:8000/api/v1/admin/resume \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
```

---

## URLs Importantes

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| API Swagger | http://localhost:8000/docs |
| API ReDoc | http://localhost:8000/redoc |

## Identifiants

- **Username:** admin
- **Password:** admin123
