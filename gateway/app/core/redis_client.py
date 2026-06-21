"""
Client Redis pour le cache, les sessions et la gestion des tokens.
Utilise le conteneur gateway-redis (redis:7-alpine) sur le port 6379.
"""
from typing import Optional, Any
import json
import redis.asyncio as aioredis
import structlog

from app.core.config import settings

logger = structlog.get_logger()


class RedisClient:
    """Client Redis asynchrone pour l'application Gateway IAM."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._redis: Optional[aioredis.Redis] = None

    async def connect(self) -> bool:
        """Etablit la connexion Redis."""
        try:
            self._redis = aioredis.from_url(
                settings.REDIS_URL,
                decode_responses=True,
                socket_connect_timeout=5
            )
            await self._redis.ping()
            logger.info("Redis connected", url=settings.REDIS_URL)
            return True
        except Exception as e:
            logger.warning("Redis connection failed, cache disabled", error=str(e))
            self._redis = None
            return False

    async def close(self):
        """Ferme la connexion Redis."""
        if self._redis:
            await self._redis.close()
            self._redis = None

    @property
    def is_connected(self) -> bool:
        return self._redis is not None

    async def health_check(self) -> dict:
        """Verifie l'etat de Redis."""
        if not self._redis:
            return {"status": "disconnected", "error": "Not connected"}
        try:
            await self._redis.ping()
            info = await self._redis.info("memory")
            return {
                "status": "healthy",
                "used_memory": info.get("used_memory_human", "unknown"),
                "connected_clients": info.get("connected_clients", 0)
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}

    # ==================== Token Blacklist ====================

    async def blacklist_token(self, token_jti: str, ttl_seconds: int = 3600) -> bool:
        """Ajoute un token JWT a la blacklist (pour logout/revocation)."""
        if not self._redis:
            return False
        try:
            await self._redis.setex(f"blacklist:{token_jti}", ttl_seconds, "1")
            return True
        except Exception as e:
            logger.error("Failed to blacklist token", error=str(e))
            return False

    async def is_token_blacklisted(self, token_jti: str) -> bool:
        """Verifie si un token est dans la blacklist."""
        if not self._redis:
            return False
        try:
            return await self._redis.exists(f"blacklist:{token_jti}") > 0
        except Exception:
            return False

    # ==================== Session Cache ====================

    async def cache_user_session(self, username: str, session_data: dict, ttl_seconds: int = 3600) -> bool:
        """Cache les donnees de session utilisateur."""
        if not self._redis:
            return False
        try:
            await self._redis.setex(
                f"session:{username}",
                ttl_seconds,
                json.dumps(session_data)
            )
            return True
        except Exception as e:
            logger.error("Failed to cache session", error=str(e))
            return False

    async def get_user_session(self, username: str) -> Optional[dict]:
        """Recupere les donnees de session depuis le cache."""
        if not self._redis:
            return None
        try:
            data = await self._redis.get(f"session:{username}")
            return json.loads(data) if data else None
        except Exception:
            return None

    async def invalidate_session(self, username: str) -> bool:
        """Invalide la session d'un utilisateur."""
        if not self._redis:
            return False
        try:
            await self._redis.delete(f"session:{username}")
            return True
        except Exception:
            return False

    # ==================== Workflow Token Cache ====================

    async def cache_workflow_token(self, token: str, workflow_data: dict, ttl_seconds: int = 259200) -> bool:
        """Cache un token d'approbation workflow (defaut: 72h)."""
        if not self._redis:
            return False
        try:
            await self._redis.setex(
                f"wf_token:{token}",
                ttl_seconds,
                json.dumps(workflow_data)
            )
            return True
        except Exception as e:
            logger.error("Failed to cache workflow token", error=str(e))
            return False

    async def get_workflow_token(self, token: str) -> Optional[dict]:
        """Recupere les donnees d'un token workflow."""
        if not self._redis:
            return None
        try:
            data = await self._redis.get(f"wf_token:{token}")
            return json.loads(data) if data else None
        except Exception:
            return None

    async def invalidate_workflow_token(self, token: str) -> bool:
        """Invalide un token workflow apres utilisation."""
        if not self._redis:
            return False
        try:
            await self._redis.delete(f"wf_token:{token}")
            return True
        except Exception:
            return False

    # ==================== General Cache ====================

    async def set_cache(self, key: str, value: Any, ttl_seconds: int = 300) -> bool:
        """Stocke une valeur dans le cache avec TTL."""
        if not self._redis:
            return False
        try:
            if isinstance(value, (dict, list)):
                value = json.dumps(value)
            await self._redis.setex(f"cache:{key}", ttl_seconds, str(value))
            return True
        except Exception as e:
            logger.error("Failed to set cache", key=key, error=str(e))
            return False

    async def get_cache(self, key: str) -> Optional[str]:
        """Recupere une valeur du cache."""
        if not self._redis:
            return None
        try:
            return await self._redis.get(f"cache:{key}")
        except Exception:
            return None

    async def delete_cache(self, key: str) -> bool:
        """Supprime une entree du cache."""
        if not self._redis:
            return False
        try:
            await self._redis.delete(f"cache:{key}")
            return True
        except Exception:
            return False

    # ==================== Rate Limiting ====================

    # Script Lua atomique: incremente et pose le TTL en une seule operation
    # (evite la fenetre INCR/EXPIRE non atomique qui laissait des cles sans TTL).
    _RATE_LIMIT_LUA = (
        "local c = redis.call('INCR', KEYS[1]) "
        "if c == 1 then redis.call('EXPIRE', KEYS[1], ARGV[1]) end "
        "return c"
    )

    async def check_rate_limit(self, key: str, max_requests: int = 10, window_seconds: int = 60) -> bool:
        """Verifie et incremente le compteur de rate limiting (atomique). Retourne True si autorise."""
        if not self._redis:
            return True  # Redis indisponible: on ne bloque pas (disponibilite > defense-en-profondeur)
        try:
            rate_key = f"rate:{key}"
            current = await self._redis.eval(self._RATE_LIMIT_LUA, 1, rate_key, window_seconds)
            return int(current) <= max_requests
        except Exception as e:
            logger.warning("Rate limit check failed (allowing)", error=str(e))
            return True


# Instance globale
redis_client = RedisClient()
