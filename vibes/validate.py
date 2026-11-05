"""Compliance. Every trade passes these checks before any order is sent.

Pure functions over plain data, so the whole rulebook is tested on fixtures. A failed check drops
that trade and records why; nothing is ever fixed by guessing.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from . import config

TICKER_RE = re.compile(r"^[A-Z]{1,5}(\.[A-Z])?$")


@dataclass
class Result:
    accepted: list[dict] = field(default_factory=list)
    declined: list[dict] = field(default_factory=list)
    cash_after: float = 0.0
    holdings_after: int = 0
    defensive: bool = False

    def to_json(self) -> dict:
        return {
            "accepted": self.accepted,
            "declined": self.declined,
            "cash_after_estimate": round(self.cash_after, 2),
            "holdings_after": self.holdings_after,
            "defensive": self.defensive,
        }


def _one_sentence(text: str) -> bool:
    # Sentence breaks: terminal punctuation followed by a space and a capital letter.
    return len(re.findall(r"[.!?]\s+[A-Z\"']", text.strip())) == 0


def is_leveraged_or_inverse(ticker: str, name: str) -> bool:
    if ticker in config.BANNED_TICKERS:
        return True
    n = (name or "").lower()
    return any(m in n for m in config.LEVERAGED_NAME_MARKERS)


def check_asset(ticker: str, asset: dict | None) -> str | None:
    if asset is None:
        return f"{ticker} is not on the asset list. Compliance cannot buy a feeling."
    if asset.get("status") != "active" or not asset.get("tradable"):
        return f"{ticker} is not active and tradable."
    if asset.get("class") != "us_equity":
        return f"{ticker} is not a US stock or ETF."
    if asset.get("exchange") not in config.ALLOWED_EXCHANGES:
        return f"{ticker} trades on {asset.get('exchange')}, not a listed exchange."
    if is_leveraged_or_inverse(ticker, asset.get("name", "")):
        return f"{ticker} is leveraged or inverse. The fund has enough leverage in its convictions."
    if not asset.get("fractionable"):
        return f"{ticker} cannot be bought in dollar amounts."
    return None


def check_liquidity(ticker: str, dollars: float, liq: dict | None) -> str | None:
    if not liq:
        return f"No trading volume on file for {ticker}."
    if liq["avg_dollar_volume"] < config.MIN_AVG_DOLLAR_VOLUME:
        return f"{ticker} trades ${liq['avg_dollar_volume'] / 1e6:,.1f}M a day, under the $50M floor."
    cap = config.MAX_ORDER_PCT_OF_VOLUME * liq["prior_dollar_volume"]
    if dollars > cap:
        return f"${dollars:,.0f} is more than 1% of a day's trading in {ticker}."
    return None


def validate(
    decision: dict,
    *,
    book: dict,
    day_number: int,
    assets: dict[str, dict | None],
    liquidity: dict[str, dict],
    headline_links: dict[str, str],
    paused_names: list[str] | None = None,
) -> Result:
    nav = float(book["nav"])
    cash = float(book["cash"])
    held = {p["ticker"]: dict(p) for p in book["positions"]}
    paused = set(paused_names or [])
    res = Result()
    seen: set[tuple[str, str]] = set()

    def decline(trade: dict, why: str) -> None:
        res.declined.append({"trade": trade, "reason": why})

    raw = [t for t in decision.get("trades", []) if isinstance(t, dict)]
    # Sells first so their proceeds can fund the buys in the same run.
    ordered = [t for t in raw if t.get("action") == "sell"] + [t for t in raw if t.get("action") != "sell"]

    for t in ordered:
        action = str(t.get("action", "")).lower()
        ticker = str(t.get("ticker", "")).upper().strip()
        reason = str(t.get("reason", "")).strip()
        hid = str(t.get("headline_id", ""))
        try:
            dollars = float(round(float(t.get("dollars", 0))))
        except (TypeError, ValueError):
            dollars = 0.0

        if len(res.accepted) >= config.MAX_TRADES_PER_DAY:
            decline(t, f"Trade limit of {config.MAX_TRADES_PER_DAY} a day reached.")
            continue
        if action not in ("buy", "sell"):
            decline(t, f"'{action}' is not buy or sell.")
            continue
        if not TICKER_RE.match(ticker):
            decline(t, f"'{ticker}' is not shaped like a ticker.")
            continue
        if (ticker, action) in seen:
            decline(t, f"Already {action}ing {ticker} today.")
            continue
        if not reason:
            decline(t, "No reason given. Compliance requires at least a feeling.")
            continue
        if len(reason) > config.MAX_REASON_CHARS:
            decline(t, f"Reason runs past {config.MAX_REASON_CHARS} characters.")
            continue
        if not _one_sentence(reason):
            decline(t, "Reason is more than one sentence.")
            continue
        link = headline_links.get(hid)
        if not link:
            decline(t, f"Cites headline '{hid}', which was not in this morning's news.")
            continue
        if ticker in paused:
            decline(t, f"Trading in {ticker} is paused pending a corporate action.")
            continue

        if action == "sell":
            pos = held.get(ticker)
            if not pos:
                decline(t, f"The fund does not hold {ticker}.")
                continue
            value = float(pos["market_value"])
            if dollars > value + 0.5:
                decline(t, f"Sell of ${dollars:,.0f} is more than the ${value:,.0f} held.")
                continue
            close_all = dollars >= config.FULL_CLOSE_THRESHOLD * value
            if dollars < config.MIN_ORDER_DOLLARS and not close_all:
                decline(t, f"Under the ${config.MIN_ORDER_DOLLARS:,.0f} minimum.")
                continue
            if close_all and day_number > config.FIRST_WEEK_DAYS and len(held) - 1 < config.MIN_HOLDINGS:
                decline(t, f"Selling all of {ticker} would leave fewer than {config.MIN_HOLDINGS} holdings.")
                continue
            why = check_liquidity(ticker, dollars, liquidity.get(ticker))
            if why:
                decline(t, why)
                continue
            proceeds = value if close_all else dollars
            cash += proceeds
            if close_all:
                held.pop(ticker)
            else:
                pos["market_value"] = value - dollars
            res.accepted.append({
                "action": "sell", "ticker": ticker, "dollars": round(proceeds, 2),
                "close_all": close_all, "qty": pos["qty"] if close_all else None,
                "reason": reason, "headline_link": link,
            })
        else:
            if dollars < config.MIN_ORDER_DOLLARS:
                decline(t, f"Under the ${config.MIN_ORDER_DOLLARS:,.0f} minimum.")
                continue
            why = check_asset(ticker, assets.get(ticker))
            if why:
                decline(t, why)
                continue
            why = check_liquidity(ticker, dollars, liquidity.get(ticker))
            if why:
                decline(t, why)
                continue
            if dollars > cash:
                decline(t, f"${dollars:,.0f} is more than the ${cash:,.0f} in cash. The fund does not borrow.")
                continue
            existing = float(held.get(ticker, {}).get("market_value", 0.0))
            if existing + dollars > config.POSITION_CAP * nav + 0.5:
                decline(t, f"{ticker} would be over {int(config.POSITION_CAP * 100)}% of the fund.")
                continue
            if ticker not in held and len(held) + 1 > config.MAX_HOLDINGS:
                decline(t, f"A new name would take the fund past {config.MAX_HOLDINGS} holdings.")
                continue
            cash -= dollars
            if ticker in held:
                held[ticker]["market_value"] = existing + dollars
            else:
                held[ticker] = {"ticker": ticker, "market_value": dollars, "qty": None}
            res.accepted.append({
                "action": "buy", "ticker": ticker, "dollars": dollars,
                "close_all": False, "qty": None, "reason": reason, "headline_link": link,
            })
        seen.add((ticker, action))

    res.cash_after = cash
    res.holdings_after = len(held)
    res.defensive = nav > 0 and cash / nav > config.MAX_CASH_NORMAL
    return res
