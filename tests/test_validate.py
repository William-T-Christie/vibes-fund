from conftest import asset

from vibes import config
from vibes import validate as v

LINKS = {"h1": "https://example.com/1", "h2": "https://example.com/2"}
LIQ = {"avg_dollar_volume": 5e9, "prior_dollar_volume": 5e9}


def book(positions=None, cash=100_000.0, nav=None):
    positions = positions or []
    nav = nav if nav is not None else cash + sum(p["market_value"] for p in positions)
    return {"nav": nav, "cash": cash, "positions": positions}


def pos(t, mv, qty="10"):
    return {"ticker": t, "market_value": mv, "qty": qty, "cost_basis": mv, "current_price": mv / 10, "gain_pct": 0}


def buy(ticker="AAPL", conviction="firm", kind="direct", reason="The fund senses a crispness.", hid="h1",
        catalyst="event"):
    return {"action": "buy", "ticker": ticker, "conviction": conviction, "kind": kind, "reason": reason,
            "headline_id": hid, "catalyst": catalyst}


def sell(ticker, size="exit", kind="direct", reason="The vibe has left the building.", hid="h2"):
    return {"action": "sell", "ticker": ticker, "size": size, "kind": kind, "reason": reason, "headline_id": hid}


def run(trades, b=None, day=1, assets=None, liq=None, paused=None, verdicts=None, mood=0.1, wild_card_used=False):
    if verdicts is None:  # by default, anything being sold has a Weakened verdict that morning
        verdicts = [{"ticker": t["ticker"], "verdict": "weakened"} for t in trades if t["action"] == "sell"]
    b = b or book()
    tickers = {t["ticker"] for t in trades} | {x["ticker"] for x in verdicts or []} | {p["ticker"] for p in b["positions"]}
    return v.validate(
        {"mood": {"label": "x", "score": mood}, "trades": trades, "book": verdicts or []},
        book=b,
        day_number=day,
        assets=assets if assets is not None else {t: asset(t) for t in tickers},
        liquidity=liq if liq is not None else {t: LIQ for t in tickers},
        headline_links=LINKS,
        paused_names=paused,
        wild_card_used=wild_card_used,
    )


def reasons(r):
    return [d["reason"] for d in r.declined]


def three(mv=25_000):
    return [pos(f"T{c}", mv) for c in "ABC"]


# -- sizing ---------------------------------------------------------------

def test_conviction_sets_dollars():
    r = run([buy("AA", "mild"), buy("BB", "firm"), buy("CC", "strong")])
    assert {t["ticker"]: t["dollars"] for t in r.accepted} == {"AA": 10_000, "BB": 20_000, "CC": 30_000}
    r = run([buy("DD", "total", catalyst="earnings_beat")])
    assert r.accepted[0]["dollars"] == 35_000


def test_dollars_round_down_to_100():
    r = run([buy(conviction="mild")], b=book(cash=123_456))
    assert r.accepted[0]["dollars"] == 12_300


def test_total_is_for_earnings_beats_only():
    assert "reserved for an earnings beat" in reasons(run([buy(conviction="total")]))[0]
    assert run([buy(conviction="total", catalyst="earnings_beat")]).accepted
    assert "does not buy on an earnings miss" in reasons(run([buy(catalyst="earnings_miss")]))[0]
    assert "not an earnings beat" in reasons(run([buy(catalyst="gut")]))[0]
    assert "mild conviction at most" in reasons(run([buy(conviction="firm", catalyst="opinion")]))[0]


def test_bad_conviction():
    assert "not mild, firm" in reasons(run([buy(conviction="enormous")]))[0]


def test_buys_strongest_first_and_mildest_shrinks():
    b = book(three(23_000), cash=31_000)  # NAV 100k
    r = run([buy("AA", "mild"), buy("BB", "firm")], b=b, day=10)
    got = {t["ticker"]: t for t in r.accepted}
    assert got["BB"]["dollars"] == 20_000 and not got["BB"]["shrunk"]
    assert got["AA"]["dollars"] == 10_000
    r = run([buy("AA", "mild"), buy("BB", "strong")], b=b, day=10)
    got = {t["ticker"]: t for t in r.accepted}
    assert got["BB"]["dollars"] == 30_000 and got["AA"]["dollars"] == 1_000 and got["AA"]["shrunk"]


