"""
Module de securite - Authentification et Autorisation.

Ce module centralise toute la logique de securite de la Gateway IAM :
    - Hachage des mots de passe avec bcrypt (salage automatique)
    - Creation et validation de tokens JWT (JSON Web Tokens)
    - Revocation de tokens via blacklist Redis (JTI unique par token)
    - Controle d'acces base sur les roles (RBAC)

Flux d'authentification :
    1. POST /api/v1/admin/token avec username/password
    2. Verification bcrypt du mot de passe
    3. Generation d'un JWT avec JTI unique (UUID v4)
    4. Client envoie le token dans Authorization: Bearer <token>
    5. Chaque requete : decode JWT + verifie JTI dans blacklist Redis
"""
import asyncio
from datetime import datetime, timedelta
from typing import Optional
import uuid
from jose import JWTError, jwt
import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import structlog

from app.core.config import settings

logger = structlog.get_logger()

# Schema OAuth2 - extrait le token du header Authorization: Bearer <token>
# tokenUrl pointe vers l'endpoint de login pour la doc Swagger
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/admin/token")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifie un mot de passe en clair contre son hash bcrypt."""
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))


def get_password_hash(password: str) -> str:
    """Hache un mot de passe avec bcrypt (sel aleatoire, cout configurable)."""
    return bcrypt.hashpw(
        password.encode('utf-8'), bcrypt.gensalt(rounds=settings.BCRYPT_ROUNDS)
    ).decode('utf-8')


async def verify_password_async(plain_password: str, hashed_password: str) -> bool:
    """Verifie un mot de passe hors de la boucle d'evenements (bcrypt est bloquant et CPU-intensif)."""
    return await asyncio.to_thread(verify_password, plain_password, hashed_password)


async def get_password_hash_async(password: str) -> str:
    """Hache un mot de passe hors de la boucle d'evenements."""
    return await asyncio.to_thread(get_password_hash, password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Cree un token JWT avec un JTI unique pour supporter la revocation.

    Le token contient : sub (username), roles, exp (expiration), jti (UUID unique).
    Le JTI permet de revoquer individuellement un token via la blacklist Redis.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    to_encode.update({
        "exp": expire,
        "iss": settings.JWT_ISSUER,
        "aud": settings.JWT_AUDIENCE,
        "jti": str(uuid.uuid4())  # ID unique pour la revocation via Redis
    })
    encoded_jwt = jwt.encode(
        to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt


def decode_token(token: str) -> dict:
    """Decode et valide un token JWT (signature + expiration)."""
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
            audience=settings.JWT_AUDIENCE,
            issuer=settings.JWT_ISSUER,
        )
        return payload
    except JWTError as e:
        logger.error("JWT decode error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    """
    Recupere l'utilisateur courant depuis le token JWT.

    Verifie : 1) validite du token, 2) presence du username,
    3) que le JTI n'est pas dans la blacklist Redis (token revoque).
    Utilisee comme dependance FastAPI (Depends) dans les endpoints proteges.
    """
    payload = decode_token(token)
    username: str = payload.get("sub")
    if username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )

    # Verifier si le token est revoque via Redis
    from app.core.redis_client import redis_client
    jti = payload.get("jti")
    if jti and await redis_client.is_token_blacklisted(jti):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked",
        )

    return {"username": username, "roles": payload.get("roles", []), "jti": jti}


def require_role(required_roles: list):
    """
    Decorateur RBAC - exige au moins un des roles specifies.

    Usage : @router.get("/", dependencies=[Depends(require_role(["admin"]))])
    Leve 403 Forbidden si aucun role de l'utilisateur ne correspond.
    """
    async def role_checker(current_user: dict = Depends(get_current_user)):
        user_roles = current_user.get("roles", [])
        # L'utilisateur doit avoir AU MOINS UN des roles requis
        if not any(role in user_roles for role in required_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        return current_user
    return role_checker
