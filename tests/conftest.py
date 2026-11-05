from __future__ import annotations

import itertools
import uuid
from datetime import datetime

import pytest

from vibes import config
from vibes.alpaca import AlpacaError


@pytest.fixture(autouse=True)
def tmp_root(tmp_path, monkeypatch):
    """Every test writes into a throwaway repo root, never the real data folder."""
    monkeypatch.setattr(config, "ROOT", tmp_path)
    monkeypatch.setattr(config, "DATA_DIR", tmp_path / "data" / "vibes")
    monkeypatch.setattr(config, "LOGS_DIR", tmp_path / "data" / "vibes" / "logs")
    monkeypatch.setattr(config, "WORK_DIR", tmp_path / ".work")
    monkeypatch.setattr(config, "PAUSED_FILE", tmp_path / "PAUSED")
    monkeypatch.setattr(config, "RSS_FEEDS", [])
    return tmp_path


def asset(symbol, name="Some Company Inc. Common Stock", exchange="NASDAQ", **kw):
    return {"symbol": symbol, "name": name, "exchange": exchange, "class": "us_equity",
            "status": "active", "tradable": True, "fractionable": True, **kw}


class FakeAlpaca:
    """Enough of the Alpaca paper API to run a full morning and evening on fixture data."""

    def __init__(self, prices: dict[str, float], cash: float = 100_000.0, is_open: bool = True):
        self.prices = dict(prices)
        self.cash = cash
        self.qty: dict[str, float] = {}
        self.cost: dict[str, float] = {}
        self.orders: dict[str, dict] = {}
        self.client_ids: set[str] = set()
        self.is_open = is_open
        self.news_items: list[dict] = []
        self.assets = {s: asset(s) for s in prices}
        self.dividends: list[dict] = []
        self.history: dict[str, float] = {}
        self.bars: dict[str, list[dict]] = {}
        self._ids = itertools.count(1)

    # trading
    def clock(self):
        return {"is_open": self.is_open}

    def calendar(self, start, end):
        days = sorted({b["t"][:10] for bs in self.bars.values() for b in bs} | {start, end})
        return [{"date": d, "open": "09:30", "close": "16:00"} for d in days if start <= d <= end]

    def equity(self):
        return self.cash + sum(q * self.prices[s] for s, q in self.qty.items())

    def account(self):
        return {"equity": str(self.equity()), "cash": str(self.cash)}

    def positions(self):
        return [{"symbol": s, "qty": str(q), "market_value": str(q * self.prices[s]),
                 "cost_basis": str(self.cost[s]), "current_price": str(self.prices[s])}
                for s, q in self.qty.items() if q > 0]

    def asset(self, s):
        return self.assets.get(s)

    def orders_since(self, after):
        return list(self.orders.values())

    def order(self, oid):
        return self.orders[oid]

    def cancel_order(self, oid):
        self.orders[oid]["status"] = "canceled"

    def submit_order(self, *, symbol, side, client_order_id, notional=None, qty=None):
        if client_order_id in self.client_ids:
            raise AlpacaError(422, "client_order_id must be unique")
        self.client_ids.add(client_order_id)
        px = self.prices[symbol]
        q = float(qty) if qty is not None else float(notional) / px
        if side == "buy":
            self.cash -= q * px
            self.qty[symbol] = self.qty.get(symbol, 0) + q
            self.cost[symbol] = self.cost.get(symbol, 0) + q * px
        else:
            held = self.qty[symbol]
            self.cost[symbol] *= (held - q) / held
            self.qty[symbol] = held - q
            self.cash += q * px
            if self.qty[symbol] <= 1e-9:
                del self.qty[symbol]
                del self.cost[symbol]
        oid = str(uuid.UUID(int=next(self._ids)))
        o = {"id": oid, "client_order_id": client_order_id, "status": "filled", "filled_qty": str(q),
             "filled_avg_price": str(px), "filled_at": datetime.now().isoformat(), "symbol": symbol}
        self.orders[oid] = o
        return o

    def portfolio_history(self, period="1M"):
        return {"timestamp": [], "equity": []}

    # data
    def daily_bars(self, symbols, start, end=None):
        return {s: [b for b in self.bars.get(s, []) if b["t"][:10] >= start and (end is None or b["t"][:10] <= end)]
                for s in symbols}

    def news(self, start, end, limit=50):
        return self.news_items

    def cash_dividends(self, symbols, start, end):
        return [d for d in self.dividends if d["symbol"] in symbols and start <= d["ex_date"] <= end]


@pytest.fixture
def fake_alpaca():
    return FakeAlpaca
