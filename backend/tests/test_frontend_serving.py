import pytest
from fastapi.testclient import TestClient

from app.main import create_app


@pytest.fixture
def spa_client(settings, tmp_path) -> TestClient:
    static = tmp_path / "static"
    (static / "assets").mkdir(parents=True)
    (static / "index.html").write_text("<html>spa</html>")
    (static / "assets" / "app.js").write_text("console.log('hi')")
    (tmp_path / "secret.txt").write_text("top secret")
    return TestClient(create_app(settings))


def test_client_side_route_returns_index(spa_client):
    response = spa_client.get("/iscrizione")
    assert response.status_code == 200
    assert "spa" in response.text


def test_static_asset_is_served(spa_client):
    response = spa_client.get("/assets/app.js")
    assert response.status_code == 200
    assert "console.log" in response.text


def test_unknown_api_route_returns_json_404(spa_client):
    response = spa_client.get("/api/does-not-exist")
    assert response.status_code == 404
    assert response.json() == {"detail": "Not Found"}


def test_path_traversal_does_not_leak_files(spa_client):
    response = spa_client.get("/..%2Fsecret.txt")
    assert "top secret" not in response.text


def test_api_still_works_with_frontend_mounted(spa_client):
    assert spa_client.get("/api/health").json() == {"status": "ok"}


def test_without_build_unknown_route_is_404(client):
    assert client.get("/iscrizione").status_code == 404
