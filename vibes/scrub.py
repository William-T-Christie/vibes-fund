"""Before every commit: scan the data and logs for anything shaped like a key, and fail if found."""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

from . import config

PATTERNS = [
    re.compile(r"sk-ant-[A-Za-z0-9_\-]{20,}"),              # Anthropic / Claude Code tokens
    re.compile(r"\b(PK|AK|CK)[A-Z0-9]{16,}\b"),               # Alpaca key ids
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{30,}\b"),            # GitHub tokens
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(r"(?i)(secret|api[_-]?key|token)[\"']?\s*[:=]\s*[\"'][A-Za-z0-9/+_\-]{24,}[\"']"),
]


def scan(paths: list[Path]) -> list[str]:
    secrets = [v for k, v in os.environ.items()
               if k in ("ALPACA_KEY", "ALPACA_SECRET", "CLAUDE_CODE_OAUTH_TOKEN") and v and len(v) >= 8]
    hits = []
    for root in paths:
        files = [root] if root.is_file() else [p for p in root.rglob("*") if p.is_file()]
        for f in files:
            try:
                text = f.read_text(errors="ignore")
            except OSError:
                continue
            for s in secrets:
                if s in text:
                    hits.append(f"{f}: contains the value of a secret")
            for p in PATTERNS:
                if p.search(text):
                    hits.append(f"{f}: matches {p.pattern[:40]}")
    return hits


def main() -> int:
    hits = scan([config.DATA_DIR])
    for h in hits:
        print(f"SCRUB FAIL {h}", file=sys.stderr)
    if hits:
        return 1
    print("scrub: clean")
    return 0
