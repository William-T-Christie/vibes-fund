from conftest import asset

from vibes import validate as v

LINKS = {"h1": "https://example.com/1", "h2": "https://example.com/2"}
LIQ = {"avg_dollar_volume": 5e9, "prior_dollar_volume": 5e9}


def book(positions=None, cash=100_000.0, nav=None):
    positions = positions or []
    nav = nav if nav is not None else cash + sum(p["market_value"] for p in positions)
    return {"nav": nav, "cash": cash, "positions": positions}


def pos(t, mv, qty="10"):
    return {"ticker": t, "market_value": mv, "qty": qty, "cost_basis": mv, "current_price": mv / 10, "gain_pct": 0}


def buy(ticker="AAPL", conviction="firm", kind="direct", reason="The fund senses a crispness.", hid="h1"):
    return {"action": "buy", "ticker": ticker, "conviction": conviction, "kind": kind, "reason": reason,
            "headline_id": hid}


def sell(ticker, size="exit", kind="direct", reason="The vibe has left the building.", hid="h2"):
    return {"action": "sell", "ticker": ticker, "size": size, "kind": kind, "reason": reason, "headline_id": hid}


def run(trades, b=None, day=1, assets=None, liq=None, paused=None, verdicts=None):
    tickers = {t["ticker"] for t in trades} | {x["ticker"] for x in verdicts or []}
    return v.validate(
        {"trades": trades, "book": verdicts or []},
        book=b or book(),
        day_number=day,
        assets=assets if assets is not None else {t: asset(t) for t in tickers},
        liquidity=liq if liq is not None else {t: LIQ for t in tickers},
        headline_links=LINKS,
        paused_names=paused,
    )


def reasons(r):
    return [d["reason"] for d in r.declined]


def five(mv=15_000):
    return [pos(f"T{c}", mv) for c in "ABCDE"]


# -- sizing ---------------------------------------------------------------

def test_conviction_sets_dollars():
    r = run([buy("AA", "mild"), buy("BB", "firm"), buy("CC", "strong"), buy("DD", "total")])
    assert {t["ticker"]: t["dollars"] for t in r.accepted} == {"AA": 5_000, "BB": 10_000, "CC": 15_000, "DD": 20_000}
    assert r.cash_after == 50_000


def test_dollars_round_down_to_100():
    r = run([buy(conviction="firm")], b=book(cash=123_456))
    assert r.accepted[0]["dollars"] == 12_300


def test_bad_conviction():
    assert "not mild, firm" in reasons(run([buy(conviction="enormous")]))[0]


def test_buys_strongest_first_and_mildest_shrinks():
    b = book(five(17_000), cash=15_000)  # NAV 100k
    r = run([buy("AA", "mild"), buy("BB", "firm")], b=b, day=10)
    got = {t["ticker"]: t for t in r.accepted}
    assert got["BB"]["dollars"] == 10_000 and not got["BB"]["shrunk"]
    assert got["AA"]["dollars"] == 5_000  # exactly fits
    r = run([buy("AA", "mild"), buy("BB", "strong")], b=b, day=10)
    got = {t["ticker"]: t for t in r.accepted}
    assert got["BB"]["dollars"] == 15_000 and "AA" not in got
    assert "Only $0 left" in reasons(r)[0]


def test_shrink_to_cash():
    b = book(five(18_000), cash=10_000)
    r = run([buy("AA", "strong")], b=b, day=10)
    assert r.accepted[0]["dollars"] == 10_000 and r.accepted[0]["shrunk"]
    b = book(five(19_900), cash=500)
    assert "Only $500 left" in reasons(run([buy("AA", "firm")], b=b, day=10))[0]


def test_position_cap_on_add():
    r = run([buy("AAPL", "firm")], b=book([pos("AAPL", 15_000)], cash=85_000))
    assert "over 20%" in reasons(r)[0]
    r = run([buy("AAPL", "mild")], b=book([pos("AAPL", 15_000)], cash=85_000))
    assert r.accepted


# -- sells ----------------------------------------------------------------

def test_trim_is_half_and_exit_is_all():
    b = book([pos("MSFT", 10_000, qty="12.5")], cash=90_000)
    r = run([sell("MSFT", "trim")], b=b)
    assert r.accepted[0]["dollars"] == 5_000 and not r.accepted[0]["close_all"]
    r = run([sell("MSFT", "exit")], b=b)
    assert r.accepted[0]["close_all"] and r.accepted[0]["qty"] == "12.5"
    assert "not trim or exit" in reasons(run([sell("MSFT", "most")], b=b))[0]


def test_tiny_trim_declined():
    r = run([sell("MSFT", "trim")], b=book([pos("MSFT", 1_500)], cash=98_500))
    assert "under the $1,000 minimum" in reasons(r)[0]


def test_sell_not_held():
    assert "does not hold" in reasons(run([sell("MSFT")]))[0]


def test_sells_fund_buys_in_same_run():
    b = book(five(19_000), cash=5_000)
    r = run([buy("NEW", "strong"), sell("TA", "exit")], b=b, day=3)
    assert [t["action"] for t in r.accepted] == ["sell", "buy"]
    assert r.accepted[1]["dollars"] == 15_000


def test_min_holdings_after_first_week():
    b = book(five(), cash=25_000)
    assert run([sell("TA")], b=b, day=3).accepted
    assert "fewer than 5" in reasons(run([sell("TA")], b=b, day=6))[0]
    assert run([sell("TA", "trim")], b=b, day=6).accepted


