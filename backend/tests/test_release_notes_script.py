import importlib.util
import subprocess
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "release_notes.py"
spec = importlib.util.spec_from_file_location("release_notes_script", SCRIPT)
script = importlib.util.module_from_spec(spec)
spec.loader.exec_module(script)


def raw(version, *subjects, date="2026-11-05T10:00:00+01:00"):
    return {"version": version, "date": date, "subjects": list(subjects)}


class TestParseSubject:
    def test_feature_and_fix_lose_their_prefix(self):
        assert script.parse_subject("feat: add the guide") == ("features", "Add the guide")
        assert script.parse_subject("fix: keep the title") == ("fixes", "Keep the title")

    def test_perf_counts_as_a_feature(self):
        assert script.parse_subject("perf: load the report faster")[0] == "features"

    def test_scope_and_breaking_mark_are_dropped(self):
        assert script.parse_subject("feat(admin)!: new menu") == ("features", "New menu")

    def test_other_types_and_free_text_are_ignored(self):
        for subject in [
            "docs: update",
            "test: add",
            "chore: bump",
            "refactor: x",
            "Merge pull request #8",
        ]:
            assert script.parse_subject(subject) is None


class TestBuildNotes:
    def test_groups_by_release_keeping_the_order(self):
        notes = script.build_notes([raw("bbb", "feat: b1", "fix: b2"), raw("aaa", "feat: a1")])[
            "releases"
        ]
        assert [r["version"] for r in notes] == ["bbb", "aaa"]
        assert notes[0]["features"] == ["B1"]
        assert notes[0]["fixes"] == ["B2"]

    def test_releases_with_nothing_to_show_are_skipped(self):
        notes = script.build_notes([raw("ccc", "docs: x", "chore: y"), raw("bbb", "fix: z")])
        assert [r["version"] for r in notes["releases"]] == ["bbb"]

    def test_repeated_lines_in_a_release_appear_once(self):
        notes = script.build_notes([raw("aaa", "fix: same", "fix: same")])["releases"]
        assert notes[0]["fixes"] == ["Same"]

    def test_limit_counts_shown_releases(self):
        many = [raw(f"v{i}", "feat: x") for i in range(10)]
        assert len(script.build_notes(many, limit=3)["releases"]) == 3


class TestCollectReleases:
    def git(self, repo, *args):
        subprocess.run(
            ["git", "-c", "user.name=T", "-c", "user.email=t@example.com", *args],
            cwd=repo,
            check=True,
            capture_output=True,
        )

    def test_a_merge_is_a_release_and_a_direct_commit_too(self, tmp_path, monkeypatch):
        self.git(tmp_path, "init", "-q", "-b", "main")
        self.git(tmp_path, "commit", "-q", "--allow-empty", "-m", "chore: start")
        self.git(tmp_path, "checkout", "-q", "-b", "topic")
        self.git(tmp_path, "commit", "-q", "--allow-empty", "-m", "feat: first")
        self.git(tmp_path, "commit", "-q", "--allow-empty", "-m", "fix: second")
        self.git(tmp_path, "checkout", "-q", "main")
        self.git(tmp_path, "merge", "-q", "--no-ff", "topic", "-m", "Merge pull request #1")
        self.git(tmp_path, "commit", "-q", "--allow-empty", "-m", "fix: direct")
        monkeypatch.chdir(tmp_path)

        notes = script.build_notes(script.collect_releases("main"))["releases"]

        assert [(r["features"], r["fixes"]) for r in notes] == [
            ([], ["Direct"]),
            (["First"], ["Second"]),
        ]