def test_shrink_to_cash():
    b = book(three(28_000), cash=16_000)
    r = run([buy("AA", "strong")], b=b, day=10)
    assert r.accepted[0]["dollars"] == 16_000 and r.accepted[0]["shrunk"]
    b = book(three(33_150), cash=550)
    assert "Only $550 left" in reasons(run([buy("AA", "firm")], b=b, day=10))[0]


STRONGER = [{"ticker": "AAPL", "verdict": "strengthened"}]


def test_position_cap_on_add():
    b = book([pos("AAPL", 20_000)], cash=80_000)
    assert "over 35%" in reasons(run([buy("AAPL", "firm")], b=b, verdicts=STRONGER))[0]
    assert run([buy("AAPL", "mild")], b=b, verdicts=STRONGER).accepted


def test_adds_need_a_strengthened_verdict():
    b = book([pos("AAPL", 10_000)], cash=90_000)
    assert "Strengthened verdict" in reasons(run([buy("AAPL", "mild")], b=b))[0]
    r = run([buy("AAPL", "mild")], b=b, verdicts=[{"ticker": "AAPL", "verdict": "intact"}])
    assert "Strengthened verdict" in reasons(r)[0]
    assert run([buy("AAPL", "mild")], b=b, verdicts=STRONGER).accepted


def test_analyst_opinions_cap_at_mild_and_never_add():
    why = "Barclays lifts its price target, and the fund feels flattered by proxy."
    assert "mild conviction at most" in reasons(run([buy("TEL", "firm", reason=why)]))[0]
    assert run([buy("TEL", "mild", reason=why)]).accepted
    b = book([pos("TEL", 10_000)], cash=90_000)
    r = run([buy("TEL", "mild", reason=why)], b=b, verdicts=[{"ticker": "TEL", "verdict": "strengthened"}])
    assert "never a reason to add" in reasons(r)[0]
    assert run([buy("TEL", "strong", reason="The connector maker raised its full-year outlook.")]).accepted


def test_recent_sales_dont_count_against_the_cash_limit():
    sessions = ["2026-11-02", "2026-11-03", "2026-11-04", "2026-11-05"]
    trades = [
        {"date": "2026-11-02", "action": "sell", "status": "filled", "dollars": 9_000},  # 4 sessions ago: counts
        {"date": "2026-11-04", "action": "sell", "status": "filled", "dollars": 5_000},
        {"date": "2026-11-05", "action": "sell", "status": "filled", "dollars": 3_000},
        {"date": "2026-11-05", "action": "buy", "status": "filled", "dollars": 2_000},
    ]
    assert v.recent_sale_cash(trades, sessions, "2026-11-05") == 8_000
    c = v.cash_check(12_000, 100_000, 8_000, 0.4, day_number=10)
    assert c == {"cash_pct": 12.0, "counted_cash_pct": 4.0, "target_pct": 5.0, "on_target": True}
    assert not v.cash_check(12_000, 100_000, 0, 0.4, day_number=10)["on_target"]
    assert v.cash_check(12_000, 100_000, 0, 0.4, day_number=3) is None


def test_cash_target_by_mood():
    assert v.cash_target(0.9, day_number=3) is None  # first week
    assert v.cash_target(0.9, day_number=6) == 0.0  # Euphoric: all in
    assert v.cash_target(0.4, day_number=6) == 0.05
    assert v.cash_target(0.0, day_number=6) == 0.15
    assert v.cash_target(-0.4, day_number=6) == 0.30
    assert v.cash_target(-0.8, day_number=6) == 0.50  # Doom: half out
    assert v.cash_target(None, day_number=6) is None


