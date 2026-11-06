import io

from PIL import Image

from app.email.card import MAX_UPLOAD_BYTES
from tests.test_auth import login


def png(size=(40, 20), color=(10, 20, 30, 0)):
    out = io.BytesIO()
    Image.new("RGBA", size, color).save(out, format="PNG")
    return out.getvalue()


def upload(client, data=None, filename="logo.png", content_type="image/png"):
    return client.put(
        "/api/admin/edition/logo",
        files={"file": (filename, data if data is not None else png(), content_type)},
    )


def test_admin_can_upload_replace_and_restore_the_edition_logo(admin_client, client, edition):
    first = upload(admin_client)
    assert first.status_code == 200
    first_url = first.json()["logo_url"]
    assert first_url.startswith("/api/public/edition/logo?v=")

    image_response = client.get(first_url)
    assert image_response.status_code == 200
    assert image_response.headers["content-type"] == "image/png"
    assert image_response.headers["cache-control"] == "public, max-age=31536000, immutable"
    image = Image.open(io.BytesIO(image_response.content))
    assert image.size == (40, 20)
    assert image.mode == "RGBA"
    assert image.getpixel((0, 0))[3] == 0

    replacement = upload(admin_client, png(color=(120, 80, 40, 255)))
    assert replacement.status_code == 200
    assert replacement.json()["logo_url"] != first_url
    assert client.get(first_url).status_code == 404

    restored = admin_client.delete("/api/admin/edition/logo")
    assert restored.status_code == 200
    assert restored.json()["logo_url"] is None
    assert client.get(first_url).status_code == 404


def test_invalid_upload_does_not_replace_the_saved_logo(admin_client, client, edition):
    saved = upload(admin_client)
    saved_url = saved.json()["logo_url"]

    invalid = upload(admin_client, b"not an image")
    oversized = upload(admin_client, b"0" * (MAX_UPLOAD_BYTES + 1))

    assert invalid.status_code == 422
    assert oversized.status_code == 413
    assert admin_client.get("/api/admin/edition").json()["logo_url"] == saved_url
    assert client.get(saved_url).status_code == 200


def test_participant_and_anonymous_visitors_cannot_change_the_logo(
    client, outbox, make_participant, edition
):
    assert upload(client).status_code == 401
    make_participant("person@example.com")
    login(client, outbox, "person@example.com")
    assert upload(client).status_code == 403
    assert client.delete("/api/admin/edition/logo").status_code == 403


def test_logo_remains_public_when_registration_is_closed(admin_client, client):
    response = admin_client.put(
        "/api/admin/edition",
        json={"name": "Camp", "start_date": "2026-07-13", "end_date": "2026-07-13"},
    )
    assert response.status_code == 200
    logo = upload(admin_client)
    assert logo.status_code == 200

    edition = client.get("/api/public/edition")
    assert edition.json()["registration_open"] is False
    assert edition.json()["logo_url"] == logo.json()["logo_url"]
    assert client.get(edition.json()["logo_url"]).status_code == 200


def test_logo_url_is_empty_until_a_logo_is_uploaded(client, edition):
    edition_response = client.get("/api/public/edition")
    assert edition_response.json()["logo_url"] is None
    assert client.get("/api/public/edition/logo").status_code == 404
