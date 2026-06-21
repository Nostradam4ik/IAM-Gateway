"""Tests for connector-level injection guards."""
import pytest

from app.connectors.connector_factory import _safe_sql_identifier


@pytest.mark.parametrize("name", ["username", "email", "first_name", "_x", "col1"])
def test_safe_sql_identifier_accepts_valid(name):
    assert _safe_sql_identifier(name) == name


@pytest.mark.parametrize(
    "name",
    [
        "email) VALUES ('a') RETURNING id; DROP TABLE users;--",
        "1col",
        "a b",
        "",
        "col;",
    ],
)
def test_safe_sql_identifier_rejects_injection(name):
    with pytest.raises(ValueError):
        _safe_sql_identifier(name)
