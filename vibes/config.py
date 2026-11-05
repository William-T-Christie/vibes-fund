"""Fund rules, paths and constants. Code enforces every rule here; Claude is told them but never trusted."""

from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(os.environ.get("VIBES_ROOT", Path(__file__).resolve().parent.parent))
DATA_DIR = ROOT / "data" / "vibes"
LOGS_DIR = DATA_DIR / "logs"
WORK_DIR = ROOT / ".work"  # gitignored scratch passed between workflow steps
PROMPTS_DIR = Path(__file__).resolve().parent / "prompts"
PAUSED_FILE = ROOT / "PAUSED"  # kill switch: present = no trading, evening record still runs

# Fund identity. The final name is still open (Mood Ring Capital or Sentimental Value Partners).
FUND_NAME = os.environ.get("VIBES_FUND_NAME", "Mood Ring Capital")
CHAIRMAN = "Sir Peregrine Ashby"

# Fund rules
STARTING_CAPITAL = 100_000.0
MIN_HOLDINGS = 5          # enforced once the first week (5 trading days) is over
MAX_HOLDINGS = 10
FIRST_WEEK_DAYS = 5
POSITION_CAP = 0.20       # of NAV, after the trade
MAX_CASH_NORMAL = 0.30    # above this is a "defensive" call and must be explained
MAX_TRADES_PER_DAY = 4
MIN_ORDER_DOLLARS = 1_000.0
MAX_REASON_CHARS = 200
FULL_CLOSE_THRESHOLD = 0.98  # a sell for >= 98% of a position closes it entirely

# Honesty corrections
SLIPPAGE_RESERVE = 0.0010          # 0.10% of every filled trade's notional, subtracted from NAV
MIN_AVG_DOLLAR_VOLUME = 50_000_000  # 20-day average daily dollar volume
MAX_ORDER_PCT_OF_VOLUME = 0.01      # of the prior session's dollar volume
LIQUIDITY_LOOKBACK_DAYS = 20

# Timing (America/New_York)
MARKET_TZ = "America/New_York"
MORNING_EARLIEST = (9, 35)   # before this a run is "too early" and exits quietly
MORNING_CUTOFF = (11, 0)     # at or after this: "The manager overslept."
EVENING_EARLIEST = (16, 15)
UNFILLED_CANCEL_MINUTES = 30

# Headlines
MAX_HEADLINES = 60
RSS_FEEDS = [
    # General news so the fund can react to the wider world, not only market news.
    # Swap freely; feeds break or move without notice.
    "https://feeds.bbci.co.uk/news/business/rss.xml",
    "https://feeds.npr.org/1006/rss.xml",
]
USE_ALPACA_NEWS = os.environ.get("VIBES_USE_ALPACA_NEWS", "1") == "1"

# Claude
CLAUDE_MODEL = os.environ.get("VIBES_CLAUDE_MODEL", "claude-sonnet-5-5")
CLAUDE_TIMEOUT_SECONDS = 300
PROMPT_VERSION_FILE = PROMPTS_DIR / "manager.md"

# Alpaca (paper only; there is deliberately no setting for the live endpoint)
ALPACA_TRADING_URL = "https://paper-api.alpaca.markets"
ALPACA_DATA_URL = "https://data.alpaca.markets"
ALLOWED_EXCHANGES = {"NYSE", "NASDAQ", "ARCA", "AMEX", "BATS"}
BENCHMARK = "SPY"

# Leveraged and inverse ETFs are banned. Alpaca does not flag them, so match on name.
LEVERAGED_NAME_MARKERS = (
    # Plain "short" is left out on purpose so short-term Treasury ETFs stay allowed.
    "2x", "3x", "1.5x", "-1x", "ultra", "leveraged", "inverse", "daily bull", "daily bear",
    "short s&p", "short qqq", "short dow", "short russell",
)
BANNED_TICKERS = {
    "TQQQ", "SQQQ", "SPXL", "SPXS", "UPRO", "SPXU", "SH", "PSQ", "SDS", "QID", "QLD", "SSO",
    "SOXL", "SOXS", "TNA", "TZA", "LABU", "LABD", "UVXY", "SVXY", "VXX", "TSLL", "NVDL",
}

MOOD_BANDS = [
    # (label, low inclusive, high exclusive, color)
    ("Doom", -1.0, -0.6, "#2B2B2B"),
    ("Nervous", -0.6, -0.2, "#C98A1B"),
    ("Unbothered", -0.2, 0.2, "#4F8A5B"),
    ("Optimistic", 0.2, 0.6, "#2F6FA8"),
    ("Euphoric", 0.6, 1.0001, "#7B4FA8"),
]


def mood_band(score: float) -> tuple[str, str]:
    """Return (band label, mood ink) for a score in [-1, 1]."""
    s = max(-1.0, min(1.0, float(score)))
    for label, lo, hi, color in MOOD_BANDS:
        if lo <= s < hi:
            return label, color
    return MOOD_BANDS[-1][0], MOOD_BANDS[-1][3]
