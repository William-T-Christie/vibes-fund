"""Thin client for the Alpaca paper trading and market data REST APIs.

Paper endpoint only. There is no switch for live trading on purpose: a leaked key can only move fake money.
"""

from __future__ import annotations

import os
import time
from typing import Any

import requests

from . import config


class AlpacaError(RuntimeError):
    def __init__(self, status: int, body: str):
        super().__init__(f"Alpaca {status}: {body[:300]}")
        self.status = status
        self.body = body


class Alpaca:
    def __init__(self, key: str | None = None, secret: str | None = None, session: requests.Session | None = None):
        key = key or os.environ.get("ALPACA_KEY")
        secret = secret or os.environ.get("ALPACA_SECRET")
        if not key or not secret:
            raise RuntimeError("ALPACA_KEY and ALPACA_SECRET must be set (paper keys only).")
        self.s = session or requests.Session()
        self.s.headers.update({"APCA-API-KEY-ID": key, "APCA-API-SECRET-KEY": secret})
        self.data_feed = os.environ.get("VIBES_ALPACA_FEED", "sip")

    # -- plumbing ---------------------------------------------------------
    def _req(self, method: str, base: str, path: str, *, retry: bool = True, **kw) -> Any:
        url = base + path
        for attempt in (1, 2):
            try:
                r = self.s.request(method, url, timeout=30, **kw)
            except requests.RequestException:
                if attempt == 1 and retry:
                    time.sleep(3)
                    continue
                raise
            if r.status_code >= 500 and attempt == 1 and retry:
                time.sleep(3)
                continue
            if r.status_code >= 400:
                raise AlpacaError(r.status_code, r.text)
            return r.json() if r.content else None
        return None  # unreachable

    def trading(self, method: str, path: str, **kw) -> Any:
        return self._req(method, config.ALPACA_TRADING_URL, path, **kw)

    def data(self, path: str, **kw) -> Any:
        return self._req("GET", config.ALPACA_DATA_URL, path, **kw)

    # -- trading ----------------------------------------------------------
    def clock(self) -> dict:
        return self.trading("GET", "/v2/clock")

    def calendar(self, start: str, end: str) -> list[dict]:
        return self.trading("GET", "/v2/calendar", params={"start": start, "end": end})

    def account(self) -> dict:
        return self.trading("GET", "/v2/account")

    def positions(self) -> list[dict]:
        return self.trading("GET", "/v2/positions")

    def asset(self, symbol: str) -> dict | None:
        try:
            return self.trading("GET", f"/v2/assets/{symbol}", retry=False)
        except AlpacaError as e:
            if e.status == 404:
                return None
            raise

    def orders_since(self, after_iso: str) -> list[dict]:
        return self.trading(
            "GET", "/v2/orders", params={"status": "all", "after": after_iso, "limit": 500, "direction": "asc"}
        )

    def order(self, order_id: str) -> dict:
        return self.trading("GET", f"/v2/orders/{order_id}")

    def submit_order(self, *, symbol: str, side: str, client_order_id: str,
                     notional: float | None = None, qty: str | None = None) -> dict:
        body: dict[str, Any] = {
            "symbol": symbol,
            "side": side,
            "type": "market",
            "time_in_force": "day",
            "client_order_id": client_order_id,
        }
        if notional is not None:
            body["notional"] = f"{notional:.2f}"
        else:
            body["qty"] = qty
        # Never retried automatically: the client_order_id makes a duplicate impossible anyway.
        return self.trading("POST", "/v2/orders", json=body, retry=False)

    def cancel_order(self, order_id: str) -> None:
        self.trading("DELETE", f"/v2/orders/{order_id}", retry=False)

    def portfolio_history(self, period: str = "1M") -> dict:
        return self.trading(
            "GET", "/v2/account/portfolio/history", params={"period": period, "timeframe": "1D"}
        )

    # -- market data ------------------------------------------------------
    def daily_bars(self, symbols: list[str], start: str, end: str | None = None) -> dict[str, list[dict]]:
        out: dict[str, list[dict]] = {s: [] for s in symbols}
        params: dict[str, Any] = {
            "symbols": ",".join(symbols),
            "timeframe": "1Day",
            "start": start,
            "adjustment": "raw",
            "feed": self.data_feed,
            "limit": 10000,
        }
        if end:
            params["end"] = end
        while True:
            page = self.data("/v2/stocks/bars", params=params)
            for sym, bars in (page.get("bars") or {}).items():
                out.setdefault(sym, []).extend(bars)
            tok = page.get("next_page_token")
            if not tok:
                return out
            params["page_token"] = tok

    def news(self, start_iso: str, end_iso: str, limit: int = 50) -> list[dict]:
        items: list[dict] = []
        params: dict[str, Any] = {"start": start_iso, "end": end_iso, "limit": 50, "sort": "desc"}
        while len(items) < limit:
            page = self.data("/v1beta1/news", params=params)
            items.extend(page.get("news") or [])
            tok = page.get("next_page_token")
            if not tok:
                break
            params["page_token"] = tok
        return items[:limit]

    def cash_dividends(self, symbols: list[str], start: str, end: str) -> list[dict]:
        if not symbols:
            return []
        page = self.data(
            "/v1/corporate-actions",
            params={"symbols": ",".join(symbols), "types": "cash_dividend", "start": start, "end": end, "limit": 1000},
        )
        return (page.get("corporate_actions") or {}).get("cash_dividends") or []
