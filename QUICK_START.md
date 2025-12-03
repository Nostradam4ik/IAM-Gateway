# Guide de Démarrage Rapide - Gateway IAM

Ce guide vous permet de démarrer rapidement le Gateway IAM avec les services essentiels.

---

## Option 1 : Démarrage Complet (Recommandé)

### Démarrer tous les services :
```bash
cd /home/vboxuser/Desktop/Project3
docker compose up -d
```

### Vérifier le statut :
```bash
docker compose ps
```

### Initialiser la base de données :
```bash
./scripts/init-db.sh
```

### Accéder aux services :
- **Gateway API** : http://localhost:8000/docs
- **Gateway Frontend** : http://localhost:3000
- **MidPoint** : http://localhost:8080/midpoint (admin / admin)
- **Keycloak** : http://localhost:8081 (admin / admin)
- **Odoo** : http://localhost:8069 (admin / admin)
- **phpLDAPadmin** : http://localhost:8088
- **Qdrant Dashboard** : http://localhost:6333/dashboard

---

## Option 2 : Démarrage Minimal (Pour Tests)

Si vous voulez tester uniquement le Gateway sans tous les services :

### 1. Créer un docker-compose minimal :
```bash
cat > docker-compose.minimal.yml << 'EOF'
version: "3.9"

services:
  gateway-db:
    image: postgres:15
    container_name: gateway-db
    environment:
      POSTGRES_DB: gateway
      POSTGRES_USER: gateway
      POSTGRES_PASSWORD: gateway
    ports:
      - "5434:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U gateway"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    container_name: gateway-redis
    ports:
      - "6379:6379"

  gateway:
    build: ./gateway
    container_name: gateway-iam
    depends_on:
      - gateway-db
      - redis
    environment:
      DATABASE_URL: postgresql+asyncpg://gateway:gateway@gateway-db:5432/gateway
      REDIS_URL: redis://redis:6379/0
      SECRET_KEY: dev-secret-key-change-in-production
      DEBUG: "true"
    ports:
      - "8000:8000"
    volumes:
      - ./gateway/app:/app/app
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

volumes:
  gateway_db_data:
EOF
```

### 2. Démarrer les services minimaux :
```bash
docker compose -f docker-compose.minimal.yml up -d
```

### 3. Initialiser la DB :
```bash
docker compose -f docker-compose.minimal.yml exec gateway python -m app.db.migrations
```

### 4. Tester l'API :
```bash
curl http://localhost:8000/
```

---

## Résolution des Problèmes

### Le build échoue
```bash
# Nettoyer et reconstruire
docker compose down -v
docker compose build --no-cache
docker compose up -d
```

### Un service ne démarre pas
```bash
# Voir les logs
docker compose logs [service_name]

# Exemples :
docker compose logs gateway
docker compose logs gateway-db
docker compose logs midpoint
```

### Ports déjà utilisés
```bash
# Trouver le processus qui utilise le port
sudo lsof -i :8000
# Ou changer le port dans docker-compose.yml
```

### Base de données non initialisée
```bash
docker compose exec gateway python -m app.db.migrations
```

---

## Commandes Utiles

### Voir tous les containers
```bash
docker compose ps -a
```

### Redémarrer un service
```bash
docker compose restart gateway
```

### Voir les logs en temps réel
```bash
docker compose logs -f gateway
```

### Arrêter tous les services
```bash
docker compose down
```

### Arrêter et supprimer les volumes
```bash
docker compose down -v
```

### Reconstruire un service spécifique
```bash
docker compose build gateway
docker compose up -d gateway
```

---

## Test Rapide de l'API

### 1. Vérifier que l'API répond
```bash
curl http://localhost:8000/
```

### 2. Se connecter (obtenir un token)
```bash
curl -X POST http://localhost:8000/api/admin/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'
```

### 3. Lister les règles (avec le token)
```bash
TOKEN="votre_token_ici"
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/rules
```

---

## Variables d'Environnement Importantes

Créez un fichier `.env` à la racine du projet :

```bash
# Security
SECRET_KEY=your-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-here

# OpenAI (optionnel)
OPENAI_API_KEY=sk-...

# Keycloak (optionnel)
KEYCLOAK_CLIENT_SECRET=your-client-secret

# Debug
DEBUG=false
```

---

## Prochaines Étapes

Une fois que tout fonctionne :

1. ✅ Testez l'API avec Swagger UI : http://localhost:8000/docs
2. ✅ Connectez-vous au Frontend : http://localhost:3000
3. ✅ Configurez les règles de provisioning
4. ✅ Testez le provisioning LDAP
5. ✅ Configurez MidPoint pour utiliser le Gateway

Consultez [TESTING_GUIDE.md](./TESTING_GUIDE.md) pour les tests détaillés.
