"""Every number the site shows. Pure functions over the NAV rows and the trade list, so the frontend only displays."""

from __future__ import annotations

import math
from datetime import date, timedelta

from . import config


def daily_returns(values: list[float]) -> list[float]:
    return [b / a - 1 for a, b in zip(values, values[1:]) if a]


def volatility(values: list[float]) -> float | None:
    """Annualized standard deviation of daily returns, once there are 20 trading days of returns."""
    r = daily_returns(values)
    if len(r) < 20:
        return None
    m = sum(r) / len(r)
    var = sum((x - m) ** 2 for x in r) / (len(r) - 1)
    return math.sqrt(var) * math.sqrt(252)


def max_drawdown(values: list[float]) -> float:
    peak, worst = -math.inf, 0.0
    for v in values:
        peak = max(peak, v)
        if peak > 0:
            worst = min(worst, v / peak - 1)
    return worst


def correlation(xs: list[float], ys: list[float]) -> float | None:
    n = len(xs)
    if n < 3:
        return None
    mx, my = sum(xs) / n, sum(ys) / n
    sx = math.sqrt(sum((x - mx) ** 2 for x in xs))
    sy = math.sqrt(sum((y - my) ** 2 for y in ys))
    if not sx or not sy:
        return None
    return sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / (sx * sy)


def fills(trades: list[dict]) -> list[dict]:
    return [t for t in trades if t.get("status") in ("filled", "partially_filled") and t.get("qty")]


def closed_trade_results(trades: list[dict]) -> list[float]:
    """Percent result of each sell against the position's average cost at the time."""
    lots: dict[str, list[float]] = {}  # ticker -> [qty, cost]
    out = []
    for t in fills(trades):
        q, px = float(t["qty"]), float(t["fill_price"])
        lot = lots.setdefault(t["ticker"], [0.0, 0.0])
        if t["action"] == "buy":
            lot[0] += q
            lot[1] += q * px
        elif lot[0] > 0:
            avg = lot[1] / lot[0]
            out.append(px / avg - 1)
            sold = min(q, lot[0])
            lot[1] -= avg * sold
            lot[0] -= sold
    return out


def update_outcomes(trades: list[dict], closes: dict[str, float]) -> None:
    """Outcome so far of each call: buys gain when the stock rises after; sells gain when it falls after."""
    for t in trades:
        c = closes.get(t["ticker"])
        if t.get("status") not in ("filled", "partially_filled") or not t.get("fill_price") or not c:
            continue
        px = float(t["fill_price"])
        t["outcome_pct"] = round(100 * ((c / px - 1) if t["action"] == "buy" else (px / c - 1)), 2)


def turnover(trades: list[dict], rows: list[dict], as_of: str, days: int = 30) -> float | None:
    start = (date.fromisoformat(as_of[:10]) - timedelta(days=days)).isoformat()
    window = [r["nav"] for r in rows if r["date"] > start]
    if not window:
        return None
    traded = sum(float(t["dollars"]) for t in fills(trades) if t["date"] > start)
    return traded / (sum(window) / len(window))


def summarize(rows: list[dict], trades: list[dict], holdings: list[dict], *, as_of: str) -> dict:
    """Build summary.json from nav rows (oldest first), the trade list and current holdings."""
    if not rows:
        return {"as_of": as_of, "status": "no_data"}
    last = rows[-1]
    navs = [r["nav"] for r in rows]
    fund_idx = [r["fund_index"] for r in rows]
    spy_idx = [r["spy_index"] for r in rows]

    fund_ret = navs[-1] / config.STARTING_CAPITAL - 1
    spy_ret = spy_idx[-1] / 100 - 1
    prev = rows[-2] if len(rows) > 1 else None
    today_fund = (last["nav"] / prev["nav"] - 1) if prev else fund_ret
    today_spy = (last["spy_index"] / prev["spy_index"] - 1) if prev else spy_ret
    days_ahead = sum(1 for f, s in zip(fund_idx, spy_idx) if f > s)

    closed = closed_trade_results(trades)
    called = [t for t in trades if t.get("outcome_pct") is not None]
    best = max(called, key=lambda t: t["outcome_pct"], default=None)
    worst = min(called, key=lambda t: t["outcome_pct"], default=None)
    longest = min(holdings, key=lambda h: h.get("date_bought") or "9999", default=None)

    mood_rows = [r for r in rows if r.get("mood_score") is not None]
    mood_corr = None
    if len(rows) >= 31:
        pairs = []
        for a, b in zip(rows, rows[1:]):
            if a.get("mood_score") is not None and a["nav"]:
                pairs.append((a["mood_score"], b["nav"] / a["nav"] - 1))
        if len(pairs) >= 30:
            mood_corr = correlation([p[0] for p in pairs], [p[1] for p in pairs])

    def pct(x):
        return None if x is None else round(100 * x, 2)

    def trade_ref(t):
        return None if not t else {"date": t["date"], "action": t["action"], "ticker": t["ticker"],
                                   "outcome_pct": t["outcome_pct"]}

    return {
        "as_of": as_of,
        "inception": rows[0]["date"],
        "trading_days": len(rows),
        "nav": round(last["nav"], 2),
        "raw_equity": round(last["raw_equity"], 2),
        "dividends_credited_total": round(last["dividends_credited_total"], 2),
        "slippage_reserve_total": round(last["slippage_reserve_total"], 2),
        "return_since_inception_pct": pct(fund_ret),
        "spy_return_since_inception_pct": pct(spy_ret),
        "gap_vs_spy_points": round(100 * (fund_ret - spy_ret), 2),
        "today": {"fund_pct": pct(today_fund), "spy_pct": pct(today_spy)},
        "beating_spy": "Yes" if fund_ret > spy_ret else "Not yet",
        "days_ahead": days_ahead,
        "share_of_days_ahead_pct": round(100 * days_ahead / len(rows), 1),
        "volatility_pct": pct(volatility(navs)),
        "spy_volatility_pct": pct(volatility(spy_idx)),
        "max_drawdown_pct": pct(max_drawdown(navs)),
        "peak": max(({"date": r["date"], "nav": round(r["nav"], 2)} for r in rows), key=lambda x: x["nav"]),
        "win_rate_pct": pct(sum(1 for c in closed if c > 0) / len(closed)) if closed else None,
        "closed_trades": len(closed),
        "trades_filled": len(fills(trades)),
        "declined_by_compliance": sum(1 for t in trades if t.get("status") == "declined"),
        "best_trade": trade_ref(best),
        "worst_trade": trade_ref(worst),
        "longest_held": None if not longest else {"ticker": longest["ticker"], "since": longest["date_bought"]},
        "turnover_30d": None if (to := turnover(trades, rows, as_of)) is None else round(to, 3),
        "mood_vs_next_day_return": None if mood_corr is None else round(mood_corr, 3),
        "mood_days": len(mood_rows),
    }
