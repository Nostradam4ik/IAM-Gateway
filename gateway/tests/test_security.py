"""Unit tests for the auth/security core: password hashing, JWT, RBAC."""
import pytest
from fastapi import HTTPException
from jose import jwt

from app.core import security as sec
from app.core.config import settings


def test_password_hash_and_verify():
    h = sec.get_password_hash("correct horse")
    assert h != "correct horse"
    assert sec.verify_password("correct horse", h) is True
    assert sec.verify_password("wrong", h) is False


async def test_async_password_helpers():
    h = await sec.get_password_hash_async("pw")
    assert await sec.verify_password_async("pw", h) is True
    assert await sec.verify_password_async("nope", h) is False


def test_jwt_roundtrip_includes_iss_aud_jti():
    token = sec.create_access_token({"sub": "alice", "roles": ["admin"]})
    payload = sec.decode_token(token)
    assert payload["sub"] == "alice"
    assert payload["roles"] == ["admin"]
    assert payload["iss"] == settings.JWT_ISSUER
    assert payload["aud"] == settings.JWT_AUDIENCE
    assert "jti" in payload


def test_jwt_forged_with_wrong_key_is_rejected():
    forged = jwt.encode(
        {"sub": "attacker", "roles": ["admin"], "iss": settings.JWT_ISSUER, "aud": settings.JWT_AUDIENCE},
        "the-wrong-signing-key",
        algorithm=settings.JWT_ALGORITHM,
    )
    with pytest.raises(HTTPException):
        sec.decode_token(forged)


def test_jwt_wrong_audience_is_rejected():
    token = jwt.encode(
        {"sub": "x", "aud": "some-other-service", "iss": settings.JWT_ISSUER},
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )
    with pytest.raises(HTTPException):
        sec.decode_token(token)


async def test_require_role_allows_matching_and_denies_others():
    checker = sec.require_role(["admin", "iam_engineer"])
    ok = await checker({"username": "a", "roles": ["iam_engineer"]})
    assert ok["username"] == "a"
    with pytest.raises(HTTPException):
        await checker({"username": "b", "roles": ["viewer"]})
