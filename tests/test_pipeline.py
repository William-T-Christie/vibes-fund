"""End to end on a fake Alpaca: morning prepare -> decide -> trade, then the evening record."""

import json
from datetime import datetime

from vibes import clock, config, morning, record, store

DAY = "2026-11-05"
PRICES = {"AAPL": 200.0, "MSFT": 400.0, "KO": 60.0, "SPY": 500.0}


def bars(sym, closes):
    return [{"t": f"{d}T05:00:00Z", "o": c * 0.995, "c": c, "v": 50_000_000} for d, c in closes]


def make_client(fake_alpaca):
    c = fake_alpaca(PRICES)
    history = [("2026-10-29", 1), ("2026-10-30", 1), ("2026-11-02", 1), ("2026-11-03", 1), ("2026-11-04", 1),
               (DAY, 1)]
    for s, p in PRICES.items():
        c.bars[s] = bars(s, [(d, p) for d, _ in history])
    c.news_items = [
        {"headline": "Fruit company unveils slightly rounder phone", "source": "benzinga",
         "url": "https://example.com/fruit", "created_at": "2026-11-05T12:00:00Z", "symbols": ["AAPL"]},
        {"headline": "Soda sales fizz", "source": "benzinga", "url": "https://example.com/soda",
         "created_at": "2026-11-05T11:00:00Z", "symbols": ["KO"]},
    ]
    return c


def claude_reply(trades):
    def caller(prompt):
        assert "Fruit company" in prompt
        return json.dumps({"type": "result", "structured_output": {
            "mood": {"label": "quietly smug", "score": 0.45}, "summary": "The world feels round.",
            "trades": trades, "holds": ""}})
    return caller


def test_full_day(fake_alpaca):
    c = make_client(fake_alpaca)
    from conftest import asset
    c.assets["TQQQ"] = asset("TQQQ", name="ProShares UltraPro QQQ")
    nine_forty = datetime(2026, 11, 5, 9, 40, tzinfo=clock.ET)

    work = morning.prepare(c, now=nine_forty)
    assert work["proceed"] and work["day_number"] == 1
    # The committed headline log never holds headline text
    committed = (config.LOGS_DIR / DAY / "headlines.json").read_text()
    assert "Fruit company" not in committed and "https://example.com/fruit" in committed

    trades = [
        {"action": "buy", "ticker": "AAPL", "dollars": 18000, "reason": "Roundness is underpriced.", "headline_id": "h1"},
        {"action": "buy", "ticker": "KO", "dollars": 15000, "reason": "Fizz is a feeling.", "headline_id": "h2"},
        {"action": "buy", "ticker": "TQQQ", "dollars": 15000, "reason": "Speed.", "headline_id": "h1"},
        {"action": "buy", "ticker": "MSFT", "dollars": 30000, "reason": "Too much.", "headline_id": "h1"},
    ]
    work = morning.decide(caller=claude_reply(trades))
    assert work["proceed"]
    decision = store.read_log(DAY, "decision.json")
    assert decision["mood_band"] == "Optimistic" and decision["prompt_version"]
    assert store.read("summary.json")["mood"]["label"] == "quietly smug"

    result = morning.run_trades(c, sleep=lambda s: None)
    assert result == {"status": "traded", "accepted": 2, "declined": 2, "filled": 2}
    assert set(c.qty) == {"AAPL", "KO"}
    log = store.read("trades.json")["trades"]
    declined = {t["ticker"]: t["compliance"] for t in log if t["status"] == "declined"}
    assert "leveraged" in declined["TQQQ"] and "20%" in declined["MSFT"]
    state = store.fund_state()
    assert state["inception"] == DAY
    assert abs(state["slippage_reserve_total"] - 33.0) < 0.01  # 0.10% of $33,000

    # A second run the same morning places nothing
    again = morning.prepare(c, now=datetime(2026, 11, 5, 10, 40, tzinfo=clock.ET))
    assert again["status"] == "done"

    # Prices move, then the evening record
    c.prices["AAPL"] = 210.0
    c.bars["SPY"][-1]["c"] = 505.0
    out = record.run(c, now=datetime(2026, 11, 5, 16, 30, tzinfo=clock.ET))
    assert out["status"] == "recorded" and out["days"] == [DAY]
    row = store.read("nav.json")["rows"][-1]
    raw = 100_000 + 90 * 10  # 90 AAPL shares gained $10 each
    assert row["raw_equity"] == raw and row["nav"] == round(raw - 33.0, 2)
    assert row["mood_band"] == "Optimistic"
    summary = store.read("summary.json")
    assert summary["mood"]["label"] == "quietly smug"
    assert summary["beating_spy"] in ("Yes", "Not yet")
    holdings = store.read("holdings.json")["holdings"]
    assert holdings[0]["ticker"] == "AAPL" and holdings[0]["buy_reason"] == "Roundness is underpriced."
    aapl_trade = next(t for t in store.read("trades.json")["trades"] if t["ticker"] == "AAPL")
    assert aapl_trade["outcome_pct"] == 5.0

    # Running the evening again is a no-op
    assert record.run(c, now=datetime(2026, 11, 5, 17, 30, tzinfo=clock.ET))["status"] == "up_to_date"


def test_paused_file_holds(fake_alpaca):
    c = make_client(fake_alpaca)
    config.PAUSED_FILE.write_text("paused")
    out = morning.prepare(c, now=datetime(2026, 11, 5, 9, 40, tzinfo=clock.ET))
    assert out["status"] == "paused"


def test_late_run_oversleeps(fake_alpaca):
    c = make_client(fake_alpaca)
    out = morning.prepare(c, now=datetime(2026, 11, 5, 11, 5, tzinfo=clock.ET))
    assert out["message"] == "The manager overslept."
    assert store.read_log(DAY, "decision.json")["status"] == "late"


def test_market_closed(fake_alpaca):
    c = make_client(fake_alpaca)
    c.is_open = False
    assert morning.prepare(c, now=datetime(2026, 11, 5, 9, 40, tzinfo=clock.ET))["status"] == "closed"


def test_quiet_morning(fake_alpaca):
    c = make_client(fake_alpaca)
    c.news_items = []
    out = morning.prepare(c, now=datetime(2026, 11, 5, 9, 40, tzinfo=clock.ET))
    assert out["message"] == "Quiet morning. The fund meditated."


def test_claude_out_of_office(fake_alpaca):
    c = make_client(fake_alpaca)
    morning.prepare(c, now=datetime(2026, 11, 5, 9, 40, tzinfo=clock.ET))
    out = morning.decide(caller=lambda p: "not json at all")
    assert out["status"] == "claude_failed"
    assert morning.run_trades(c)["status"] == "claude_failed"
    assert not c.orders


def test_retry_cannot_trade_twice(fake_alpaca):
    c = make_client(fake_alpaca)
    morning.prepare(c, now=datetime(2026, 11, 5, 9, 40, tzinfo=clock.ET))
    morning.decide(caller=claude_reply([
        {"action": "buy", "ticker": "AAPL", "dollars": 10000, "reason": "Round.", "headline_id": "h1"}]))
    morning.run_trades(c, sleep=lambda s: None)
    # A rerun of the trade step is stopped by the order log...
    assert morning.run_trades(c, sleep=lambda s: None)["status"] == "already_traded"
    # ...and if the run crashed before writing it, Alpaca rejects the reused order id.
    (config.LOGS_DIR / DAY / "orders.json").unlink()
    morning.run_trades(c, sleep=lambda s: None)
    assert len(c.orders) == 1
