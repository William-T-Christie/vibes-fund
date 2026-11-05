"""Private replay of past trading days through the current playbook.

Each simulated morning sees only headlines published before 9:40 ET that day. Claude decides with the
real prompt, real Compliance checks it, fills use that morning's real 9:40 prices plus the slippage
reserve, and the book carries forward. Everything is written to .replays/<name>/ (gitignored).

This is a behavior check, not a track record:
- Claude may already know how some of these days turned out if they fall inside its training data.
- One run is one sample; run it a few times to see the spread.
- Only Alpaca's market news has history, so the general world news the live fund reads is missing.
Never publish these results or put them in data/vibes/, and only change the prompt to fix behavior,
never to raise the replayed return.
"""

from __future__ import annotations

import itertools
import json
import re
import uuid
from collections import Counter
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from typing import Callable

from . import clock, config, decide as decide_mod, fetch_news, metrics, morning, record, trade as trade_mod
from . import validate as validate_mod



def replays_dir() -> Path:
    return config.ROOT / ".replays"


class SimBroker:
    """The paper account, simulated: market orders fill instantly at the price set for the moment."""

    def __init__(self, cash: float = config.STARTING_CAPITAL, qty=None, cost=None):
        self.cash = cash
        self.qty: dict[str, float] = dict(qty or {})
        self.cost: dict[str, float] = dict(cost or {})
        self.prices: dict[str, float] = {}
        self.orders: dict[str, dict] = {}
        self.client_ids: set[str] = set()
        self._ids = itertools.count(1)

    def to_json(self) -> dict:
        return {"cash": self.cash, "qty": self.qty, "cost": self.cost}

    def equity(self) -> float:
        return self.cash + sum(q * self.prices[s] for s, q in self.qty.items())

    def account(self) -> dict:
        return {"cash": str(self.cash), "equity": str(self.equity())}

    def positions(self) -> list[dict]:
        return [{"symbol": s, "qty": str(q), "market_value": str(q * self.prices[s]), "cost_basis": str(self.cost[s]),
                 "current_price": str(self.prices[s])} for s, q in sorted(self.qty.items()) if q > 1e-9]

    def submit_order(self, *, symbol, side, client_order_id, notional=None, qty=None):
        from .alpaca import AlpacaError
        if client_order_id in self.client_ids:
            raise AlpacaError(422, "client_order_id must be unique")
        px = self.prices.get(symbol)
        if not px:
            raise AlpacaError(422, f"no price for {symbol} at 9:40")
        self.client_ids.add(client_order_id)
        q = float(qty) if qty is not None else float(notional) / px
        if side == "buy":
            q = min(q, self.cash / px)  # never margin
            self.cash -= q * px
            self.qty[symbol] = self.qty.get(symbol, 0.0) + q
            self.cost[symbol] = self.cost.get(symbol, 0.0) + q * px
        else:
            held = self.qty.get(symbol, 0.0)
            q = min(q, held)
            self.cost[symbol] *= (held - q) / held if held else 0
            self.qty[symbol] = held - q
            self.cash += q * px
            if self.qty[symbol] <= 1e-9:
                self.qty.pop(symbol)
                self.cost.pop(symbol)
        oid = str(uuid.UUID(int=next(self._ids)))
        o = {"id": oid, "client_order_id": client_order_id, "status": "filled", "filled_qty": str(q),
             "filled_avg_price": str(px), "filled_at": None, "symbol": symbol}
        self.orders[oid] = o
        return o

    def order(self, oid):
        return self.orders[oid]

    def cancel_order(self, oid):
        pass


# -- prices -------------------------------------------------------------------

def _at_et(day: str, hh: int, mm: int) -> datetime:
    return datetime.combine(date.fromisoformat(day), time(hh, mm), tzinfo=clock.ET)


