"""Tests for the fail-fast secret validation in Settings."""
import pytest

from app.core.config import Settings


def test_production_rejects_missing_secret():
    with pytest.raises(RuntimeError):
        Settings(DEBUG=False, SECRET_KEY="", JWT_SECRET_KEY="")


def test_production_rejects_known_placeholder():
    with pytest.raises(RuntimeError):
        Settings(
            DEBUG=False,
            SECRET_KEY="a" * 48,
            JWT_SECRET_KEY="jwt-secret-change-in-production",
        )


def test_production_rejects_short_secret():
    with pytest.raises(RuntimeError):
        Settings(DEBUG=False, SECRET_KEY="a" * 48, JWT_SECRET_KEY="short")


def test_production_accepts_strong_secrets():
    s = Settings(DEBUG=False, SECRET_KEY="a" * 48, JWT_SECRET_KEY="b" * 48)
    assert s.JWT_SECRET_KEY == "b" * 48


def test_debug_autogenerates_when_unset():
    s = Settings(DEBUG=True, SECRET_KEY="", JWT_SECRET_KEY="")
    assert len(s.SECRET_KEY) >= 32
    assert len(s.JWT_SECRET_KEY) >= 32
