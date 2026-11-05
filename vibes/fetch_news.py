"""Read the morning's headlines: Alpaca's news feed plus a couple of general RSS feeds.

Only headlines published between the prior close and the moment the run started are kept,
so a late run never sees news it shouldn't. Headline text goes to the gitignored work folder
for Claude; only links and sources are committed, since the repo is public.
"""

from __future__ import annotations

import calendar
import re
from datetime import datetime, timezone
from typing import Callable

from . import config


def _norm_title(t: str) -> str:
    return re.sub(r"[^a-z0-9 ]", "", t.lower()).strip()


def from_alpaca(client, start: datetime, end: datetime) -> list[dict]:
    raw = client.news(start.isoformat(), end.isoformat(), limit=config.MAX_HEADLINES * 2)
    out = []
    for n in raw:
        out.append({
            "title": (n.get("headline") or "").strip(),
            "source": n.get("source") or "alpaca",
            "link": n.get("url") or "",
            "published": n.get("created_at"),
            "tickers": n.get("symbols") or [],
        })
    return out


def from_rss(feeds: list[str], start: datetime, end: datetime,
             parse: Callable | None = None) -> list[dict]:
    if parse is None:
        import feedparser
        parse = feedparser.parse
    out = []
    for url in feeds:
        try:
            feed = parse(url)
        except Exception:
            continue  # feeds break or move without notice; skip quietly
        source = (getattr(feed, "feed", {}) or {}).get("title") or url
        for e in getattr(feed, "entries", []) or []:
            ts = e.get("published_parsed") or e.get("updated_parsed")
            if not ts:
                continue
            published = datetime.fromtimestamp(calendar.timegm(ts), tz=timezone.utc)
            if not (start <= published < end):
                continue
            out.append({
                "title": (e.get("title") or "").strip(),
                "source": source,
                "link": e.get("link") or "",
                "published": published.isoformat(),
                "tickers": [],
            })
    return out


def clean(items: list[dict], cap: int = config.MAX_HEADLINES) -> list[dict]:
    """Drop empties and duplicates (by link and by normalized title), newest first, capped."""
    seen_links, seen_titles, out = set(), set(), []
    items = sorted(items, key=lambda x: x.get("published") or "", reverse=True)
    for it in items:
        if not it["title"] or not it["link"].startswith("http"):
            continue
        nt = _norm_title(it["title"])
        if it["link"] in seen_links or nt in seen_titles:
            continue
        seen_links.add(it["link"])
        seen_titles.add(nt)
        out.append(it)
        if len(out) >= cap:
            break
    for i, it in enumerate(out, 1):
        it["id"] = f"h{i}"
    return out


def fetch(client, start: datetime, end: datetime) -> list[dict]:
    items: list[dict] = []
    if config.USE_ALPACA_NEWS and client is not None:
        try:
            items += from_alpaca(client, start, end)
        except Exception:
            pass  # free-plan access unconfirmed; RSS still runs
    items += from_rss(config.RSS_FEEDS, start, end)
    return clean(items)


def public_log(headlines: list[dict]) -> list[dict]:
    """What gets committed: ids, links, sources and times. Never the headline text."""
    return [{k: h[k] for k in ("id", "source", "link", "published", "tickers")} for h in headlines]
