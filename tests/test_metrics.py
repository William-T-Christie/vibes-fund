import json
from pathlib import Path

from vibes import config, metrics

SAMPLE = json.loads((Path(__file__).resolve().parents[1] / "design" / "sample-data.json").read_text())


def sample_rows():
    return [{"date": d["date"], "nav": d["fund"], "fund_index": d["fund"] / 1000, "spy_index": d["spy"] / 1000,
             "raw_equity": d["fund"], "dividends_credited_total": 0, "slippage_reserve_total": 0,
             "mood_score": 0.1} for d in SAMPLE["days"]]


def test_max_drawdown_basic():
    assert metrics.max_drawdown([100, 110, 99, 120]) == 99 / 110 - 1
    assert metrics.max_drawdown([100, 101, 102]) == 0


def test_volatility_needs_20_returns():
    assert metrics.volatility([100] * 20) is None
    assert metrics.volatility([100 + (i % 2) for i in range(21)]) > 0


def test_mood_bands():
    assert config.mood_band(-1)[0] == "Doom"
    assert config.mood_band(-0.6)[0] == "Nervous"
    assert config.mood_band(0)[0] == "Unbothered"
    assert config.mood_band(0.2)[0] == "Optimistic"
    assert config.mood_band(1)[0] == "Euphoric"
    assert config.mood_band(5)[0] == "Euphoric"


def test_summary_matches_sample_data():
    s = metrics.summarize(sample_rows(), [], [], as_of="2026-11-05")
    assert s["return_since_inception_pct"] == SAMPLE["end"]["fund_return_pct"]
    assert s["spy_return_since_inception_pct"] == SAMPLE["end"]["spy_return_pct"]
    assert s["beating_spy"] == "Not yet"
    assert s["days_ahead"] == SAMPLE["facts"]["days_ahead"]
    assert s["peak"]["date"] == SAMPLE["facts"]["peak"]["date"]
    assert s["today"] == SAMPLE["facts"]["today"]
    assert abs(s["max_drawdown_pct"] + SAMPLE["facts"]["max_drawdown_pct"]) < 0.05  # sample rounds to 0.1
    assert s["volatility_pct"] is not None
    assert s["mood_vs_next_day_return"] is None  # constant mood: no correlation to report


def fill(day, action, ticker, qty, px):
    return {"date": day, "action": action, "ticker": ticker, "qty": qty, "fill_price": px,
            "dollars": qty * px, "status": "filled", "reason": "r"}


def test_closed_trade_results_and_outcomes():
    trades = [fill("2026-11-02", "buy", "A", 10, 100), fill("2026-11-03", "buy", "A", 10, 120),
              fill("2026-11-04", "sell", "A", 10, 121), fill("2026-11-04", "buy", "B", 5, 50)]
    assert metrics.closed_trade_results(trades) == [121 / 110 - 1]
    metrics.update_outcomes(trades, {"A": 110, "B": 40})
    assert trades[0]["outcome_pct"] == 10.0
    assert trades[2]["outcome_pct"] == round(100 * (121 / 110 - 1), 2)  # sold before a fall: good call
    assert trades[3]["outcome_pct"] == -20.0
