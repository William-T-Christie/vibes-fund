"""The morning trade, split into three steps so each secret reaches only the step that needs it.

1. prepare  (Alpaca keys)  gate, read the news, load the book       -> .work/morning.json
2. decide   (Claude token) ask the Chairman, write the decision      -> logs/DATE/decision.json, committed
3. trade    (Alpaca keys)  validate, place orders, record the fills  -> trades.json, committed
"""

from __future__ import annotations

from datetime import datetime, time, timedelta, timezone

from . import clock, config, decide as decide_mod, fetch_news, store, trade as trade_mod, validate as validate_mod
from .alpaca import Alpaca

QUIET = {
    "early": "Too early. The market is not open yet.",
    "closed": "Market closed today. The fund rests.",
    "late": "The manager overslept.",
    "done": "Today's decision is already on file.",
    "paused": "Trading paused by the PAUSED file.",
    "already_traded": "Alpaca already shows orders from today.",
    "no_news": "Quiet morning. The fund meditated.",
    "claude_failed": "Manager out of office.",
}


def _stop(day: str, code: str, extra: dict | None = None) -> dict:
    out = {"date": day, "proceed": False, "status": code, "message": QUIET[code], **(extra or {})}
    store.write_work("morning.json", out)
    return out


def trading_day_number(day: str, nav_rows: list[dict], inception: str | None) -> int:
    """1 on inception day; otherwise one more than the number of recorded days on or after inception."""
    if not inception:
        return 1
    return 1 + sum(1 for r in nav_rows if inception <= r["date"] < day)


def book_from_alpaca(client: Alpaca) -> dict:
    acct = client.account()
    positions = []
    for p in client.positions():
        cost = float(p["cost_basis"])
        mv = float(p["market_value"])
        positions.append({
            "ticker": p["symbol"],
            "qty": p["qty"],
            "market_value": mv,
            "cost_basis": cost,
            "current_price": float(p["current_price"]),
            "gain_pct": 100 * (mv - cost) / cost if cost else 0.0,
        })
    nav = float(acct["equity"])
    return {"nav": nav, "cash": float(acct["cash"]), "positions": positions}


def prepare(client: Alpaca, now: datetime | None = None) -> dict:
    now = now or clock.now_et()
    day = clock.today_et(now)

    window = clock.morning_window(now)
    if window == "early":
        return _stop(day, "early")
    if store.read_log(day, "decision.json") is not None:
        return _stop(day, "done")

    c = client.clock()
    if not c.get("is_open"):
        return _stop(day, "closed")
    if config.PAUSED_FILE.exists():
        _log_hold(day, "paused")
        return _stop(day, "paused")
    if window == "late":
        _log_hold(day, "late", started=now.isoformat())
        return _stop(day, "late")

    open_et = datetime.combine(now.date(), time(0, 0), tzinfo=clock.ET)
    todays = [o for o in client.orders_since(open_et.astimezone(timezone.utc).isoformat())
              if (o.get("client_order_id") or "").startswith(f"vibes-{day}-")]
    if todays:
        return _stop(day, "already_traded")

    # Headlines from the prior session's close up to the moment this run started.
    prev = client.calendar((now.date() - timedelta(days=10)).isoformat(), (now.date() - timedelta(days=1)).isoformat())
    prev_close = (
        datetime.fromisoformat(f"{prev[-1]['date']}T{prev[-1]['close']}").replace(tzinfo=clock.ET)
        if prev else now - timedelta(hours=18)
    )
    headlines = fetch_news.fetch(client, prev_close.astimezone(timezone.utc), now.astimezone(timezone.utc))
    if not headlines:
        _log_hold(day, "no_news")
        return _stop(day, "no_news")

    state = store.fund_state()
    nav_rows = store.read("nav.json", {"rows": []})["rows"]
    trades = store.read("trades.json", {"trades": []})["trades"]
    out = {
        "date": day,
        "proceed": True,
        "started_at": now.isoformat(),
        "day_number": trading_day_number(day, nav_rows, state.get("inception")),
        "book": book_from_alpaca(client),
        "headlines": headlines,
        "recent_reasons": [t["reason"] for t in trades[-5:]],
    }
    store.write_work("morning.json", out)
    store.write_log(day, "headlines.json", {"window_start": prev_close.isoformat(), "window_end": now.isoformat(),
                                            "items": fetch_news.public_log(headlines)})
    return out


def _log_hold(day: str, code: str, **extra) -> None:
    store.write_log(day, "decision.json", {"date": day, "status": code, "message": QUIET[code],
                                           "decision": None, **extra})


