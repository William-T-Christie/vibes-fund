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
    if ticker not in config.LEVERAGED_ALLOWED and is_leveraged_or_inverse(ticker, asset.get("name", "")):
        return f"{ticker} is a leveraged or inverse fund that isn't on the approved list."
    if not asset.get("fractionable"):
        return f"{ticker} cannot be bought in dollar amounts."
    return None


def check_liquidity(ticker: str, dollars: float, liq: dict | None) -> str | None:
    if not liq:
        return f"No trading volume on file for {ticker}."
    if liq["avg_dollar_volume"] < config.MIN_AVG_DOLLAR_VOLUME:
        return f"{ticker} trades ${liq['avg_dollar_volume'] / 1e6:,.1f}M a day, under the ${config.MIN_AVG_DOLLAR_VOLUME / 1e6:,.0f}M floor."
    cap = config.MAX_ORDER_PCT_OF_VOLUME * liq["prior_dollar_volume"]
    if dollars > cap:
        return f"${dollars:,.0f} is more than 1% of a day's trading in {ticker}."
    return None


PRICE_ONLY_RE = re.compile(
    r"\b(share price|stock price|its price|the price|shares)\b[^.]{0,40}\b(fell|fallen|dropped|drop|slid|slumped|"
    r"plunged|tumbled|declined|down|cheap|cheaper|dipped|dip)\b",
    re.I,
)
CONVICTION_RANK = {k: i for i, k in enumerate(config.CONVICTION)}
OPINION_RE = re.compile(
    r"\b(analysts?|upgrade[sd]?|downgrade[sd]?|price targets?|targets? (raised|lifted|cut|to \$)|"
    r"(raises?|raised|lifts?|lifted|cuts?) (its |the |their )?targets?|overweight|underweight|outperform|"
    r"buy rating|ratings?|initiates? coverage|initiated)\b",
    re.I,
)


