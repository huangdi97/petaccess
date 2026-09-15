"""Startup configuration validation (§75).

A missing configuration must fail at boot with a named reason — not surface
later as a ``KeyError`` in a request handler, and definitely not silently run
with a secret that is published in this repository.
"""

from __future__ import annotations

import pytest

from app.core.config import (
    DEV_ONLY_DEFAULTS,
    InsecureDefaultSecret,
    Settings,
    validate_runtime,
)

DEV_SECRET = "dev_only_change_me_min_32_bytes_0123456789abcdef"


def _settings(**over) -> Settings:
    base = {
        "app_env": "development",
        "database_url": "postgresql+psycopg://u:p@localhost:5432/db",
        "redis_url": "redis://localhost:6379/0",
        "jwt_secret": "x" * 40,
    }
    base.update(over)
    return Settings(**base)


def test_a_development_environment_may_keep_the_dev_default():
    validate_runtime(_settings(app_env="development", jwt_secret=DEV_SECRET))


@pytest.mark.parametrize("env", sorted({"production", "prod", "staging"}))
def test_a_production_environment_must_not_keep_the_dev_default(env):
    with pytest.raises(InsecureDefaultSecret) as exc:
        validate_runtime(_settings(app_env=env, jwt_secret=DEV_SECRET))
    assert "jwt_secret" in str(exc.value)


def test_a_production_environment_with_a_real_secret_starts():
    validate_runtime(_settings(app_env="production", jwt_secret="a" * 48))


def test_the_known_dev_default_is_the_one_declared_in_settings():
    """Guard against the default drifting without the guard noticing."""
    assert DEV_SECRET in DEV_ONLY_DEFAULTS
    assert Settings().jwt_secret == DEV_SECRET