# -- sells ----------------------------------------------------------------

def test_trims_need_a_turned_verdict():
    b = book([pos("MSFT", 10_000)], cash=90_000)
    assert "Trims need a Weakened or Dead verdict" in reasons(run([sell("MSFT", "trim")], b=b, verdicts=[]))[0]
    r = run([sell("MSFT", "trim")], b=b, verdicts=[{"ticker": "MSFT", "verdict": "intact"}])
    assert "Trims need" in reasons(r)[0]
    assert run([sell("MSFT", "exit")], b=b, verdicts=[]).accepted


def test_drift_window_protects_earnings_winners():
    p = pos("NVDA", 15_000)
    p["drift_days_left"] = 12
    b = book([p], cash=85_000)
    r = run([sell("NVDA", "exit")], b=b, verdicts=[{"ticker": "NVDA", "verdict": "intact"}])
    assert "drift window for 12 more days" in reasons(r)[0]
    assert run([sell("NVDA", "exit")], b=b, verdicts=[{"ticker": "NVDA", "verdict": "dead"}]).accepted
    p["drift_days_left"] = 0
    assert run([sell("NVDA", "exit")], b=b, verdicts=[]).accepted


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
    b = book(three(30_000), cash=10_000)
    r = run([buy("NEW", "strong"), sell("TA", "exit")], b=b, day=3)
    assert [t["action"] for t in r.accepted] == ["sell", "buy"]
    assert r.accepted[1]["dollars"] == 30_000


def test_min_holdings_after_first_week():
    b = book(three(), cash=25_000)
    assert run([sell("TA")], b=b, day=3).accepted
    assert "fewer than 3" in reasons(run([sell("TA")], b=b, day=6))[0]
    assert run([sell("TA", "trim")], b=b, day=6).accepted


def test_exit_allowed_when_same_run_buys_keep_the_minimum():
    b = book(three(), cash=25_000)
    r = run([sell("TA"), buy("NEW", "firm")], b=b, day=6)
    assert [t["ticker"] for t in r.accepted] == ["TA", "NEW"]
    # Adding to an existing name doesn't count as a new holding
    r = run([sell("TA"), buy("TB", "mild")], b=b, day=6,
            verdicts=[{"ticker": "TA", "verdict": "weakened"}, {"ticker": "TB", "verdict": "strengthened"}])
    assert "fewer than 3" in reasons(r)[0]
    # Already under the minimum: an exit is fine if the run still leaves more names than it started with
    b = book([pos("KO", 15_000)], cash=85_000)
    r = run([sell("KO"), buy("AA", "firm"), buy("BB", "firm")], b=b, day=12)
    assert len(r.accepted) == 3
    assert "fewer than 3" in reasons(run([sell("KO")], b=b, day=12))[0]


def test_max_holdings_needs_exit_first():
    b = book([pos(f"T{c}", 15_000) for c in "ABCDEF"], cash=10_000)
    assert "past 6 holdings" in reasons(run([buy("NEW", "mild")], b=b))[0]
    assert len(run([buy("NEW", "mild"), sell("TA")], b=b, day=10).accepted) == 2


# -- verdicts -------------------------------------------------------------

def test_dead_verdict_adds_missing_exit():
    b = book(three() + [pos("KO", 10_000)], cash=15_000)
    r = run([], b=b, day=10, verdicts=[{"ticker": "KO", "verdict": "dead", "note": "Fizz is over.", "headline_id": "h2"}])
    assert r.accepted[0]["ticker"] == "KO" and r.accepted[0]["close_all"] and r.accepted[0]["from_verdict"]


def test_dead_verdict_not_doubled_when_exit_listed():
    b = book(three() + [pos("KO", 10_000)], cash=15_000)
    r = run([sell("KO")], b=b, day=10, verdicts=[{"ticker": "KO", "verdict": "dead", "headline_id": "h2"}])
    assert len(r.accepted) == 1 and not r.declined


