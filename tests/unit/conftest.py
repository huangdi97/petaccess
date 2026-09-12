"""Unit-test fixtures: DB session rolled back per test (real Postgres)."""

import pytest

from app.db.session import get_session_factory


@pytest.fixture
def db_session():
    session = get_session_factory()()
    try:
        yield session
        session.rollback()
    finally:
        session.close()
