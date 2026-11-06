#!/usr/bin/env bash
# Fails when a change touches what users see (pages or API) without touching the in-app guide
# in both languages (it/ and en/).
# Reads the changed file names on stdin. Set SKIP_GUIDE_CHECK=1 to skip (the `senza-guida` label).
set -euo pipefail

if [ "${SKIP_GUIDE_CHECK:-}" = "1" ]; then
  echo "Guide check skipped (label senza-guida)."
  exit 0
fi

files=$(cat)
visible=$(printf '%s\n' "$files" | grep -E '^(frontend/src/pages/|backend/app/api/)' | grep -Ev '\.test\.tsx?$' || true)
guide_it=$(printf '%s\n' "$files" | grep -E '^frontend/src/guide/it/.+\.md$' || true)
guide_en=$(printf '%s\n' "$files" | grep -E '^frontend/src/guide/en/.+\.md$' || true)

if [ -n "$visible" ] && { [ -z "$guide_it" ] || [ -z "$guide_en" ]; }; then
  echo "This change touches pages or API but not the guide in both languages"
  echo "(frontend/src/guide/it/ and frontend/src/guide/en/):"
  printf '%s\n' "$visible" | sed 's/^/  /'
  [ -z "$guide_it" ] && echo "  missing: Italian guide (it/)"
  [ -z "$guide_en" ] && echo "  missing: English guide (en/)"
  echo
  echo "Update the matching section of the guide (participant/ or admin/) in Italian and English,"
  echo "or add the 'senza-guida' label to the pull request if nothing visible changes."
  exit 1
fi
echo "Guide check passed."
