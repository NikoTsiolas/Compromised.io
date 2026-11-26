"""Shared fixtures. Suites: tests/pipeline (pipeline seam) and tests/api (HTTP API seam)."""

import os

import psycopg
import pytest

from compromised import storage

TEST_DATABASE_URL = os.environ.get("TEST_DATABASE_URL", "postgresql:///compromised_test")


@pytest.fixture(scope="session")
def database_url() -> str:
    storage.migrate(TEST_DATABASE_URL)
    return TEST_DATABASE_URL


@pytest.fixture
def conn(database_url):
    with psycopg.connect(database_url, autocommit=True) as connection:
        storage.reset_for_tests(connection)
        yield connection
