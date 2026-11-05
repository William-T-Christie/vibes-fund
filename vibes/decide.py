"""Ask the Chairman for today's trades.

Runs Claude Code headless on the subscription token (CLAUDE_CODE_OAUTH_TOKEN) with every tool
turned off, so Claude can only read the prompt and return text. Its output is plain data that
validate.py checks before anything reaches Alpaca. This step never sees the Alpaca keys.

The call is one swappable function (`call_claude`), so moving to a paid API key later is a small change.
"""

from __future__ import annotations

import json
import re
import subprocess
import tempfile
from typing import Callable

from . import config

DECISION_SCHEMA = {
    "type": "object",
    "required": ["mood", "summary", "trades"],
    "properties": {
        "mood": {
            "type": "object",
            "required": ["label", "score"],
            "properties": {"label": {"type": "string"}, "score": {"type": "number"}},
        },
        "summary": {"type": "string"},
        "trades": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["action", "ticker", "dollars", "reason", "headline_id"],
                "properties": {
                    "action": {"type": "string", "enum": ["buy", "sell"]},
                    "ticker": {"type": "string"},
                    "dollars": {"type": "number"},
                    "reason": {"type": "string"},
                    "headline_id": {"type": "string"},
                },
            },
        },
        "holds": {"type": "string"},
    },
}


class DecisionError(RuntimeError):
    pass


def prompt_version() -> str:
    first = config.PROMPT_VERSION_FILE.read_text().splitlines()[0]
    m = re.search(r"prompt-version:\s*([\w.\-]+)", first)
    return m.group(1) if m else "unknown"


def build_prompt(*, date: str, day_number: int, book: dict, headlines: list[dict], recent_reasons: list[str]) -> str:
    template = config.PROMPT_VERSION_FILE.read_text()
    template = re.sub(r"<!--.*?-->\n?", "", template, flags=re.S)
    nav = book["nav"]
    cash = book["cash"]
    if book["positions"]:
        rows = ["| Ticker | Value | Weight | Gain since bought |", "| --- | --- | --- | --- |"]
        for p in book["positions"]:
            rows.append(
                f"| {p['ticker']} | ${p['market_value']:,.0f} | {100 * p['market_value'] / nav:.1f}% "
                f"| {p['gain_pct']:+.1f}% |"
            )
        holdings_table = "\n".join(rows)
    else:
        holdings_table = "The fund holds nothing yet. It is all cash and conviction."
    lines = []
    for h in headlines:
        tick = f" [{', '.join(h['tickers'][:5])}]" if h.get("tickers") else ""
        lines.append(f"- {h['id']} ({h['source']}, {h['published']}){tick}: {h['title']}")
    return template.format(
        chairman=config.CHAIRMAN,
        fund_name=config.FUND_NAME,
        date=date,
        day_number=day_number,
        max_trades=config.MAX_TRADES_PER_DAY,
        min_holdings=config.MIN_HOLDINGS,
        max_holdings=config.MAX_HOLDINGS,
        position_cap_pct=int(config.POSITION_CAP * 100),
        max_cash_pct=int(config.MAX_CASH_NORMAL * 100),
        min_order=config.MIN_ORDER_DOLLARS,
        max_reason=config.MAX_REASON_CHARS,
        nav=nav,
        cash=cash,
        cash_pct=100 * cash / nav if nav else 0,
        holdings_table=holdings_table,
        recent_reasons="\n".join(f"- {r}" for r in recent_reasons) or "- None yet. This is the beginning.",
        headlines="\n".join(lines),
    )


def call_claude(prompt: str) -> str:
    """Run Claude Code headless with no tools. Returns the raw stdout (Claude Code's JSON envelope)."""
    cmd = [
        "claude", "-p",
        "--model", config.CLAUDE_MODEL,
        "--output-format", "json",
        "--tools", "",
        "--strict-mcp-config",
        "--no-session-persistence",
        "--json-schema", json.dumps(DECISION_SCHEMA),
    ]
    # Run from an empty folder so no project settings or CLAUDE.md are picked up.
    with tempfile.TemporaryDirectory() as empty:
        proc = subprocess.run(
            cmd, input=prompt, capture_output=True, text=True,
            timeout=config.CLAUDE_TIMEOUT_SECONDS, cwd=empty,
        )
    if proc.returncode != 0:
        raise DecisionError(f"claude exited {proc.returncode}: {proc.stderr[-500:]}")
    return proc.stdout


def parse(raw: str) -> dict:
    """Pull the decision object out of Claude Code's JSON envelope, or out of bare text."""
    try:
        env = json.loads(raw)
    except json.JSONDecodeError:
        env = None
    if isinstance(env, dict):
        if env.get("is_error"):
            raise DecisionError(f"claude reported an error: {str(env.get('result'))[:300]}")
        if isinstance(env.get("structured_output"), dict):
            return _check_shape(env["structured_output"])
        if "mood" in env and "trades" in env:
            return _check_shape(env)
        text = env.get("result") or ""
    else:
        text = raw
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip(), flags=re.M)
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end <= start:
        raise DecisionError("no JSON object in Claude's reply")
    try:
        obj = json.loads(text[start : end + 1])
    except json.JSONDecodeError as e:
        raise DecisionError(f"broken JSON: {e}") from e
    return _check_shape(obj)


def _check_shape(obj: dict) -> dict:
    if not isinstance(obj, dict):
        raise DecisionError("decision is not an object")
    mood = obj.get("mood")
    if not isinstance(mood, dict) or not isinstance(mood.get("score"), (int, float)):
        raise DecisionError("missing mood score")
    if not isinstance(obj.get("trades"), list):
        raise DecisionError("trades must be a list")
    obj.setdefault("summary", "")
    obj.setdefault("holds", "")
    return obj


def decide(prompt: str, caller: Callable[[str], str] = call_claude) -> tuple[dict | None, list[dict]]:
    """Call Claude, retry once on failure (with the error attached if the JSON was broken).

    Returns (decision or None, attempts log). None means hold for the day.
    """
    attempts: list[dict] = []
    current = prompt
    for n in (1, 2):
        try:
            raw = caller(current)
        except (DecisionError, subprocess.TimeoutExpired, FileNotFoundError) as e:
            attempts.append({"attempt": n, "error": f"call failed: {e}"})
            continue
        try:
            decision = parse(raw)
            attempts.append({"attempt": n, "raw": raw})
            return decision, attempts
        except DecisionError as e:
            attempts.append({"attempt": n, "raw": raw, "error": str(e)})
            current = (
                prompt
                + f"\n\nYour previous reply could not be used ({e}). Reply with only the JSON object."
            )
    return None, attempts