def fill_prices(data, symbols: list[str], day: str) -> dict[str, float]:
    """Price at 9:40 ET: the open of the first minute bar at or after 9:40, else the day's open."""
    if not symbols:
        return {}
    out: dict[str, float] = {}
    intraday = getattr(data, "intraday_bars", None)
    if intraday:
        start = _at_et(day, 9, 40).astimezone(timezone.utc).isoformat()
        end = _at_et(day, 9, 50).astimezone(timezone.utc).isoformat()
        for s, bars in (intraday(symbols, start, end) or {}).items():
            if bars:
                out[s] = float(bars[0]["o"])
    missing = [s for s in symbols if s not in out]
    if missing:
        for s, bars in data.daily_bars(missing, start=day, end=day).items():
            if bars:
                out[s] = float(bars[0]["o"])
    return out


def closes(data, symbols: list[str], day: str) -> dict[str, float]:
    if not symbols:
        return {}
    return {s: float(b[-1]["c"]) for s, b in data.daily_bars(symbols, start=day, end=day).items() if b}


# -- the run ------------------------------------------------------------------

def sessions_for(data, end: str, days: int, start: str | None) -> tuple[list[dict], dict | None]:
    """The trading sessions to replay, plus the session before the first one (for its close)."""
    lookback = (date.fromisoformat(start) if start else date.fromisoformat(end) - timedelta(days=int(days * 1.6) + 20))
    cal = data.calendar((lookback - timedelta(days=10)).isoformat(), end)
    if start:
        idx = next((i for i, c in enumerate(cal) if c["date"] >= start), len(cal))
        chosen = cal[idx: idx + days]
    else:
        idx = max(0, len(cal) - days)
        chosen = cal[idx:]
    prev = cal[idx - 1] if idx > 0 else None
    return chosen, prev


def _close_dt(session: dict) -> datetime:
    return datetime.fromisoformat(f"{session['date']}T{session['close']}").replace(tzinfo=clock.ET)


def _load(out: Path) -> dict:
    p = out / "state.json"
    if p.exists():
        return json.loads(p.read_text())
    return {"done": [], "broker": SimBroker().to_json(), "trades": [], "rows": [], "days": [],
            "fund": {"slippage_reserve_total": 0.0, "dividends_credited_total": 0.0, "dividends_credited": [],
                     "last_support": {}}}


def _save(out: Path, st: dict) -> None:
    (out / "state.json").write_text(json.dumps(st, indent=1))


