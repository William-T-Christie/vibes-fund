"""The evening record. Pure code, no Claude, so a Claude outage never breaks the chart.

Marks the book at the close, credits dividends, tracks SPY on a total-return basis, backfills any
missed days, and writes nav.json, holdings.json, trades.json and summary.json.

Adjusted NAV = Alpaca paper equity + dividends credited - slippage reserve.
SPY's index starts at 100 at the inception-day open (the fund deploys at 9:40) and reinvests dividends.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

from . import clock, config, metrics, store
from .alpaca import Alpaca


def _first_buy_dates(trades: list[dict]) -> dict[str, str]:
    """Date the current position in each name was opened (resets after a full close)."""
    held: dict[str, float] = {}
    opened: dict[str, str] = {}
    for t in metrics.fills(trades):
        q = float(t["qty"])
        if t["action"] == "buy":
            if held.get(t["ticker"], 0) <= 1e-9:
                opened[t["ticker"]] = t["date"]
            held[t["ticker"]] = held.get(t["ticker"], 0) + q
        else:
            held[t["ticker"]] = held.get(t["ticker"], 0) - q
    return {k: opened[k] for k, v in held.items() if v > 1e-9 and k in opened}


def credit_dividends(state: dict, divs: list[dict], positions: list[dict], opened: dict[str, str], day: str) -> float:
    """Credit each cash dividend on a holding once, on its ex-date, if the name was held before it."""
    credited = {(d["ticker"], d["ex_date"]) for d in state.setdefault("dividends_credited", [])}
    qty = {p["symbol"]: float(p["qty"]) for p in positions}
    total = 0.0
    for d in divs:
        sym, ex = d["symbol"], d["ex_date"]
        if ex != day or sym not in qty or (sym, ex) in credited:
            continue
        if not opened.get(sym) or opened[sym] >= ex:
            continue  # bought on or after the ex-date: not entitled
        amt = round(float(d["rate"]) * qty[sym], 2)
        state["dividends_credited"].append({"ticker": sym, "ex_date": ex, "rate": float(d["rate"]),
                                            "qty": qty[sym], "amount": amt})
        total += amt
    state["dividends_credited_total"] = round(state.get("dividends_credited_total", 0.0) + total, 2)
    return total


def spy_index_series(bars: list[dict], spy_divs: list[dict], inception: str) -> dict[str, dict]:
    """Total-return index for SPY: 100 at the inception-day open, dividends reinvested on ex-dates."""
    div_by_day = {d["ex_date"]: float(d["rate"]) for d in spy_divs}
    out: dict[str, dict] = {}
    idx, prev_close = None, None
    for b in bars:
        d = b["t"][:10]
        if d < inception:
            continue
        if idx is None:
            idx = 100 * b["c"] / b["o"]
        else:
            idx *= (b["c"] + div_by_day.get(d, 0.0)) / prev_close
        prev_close = b["c"]
        out[d] = {"spy_close": b["c"], "spy_index": idx}
    return out


def _equity_history(client: Alpaca) -> dict[str, float]:
    h = client.portfolio_history("3M")
    out = {}
    for ts, eq in zip(h.get("timestamp") or [], h.get("equity") or []):
        if eq is None:
            continue
        out[datetime.fromtimestamp(ts, tz=timezone.utc).astimezone(clock.ET).date().isoformat()] = float(eq)
    return out


def detect_unexplained_changes(prev_holdings: list[dict], positions: list[dict], trades_today: list[dict]) -> list[str]:
    """Names that appeared or vanished without a trade: acquisitions, renames, delistings."""
    before = {h["ticker"] for h in prev_holdings}
    now = {p["symbol"] for p in positions}
    traded = {t["ticker"] for t in trades_today if t.get("qty")}
    return sorted((before ^ now) - traded)


def run(client: Alpaca, now: datetime | None = None) -> dict:
    now = now or clock.now_et()
    day = clock.today_et(now)
    if not clock.evening_ready(now):
        return {"status": "early", "message": "Market still open. Come back after the close."}

    state = store.fund_state()
    inception = state.get("inception")
    if not inception:
        return {"status": "not_incepted", "message": "No trades yet, so no fund to record."}

    cal = client.calendar(inception, day)
    sessions = [c["date"] for c in cal]
    nav = store.read("nav.json", {"rows": []})
    have = {r["date"] for r in nav["rows"]}
    missing = [d for d in sessions if d not in have]
    if not missing:
        return {"status": "up_to_date"}

    positions = client.positions()
    trades_doc = store.read("trades.json", {"trades": []})
    trades = trades_doc["trades"]
    opened = _first_buy_dates(trades)

    # Benchmark: SPY daily bars and dividends since inception.
    bars = client.daily_bars([config.BENCHMARK], start=inception, end=day)[config.BENCHMARK]
    spy_divs = client.cash_dividends([config.BENCHMARK], inception, day)
    spy = spy_index_series(bars, spy_divs, inception)

    held_syms = sorted({p["symbol"] for p in positions})
    divs = client.cash_dividends(held_syms, missing[0], day) if held_syms else []
    history = _equity_history(client) if any(d != day for d in missing) else {}
    acct = client.account()

    moods = {}
    for d in missing:
        log = store.read_log(d, "decision.json") or {}
        if log.get("decision"):
            moods[d] = (log["decision"]["mood"]["score"], log.get("mood_band"))

    written = []
    for d in missing:
        if d not in spy:
            continue  # SPY bar not published yet; tomorrow's run backfills
        equity = float(acct["equity"]) if d == day else history.get(d)
        if equity is None:
            continue
        credit_dividends(state, divs, positions, opened, d)
        adj = equity + state["dividends_credited_total"] - state.get("slippage_reserve_total", 0.0)
        score, band = moods.get(d, (None, None))
        nav["rows"].append({
            "date": d,
            "raw_equity": round(equity, 2),
            "dividends_credited_total": state["dividends_credited_total"],
            "slippage_reserve_total": round(state.get("slippage_reserve_total", 0.0), 2),
            "nav": round(adj, 2),
            "fund_index": round(100 * adj / config.STARTING_CAPITAL, 4),
            "spy_close": spy[d]["spy_close"],
            "spy_index": round(spy[d]["spy_index"], 4),
            "mood_score": score,
            "mood_band": band,
            "backfilled": d != day,
        })
        written.append(d)
    nav["rows"].sort(key=lambda r: r["date"])
    nav["as_of"] = now.isoformat()

    # Corporate actions we can't explain pause trading in that name.
    prev_holdings = store.read("holdings.json", {"holdings": []})["holdings"]
    odd = detect_unexplained_changes(prev_holdings, positions, [t for t in trades if t["date"] == day])
    if odd:
        state["paused_names"] = sorted(set(state.get("paused_names", [])) | set(odd))
        store.write_log(day, "corporate_actions.json", {"unexplained": odd})

    closes = {p["symbol"]: float(p["current_price"]) for p in positions}
    closes.update({config.BENCHMARK: bars[-1]["c"]} if bars else {})
    missing_closes = sorted({t["ticker"] for t in trades if t["ticker"] not in closes and t.get("qty")})
    if missing_closes:
        start = (date.fromisoformat(day) - timedelta(days=7)).isoformat()
        for sym, bs in client.daily_bars(missing_closes, start=start, end=day).items():
            if bs:
                closes[sym] = bs[-1]["c"]
    metrics.update_outcomes(trades, closes)

    reasons = {}
    for t in metrics.fills(trades):
        if t["action"] == "buy":
            reasons[t["ticker"]] = t["reason"]
    nav_now = nav["rows"][-1]["nav"] if nav["rows"] else float(acct["equity"])
    holdings = []
    for p in sorted(positions, key=lambda p: -float(p["market_value"])):
        mv, cost = float(p["market_value"]), float(p["cost_basis"])
        holdings.append({
            "ticker": p["symbol"],
            "shares": float(p["qty"]),
            "market_value": round(mv, 2),
            "weight_pct": round(100 * mv / nav_now, 2) if nav_now else None,
            "cost": round(cost, 2),
            "gain_pct": round(100 * (mv - cost) / cost, 2) if cost else None,
            "date_bought": opened.get(p["symbol"]),
            "buy_reason": reasons.get(p["symbol"]),
        })

    store.write("nav.json", nav)
    store.write("holdings.json", {"as_of": now.isoformat(), "cash": round(float(acct["cash"]), 2), "holdings": holdings})
    store.write("trades.json", trades_doc)
    summary = metrics.summarize(nav["rows"], trades, holdings, as_of=now.isoformat())
    old = store.read("summary.json", {})
    summary["mood"] = old.get("mood")
    summary["mode"] = state.get("mode", "dry_run")
    summary["fund_name"] = config.FUND_NAME
    summary["last_updated"] = now.isoformat()
    store.write("summary.json", summary)
    store.save_fund_state(state)
    return {"status": "recorded", "days": written, "unexplained": odd}
