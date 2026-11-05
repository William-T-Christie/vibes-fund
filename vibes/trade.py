"""Place validated orders on the Alpaca paper account and wait for fills.

Every order's client_order_id is built from the date, ticker and side, and Alpaca rejects a reused
id, so a crashed run that retries can never trade twice. Sells go first; buys go only once the sells
have filled, and only out of real cash (never margin).
"""

from __future__ import annotations

import time
from datetime import date, timedelta
from typing import Callable

from . import config
from .alpaca import Alpaca, AlpacaError

TERMINAL = {"filled", "canceled", "expired", "rejected", "done_for_day"}


def client_order_id(day: str, ticker: str, side: str) -> str:
    return f"vibes-{day}-{ticker}-{side}"


def liquidity(client: Alpaca, tickers: list[str], today: str) -> dict[str, dict]:
    """20-day average and prior-session dollar volume from daily bars."""
    if not tickers:
        return {}
    start = (date.fromisoformat(today) - timedelta(days=45)).isoformat()
    bars = client.daily_bars(tickers, start=start)
    out = {}
    for t in tickers:
        past = [b for b in bars.get(t, []) if b["t"][:10] < today]
        if not past:
            continue
        recent = past[-config.LIQUIDITY_LOOKBACK_DAYS:]
        dv = [b["c"] * b["v"] for b in recent]
        out[t] = {
            "avg_dollar_volume": sum(dv) / len(dv),
            "prior_dollar_volume": dv[-1],
            "days": len(dv),
        }
    return out


def _wait(client: Alpaca, orders: list[dict], deadline: float, sleep: Callable[[float], None]) -> list[dict]:
    pending = {o["id"]: o for o in orders}
    done: dict[str, dict] = {}
    while pending and time.time() < deadline:
        for oid in list(pending):
            o = client.order(oid)
            if o["status"] in TERMINAL:
                done[oid] = o
                pending.pop(oid)
            else:
                pending[oid] = o
        if pending:
            sleep(10)
    for oid, o in pending.items():
        # Unfilled orders are canceled once the window closes; the evening run records what really happened.
        try:
            client.cancel_order(oid)
        except AlpacaError:
            pass
        done[oid] = client.order(oid)
    return [done[o["id"]] for o in orders]


def _submit(client: Alpaca, day: str, t: dict) -> tuple[dict | None, str | None]:
    try:
        if t["action"] == "sell" and t["close_all"]:
            o = client.submit_order(symbol=t["ticker"], side="sell", qty=str(t["qty"]),
                                    client_order_id=client_order_id(day, t["ticker"], "sell"))
        else:
            o = client.submit_order(symbol=t["ticker"], side=t["action"], notional=t["dollars"],
                                    client_order_id=client_order_id(day, t["ticker"], t["action"]))
        return o, None
    except AlpacaError as e:
        return None, e.body[:300]


def execute(client: Alpaca, day: str, accepted: list[dict], *, sleep: Callable[[float], None] = time.sleep,
            window_minutes: float = config.UNFILLED_CANCEL_MINUTES) -> list[dict]:
    """Place sells, wait, place buys out of real cash, wait. Returns one record per trade."""
    records: list[dict] = []
    deadline = time.time() + window_minutes * 60

    sells = [t for t in accepted if t["action"] == "sell"]
    buys = [t for t in accepted if t["action"] == "buy"]

    placed = []
    for t in sells:
        o, err = _submit(client, day, t)
        if o:
            placed.append((t, o))
        else:
            records.append({**t, "status": "rejected", "broker_message": err})
    for (t, _), o in zip(placed, _wait(client, [o for _, o in placed], deadline, sleep)):
        records.append(_record(t, o))

    cash = float(client.account()["cash"])
    placed = []
    for t in buys:
        if t["dollars"] > cash:
            records.append({**t, "status": "declined",
                            "broker_message": f"Only ${cash:,.0f} in cash after the sells filled."})
            continue
        o, err = _submit(client, day, t)
        if o:
            cash -= t["dollars"]
            placed.append((t, o))
        else:
            records.append({**t, "status": "rejected", "broker_message": err})
    for (t, _), o in zip(placed, _wait(client, [o for _, o in placed], deadline, sleep)):
        records.append(_record(t, o))
    return records


def _record(t: dict, o: dict) -> dict:
    qty = float(o.get("filled_qty") or 0)
    px = float(o["filled_avg_price"]) if o.get("filled_avg_price") else None
    return {
        **t,
        "order_id": o["id"],
        "client_order_id": o.get("client_order_id"),
        "status": o["status"],
        "filled_qty": qty,
        "fill_price": px,
        "filled_dollars": round(qty * px, 2) if px else 0.0,
        "filled_at": o.get("filled_at"),
    }
