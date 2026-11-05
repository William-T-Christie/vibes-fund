"""Time helpers. GitHub cron runs in UTC; every gate checks the real New York time."""

from __future__ import annotations

from datetime import datetime, time, timezone
from zoneinfo import ZoneInfo

from . import config

ET = ZoneInfo(config.MARKET_TZ)


def now_et() -> datetime:
    return datetime.now(timezone.utc).astimezone(ET)


def today_et(now: datetime | None = None) -> str:
    return (now or now_et()).date().isoformat()


def morning_window(now: datetime) -> str:
    """'early', 'open' or 'late' for a morning run starting at `now` (ET)."""
    t = now.astimezone(ET).time()
    if t < time(*config.MORNING_EARLIEST):
        return "early"
    if t >= time(*config.MORNING_CUTOFF):
        return "late"
    return "open"


def evening_ready(now: datetime) -> bool:
    return now.astimezone(ET).time() >= time(*config.EVENING_EARLIEST)
