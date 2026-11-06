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
        {"action": "buy", "ticker": "AAPL", "kind": "direct", "conviction": "strong",
         "reason": "Roundness is underpriced.", "headline_id": "h1"},
        {"action": "buy", "ticker": "KO", "kind": "direct", "conviction": "total", "catalyst": "earnings_beat",
         "reason": "Fizz is a feeling.", "headline_id": "h2"},
        {"action": "buy", "ticker": "TQQQ", "kind": "leap", "conviction": "strong", "reason": "Speed.", "headline_id": "h1"},
        {"action": "buy", "ticker": "MSFT", "kind": "leap", "conviction": "mega", "reason": "Too much.",
         "headline_id": "h1"},
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
    assert "top out at a firm" in declined["TQQQ"] and "not mild, firm" in declined["MSFT"]
    kinds = {t["ticker"]: (t["kind"], t["conviction"], t["catalyst"]) for t in log if t["status"] == "filled"}
    assert kinds == {"AAPL": ("direct", "strong", "event"), "KO": ("direct", "total", "earnings_beat")}
    state = store.fund_state()
    assert state["inception"] == DAY
    assert abs(state["slippage_reserve_total"] - 65.0) < 0.01  # 0.10% of $65,000
    assert state["last_support"] == {"AAPL": DAY, "KO": DAY}

    # A second run the same morning places nothing
    again = morning.prepare(c, now=datetime(2026, 11, 5, 10, 40, tzinfo=clock.ET))
    assert again["status"] == "done"

    # Prices move, then the evening record
    c.prices["AAPL"] = 210.0
    c.bars["SPY"][-1]["c"] = 505.0
    out = record.run(c, now=datetime(2026, 11, 5, 16, 30, tzinfo=clock.ET))
    assert out["status"] == "recorded" and out["days"] == [DAY]
    row = store.read("nav.json")["rows"][-1]
    raw = 100_000 + 150 * 10  # 150 AAPL shares gained $10 each
    assert row["raw_equity"] == raw and row["nav"] == round(raw - 65.0, 2)
    assert "cash_pct" not in row  # first week: no mood cash target
    assert row["mood_band"] == "Optimistic"
    summary = store.read("summary.json")
    assert summary["mood"]["label"] == "quietly smug"
    assert summary["beating_spy"] in ("Yes", "Not yet")
    holdings = {h["ticker"]: h for h in store.read("holdings.json")["holdings"]}
    assert holdings["AAPL"]["buy_reason"] == "Roundness is underpriced."
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
        {"action": "buy", "ticker": "AAPL", "kind": "direct", "conviction": "firm", "reason": "Round.",
         "headline_id": "h1"}]))
    morning.run_trades(c, sleep=lambda s: None)
    # A rerun of the trade step is stopped by the order log...
    assert morning.run_trades(c, sleep=lambda s: None)["status"] == "already_traded"
    # ...and if the run crashed before writing it, Alpaca rejects the reused order id.
    (config.LOGS_DIR / DAY / "orders.json").unlink()
    morning.run_trades(c, sleep=lambda s: None)
    assert len(c.orders) == 1


def seed_week(store_rows_until="2026-11-04"):
    """Pretend the fund has been live for a while, so first-week rules no longer apply."""
    days = ["2026-10-%02d" % d for d in (12, 13, 14, 15, 16, 19, 20, 21, 22, 23, 26, 27, 28, 29, 30)]
    days += ["2026-11-02", "2026-11-03", "2026-11-04"]
    rows = [{"date": d, "nav": 100_000, "fund_index": 100, "spy_index": 100, "raw_equity": 100_000,
             "dividends_credited_total": 0, "slippage_reserve_total": 0, "mood_score": 0.1} for d in days]
    store.write("nav.json", {"rows": rows})
    st = store.fund_state()
    st["inception"] = days[0]
    st["last_support"] = {"KO": days[0], "AAPL": "2026-11-03"}
    store.save_fund_state(st)
    store.write("trades.json", {"trades": [
        {"date": days[0], "action": "buy", "ticker": "KO", "qty": 100, "fill_price": 60.0, "dollars": 6000,
         "status": "filled", "reason": "Fizz is a feeling."},
        {"date": "2026-11-03", "action": "buy", "ticker": "AAPL", "qty": 50, "fill_price": 200.0, "dollars": 10000,
         "status": "filled", "reason": "Roundness is underpriced."},
    ]})
    return days