def size_dollars(conviction: str, nav: float) -> float:
    raw = config.CONVICTION[conviction] * nav
    return float(int(raw // config.SIZE_ROUNDING) * config.SIZE_ROUNDING)


def shrink_to_cash(dollars: float, cash: float) -> float | None:
    """A buy bigger than the cash left shrinks to fit, rounded down, if that is still at least the minimum."""
    if dollars <= cash:
        return dollars
    fit = float(int(cash // config.SIZE_ROUNDING) * config.SIZE_ROUNDING)
    return fit if fit >= config.MIN_ORDER_DOLLARS else None


def _dead_exits(decision: dict, held: dict, trades: list[dict]) -> list[dict]:
    """A Dead verdict always means Exit. If Claude forgot to list the exit, add it from the verdict."""
    selling = {str(t.get("ticker", "")).upper() for t in trades if t.get("action") == "sell"}
    out = []
    for v in decision.get("book", []) or []:
        if not isinstance(v, dict):
            continue
        tk = str(v.get("ticker", "")).upper()
        if v.get("verdict") == "dead" and tk in held and tk not in selling:
            out.append({"action": "sell", "ticker": tk, "kind": "direct", "size": "exit",
                        "reason": str(v.get("note") or "The thesis has died, and the fund attended the funeral."),
                        "headline_id": str(v.get("headline_id", "")), "from_verdict": True})
    return out


def _mood_flip_exits(decision: dict, held: dict, trades: list[dict]) -> list[dict]:
    """A leveraged fund is held only while the mood points its way. When the mood flips, code exits it."""
    score = float((decision.get("mood") or {}).get("score", 0.0))
    selling = {str(t.get("ticker", "")).upper() for t in trades if t.get("action") == "sell"}
    out = []
    for tk in held:
        lev = config.LEVERAGED_ALLOWED.get(tk)
        if not lev or tk in selling:
            continue
        direction = lev[0]
        if (direction == "bull" and score < 0) or (direction == "bear" and score > 0):
            out.append({"action": "sell", "ticker": tk, "kind": "direct", "size": "exit", "catalyst": "event",
                        "reason": "The mood has turned, and leverage does not wait for the Chairman to catch up.",
                        "from_rule": "mood_flip"})
    return out


def slippage_rate(liq: dict | None) -> float:
    if liq and liq.get("avg_dollar_volume", 0) < config.THIN_DOLLAR_VOLUME:
        return config.SLIPPAGE_RESERVE_THIN
    return config.SLIPPAGE_RESERVE


def validate(
    decision: dict,
    *,
    book: dict,
    day_number: int,
    assets: dict[str, dict | None],
    liquidity: dict[str, dict],
    headline_links: dict[str, str],
    paused_names: list[str] | None = None,
    wild_card_used: bool = False,
) -> Result:
    """Check every trade. The holdings minimum counts new names bought in the same run, via a second pass."""
    kw = dict(book=book, day_number=day_number, assets=assets, liquidity=liquidity,
              headline_links=headline_links, paused_names=paused_names, wild_card_used=wild_card_used)
    first = _validate(decision, **kw, new_names_credit=0)
    blocked = [d for d in first.declined if d["reason"].startswith("Selling all of")]
    if not blocked:
        return first
    held = {p["ticker"] for p in book["positions"]}
    credit = sum(1 for t in first.accepted if t["action"] == "buy" and t["ticker"] not in held)
    if not credit:
        return first
    # Exits only add cash and free slots, so every buy accepted in the first pass is accepted again.
    return _validate(decision, **kw, new_names_credit=credit)


def _validate(
    decision: dict,
    *,
    book: dict,
    day_number: int,
    assets: dict[str, dict | None],
    liquidity: dict[str, dict],
    headline_links: dict[str, str],
    paused_names: list[str] | None,
    wild_card_used: bool,
    new_names_credit: int,
) -> Result:
    nav = float(book["nav"])
    cash = float(book["cash"])
    held = {p["ticker"]: dict(p) for p in book["positions"]}
    paused = set(paused_names or [])
    verdict_of = {str(v.get("ticker", "")).upper(): v.get("verdict") for v in decision.get("book", []) or []
                  if isinstance(v, dict)}
    strengthened = {t for t, v in verdict_of.items() if v == "strengthened"}
    res = Result()
    seen: set[tuple[str, str]] = set()
    leaps = 0
    wild_cards = 1 if wild_card_used else 0
    mood = float((decision.get("mood") or {}).get("score", 0.0))

    def decline(trade: dict, why: str) -> None:
        res.declined.append({"trade": trade, "reason": why})

    raw = [t for t in decision.get("trades", []) if isinstance(t, dict)]
    raw += _dead_exits(decision, held, raw)
    raw += _mood_flip_exits(decision, held, raw)
    sells = [t for t in raw if t.get("action") == "sell"]
    # Buys strongest first, so if cash runs short it is the mildest idea that shrinks.
    buys = sorted((t for t in raw if t.get("action") != "sell"),
                  key=lambda t: -CONVICTION_RANK.get(str(t.get("conviction", "")).lower(), -1))

    for t in sells + buys:
        action = str(t.get("action", "")).lower()
        ticker = str(t.get("ticker", "")).upper().strip()
        reason = str(t.get("reason", "")).strip()
        kind = str(t.get("kind", "")).lower()
        hid = str(t.get("headline_id", ""))

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
        if kind not in config.TRADE_KINDS:
            decline(t, f"'{kind}' is not a direct, sector, leap or wild card trade.")
            continue
        if kind == "wild_card" and wild_cards >= config.WILD_CARDS_PER_WEEK:
            decline(t, "The week's wild card has been played. The Chairman is not a casino.")
            continue
        if kind == "leap" and leaps >= config.MAX_LEAPS_PER_DAY:
            decline(t, f"Already {config.MAX_LEAPS_PER_DAY} leaps today. The fund must keep one foot on the ground.")
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
        if PRICE_ONLY_RE.search(reason):
            decline(t, "A falling price is not news. The fund trades on vibes.")
            continue
        rule = t.get("from_rule")
        link = None if rule else headline_links.get(hid)
        if not link and not rule:
            decline(t, f"Cites headline '{hid}', which was not in this morning's news.")
            continue
        if ticker in paused:
            decline(t, f"Trading in {ticker} is paused pending a corporate action.")
            continue

        if action == "sell":
            size = str(t.get("size", "")).lower()
            pos = held.get(ticker)
            if not pos:
                decline(t, f"The fund does not hold {ticker}.")
                continue
            if size not in config.SELL_SIZES:
                decline(t, f"'{size}' is not trim or exit.")
                continue
            turned = verdict_of.get(ticker) in ("weakened", "dead") or bool(t.get("from_verdict")) or bool(rule)
            if size == "trim" and not turned:
                decline(t, f"Trims need a Weakened or Dead verdict on {ticker}. Nothing about it has changed.")
                continue
            if (pos.get("drift_days_left") or 0) > 0 and not turned:
                decline(t, f"{ticker} is in its earnings drift window for {pos['drift_days_left']} more days. "
                           "The fund is patient with good news.")
                continue
            value = float(pos["market_value"])
            close_all = size == "exit"
            dollars = value if close_all else round(value * config.SELL_SIZES["trim"], 2)
            if not close_all and dollars < config.MIN_ORDER_DOLLARS:
                decline(t, f"Half of {ticker} is under the ${config.MIN_ORDER_DOLLARS:,.0f} minimum. Exit or hold.")
                continue
            after = len(held) - 1 + new_names_credit
            if close_all and day_number > config.FIRST_WEEK_DAYS and \
                    after < config.MIN_HOLDINGS and after < len(book["positions"]):
                decline(t, f"Selling all of {ticker} would leave fewer than {config.MIN_HOLDINGS} holdings.")
                continue
            why = check_liquidity(ticker, dollars, liquidity.get(ticker))
            if why:
                decline(t, why)
                continue
            cash += dollars
            if close_all:
                held.pop(ticker)
            else:
                pos["market_value"] = value - dollars
            res.accepted.append({
                "action": "sell", "ticker": ticker, "dollars": round(dollars, 2), "size": size, "kind": kind,
                "conviction": None, "catalyst": str(t.get("catalyst") or "event").lower(), "close_all": close_all, "qty": pos["qty"] if close_all else None,
                "reason": reason, "headline_link": link, "from_verdict": bool(t.get("from_verdict")),
                "from_rule": rule, "slippage_rate": slippage_rate(liquidity.get(ticker)),
            })
        else:
            conviction = str(t.get("conviction", "")).lower()
            if conviction not in config.CONVICTION:
                decline(t, f"'{conviction}' is not mild, firm, strong or total.")
                continue
            if ticker in held and ticker not in strengthened:
                decline(t, f"Adds need a Strengthened verdict on {ticker}. The fund does not top up out of boredom.")
                continue
            catalyst = str(t.get("catalyst") or "event").lower()
            if catalyst not in config.CATALYSTS:
                decline(t, f"'{catalyst}' is not an earnings beat, earnings miss, event or opinion.")
                continue
            if catalyst == "earnings_miss":
                decline(t, "The fund does not buy on an earnings miss. Drift works both ways.")
                continue
            if conviction == "total" and catalyst != "earnings_beat":
                decline(t, "Total conviction is reserved for an earnings beat. Settle for strong.")
                continue
            if catalyst == "opinion" and CONVICTION_RANK[conviction] > CONVICTION_RANK["mild"]:
                decline(t, "An analyst's opinion earns a mild conviction at most. Events outrank opinions.")
                continue
            if CONVICTION_RANK[conviction] > CONVICTION_RANK["mild"] and OPINION_RE.search(reason):
                decline(t, "An analyst's opinion earns a mild conviction at most. Events outrank opinions.")
                continue
            if ticker in held and (catalyst == "opinion" or OPINION_RE.search(reason)):
                decline(t, "An analyst's opinion is never a reason to add.")
                continue
            dollars = size_dollars(conviction, nav)
            if dollars < config.MIN_ORDER_DOLLARS:
                decline(t, f"Under the ${config.MIN_ORDER_DOLLARS:,.0f} minimum.")
                continue
            why = check_asset(ticker, assets.get(ticker))
            if why:
                decline(t, why)
                continue
            lev = config.LEVERAGED_ALLOWED.get(ticker)
            if lev:
                direction, x = lev
                if direction == "bull" and mood < config.LEVERAGED_BULL_MIN_MOOD:
                    decline(t, f"{ticker} is a {x}x bull fund, and a {mood:+.2f} morning is not that good.")
                    continue
                if direction == "bear" and mood > config.LEVERAGED_BEAR_MAX_MOOD:
                    decline(t, f"{ticker} is a {x}x bear fund, and a {mood:+.2f} morning is not that grim.")
                    continue
                if CONVICTION_RANK[conviction] > CONVICTION_RANK[config.LEVERAGED_MAX_CONVICTION]:
                    decline(t, "Leveraged funds top out at a firm conviction. The leverage is the conviction.")
                    continue
                others = [h for h in held if h in config.LEVERAGED_ALLOWED and h != ticker]
                if len(others) >= config.LEVERAGED_MAX_HOLDINGS:
                    decline(t, f"The fund already holds {others[0]}. One leveraged fund at a time.")
                    continue
            if kind == "wild_card" and CONVICTION_RANK[conviction] > CONVICTION_RANK["strong"]:
                decline(t, "A wild card tops out at a strong conviction.")
                continue
            existing = float(held.get(ticker, {}).get("market_value", 0.0))
            if existing + dollars > config.POSITION_CAP * nav + 0.5:
                decline(t, f"{ticker} would be over {int(config.POSITION_CAP * 100)}% of the fund.")
                continue
            names = [h for h in held if h not in config.LEVERAGED_ALLOWED]  # a leveraged fund is a market bet, not a name
            if ticker not in held and not lev and len(names) + 1 > config.MAX_HOLDINGS:
                decline(t, f"A new name would take the fund past {config.MAX_HOLDINGS} holdings. Exit something first.")
                continue
            fit = shrink_to_cash(dollars, cash)
            if fit is None:
                decline(t, f"Only ${cash:,.0f} left in cash. The fund does not borrow.")
                continue
            why = check_liquidity(ticker, fit, liquidity.get(ticker))
            if why:
                decline(t, why)
                continue
            cash -= fit
            if ticker in held:
                held[ticker]["market_value"] = existing + fit
            else:
                held[ticker] = {"ticker": ticker, "market_value": fit, "qty": None}
            res.accepted.append({
                "action": "buy", "ticker": ticker, "dollars": fit, "size": None, "kind": kind,
                "conviction": conviction, "catalyst": catalyst, "shrunk": fit < dollars, "close_all": False, "qty": None,
                "reason": reason, "headline_link": link, "from_verdict": False, "from_rule": None,
                "leveraged": bool(lev), "slippage_rate": slippage_rate(liquidity.get(ticker)),
            })
        if kind == "leap":
            leaps += 1
        if kind == "wild_card":
            wild_cards += 1
        seen.add((ticker, action))

    res.cash_after = cash
    res.holdings_after = len(held)
    res.defensive = nav > 0 and cash / nav > config.MAX_CASH_NORMAL
    return res


def cash_target(mood_score: float | None, day_number: int) -> float | None:
    """Most cash the mood allows, or None during the first week or without a mood."""
    if mood_score is None or day_number <= config.FIRST_WEEK_DAYS:
        return None
    return config.MOOD_CASH_CEILING[config.mood_band(mood_score)[0]]


def recent_sale_cash(trades: list[dict], session_dates: list[str], day: str,
                     days: int = config.RECENT_SALE_DAYS) -> float:
    """Proceeds of sells filled in the last `days` trading sessions, today included.

    That cash doesn't count against the mood's cash limit, so a trim never forces a same-day rebuy.
    """
    past = sorted(d for d in set(session_dates) | {day} if d <= day)[-days:]
    if not past:
        return 0.0
    return sum(float(t.get("dollars") or 0) for t in trades
               if t.get("action") == "sell" and t.get("status") in ("filled", "partially_filled")
               and t.get("date") in past)


def cash_check(cash: float, nav: float, recent_sales: float, mood_score: float | None, day_number: int) -> dict | None:
    """Compare cash, net of recent sale proceeds, with the mood's limit."""
    target = cash_target(mood_score, day_number)
    if target is None or not nav:
        return None
    counted = max(0.0, cash - recent_sales) / nav
    return {"cash_pct": round(100 * cash / nav, 1), "counted_cash_pct": round(100 * counted, 1),
            "target_pct": round(100 * target, 1), "on_target": counted <= target + 0.005}


def wild_card_used_this_week(trades: list[dict], day: str) -> bool:
    """Whether a wild card already filled in the same Monday-to-Friday week as `day`."""
    from datetime import date as _d
    wk = _d.fromisoformat(day).isocalendar()[:2]
    return any(t.get("kind") == "wild_card" and t.get("status") in ("filled", "partially_filled")
               and _d.fromisoformat(t["date"]).isocalendar()[:2] == wk for t in trades)


def slippage_charge(records: list[dict]) -> float:
    """The reserve for today's fills: each trade's own rate times what actually filled."""
    return sum(float(r.get("filled_dollars") or 0) * float(r.get("slippage_rate") or config.SLIPPAGE_RESERVE)
               for r in records if r.get("filled_qty"))


def declined_leverage(mood_score: float, positions: list[dict], accepted: list[dict]) -> str | None:
    """On an extreme morning, the direction the Chairman should have bet but didn't, else None."""
    if mood_score >= config.LEVERAGED_BULL_MIN_MOOD:
        want = "bull"
    elif mood_score <= config.LEVERAGED_BEAR_MAX_MOOD:
        want = "bear"
    else:
        return None
    sold = {t["ticker"] for t in accepted if t["action"] == "sell" and t.get("close_all")}
    held = [p["ticker"] for p in positions if p["ticker"] not in sold] + \
           [t["ticker"] for t in accepted if t["action"] == "buy"]
    if any(config.LEVERAGED_ALLOWED.get(t, ("",))[0] == want for t in held):
        return None
    return want
