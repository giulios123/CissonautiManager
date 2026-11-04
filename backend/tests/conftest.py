import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


@pytest.fixture
def settings(tmp_path) -> Settings:
    return Settings(
        _env_file=None,
        app_env="test",
        database_url=f"sqlite:///{tmp_path / 'test.db'}",
        static_dir=str(tmp_path / "static"),
        secret_key="test-secret",
    )


@pytest.fixture
def client(settings: Settings) -> TestClient:
    return TestClient(create_app(settings))
