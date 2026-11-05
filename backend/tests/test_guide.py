import json

from tests.test_auth import login


def write_notes(settings, tmp_path, content: str) -> None:
    path = tmp_path / "release_notes.json"
    path.write_text(content, encoding="utf-8")
    settings.release_notes_path = str(path)


class TestVersion:
    def test_defaults_to_dev_without_build_info(self, client):
        assert client.get("/api/version").json() == {"version": "dev", "built_at": None}

    def test_reports_the_deployed_version(self, app, client):
        app.state.settings.app_version = "abc1234"
        app.state.settings.built_at = "2026-11-05T10:30:00+00:00"
        body = client.get("/api/version").json()
        assert body["version"] == "abc1234"
        assert body["built_at"].startswith("2026-11-05T10:30:00")


class TestReleaseNotes:
    def test_anonymous_is_refused(self, client):
        assert client.get("/api/admin/release-notes").status_code == 401

    def test_participant_is_refused(self, client, outbox, make_participant):
        make_participant("ada@example.com")
        login(client, outbox)
        assert client.get("/api/admin/release-notes").status_code == 403

    def test_admin_gets_the_releases(self, admin_client, settings, tmp_path):
        notes = {
            "releases": [
                {
                    "version": "abc1234",
                    "date": "2026-11-05T10:30:00+00:00",
                    "features": ["add the guide"],
                    "fixes": ["fix the title"],
                }
            ]
        }
        write_notes(settings, tmp_path, json.dumps(notes))
        releases = admin_client.get("/api/admin/release-notes").json()["releases"]
        assert releases[0]["version"] == "abc1234"
        assert releases[0]["features"] == ["add the guide"]
        assert releases[0]["fixes"] == ["fix the title"]

    def test_missing_file_means_no_releases(self, admin_client, settings, tmp_path):
        settings.release_notes_path = str(tmp_path / "nothing.json")
        assert admin_client.get("/api/admin/release-notes").json() == {"releases": []}

    def test_broken_file_means_no_releases(self, admin_client, settings, tmp_path):
        write_notes(settings, tmp_path, "{not json")
        assert admin_client.get("/api/admin/release-notes").json() == {"releases": []}

    def test_invalid_entry_means_no_releases(self, admin_client, settings, tmp_path):
        write_notes(settings, tmp_path, '{"releases": [{}]}')
        response = admin_client.get("/api/admin/release-notes")
        assert response.status_code == 200
        assert response.json() == {"releases": []}

    def test_unexpected_shape_means_no_releases(self, admin_client, settings, tmp_path):
        write_notes(settings, tmp_path, '{"releases": "oops"}')
        assert admin_client.get("/api/admin/release-notes").json() == {"releases": []}
