from app.config import Settings


def test_health_returns_ok(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_settings_read_environment(monkeypatch):
    monkeypatch.setenv("ADMIN_EMAIL", "boss@example.com")
    monkeypatch.setenv("APP_ENV", "production")
    settings = Settings(_env_file=None)
    assert settings.admin_email == "boss@example.com"
    assert settings.is_production is True