def test_book_review_context_and_fading(fake_alpaca):
    c = make_client(fake_alpaca)
    days = seed_week()
    c.qty = {"KO": 100.0, "AAPL": 50.0}
    c.cost = {"KO": 6000.0, "AAPL": 10000.0}
    c.cash = 100_000 - 16_000
    work = morning.prepare(c, now=datetime(2026, 11, 5, 9, 40, tzinfo=clock.ET))
    p = {x["ticker"]: x for x in work["book"]["positions"]}
    assert p["KO"]["thesis"] == "Fizz is a feeling." and p["KO"]["days_held"] == len(days)
    assert p["KO"]["fading"] and p["KO"]["days_since_support"] == len(days)
    assert not p["AAPL"]["fading"] and p["AAPL"]["days_since_support"] == 2

    seen = {}

    def caller(prompt):
        seen["prompt"] = prompt
        return json.dumps({"structured_output": {
            "mood": {"label": "beaming", "score": 0.8}, "summary": "Sunny.",
            "book": [{"ticker": "KO", "verdict": "intact", "note": "Fizz endures, as fizz does."},
                     {"ticker": "AAPL", "verdict": "intact"}],
            "trades": [], "holds": ""}})

    morning.decide(caller=caller)
    assert "(FADING)" in seen["prompt"] and "Fizz is a feeling." in seen["prompt"]
    morning.run_trades(c, sleep=lambda s: None)
    assert store.fund_state()["last_support"]["KO"] == DAY  # reaffirmed while fading

    # Euphoric with 84% cash: the evening log calls it out
    out = record.run(c, now=datetime(2026, 11, 5, 16, 30, tzinfo=clock.ET))
    assert out["status"] == "recorded"
    notes = [t for t in store.read("trades.json")["trades"] if t["status"] == "note"]
    assert [n["reason"] for n in notes if not n.get("note_kind")] == ["The Chairman felt Euphoric and remained 84% in cash."]
    assert [n["reason"] for n in notes if n.get("note_kind") == "declined_leverage"] == [
        "The Chairman felt Euphoric and declined the bull fund."]
    s = store.read("summary.json")
    assert s["cash_vs_mood"] == {"cash_pct": 84.0, "counted_cash_pct": 84.0, "target_pct": 0.0, "on_target": False}
    h = {x["ticker"]: x for x in store.read("holdings.json")["holdings"]}
    assert h["KO"]["verdict"] == "intact" and h["KO"]["verdict_note"] == "Fizz endures, as fizz does."


def test_drift_window_in_the_book(fake_alpaca):
    c = make_client(fake_alpaca)
    days = seed_week()
    trades = store.read("trades.json")
    trades["trades"][1]["catalyst"] = "earnings_beat"  # AAPL bought on a beat two sessions ago
    trades["trades"][0]["catalyst"] = "earnings_beat"  # KO bought on a beat 18 sessions ago
    store.write("trades.json", trades)
    c.qty, c.cost, c.cash = {"KO": 100.0, "AAPL": 50.0}, {"KO": 6000.0, "AAPL": 10000.0}, 84_000
    work = morning.prepare(c, now=datetime(2026, 11, 5, 9, 40, tzinfo=clock.ET))
    p = {x["ticker"]: x for x in work["book"]["positions"]}
    assert p["AAPL"]["drift_days_left"] == config.DRIFT_DAYS - 2
    assert p["KO"]["drift_days_left"] == config.DRIFT_DAYS - len(days)
    assert not p["KO"]["fading"]  # the fading clock waits for the drift window to end