def test_dead_verdict_without_headline_is_declined():
    b = book(three() + [pos("KO", 10_000)], cash=15_000)
    r = run([], b=b, day=10, verdicts=[{"ticker": "KO", "verdict": "dead", "note": "Gone."}])
    assert not r.accepted and "not in this morning's news" in reasons(r)[0]


# -- leveraged funds --------------------------------------------------------

def lev(t):
    return asset(t, name="ProShares UltraPro QQQ", exchange="NASDAQ")


def test_leveraged_bull_fund_needs_a_good_morning():
    assets = {"TQQQ": lev("TQQQ")}
    assert "not that good" in reasons(run([buy("TQQQ", "mild")], assets=assets, mood=0.3))[0]
    r = run([buy("TQQQ", "firm")], assets=assets, mood=0.45)
    assert r.accepted and r.accepted[0]["leveraged"] and r.accepted[0]["dollars"] == 20_000


def test_leveraged_bear_fund_needs_a_grim_morning():
    assets = {"SQQQ": lev("SQQQ")}
    assert "not that grim" in reasons(run([buy("SQQQ", "mild")], assets=assets, mood=-0.3))[0]
    assert run([buy("SQQQ", "mild")], assets=assets, mood=-0.5).accepted


def test_leveraged_funds_top_out_at_firm_and_one_at_a_time():
    assets = {"TQQQ": lev("TQQQ"), "SOXL": lev("SOXL")}
    assert "top out at a firm" in reasons(run([buy("TQQQ", "strong")], assets=assets, mood=0.5))[0]
    b = book([pos("SOXL", 20_000)], cash=80_000)
    assert "One leveraged fund at a time" in reasons(run([buy("TQQQ", "mild")], b=b, assets=assets, mood=0.5))[0]


def test_mood_flip_forces_the_leveraged_fund_out():
    b = book(three() + [pos("TQQQ", 20_000)], cash=5_000)
    r = run([], b=b, day=10, mood=-0.1, verdicts=[], assets={"TQQQ": lev("TQQQ")})
    assert r.accepted[0]["ticker"] == "TQQQ" and r.accepted[0]["from_rule"] == "mood_flip"
    assert r.accepted[0]["close_all"] and r.accepted[0]["headline_link"] is None
    # Still pointing the right way: nothing happens
    assert not run([], b=b, day=10, mood=0.1, verdicts=[], assets={"TQQQ": lev("TQQQ")}).accepted
    # A bear fund flips out on a cheerful morning
    b = book(three() + [pos("SQQQ", 20_000)], cash=5_000)
    assert run([], b=b, day=10, mood=0.2, verdicts=[], assets={"SQQQ": lev("SQQQ")}).accepted[0]["ticker"] == "SQQQ"


def test_leveraged_fund_does_not_take_a_holding_slot():
    b = book([pos(f"T{c}", 15_000) for c in "ABCDEF"], cash=10_000)
    r = run([buy("SQQQ", "mild")], b=b, mood=-0.5, assets={"SQQQ": lev("SQQQ")})
    assert r.accepted and r.holdings_after == 7
    b = book([pos(f"T{c}", 13_000) for c in "ABCDE"] + [pos("SQQQ", 10_000)], cash=25_000)
    assert run([buy("NEW", "mild")], b=b, mood=-0.5).accepted  # the bear fund isn't one of the 6 names


def test_unapproved_leveraged_funds_and_volatility_products_stay_banned():
    r = run([buy("ABCD")], assets={"ABCD": asset("ABCD", name="Direxion Daily Semis Bull 3X Shares")}, mood=0.5)
    assert "isn't on the approved list" in reasons(r)[0]
    assert "isn't on the approved list" in reasons(run([buy("UVXY")], mood=0.5))[0]
    assert "isn't on the approved list" in reasons(run([buy("TSLL")], mood=0.5))[0]


# -- wild cards, kinds, reasons, assets -------------------------------------