def test_exit_allowed_when_same_run_buys_keep_five():
    b = book(five(), cash=25_000)
    r = run([sell("TA"), buy("NEW", "firm")], b=b, day=6)
    assert [t["ticker"] for t in r.accepted] == ["TA", "NEW"]
    # Adding to an existing name doesn't count as a new holding
    r = run([sell("TA"), buy("TB", "mild")], b=b, day=6)
    assert "fewer than 5" in reasons(r)[0]
    # Already under 5: an exit is fine if the run still leaves more names than it started with
    b = book([pos("KO", 15_000), pos("XLE", 18_000)], cash=67_000)
    r = run([sell("KO"), buy("AA", "firm"), buy("BB", "firm")], b=b, day=12)
    assert len(r.accepted) == 3
    assert "fewer than 5" in reasons(run([sell("KO")], b=b, day=12))[0]


def test_max_holdings_needs_exit_first():
    b = book([pos(f"T{c}", 9_000) for c in "ABCDEFGHIJ"], cash=10_000)
    assert "Exit something first" in reasons(run([buy("NEW", "mild")], b=b))[0]
    assert len(run([buy("NEW", "mild"), sell("TA")], b=b, day=10).accepted) == 2


# -- verdicts -------------------------------------------------------------

def test_dead_verdict_adds_missing_exit():
    b = book(five() + [pos("KO", 10_000)], cash=15_000)
    r = run([], b=b, day=10, verdicts=[{"ticker": "KO", "verdict": "dead", "note": "Fizz is over.", "headline_id": "h2"}])
    assert r.accepted[0]["ticker"] == "KO" and r.accepted[0]["close_all"] and r.accepted[0]["from_verdict"]


def test_dead_verdict_not_doubled_when_exit_listed():
    b = book(five() + [pos("KO", 10_000)], cash=15_000)
    r = run([sell("KO")], b=b, day=10, verdicts=[{"ticker": "KO", "verdict": "dead", "headline_id": "h2"}])
    assert len(r.accepted) == 1 and not r.declined


def test_dead_verdict_without_headline_is_declined():
    b = book(five() + [pos("KO", 10_000)], cash=15_000)
    r = run([], b=b, day=10, verdicts=[{"ticker": "KO", "verdict": "dead", "note": "Gone."}])
    assert not r.accepted and "not in this morning's news" in reasons(r)[0]


# -- kinds, reasons, assets ------------------------------------------------

def test_kind_required_and_leap_limit():
    assert "not a direct, sector or leap" in reasons(run([buy(kind="hunch")]))[0]
    r = run([buy("AA", kind="leap"), buy("BB", kind="leap"), buy("CC", kind="leap")])
    assert len(r.accepted) == 2 and "leaps today" in reasons(r)[0]


def test_price_only_reasons_declined():
    assert "falling price is not news" in reasons(run([buy(reason="The share price has fallen, so in we go.")]))[0]
    assert "falling price is not news" in reasons(
        run([sell("MSFT", reason="Its shares dropped and the fund panicked.")], b=book([pos("MSFT", 10_000)])))[0]
    # A price in the news itself is fair game
    assert run([buy(reason="Oil prices fell, and the fund feels lighter.")]).accepted


def test_unknown_ticker_declined():
    r = run([buy("ZZZZ")], assets={"ZZZZ": None})
    assert not r.accepted and "not on the asset list" in reasons(r)[0]


def test_bad_ticker_shape():
    assert "not shaped like a ticker" in reasons(run([buy("not a ticker")]))[0]


def test_leveraged_etf_declined_by_list_and_name():
    assert "leveraged or inverse" in reasons(run([buy("TQQQ")]))[0]
    r = run([buy("ABCD")], assets={"ABCD": asset("ABCD", name="Direxion Daily Semis Bull 3X Shares")})
    assert "leveraged or inverse" in reasons(r)[0]


def test_short_term_treasury_etf_allowed():
    assert run([buy("SHV")], assets={"SHV": asset("SHV", name="iShares Short Treasury Bond ETF")}).accepted


def test_otc_declined():
    assert "not a listed exchange" in reasons(run([buy("ABCD")], assets={"ABCD": asset("ABCD", exchange="OTC")}))[0]


def test_trade_limit():
    r = run([buy(t, "mild") for t in ("AA", "BB", "CC", "DD", "EE")])
    assert len(r.accepted) == 4 and "Trade limit" in reasons(r)[0]


def test_reason_rules():
    assert "No reason" in reasons(run([buy(reason="")]))[0]
    assert "200 characters" in reasons(run([buy(reason="x" * 201)]))[0]
    assert "more than one sentence" in reasons(run([buy(reason="Bought it. Then More things.")]))[0]


def test_headline_must_be_from_this_morning():
    assert "not in this morning's news" in reasons(run([buy(hid="h99")]))[0]


def test_liquidity_floor_and_volume_cap():
    r = run([buy()], liq={"AAPL": {"avg_dollar_volume": 10e6, "prior_dollar_volume": 10e6}})
    assert "under the $50M floor" in reasons(r)[0]
    r = run([buy()], liq={"AAPL": {"avg_dollar_volume": 60e6, "prior_dollar_volume": 600_000}})
    assert "more than 1%" in reasons(r)[0]
    assert "No trading volume" in reasons(run([buy()], liq={}))[0]


def test_paused_name():
    assert "paused" in reasons(run([buy()], paused=["AAPL"]))[0]


def test_duplicate_trade_same_day():
    r = run([buy(conviction="mild"), buy(conviction="mild")])
    assert len(r.accepted) == 1 and "Already buying" in reasons(r)[0]


def test_cash_target_by_mood():
    assert v.cash_target(0.9, day_number=3) is None  # first week
    assert v.cash_target(0.9, day_number=6) == 0.05
    assert v.cash_target(-0.8, day_number=6) == 0.30
    assert v.cash_target(0.0, day_number=6) == 0.10
    assert v.cash_target(None, day_number=6) is None