def run(data, *, name: str, days: int = 100, end: str | None = None, start: str | None = None,
        caller: Callable[[str], str] = decide_mod.call_claude, log: Callable[[str], None] = print) -> dict:
    out = replays_dir() / name
    (out / "claude").mkdir(parents=True, exist_ok=True)
    end = end or (clock.now_et().date() - timedelta(days=1)).isoformat()
    sessions, prev = sessions_for(data, end, days, start)
    if not sessions:
        raise RuntimeError("No trading sessions in that range.")
    first = sessions[0]["date"]
    st = _load(out)
    st.setdefault("meta", {"name": name, "first": first, "last": sessions[-1]["date"], "sessions": len(sessions),
                           "prompt_version": decide_mod.prompt_version(), "model": config.CLAUDE_MODEL,
                           "started_at": datetime.now(timezone.utc).isoformat()})

    spy_bars = data.daily_bars([config.BENCHMARK], start=first, end=sessions[-1]["date"])[config.BENCHMARK]
    spy = record.spy_index_series(spy_bars, data.cash_dividends([config.BENCHMARK], first, sessions[-1]["date"]), first)
    assets_cache: dict[str, dict | None] = {}

    for i, sess in enumerate(sessions):
        day = sess["date"]
        if day in st["done"]:
            continue
        b = st["broker"]
        broker = SimBroker(b["cash"], b["qty"], b["cost"])
        held = sorted(broker.qty)
        before = sessions[i - 1] if i else prev
        prev_close_dt = _close_dt(before) if before else _at_et(day, 0, 0) - timedelta(hours=8)
        prev_day = before["date"] if before else day
        broker.prices = closes(data, held, prev_day) if held else {}
        for s in held:
            broker.prices.setdefault(s, broker.cost[s] / broker.qty[s])
        nine_forty = _at_et(day, 9, 40)
        day_number = i + 1
        entry = {"date": day, "day_number": day_number, "status": None}

        # The morning
        headlines = fetch_news.clean(fetch_news.from_alpaca(data, prev_close_dt.astimezone(timezone.utc),
                                                            nine_forty.astimezone(timezone.utc)))
        book = morning.book_from_alpaca(broker)
        morning.enrich_positions(book["positions"], st["trades"], st["fund"], st["rows"], day)
        decision = None
        if not headlines:
            entry["status"] = "no_news"
        else:
            cache = out / "claude" / f"{day}.json"
            if cache.exists():
                decision = json.loads(cache.read_text()).get("decision")
            else:
                prompt = decide_mod.build_prompt(date=day, day_number=day_number, book=book, headlines=headlines,
                                                 recent_reasons=[t["reason"] for t in st["trades"]
                                                                 if t.get("status") == "filled"][-5:])
                decision, attempts = decide_mod.decide(prompt, caller)
                cache.write_text(json.dumps({"decision": decision, "attempts": attempts}, indent=1))
            entry["status"] = "decided" if decision else "claude_failed"

        records, result = [], None
        if decision:
            named = [t for t in decision["trades"] if isinstance(t, dict)]
            named += [v for v in decision.get("book", []) if isinstance(v, dict) and v.get("verdict") == "dead"]
            tickers = sorted({str(t.get("ticker", "")).upper() for t in named} - {""})
            for t in tickers:
                if t not in assets_cache and validate_mod.TICKER_RE.match(t):
                    assets_cache[t] = data.asset(t)
            liq = trade_mod.liquidity(data, [t for t in tickers if assets_cache.get(t)], day)
            links = {h["id"]: h["link"] for h in headlines}
            result = validate_mod.validate(decision, book=book, day_number=day_number,
                                           assets={t: assets_cache.get(t) for t in tickers}, liquidity=liq,
                                           headline_links=links, paused_names=[])
            if result.accepted:
                broker.prices.update(fill_prices(data, sorted({t["ticker"] for t in result.accepted} | set(held)), day))
                records = trade_mod.execute(broker, day, result.accepted, sleep=lambda s: None, window_minutes=1)
            st["trades"].extend(morning.trade_log_rows(day, records, result.declined, links))
            morning.update_support(st["fund"], day, decision, book["positions"], records)
            notional = sum(r.get("filled_dollars", 0.0) for r in records if r.get("filled_qty"))
            st["fund"]["slippage_reserve_total"] = round(
                st["fund"]["slippage_reserve_total"] + config.SLIPPAGE_RESERVE * notional, 2)
            entry.update(mood=decision["mood"], mood_band=config.mood_band(decision["mood"]["score"])[0],
                         book=decision.get("book", []), accepted=len(result.accepted), declined=len(result.declined),
                         fading=[p["ticker"] for p in book["positions"] if p.get("fading")])

        # The evening
        now_held = sorted(broker.qty)
        broker.prices.update(closes(data, now_held, day))
        divs = data.cash_dividends(now_held, day, day) if now_held else []
        record.credit_dividends(st["fund"], divs, broker.positions(), record.first_buy_dates(st["trades"]), day)
        equity = broker.equity()
        adj = equity + st["fund"]["dividends_credited_total"] - st["fund"]["slippage_reserve_total"]
        cash_pct = broker.cash / adj if adj else 0.0
        target = validate_mod.cash_target(decision["mood"]["score"], day_number) if decision else None
        if day not in spy:
            log(f"{day}: no SPY bar; skipping the row")
        else:
            st["rows"].append({
                "date": day, "raw_equity": round(equity, 2),
                "dividends_credited_total": st["fund"]["dividends_credited_total"],
                "slippage_reserve_total": st["fund"]["slippage_reserve_total"],
                "nav": round(adj, 2), "fund_index": round(100 * adj / config.STARTING_CAPITAL, 4),
                "spy_close": spy[day]["spy_close"], "spy_index": round(spy[day]["spy_index"], 4),
                "mood_score": decision["mood"]["score"] if decision else None,
                "cash_pct": round(100 * cash_pct, 1), "cash_target_pct": None if target is None else 100 * target,
                "holdings": len(now_held),
            })
        entry.update(cash_pct=round(100 * cash_pct, 1), cash_target_pct=None if target is None else 100 * target,
                     off_target=target is not None and cash_pct > target + 0.005, holdings=len(now_held))
        st["days"].append(entry)
        st["broker"] = broker.to_json()
        st["done"].append(day)
        _save(out, st)
        row = st["rows"][-1] if st["rows"] else {}
        log(f"{day} day {day_number:>3}  {entry['status']:<13} NAV {row.get('nav', 0):>11,.2f}  "
            f"SPY idx {row.get('spy_index', 0):7.2f}  cash {entry['cash_pct']:5.1f}%  holdings {len(now_held)}")

    last_day = st["done"][-1]
    metrics.update_outcomes(st["trades"], {**closes(data, sorted({t["ticker"] for t in metrics.fills(st["trades"])}),
                                                     last_day)})
    opened = record.first_buy_dates(st["trades"])
    holdings = [{"ticker": t, "date_bought": opened.get(t)} for t in st["broker"]["qty"]]
    rep = report(st, metrics.summarize(st["rows"], st["trades"], holdings, as_of=last_day))
    (out / "report.json").write_text(json.dumps(rep, indent=1))
    (out / "report.md").write_text(report_markdown(rep))
    _save(out, st)
    return rep


