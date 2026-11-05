"""The replay on fixture data: 8 sessions, real Compliance, a simulated broker, a scripted Chairman."""

import json

from vibes import config, replay

DAYS = ["2026-10-26", "2026-10-27", "2026-10-28", "2026-10-29", "2026-10-30", "2026-11-02", "2026-11-03",
        "2026-11-04"]
START = {"AAPL": 200.0, "KO": 60.0, "XLE": 90.0, "SPY": 500.0}


def make_data(fake_alpaca):
    d = fake_alpaca(START)
    for s, p in START.items():
        drift = {"AAPL": 1.01, "KO": 0.99, "XLE": 1.0, "SPY": 1.002}[s]
        d.bars[s] = [{"t": f"{day}T04:00:00Z", "o": p * drift ** i, "c": p * drift ** (i + 0.5), "v": 80_000_000}
                     for i, day in enumerate(["2026-10-%02d" % x for x in (12, 13, 14, 15, 16, 19, 20, 21, 22, 23)] + DAYS)]
    d.calendar = lambda start, end: [{"date": b["t"][:10], "open": "09:30", "close": "16:00"}
                                     for b in d.bars["SPY"] if start <= b["t"][:10] <= end]
    d.news_items = [
        {"headline": "Fruit company unveils rounder phone", "source": "benzinga", "url": "https://e.com/1",
         "created_at": "2026-10-26T12:00:00Z", "symbols": ["AAPL"]},
        {"headline": "Soda maker warns on demand", "source": "benzinga", "url": "https://e.com/2",
         "created_at": "2026-10-26T11:00:00Z", "symbols": ["KO"]},
    ]
    return d


def chairman():
    calls = []

    def caller(prompt):
        calls.append(prompt)
        n = len(calls)
        if n == 1:
            trades = [
                {"action": "buy", "ticker": "AAPL", "kind": "direct", "conviction": "strong", "reason": "Round is in.", "headline_id": "h1"},
                {"action": "buy", "ticker": "KO", "kind": "direct", "conviction": "firm", "reason": "Thirst is eternal.", "headline_id": "h2"},
                {"action": "buy", "ticker": "XLE", "kind": "sector", "conviction": "firm", "reason": "Oil, broadly.", "headline_id": "h1"},
                {"action": "buy", "ticker": "TQQQ", "kind": "leap", "conviction": "mild", "reason": "Faster.", "headline_id": "h1"},
            ]
            book = []
        else:
            trades = []
            book = [{"ticker": "AAPL", "verdict": "intact"}, {"ticker": "XLE", "verdict": "intact"}]
            if n == 4:
                book.append({"ticker": "KO", "verdict": "dead", "note": "The thirst has passed.", "headline_id": "h2"})
            elif n < 4:
                book.append({"ticker": "KO", "verdict": "intact"})
        return json.dumps({"structured_output": {"mood": {"label": "chipper", "score": 0.5}, "summary": "Fine.",
                                                 "book": book, "trades": trades}})
    return caller, calls


def test_replay_end_to_end(fake_alpaca):
    data = make_data(fake_alpaca)
    caller, calls = chairman()
    rep = replay.run(data, name="t1", days=8, end=DAYS[-1], caller=caller, log=lambda m: None)

    assert rep["meta"]["first"] == DAYS[0] and rep["meta"]["sessions"] == 8
    assert len(calls) == 8
    b = rep["behavior"]
    assert b["trades_filled"] == 4  # three buys, then the Dead-verdict exit on day 4
    assert b["exits_from_dead_verdicts"] == 1
    assert b["declined"] == 1 and any("asset list" in k for k in b["declined_by_reason"])
    assert b["buys_by_conviction"] == {"strong": 1, "firm": 2}
    # Optimistic mood allows 5% cash; the fund sat at 60%+ from day 6 onward
    assert b["days_with_cash_target"] == 3 and b["days_off_cash_target"] == 3
    p = rep["performance"]
    assert p["trading_days"] == 8 and p["slippage_reserve_total"] > 0

    out = config.ROOT / ".replays" / "t1"
    assert (out / "report.md").read_text().startswith("# Replay: t1")
    assert "Never publish" in (out / "report.md").read_text()
    # Nothing touches the fund's public data
    assert not config.DATA_DIR.exists()

    # A second run with the same name resumes: no new Claude calls, same report
    rep2 = replay.run(data, name="t1", days=8, end=DAYS[-1], caller=caller, log=lambda m: None)
    assert len(calls) == 8 and rep2["performance"]["nav"] == p["nav"]


def test_sim_broker_never_borrows():
    b = replay.SimBroker(cash=1_000)
    b.prices = {"AAPL": 100.0}
    b.submit_order(symbol="AAPL", side="buy", notional=5_000, client_order_id="x")
    assert b.cash == 0 and b.qty["AAPL"] == 10


def test_replay_stops_and_resumes_when_claude_is_unavailable(fake_alpaca):
    import pytest
    data = make_data(fake_alpaca)
    good, calls = chairman()
    state = {"down": False}

    def flaky(prompt):
        if state["down"]:
            raise replay.decide_mod.DecisionError("rate limited")
        out = good(prompt)
        if len(calls) == 3:
            state["down"] = True
        return out

    with pytest.raises(RuntimeError, match="resume"):
        replay.run(data, name="t2", days=8, end=DAYS[-1], caller=flaky, log=lambda m: None)
    st = json.loads((config.ROOT / ".replays" / "t2" / "state.json").read_text())
    assert st["done"] == DAYS[:3]
    state["down"] = False
    rep = replay.run(data, name="t2", days=8, end=DAYS[-1], caller=good, log=lambda m: None)
    assert rep["behavior"]["days_by_status"] == {"decided": 8}
