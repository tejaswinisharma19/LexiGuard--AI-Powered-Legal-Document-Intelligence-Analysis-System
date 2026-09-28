import os
import pytest
from config import get_secret_key, INSECURE_SECRET_KEYS


def test_development_mode_default_secret_key(monkeypatch):
    monkeypatch.setenv("FLASK_ENV", "development")
    monkeypatch.delenv("SECRET_KEY", raising=False)
    secret = get_secret_key()
    assert secret == "lexiguard-dev-secret-key-do-not-use-in-production"


def test_development_mode_custom_secret_key(monkeypatch):
    monkeypatch.setenv("FLASK_ENV", "development")
    monkeypatch.setenv("SECRET_KEY", "custom-dev-key")
    secret = get_secret_key()
    assert secret == "custom-dev-key"


def test_production_mode_valid_secret_key(monkeypatch):
    monkeypatch.setenv("FLASK_ENV", "production")
    monkeypatch.setenv("SECRET_KEY", "a-very-secure-production-secret-key-9988776655")
    secret = get_secret_key()
    assert secret == "a-very-secure-production-secret-key-9988776655"


def test_production_mode_missing_secret_key(monkeypatch):
    monkeypatch.setenv("FLASK_ENV", "production")
    monkeypatch.delenv("SECRET_KEY", raising=False)
    with pytest.raises(ValueError, match="SECRET_KEY must be securely and explicitly configured"):
        get_secret_key()


def test_production_mode_insecure_secret_key(monkeypatch):
    monkeypatch.setenv("FLASK_ENV", "production")
    for key in INSECURE_SECRET_KEYS:
        monkeypatch.setenv("SECRET_KEY", key)
        with pytest.raises(ValueError, match="SECRET_KEY must be securely and explicitly configured"):
            get_secret_key()