# -- the report ---------------------------------------------------------------

def _reason_key(text: str) -> str:
    """Group Compliance reasons by their shape, ignoring tickers and numbers."""
    t = re.sub(r"\$?\d[\d,.]*[%MK]?", "#", text)
    t = re.sub(r"\b[A-Z]{1,5}(\.[A-Z])?\b", "TICKER", t)
    t = re.sub(r"'[^']*'", "'…'", t)
    return t


def report(st: dict, perf: dict) -> dict:
    days = st["days"]
    trades = st["trades"]
    filled = metrics.fills(trades)
    declined = [t for t in trades if t.get("status") == "declined"]
    eligible = [d for d in days if d.get("cash_target_pct") is not None]
    verdicts = Counter(v.get("verdict") for d in days for v in d.get("book", []) if isinstance(v, dict))
    reasons = [t["reason"] for t in filled]
    openings = Counter(" ".join(r.lower().split()[:5]) for r in reasons)
    repeated = sum(c for c in openings.values() if c > 1)
    rows = st["rows"]
    avg_nav = sum(r["nav"] for r in rows) / len(rows) if rows else 0
    return {
        "meta": st["meta"],
        "caveats": [
            "Private replay. Not the fund's record. Never publish it or copy it into data/vibes/.",
            "Claude may know how some of these days turned out if they fall inside its training data.",
            "One run is one sample. Run it again under another name to see the spread.",
            "Market news only: Alpaca has no history for the general world news the live fund reads.",
        ],
        "performance": perf,
        "behavior": {
            "sessions": len(days),
            "days_by_status": dict(Counter(d["status"] for d in days)),
            "avg_cash_pct": round(sum(d["cash_pct"] for d in days) / len(days), 1) if days else None,
            "avg_holdings": round(sum(d["holdings"] for d in days) / len(days), 1) if days else None,
            "max_holdings": max((d["holdings"] for d in days), default=0),
            "mood_bands": dict(Counter(d.get("mood_band") for d in days if d.get("mood_band"))),
            "days_off_cash_target": sum(1 for d in eligible if d["off_target"]),
            "days_with_cash_target": len(eligible),
            "trades_filled": len(filled),
            "buys_by_conviction": dict(Counter(t.get("conviction") for t in filled if t["action"] == "buy")),
            "sells_by_size": dict(Counter(t.get("size") for t in filled if t["action"] == "sell")),
            "trades_by_kind": dict(Counter(t.get("kind") for t in filled)),
            "exits_from_dead_verdicts": sum(1 for t in filled if t.get("from_verdict")),
            "buys_shrunk_to_fit_cash": sum(1 for t in filled if t.get("shrunk")),
            "verdicts": dict(verdicts),
            "fading_flags": sum(len(d.get("fading", [])) for d in days),
            "declined": len(declined),
            "declined_by_reason": dict(Counter(_reason_key(t.get("compliance", "")) for t in declined).most_common(12)),
            "turnover_total": round(sum(float(t["dollars"]) for t in filled) / avg_nav, 2) if avg_nav else None,
            "reasons_with_repeated_opening": repeated,
            "most_repeated_openings": [k for k, c in openings.most_common(5) if c > 1],
        },
    }