def decide(caller=decide_mod.call_claude) -> dict:
    work = store.read_work("morning.json")
    if not work.get("proceed"):
        return work
    day = work["date"]
    prompt = decide_mod.build_prompt(date=day, day_number=work["day_number"], book=work["book"],
                                     headlines=work["headlines"], recent_reasons=work["recent_reasons"])
    decision, attempts = decide_mod.decide(prompt, caller)
    store.write_log(day, "claude_raw.json", {"prompt_version": decide_mod.prompt_version(),
                                             "model": config.CLAUDE_MODEL, "attempts": attempts})
    if decision is None:
        _log_hold(day, "claude_failed")
        work.update(proceed=False, status="claude_failed", message=QUIET["claude_failed"])
        store.write_work("morning.json", work)
        return work
    label, ink = config.mood_band(decision["mood"]["score"])
    record = {
        "date": day,
        "status": "decided",
        "prompt_version": decide_mod.prompt_version(),
        "model": config.CLAUDE_MODEL,
        "day_number": work["day_number"],
        "decision": decision,
        "mood_band": label,
        "mood_ink": ink,
    }
    store.write_log(day, "decision.json", record)
    _update_summary_mood(day, decision, label, ink)
    work["decision"] = decision
    store.write_work("morning.json", work)
    return work


def _update_summary_mood(day: str, decision: dict, band: str, ink: str) -> None:
    summary = store.read("summary.json", {})
    summary["mood"] = {"date": day, "label": decision["mood"].get("label", ""), "score": decision["mood"]["score"],
                       "band": band, "ink": ink, "summary": decision.get("summary", "")}
    store.write("summary.json", summary)


def run_trades(client: Alpaca, *, sleep=None) -> dict:
    work = store.read_work("morning.json")
    if not work.get("proceed") or "decision" not in work:
        return work
    day = work["date"]
    decision = work["decision"]
    if config.PAUSED_FILE.exists():
        return {"status": "paused"}
    if store.read_log(day, "orders.json") is not None:
        return {"status": "already_traded", "message": QUIET["already_traded"]}

    tickers = sorted({str(t.get("ticker", "")).upper() for t in decision["trades"] if isinstance(t, dict)} - {""})
    assets = {t: client.asset(t) for t in tickers if validate_mod.TICKER_RE.match(t)}
    liq = trade_mod.liquidity(client, [t for t in tickers if assets.get(t)], day)
    links = {h["id"]: h["link"] for h in work["headlines"]}
    state = store.fund_state()
    result = validate_mod.validate(decision, book=work["book"], day_number=work["day_number"], assets=assets,
                                   liquidity=liq, headline_links=links, paused_names=state.get("paused_names"))
    store.write_log(day, "validation.json", result.to_json())

    kw = {"sleep": sleep} if sleep else {}
    records = trade_mod.execute(client, day, result.accepted, **kw) if result.accepted else []
    store.write_log(day, "orders.json", records)

    trades = store.read("trades.json", {"trades": []})
    for r in records:
        trades["trades"].append({
            "date": day,
            "action": r["action"],
            "ticker": r["ticker"],
            "dollars": r.get("filled_dollars", 0.0),
            "fill_price": r.get("fill_price"),
            "qty": r.get("filled_qty", 0.0),
            "status": r["status"],
            "reason": r["reason"],
            "link": r["headline_link"],
            "outcome_pct": None,
        })
    for d in result.declined:
        t = d["trade"]
        trades["trades"].append({
            "date": day, "action": str(t.get("action", "")).lower(), "ticker": str(t.get("ticker", "")).upper(),
            "dollars": 0.0, "fill_price": None, "qty": 0.0, "status": "declined",
            "reason": str(t.get("reason", "")), "link": links.get(str(t.get("headline_id", ""))),
            "compliance": d["reason"], "outcome_pct": None,
        })
    store.write("trades.json", trades)

    filled_notional = sum(r.get("filled_dollars", 0.0) for r in records if r.get("filled_qty"))
    if filled_notional:
        state["slippage_reserve_total"] = round(
            state.get("slippage_reserve_total", 0.0) + config.SLIPPAGE_RESERVE * filled_notional, 2)
        if not state.get("inception"):
            state["inception"] = day
    store.save_fund_state(state)
    return {"status": "traded", "accepted": len(result.accepted), "declined": len(result.declined),
            "filled": sum(1 for r in records if r.get("filled_qty"))}
