"""Build the release notes shown to admins from the git history.

Every merge on the first-parent line of the branch is a deploy. The notes of a deploy are the
`feat`, `fix` and `perf` commits that the merge brought in. Run at deploy time (full history is
needed) and written as JSON for the backend to serve.

    python scripts/release_notes.py --out backend/release_notes.json
"""

import argparse
import json
import re
import subprocess
from pathlib import Path

MAX_RELEASES = 30
FEATURE_TYPES = {"feat", "perf"}
FIX_TYPES = {"fix"}
CONVENTIONAL = re.compile(r"^(?P<type>[a-z]+)(\([^)]*\))?!?:\s*(?P<text>\S.*)$")

FIELD = "\x1f"
RECORD = "\x1e"


def parse_subject(subject: str) -> tuple[str, str] | None:
    """('features' | 'fixes', text) for a commit worth showing, None for the rest."""
    match = CONVENTIONAL.match(subject.strip())
    if not match:
        return None
    kind, text = match.group("type"), match.group("text").strip()
    text = text[0].upper() + text[1:]
    if kind in FEATURE_TYPES:
        return "features", text
    if kind in FIX_TYPES:
        return "fixes", text
    return None


def build_notes(raw_releases: list[dict], limit: int = MAX_RELEASES) -> dict:
    """`raw_releases` is newest first: {version, date, subjects}. Releases with nothing to show
    (documentation, tests, chores) are left out."""
    releases = []
    for raw in raw_releases:
        entry = {"version": raw["version"], "date": raw["date"], "features": [], "fixes": []}
        for subject in raw["subjects"]:
            parsed = parse_subject(subject)
            if parsed and parsed[1] not in entry[parsed[0]]:
                entry[parsed[0]].append(parsed[1])
        if entry["features"] or entry["fixes"]:
            releases.append(entry)
        if len(releases) == limit:
            break
    return {"releases": releases}


def _git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], check=True, capture_output=True, text=True, encoding="utf-8"
    ).stdout


def collect_releases(ref: str = "HEAD", scan: int = 200) -> list[dict]:
    """Newest first. A merge is a release made of the commits of the merged branch; a commit
    pushed straight to the branch is a release of its own."""
    log = _git(
        "log", "--first-parent", f"-{scan}", f"--format=%H{FIELD}%P{FIELD}%cI{FIELD}%s{RECORD}", ref
    )
    releases = []
    for record in filter(None, (r.strip() for r in log.split(RECORD))):
        sha, parents, date, subject = record.split(FIELD, 3)
        parent_list = parents.split()
        if len(parent_list) > 1:
            merged = _git("log", "--format=%s", f"{parent_list[0]}..{parent_list[1]}")
            subjects = [line for line in merged.splitlines() if line]
        else:
            subjects = [subject]
        releases.append({"version": sha[:7], "date": date, "subjects": subjects})
    return releases


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--ref", default="HEAD")
    args = parser.parse_args()
    notes = build_notes(collect_releases(args.ref))
    args.out.write_text(json.dumps(notes, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"{len(notes['releases'])} releases written to {args.out}")


if __name__ == "__main__":
    main()
