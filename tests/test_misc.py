import time as _time
from datetime import datetime, timezone

from vibes import clock, config, fetch_news, scrub


def et(y, m, d, hh, mm):
    return datetime(y, m, d, hh, mm, tzinfo=clock.ET)


def test_morning_window_both_crons_dst_and_standard():
    # Daylight time: 13:40 UTC = 9:40 ET (trade), 14:40 UTC = 10:40 ET (open, but stopped by "done")
    assert clock.morning_window(datetime(2026, 7, 1, 13, 40, tzinfo=timezone.utc)) == "open"
    # Standard time: 13:40 UTC = 8:40 ET (early), 14:40 UTC = 9:40 ET (trade)
    assert clock.morning_window(datetime(2026, 12, 1, 13, 40, tzinfo=timezone.utc)) == "early"
    assert clock.morning_window(datetime(2026, 12, 1, 14, 40, tzinfo=timezone.utc)) == "open"
    assert clock.morning_window(et(2026, 12, 1, 11, 0)) == "late"


def test_evening_ready():
    assert not clock.evening_ready(datetime(2026, 12, 1, 20, 30, tzinfo=timezone.utc))  # 3:30 PM EST
    assert clock.evening_ready(datetime(2026, 12, 1, 21, 30, tzinfo=timezone.utc))


def test_clean_dedupes_and_caps():
    items = [
        {"title": "Stocks Rise!", "source": "a", "link": "https://a/1", "published": "2026-11-05T13:00:00Z"},
        {"title": "stocks rise", "source": "b", "link": "https://b/1", "published": "2026-11-05T12:00:00Z"},
        {"title": "Other", "source": "a", "link": "https://a/1", "published": "2026-11-05T11:00:00Z"},
        {"title": "", "source": "a", "link": "https://a/2", "published": "2026-11-05T11:00:00Z"},
        {"title": "Fine", "source": "a", "link": "ftp://x", "published": "2026-11-05T11:00:00Z"},
    ] + [{"title": f"T{i}", "source": "c", "link": f"https://c/{i}", "published": "2026-11-05T10:00:00Z"}
         for i in range(100)]
    out = fetch_news.clean(items)
    assert len(out) == config.MAX_HEADLINES
    assert out[0]["link"] == "https://a/1" and out[0]["id"] == "h1"
    assert sum(1 for o in out if o["title"].lower().startswith("stocks rise")) == 1


def test_rss_window_and_public_log_hides_titles():
    class Feed:
        feed = {"title": "Wire"}
        entries = [
            {"title": "In window", "link": "https://w/1", "published_parsed": _time.gmtime(1_800_000_000)},
            {"title": "Too new", "link": "https://w/2", "published_parsed": _time.gmtime(1_900_000_000)},
            {"title": "No date", "link": "https://w/3"},
        ]

    start = datetime.fromtimestamp(1_799_990_000, tz=timezone.utc)
    end = datetime.fromtimestamp(1_800_010_000, tz=timezone.utc)
    got = fetch_news.from_rss(["x"], start, end, parse=lambda u: Feed())
    assert [g["title"] for g in got] == ["In window"]
    pub = fetch_news.public_log(fetch_news.clean(got))
    assert "title" not in pub[0] and pub[0]["source"] == "Wire"


def test_scrub(tmp_path, monkeypatch):
    (tmp_path / "ok.json").write_text('{"nav": 100000}')
    assert scrub.scan([tmp_path]) == []
    (tmp_path / "bad.json").write_text('{"oops": "sk-ant-oat01-' + "a" * 40 + '"}')
    assert scrub.scan([tmp_path])
    monkeypatch.setenv("ALPACA_SECRET", "supersecretvalue123")
    (tmp_path / "bad.json").write_text("supersecretvalue123")
    assert any("value of a secret" in h for h in scrub.scan([tmp_path]))
