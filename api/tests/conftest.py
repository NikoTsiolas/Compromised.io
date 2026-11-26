import os
from pathlib import Path

import psycopg
import pytest

from compromised import storage

FIXTURES = Path(__file__).parent / "fixtures"
TEST_DATABASE_URL = os.environ.get("TEST_DATABASE_URL", "postgresql:///compromised_test")


def real_sample(name: str) -> bytes:
    """Bytes of a real captured feed response (see fixtures/real/README.md)."""
    return (FIXTURES / "real" / name).read_bytes()


@pytest.fixture(scope="session")
def database_url() -> str:
    storage.migrate(TEST_DATABASE_URL)
    return TEST_DATABASE_URL


@pytest.fixture
def conn(database_url):
    with psycopg.connect(database_url, autocommit=True) as connection:
        storage.reset_for_tests(connection)
        yield connection
