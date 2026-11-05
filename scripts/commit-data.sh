#!/usr/bin/env bash
# Commit and push only data/vibes/. Scrubs for key-shaped strings first, rebases, retries once.
set -euo pipefail
msg="${1:?commit message}"

uv run vibes scrub

git config user.name "vibes-fund-bot"
git config user.email "vibes-fund-bot@users.noreply.github.com"
git add data/vibes/
if git diff --cached --quiet; then
  echo "Nothing to commit."
  exit 0
fi
git commit -m "$msg"
for attempt in 1 2; do
  git pull --rebase origin "${GITHUB_REF_NAME:-main}" && git push origin "HEAD:${GITHUB_REF_NAME:-main}" && exit 0
  echo "Push failed (attempt $attempt); retrying."
  sleep 5
done
exit 1
