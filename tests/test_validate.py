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


def trade(action="buy", ticker="AAPL", dollars=10_000, reason="The fund senses a crispness.", hid="h1"):
    return {"action": action, "ticker": ticker, "dollars": dollars, "reason": reason, "headline_id": hid}


def run(trades, b=None, day=1, assets=None, liq=None, paused=None):
    tickers = {t["ticker"] for t in trades}
    return v.validate(
        {"trades": trades},
        book=b or book(),
        day_number=day,
        assets=assets if assets is not None else {t: asset(t) for t in tickers},
        liquidity=liq if liq is not None else {t: LIQ for t in tickers},
        headline_links=LINKS,
        paused_names=paused,
    )


def reasons(r):
    return [d["reason"] for d in r.declined]


def test_simple_buy_accepted():
    r = run([trade()])
    assert [t["ticker"] for t in r.accepted] == ["AAPL"]
    assert r.accepted[0]["headline_link"] == LINKS["h1"]
    assert r.cash_after == 90_000


def test_unknown_ticker_declined():
    r = run([trade(ticker="ZZZZ")], assets={"ZZZZ": None})
    assert not r.accepted and "not on the asset list" in reasons(r)[0]


def test_bad_ticker_shape():
    r = run([trade(ticker="not a ticker")])
    assert "not shaped like a ticker" in reasons(r)[0]


def test_leveraged_etf_declined_by_list_and_name():
    r = run([trade(ticker="TQQQ")])
    assert "leveraged or inverse" in reasons(r)[0]
    r = run([trade(ticker="ABCD")], assets={"ABCD": asset("ABCD", name="Direxion Daily Semis Bull 3X Shares")})
    assert "leveraged or inverse" in reasons(r)[0]


def test_short_term_treasury_etf_allowed():
    r = run([trade(ticker="SHV")], assets={"SHV": asset("SHV", name="iShares Short Treasury Bond ETF")})
    assert r.accepted


def test_otc_declined():
    r = run([trade(ticker="ABCD")], assets={"ABCD": asset("ABCD", exchange="OTC")})
    assert "not a listed exchange" in reasons(r)[0]


def test_position_cap():
    r = run([trade(dollars=21_000)])
    assert "over 20%" in reasons(r)[0]
    r = run([trade(dollars=10_000)], b=book([pos("AAPL", 15_000)], cash=85_000))
    assert "over 20%" in reasons(r)[0]


def test_buy_more_than_cash_declined():
    r = run([trade(dollars=5_000)], b=book([pos(f"T{i}", 19_000) for i in range(5)], cash=4_000))
    assert "more than the $4,000 in cash" in reasons(r)[0]


def test_sells_fund_buys_in_same_run():
    b = book([pos(f"T{c}", 19_000) for c in "ABCDE"], cash=5_000)
    r = run([trade(ticker="NEW", dollars=15_000), trade("sell", "TA", 12_000, hid="h2")], b=b, day=10)
    assert [t["action"] for t in r.accepted] == ["sell", "buy"]


def test_sell_not_held_and_oversell():
    r = run([trade("sell", "MSFT", 5_000)])
    assert "does not hold" in reasons(r)[0]
    r = run([trade("sell", "MSFT", 50_000)], b=book([pos("MSFT", 10_000)], cash=90_000))
    assert "more than the" in reasons(r)[0]


def test_near_full_sell_closes_position():
    r = run([trade("sell", "MSFT", 9_900)], b=book([pos("MSFT", 10_000, qty="12.5")], cash=90_000))
    assert r.accepted[0]["close_all"] and r.accepted[0]["qty"] == "12.5"


def test_min_holdings_after_first_week():
    b = book([pos(f"T{c}", 15_000) for c in "ABCDE"], cash=25_000)
    assert run([trade("sell", "TA", 15_000)], b=b, day=3).accepted
    r = run([trade("sell", "TA", 15_000)], b=b, day=6)
    assert "fewer than 5" in reasons(r)[0]
    # A partial sell is fine
    assert run([trade("sell", "TA", 5_000)], b=b, day=6).accepted


def test_max_holdings():
    b = book([pos(f"T{c}", 9_000) for c in "ABCDEFGHIJ"], cash=10_000)
    r = run([trade(ticker="NEW", dollars=5_000)], b=b)
    assert "past 10 holdings" in reasons(r)[0]


def test_trade_limit():
    ts = [trade(ticker=t, dollars=5_000) for t in ("AA", "BB", "CC", "DD", "EE")]
    r = run(ts)
    assert len(r.accepted) == 4 and "Trade limit" in reasons(r)[0]


def test_min_order_size():
    assert "minimum" in reasons(run([trade(dollars=500)]))[0]


def test_reason_rules():
    assert "No reason" in reasons(run([trade(reason="")]))[0]
    assert "200 characters" in reasons(run([trade(reason="x" * 201)]))[0]
    assert "more than one sentence" in reasons(run([trade(reason="Bought it. Then More things.")]))[0]


def test_headline_must_be_from_this_morning():
    r = run([trade(hid="h99")])
    assert "not in this morning's news" in reasons(r)[0]


def test_liquidity_floor_and_volume_cap():
    r = run([trade()], liq={"AAPL": {"avg_dollar_volume": 10e6, "prior_dollar_volume": 10e6}})
    assert "under the $50M floor" in reasons(r)[0]
    r = run([trade(dollars=10_000)], liq={"AAPL": {"avg_dollar_volume": 60e6, "prior_dollar_volume": 600_000}})
    assert "more than 1%" in reasons(r)[0]
    r = run([trade()], liq={})
    assert "No trading volume" in reasons(r)[0]


def test_paused_name():
    assert "paused" in reasons(run([trade()], paused=["AAPL"]))[0]


def test_duplicate_trade_same_day():
    r = run([trade(dollars=5_000), trade(dollars=5_000)])
    assert len(r.accepted) == 1 and "Already buying" in reasons(r)[0]


def test_defensive_flag():
    assert run([trade(dollars=5_000)]).defensive  # 95% cash
    b = book([pos(f"T{c}", 18_000) for c in "ABCDE"], cash=10_000)
    assert not run([trade("sell", "TA", 2_000)], b=b, day=10).defensive


def test_garbage_dollars():
    assert "minimum" in reasons(run([trade(dollars="lots")]))[0]
