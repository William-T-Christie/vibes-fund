import json

import pytest

from vibes import decide

GOOD = {"mood": {"label": "calm", "score": 0.3}, "summary": "Fine.", "trades": []}


def test_parse_structured_output():
    raw = json.dumps({"type": "result", "result": "", "structured_output": GOOD})
    assert decide.parse(raw)["mood"]["score"] == 0.3


def test_parse_result_text_with_fences():
    raw = json.dumps({"type": "result", "result": "```json\n" + json.dumps(GOOD) + "\n```"})
    assert decide.parse(raw)["summary"] == "Fine."


def test_parse_bare_text():
    assert decide.parse("Sure! " + json.dumps(GOOD))["trades"] == []


def test_parse_errors():
    with pytest.raises(decide.DecisionError):
        decide.parse(json.dumps({"result": "no json here"}))
    with pytest.raises(decide.DecisionError):
        decide.parse(json.dumps({"is_error": True, "result": "rate limited"}))
    with pytest.raises(decide.DecisionError):
        decide.parse(json.dumps({"result": '{"mood": {"label": "x"}, "trades": []}'}))


def test_retry_with_error_attached():
    prompts = []

    def caller(p):
        prompts.append(p)
        return "{broken" if len(prompts) == 1 else json.dumps({"result": json.dumps(GOOD)})

    d, attempts = decide.decide("PROMPT", caller)
    assert d["mood"]["label"] == "calm"
    assert len(attempts) == 2 and "could not be used" in prompts[1]


def test_two_failures_means_hold():
    def caller(p):
        raise decide.DecisionError("timeout")

    d, attempts = decide.decide("PROMPT", caller)
    assert d is None and len(attempts) == 2


def test_build_prompt_renders():
    book = {"nav": 100_000, "cash": 80_000,
            "positions": [{"ticker": "AAPL", "market_value": 20_000, "gain_pct": 1.5}]}
    heads = [{"id": "h1", "source": "Wire", "published": "2026-11-05T12:00:00Z", "title": "A {brace} headline",
              "tickers": ["AAPL"]}]
    p = decide.build_prompt(date="2026-11-05", day_number=3, book=book, headlines=heads, recent_reasons=["Old."])
    assert "day 3" in p and "A {brace} headline" in p and "| AAPL |" in p
    assert "prompt-version" not in p
    assert '"headline_id": "h3"' in p


def test_prompt_knows_the_weekday_and_wild_card():
    book = {"nav": 100_000, "cash": 100_000, "positions": []}
    heads = [{"id": "h1", "source": "Wire", "published": "t", "title": "x", "tickers": []}]
    fri = decide.build_prompt(date="2026-11-06", day_number=9, book=book, headlines=heads, recent_reasons=[])
    assert "Friday 2026-11-06" in fri and "it is Friday: play it today" in fri
    wed = decide.build_prompt(date="2026-11-04", day_number=7, book=book, headlines=heads, recent_reasons=[])
    assert "has not been played yet" in wed
    used = decide.build_prompt(date="2026-11-06", day_number=9, book=book, headlines=heads, recent_reasons=[],
                               wild_card_used=True)
    assert "already been played" in used


def test_prompt_version():
    assert decide.prompt_version().startswith("2026-")
