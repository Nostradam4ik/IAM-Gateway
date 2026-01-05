# TODO LIST - Etapes suivantes apres TP1

## Statut : TP1 Complete

---

## PHASE 1 : Configuration MidPoint (En cours)

### Connecteur LDAP
- [x] Creer le fichier XML de configuration (`ldap-resource.xml`)
- [ ] Configurer le connecteur via l'interface MidPoint
  - [ ] Selectionner LdapConnector
  - [ ] Configurer les parametres de connexion (host: openldap, port: 389)
  - [ ] Configurer le Bind DN et mot de passe
  - [ ] Selectionner l'Object Class `inetOrgPerson`
  - [ ] Configurer le schema (ou=people,dc=example,dc=com)
- [ ] Tester la connexion LDAP
- [ ] Mapper les attributs (uid, cn, sn, givenName, mail)

### Connecteur CSV
- [x] Creer le fichier XML de configuration (`csv-resource.xml`)
- [ ] Creer le repertoire CSV dans MidPoint
  ```bash
  docker compose exec midpoint-core mkdir -p /opt/midpoint/var/csv
  docker compose exec midpoint-core bash -c "echo 'uid,firstname,lastname,email' > /opt/midpoint/var/csv/users.csv"
  ```
- [ ] Configurer le connecteur via l'interface MidPoint
- [ ] Tester la connexion CSV

### Connecteur Database (Intranet)
- [x] Creer le fichier XML de configuration (`database-resource.xml`)
- [ ] Configurer le connecteur via l'interface MidPoint
  - [ ] JDBC URL: jdbc:postgresql://intranet-db:5432/intranet
  - [ ] Table: users
  - [ ] Key Column: id
- [ ] Tester la connexion Database
- [ ] Mapper les colonnes (username, email, first_name, last_name)

---

## PHASE 2 : Configuration des Roles MidPoint

- [ ] Creer le role "Employee"
  - [ ] Ajouter l'inducement LDAP account
  - [ ] Ajouter l'inducement Database account
  - [ ] Ajouter l'inducement CSV account
- [ ] Creer le role "Manager"
  - [ ] Heriter du role Employee
  - [ ] Ajouter des droits supplementaires
- [ ] Creer le role "IT Admin"
  - [ ] Acces complet aux systemes

---

## PHASE 3 : Tests de Provisionnement

### Test 1 : Creation d'utilisateur via MidPoint
- [ ] Creer un utilisateur test (jdoe) dans MidPoint
- [ ] Assigner le role "Employee"
- [ ] Verifier la creation dans LDAP :
  ```bash
  docker compose exec openldap ldapsearch -x -b "dc=example,dc=com" "(uid=jdoe)"
  ```
- [ ] Verifier la creation dans Intranet DB :
  ```bash
  docker compose exec intranet-db psql -U intranet -d intranet -c "SELECT * FROM users WHERE username='jdoe';"
  ```
- [ ] Verifier la creation dans le fichier CSV

### Test 2 : Creation d'utilisateur via Gateway
- [ ] Utiliser l'API Gateway pour creer un utilisateur :
  ```bash
  curl -X POST http://localhost:8000/api/v1/provision/ \
    -H "Authorization: Bearer <TOKEN>" \
    -H "Content-Type: application/json" \
    -d '{
      "source_type": "HR",
      "target_systems": ["LDAP", "SQL"],
      "user_data": {
        "employee_id": "EMP002",
        "firstname": "Marie",
        "lastname": "Martin",
        "email": "marie.martin@example.com",
        "department": "HR"
      }
    }'
  ```
- [ ] Verifier le statut de l'operation
- [ ] Verifier la propagation vers les systemes cibles

### Test 3 : Modification d'utilisateur
- [ ] Modifier un attribut utilisateur via Gateway
- [ ] Verifier la synchronisation vers tous les systemes

### Test 4 : Suppression d'utilisateur
- [ ] Supprimer un utilisateur via Gateway
- [ ] Verifier la desactivation/suppression dans les systemes cibles

---

## PHASE 4 : Workflows d'Approbation

- [ ] Configurer un workflow a 1 niveau
  - [ ] Demande -> Approbation Manager -> Execution
- [ ] Configurer un workflow a 2 niveaux
  - [ ] Demande -> Manager -> RH -> Execution
- [ ] Tester le processus d'approbation
  - [ ] Creer une demande
  - [ ] Approuver/Rejeter
  - [ ] Verifier l'execution ou l'annulation

---

## PHASE 5 : Assistant IA (Optionnel)

- [ ] Configurer l'API Key (OpenAI ou DeepSeek)
  ```env
  OPENAI_API_KEY=sk-...
  # ou
  DEEPSEEK_API_KEY=...
  ```
- [ ] Tester les requetes en langage naturel :
  - [ ] "Cree un compte pour Jean Dupont dans le departement IT"
  - [ ] "Liste tous les utilisateurs du departement HR"
  - [ ] "Desactive le compte de jdoe"

---

## PHASE 6 : Monitoring et Audit

- [ ] Verifier les logs d'audit dans la Gateway
- [ ] Configurer les alertes email (optionnel)
- [ ] Tester le bouton "Emergency Stop"
- [ ] Tester la reprise du systeme

---

## PHASE 7 : Documentation

- [x] Creer RAPPORT_TP1_GATEWAY_IAM.md
- [x] Creer GUIDE_CONFIGURATION_MIDPOINT.md
- [ ] Documenter les tests effectues
- [ ] Preparer la presentation finale

---

## Commandes Utiles

### Demarrage
```bash
docker compose up -d
docker compose logs -f gateway
```

### Obtenir un token JWT
```bash
curl -X POST http://localhost:8000/api/v1/admin/token \
  -d "username=admin&password=admin123"
```

### Verifier le statut des connecteurs
```bash
TOKEN="<votre_token>"
curl http://localhost:8000/api/v1/admin/connectors/status \
  -H "Authorization: Bearer $TOKEN"
```

### Acces aux interfaces
- Gateway Frontend : http://localhost:3001
- MidPoint Admin : http://localhost:8080/midpoint/admin/
- Odoo : http://localhost:8069
- Keycloak : http://localhost:8081

---

## Problemes Connus et Solutions

| Probleme | Solution |
|----------|----------|
| MidPoint ne demarre pas | Attendre 2-3 minutes, verifier les logs |
| Erreur LDAP connection | Verifier que openldap est demarré |
| Erreur Database | Verifier les credentials dans config.py |
| Token expire | Regenerer un nouveau token |

---

**Derniere mise a jour** : Decembre 2025