def test_wild_card_once_a_week_and_capped_at_strong():
    assert run([buy("AA", "strong", kind="wild_card")]).accepted
    assert "wild card has been played" in reasons(run([buy("AA", "mild", kind="wild_card")], wild_card_used=True))[0]
    r = run([buy("AA", "mild", kind="wild_card"), buy("BB", "mild", kind="wild_card")])
    assert len(r.accepted) == 1 and "wild card has been played" in reasons(r)[0]
    r = run([buy("AA", "total", kind="wild_card", catalyst="earnings_beat")])
    assert "tops out at a strong" in reasons(r)[0]


def test_wild_card_used_this_week():
    trades = [{"date": "2026-11-02", "kind": "wild_card", "status": "filled"}]
    assert v.wild_card_used_this_week(trades, "2026-11-05")
    assert not v.wild_card_used_this_week(trades, "2026-11-09")


def test_kind_required_and_leap_limit():
    assert "not a direct, sector, leap or wild card" in reasons(run([buy(kind="hunch")]))[0]
    r = run([buy(t, "mild", kind="leap") for t in ("AA", "BB", "CC", "DD")], b=book(cash=200_000))
    assert len(r.accepted) == 3 and "leaps today" in reasons(r)[0]


def test_tiered_slippage():
    thin = {"avg_dollar_volume": 30e6, "prior_dollar_volume": 30e6}
    r = run([buy("AA", "mild"), buy("BB", "mild")], liq={"AA": thin, "BB": LIQ})
    rate = {t["ticker"]: t["slippage_rate"] for t in r.accepted}
    assert rate == {"AA": config.SLIPPAGE_RESERVE_THIN, "BB": config.SLIPPAGE_RESERVE}
    recs = [{"filled_qty": 1, "filled_dollars": 10_000, "slippage_rate": 0.0025},
            {"filled_qty": 1, "filled_dollars": 10_000, "slippage_rate": 0.001},
            {"filled_qty": 0, "filled_dollars": 0, "slippage_rate": 0.001}]
    assert round(v.slippage_charge(recs), 2) == 35.0


def test_price_only_reasons_declined():
    assert "falling price is not news" in reasons(run([buy(reason="The share price has fallen, so in we go.")]))[0]
    assert "falling price is not news" in reasons(
        run([sell("MSFT", reason="Its shares dropped and the fund panicked.")], b=book([pos("MSFT", 10_000)])))[0]
    assert run([buy(reason="Oil prices fell, and the fund feels lighter.")]).accepted


def test_unknown_ticker_declined():
    r = run([buy("ZZZZ")], assets={"ZZZZ": None})
    assert not r.accepted and "not on the asset list" in reasons(r)[0]


def test_bad_ticker_shape():
    assert "not shaped like a ticker" in reasons(run([buy("not a ticker")]))[0]


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
    assert "under the $20M floor" in reasons(r)[0]
    r = run([buy()], liq={"AAPL": {"avg_dollar_volume": 60e6, "prior_dollar_volume": 600_000}})
    assert "more than 1%" in reasons(r)[0]
    assert "No trading volume" in reasons(run([buy()], liq={}))[0]


def test_paused_name():
    assert "paused" in reasons(run([buy()], paused=["AAPL"]))[0]


def test_duplicate_trade_same_day():
    r = run([buy(conviction="mild"), buy(conviction="mild")])
    assert len(r.accepted) == 1 and "Already buying" in reasons(r)[0]


def test_declined_leverage():
    assert v.declined_leverage(-0.5, [], []) == "bear"
    assert v.declined_leverage(0.5, [], []) == "bull"
    assert v.declined_leverage(0.1, [], []) is None
    assert v.declined_leverage(-0.5, [pos("SQQQ", 10_000)], []) is None
    assert v.declined_leverage(-0.5, [], [{"action": "buy", "ticker": "SPXU"}]) is None
    # Holding a bull fund on a grim morning still counts as declining the bear fund
    assert v.declined_leverage(-0.5, [pos("TQQQ", 10_000)], []) == "bear"
