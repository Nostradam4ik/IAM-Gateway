"""
Shared pytest fixtures/configuration.

Sets a DEBUG environment with deterministic secrets BEFORE any app module is
imported, so app.core.config's startup secret validator passes during tests.
"""
import os

os.environ.setdefault("DEBUG", "true")
os.environ.setdefault("SECRET_KEY", "test-secret-" + "x" * 40)
os.environ.setdefault("JWT_SECRET_KEY", "test-jwt-secret-" + "y" * 40)
os.environ.setdefault("BCRYPT_ROUNDS", "4")  # fast hashing in tests