def _pct(x) -> str:
    return "n/a" if x is None else f"{x}%"


def report_markdown(rep: dict) -> str:
    m, p, b = rep["meta"], rep["performance"], rep["behavior"]
    lines = [
        f"# Replay: {m['name']}",
        "",
        f"{m['first']} to {m['last']}, {b['sessions']} sessions · prompt {m['prompt_version']} · {m['model']}",
        "",
        "## Read this first",
        "",
        *[f"- {c}" for c in rep["caveats"]],
        "",
        "## How it behaved",
        "",
        "| Measure | Value |",
        "| --- | --- |",
        f"| Days by outcome | {', '.join(f'{k}: {v}' for k, v in b['days_by_status'].items())} |",
        f"| Average cash | {b['avg_cash_pct']}% |",
        f"| Off the mood's cash target | {b['days_off_cash_target']} of {b['days_with_cash_target']} days |",
        f"| Holdings, average and most | {b['avg_holdings']} and {b['max_holdings']} |",
        f"| Mood bands | {', '.join(f'{k}: {v}' for k, v in b['mood_bands'].items())} |",
        f"| Trades filled | {b['trades_filled']} |",
        f"| Buys by conviction | {', '.join(f'{k}: {v}' for k, v in b['buys_by_conviction'].items())} |",
        f"| Sells by size | {', '.join(f'{k}: {v}' for k, v in b['sells_by_size'].items()) or 'none'} |",
        f"| Trades by kind | {', '.join(f'{k}: {v}' for k, v in b['trades_by_kind'].items())} |",
        f"| Exits from Dead verdicts | {b['exits_from_dead_verdicts']} |",
        f"| Buys shrunk to fit cash | {b['buys_shrunk_to_fit_cash']} |",
        f"| Verdicts | {', '.join(f'{k}: {v}' for k, v in b['verdicts'].items()) or 'none'} |",
        f"| Fading flags | {b['fading_flags']} |",
        f"| Turnover over the run | {b['turnover_total']}x average NAV |",
        f"| Reasons sharing an opening with another | {b['reasons_with_repeated_opening']} of {b['trades_filled']} |",
        "",
        f"## Declined by Compliance ({b['declined']})",
        "",
        *[f"- {v} × {k}" for k, v in b["declined_by_reason"].items()],
        "",
        "## Performance (one noisy sample)",
        "",
        "| Measure | Value |",
        "| --- | --- |",
    ]
    if p.get("status") == "no_data":
        lines.append("| Rows | none |")
    else:
        lines += [
            f"| Return | {p['return_since_inception_pct']}% |",
            f"| SPY total return | {p['spy_return_since_inception_pct']}% |",
            f"| Gap vs SPY | {p['gap_vs_spy_points']} points |",
            f"| Days ahead of SPY | {p['days_ahead']} of {p['trading_days']} |",
            f"| Max drawdown | {_pct(p['max_drawdown_pct'])} |",
            f"| Volatility, annualized | {_pct(p['volatility_pct'])} (SPY {_pct(p['spy_volatility_pct'])}); needs 20 days |",
            f"| Win rate on closed trades | {_pct(p['win_rate_pct'])} of {p['closed_trades']} |",
            f"| Slippage reserve charged | ${p['slippage_reserve_total']:,.2f} |",
        ]
    return "\n".join(lines) + "\n"
