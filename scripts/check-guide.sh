#!/usr/bin/env bash
# Fails when a change touches what users see (pages or API) without touching the in-app guide.
# Reads the changed file names on stdin. Set SKIP_GUIDE_CHECK=1 to skip (the `senza-guida` label).
set -euo pipefail

if [ "${SKIP_GUIDE_CHECK:-}" = "1" ]; then
  echo "Guide check skipped (label senza-guida)."
  exit 0
fi

files=$(cat)
visible=$(printf '%s\n' "$files" | grep -E '^(frontend/src/pages/|backend/app/api/)' | grep -Ev '\.test\.tsx?$' || true)
guide=$(printf '%s\n' "$files" | grep -E '^frontend/src/guide/.+\.md$' || true)

if [ -n "$visible" ] && [ -z "$guide" ]; then
  echo "This change touches pages or API but not the guide in frontend/src/guide/:"
  printf '%s\n' "$visible" | sed 's/^/  /'
  echo
  echo "Update the matching section of the guide (partecipante/ or admin/), or add the"
  echo "'senza-guida' label to the pull request if nothing visible changes."
  exit 1
fi
echo "Guide check passed."
