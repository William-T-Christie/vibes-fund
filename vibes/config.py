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
MIN_HOLDINGS = 3          # enforced once the first week (5 trading days) is over
MAX_HOLDINGS = 6          # high conviction: few, big bets
FIRST_WEEK_DAYS = 5
POSITION_CAP = 0.35       # of NAV, after the trade
MAX_CASH_NORMAL = 0.30    # above this is a "defensive" call and must be explained
MAX_TRADES_PER_DAY = 4
MIN_ORDER_DOLLARS = 1_000.0
MAX_REASON_CHARS = 200
FULL_CLOSE_THRESHOLD = 0.98  # a sell for >= 98% of a position closes it entirely

# Honesty corrections
SLIPPAGE_RESERVE = 0.0010          # 0.10% of every filled trade's notional, subtracted from NAV
SLIPPAGE_RESERVE_THIN = 0.0025     # 0.25% for names trading under $200M a day, which really do cost more
THIN_DOLLAR_VOLUME = 200_000_000
MIN_AVG_DOLLAR_VOLUME = 20_000_000  # 20-day average daily dollar volume
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

# Leveraged and inverse ETFs: only these broad and sector funds, one at a time, gated by the mood.
# Everything else that looks leveraged (single-stock funds, volatility products) stays banned.
LEVERAGED_ALLOWED = {
    # ticker: (direction, leverage)
    "QLD": ("bull", 2), "SSO": ("bull", 2), "TQQQ": ("bull", 3), "UPRO": ("bull", 3), "SPXL": ("bull", 3),
    "TNA": ("bull", 3), "SOXL": ("bull", 3), "TECL": ("bull", 3), "FAS": ("bull", 3), "ERX": ("bull", 2),
    "LABU": ("bull", 3),
    "PSQ": ("bear", 1), "SH": ("bear", 1), "QID": ("bear", 2), "SDS": ("bear", 2), "SQQQ": ("bear", 3),
    "SPXU": ("bear", 3), "SPXS": ("bear", 3), "TZA": ("bear", 3), "SOXS": ("bear", 3), "FAZ": ("bear", 3),
    "LABD": ("bear", 3),
}
LEVERAGED_MAX_HOLDINGS = 1
LEVERAGED_MAX_CONVICTION = "firm"  # 20% of NAV, so at most 60% market exposure
LEVERAGED_BULL_MIN_MOOD = 0.4      # bull funds only on mornings this good
LEVERAGED_BEAR_MAX_MOOD = -0.4     # bear funds only on mornings this grim
LEVERAGED_NAME_MARKERS = (
    # Plain "short" is left out on purpose so short-term Treasury ETFs stay allowed.
    "2x", "3x", "1.5x", "-1x", "ultra", "leveraged", "inverse", "daily bull", "daily bear",
    "short s&p", "short qqq", "short dow", "short russell",
)
BANNED_TICKERS = {"UVXY", "SVXY", "VXX", "VIXY", "TSLL", "NVDL", "TSLQ", "NVDQ", "CONL", "MSTU", "MSTX"}

# The vibes playbook (docs/vibes-playbook.md)
CONVICTION = {"mild": 0.10, "firm": 0.20, "strong": 0.30, "total": 0.35}  # share of NAV per buy
SELL_SIZES = {"trim": 0.5, "exit": 1.0}
TRADE_KINDS = ("direct", "sector", "leap", "wild_card")
WILD_CARDS_PER_WEEK = 1
# What a trade is based on. Earnings drift: after a beat-and-raise, prices tend to keep moving for weeks.
CATALYSTS = ("earnings_beat", "earnings_miss", "event", "opinion")
DRIFT_DAYS = 30  # trading days a position opened on an earnings beat is held unless the news turns
MAX_LEAPS_PER_DAY = 3
VERDICTS = ("intact", "strengthened", "weakened", "dead")
FADING_DAYS = 15  # trading days without a supporting headline
RECENT_SALE_DAYS = 3  # sale proceeds this recent don't count against the mood's cash limit
SIZE_ROUNDING = 100  # dollars round down to this
# Most cash allowed in each mood once the first week is over (the 30% rule stays the hard limit).
MOOD_CASH_CEILING = {"Doom": 0.50, "Nervous": 0.30, "Unbothered": 0.15, "Optimistic": 0.05, "Euphoric": 0.0}
SECTOR_FUNDS = {
    "XLK": "tech", "XLF": "financials", "XLE": "energy", "XLV": "health care",
    "XLY": "consumer discretionary", "XLP": "consumer staples", "XLI": "industrials",
    "XLB": "materials", "XLU": "utilities", "XLRE": "real estate", "XLC": "communication", "GLD": "gold",
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
