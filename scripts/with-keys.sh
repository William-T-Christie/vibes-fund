#!/usr/bin/env bash
# Run a command with the Alpaca paper keys read from the macOS Keychain.
# Keys are never written to a file, an env file, or shell history.
#
# One-time setup (each command prompts for the value; nothing is echoed):
#   security add-generic-password -a "$USER" -s vibes-alpaca-key -w
#   security add-generic-password -a "$USER" -s vibes-alpaca-secret -w
#
# Usage:
#   scripts/with-keys.sh uv run vibes replay --name first-look --days 5
set -euo pipefail
ALPACA_KEY="$(security find-generic-password -a "$USER" -s vibes-alpaca-key -w 2>/dev/null)" || {
  echo "No vibes-alpaca-key in the Keychain. See the setup lines at the top of this script." >&2; exit 1; }
ALPACA_SECRET="$(security find-generic-password -a "$USER" -s vibes-alpaca-secret -w 2>/dev/null)" || {
  echo "No vibes-alpaca-secret in the Keychain. See the setup lines at the top of this script." >&2; exit 1; }
case "$ALPACA_KEY" in
  PK*) ;;
  *) echo "That key doesn't look like a paper key (paper keys start with PK). Use paper keys only." >&2; exit 1 ;;
esac
export ALPACA_KEY ALPACA_SECRET
exec "$@"
