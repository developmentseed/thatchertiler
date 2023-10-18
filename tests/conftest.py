"""``pytest`` configuration."""

import os

import pytest
from starlette.testclient import TestClient

DATA_DIR = os.path.join(os.path.dirname(__file__), "fixtures")


@pytest.fixture
def set_env(monkeypatch):
    """Set Env variables."""
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "jqt")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "rde")
    monkeypatch.setenv("AWS_DEFAULT_REGION", "us-west-2")
    monkeypatch.setenv("AWS_REGION", "us-west-2")
    monkeypatch.delenv("AWS_PROFILE", raising=False)
    monkeypatch.setenv("AWS_CONFIG_FILE", "/tmp/noconfigheere")
    monkeypatch.setenv("THATCHERTILER_API_CACHECONTROL", "private, max-age=3600")


@pytest.fixture(autouse=True)
def app(set_env) -> TestClient:
    """Create App."""
    from thatchertiler.main import app

    return TestClient(app)
