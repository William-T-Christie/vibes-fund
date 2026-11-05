# Vibes Fund

A fake $100,000 paper portfolio that Claude trades once each weekday on the mood of the morning's news headlines, tracked against SPY. The question the whole project answers: can a fund run on nothing but vibes beat the S&P 500?

Paper trading only. Fake money. Not investment advice.

**Status (Nov 5, 2026):** planning and design are done for now. The trading pipeline is built and tested against a fake Alpaca, but has not run against a real paper account yet. The site, Friday letter, factsheet and video are not built. The working name and look are Mood Ring Capital, direction A v3.

## The pipeline

| Path | What it does |
| --- | --- |
| `vibes/morning.py` | The morning trade in three steps (prepare, decide, trade), so each secret reaches only the step that needs it |
| `vibes/fetch_news.py` | Alpaca news plus general RSS, cut off at the run's start time, deduplicated, capped at 60 |
| `vibes/decide.py` | Runs Claude Code headless with every tool off and a JSON schema; retries once, then holds |
| `vibes/prompts/manager.md` | The Chairman's prompt. The version line at the top is dated on every change |
| `vibes/validate.py` | Compliance: every guardrail in the spec, as pure functions |
| `vibes/trade.py` | Sells first, then buys from real cash only; order IDs built from the date, ticker and side |
| `vibes/record.py` | Evening record: adjusted NAV, dividends credited, SPY total return, backfill, corporate action pauses |
| `vibes/metrics.py` | Every number on the site |
| `vibes/replay.py` | Private replay of past sessions on a simulated paper account (see `docs/replay.md`) |
| `vibes/scrub.py` | Fails the commit if anything in `data/vibes/` looks like a key |
| `.github/workflows/` | Morning, evening, Sunday health check, tests. Schedule or manual runs only; actions pinned to commit SHAs |
| `data/vibes/` | The JSON the site reads, plus `logs/YYYY-MM-DD/` |

```bash
uv sync
```

```bash
uv run pytest -q
```

Other commands: `vibes morning-prepare | morning-decide | morning-trade | evening | healthcheck | scrub`, plus `vibes reset --confirm` (wipes dry run data; refuses once live) and `vibes go-live --confirm`. A `PAUSED` file at the repo root stops trading; the evening record keeps running.

Choices the spec left open, made in code:
- **SPY baseline:** SPY's index starts at 100 at the inception-day open, since the fund deploys at 9:40, and it reinvests dividends on ex-dates.
- **Volume cap:** "no order above 1% of that day's volume" uses the prior session's dollar volume, because at 9:40 the current day has barely traded.
- **Headline links:** Claude cites a headline id, never a URL, and code maps the id to the link. A made-up link can't get in.
- **Trade outcomes:** a buy's outcome is the latest close vs its fill price. A sell's outcome is its fill price vs the latest close, so selling before a fall counts as a good call.
- **Dry run vs live:** `fund.json` holds the mode. Inception is set by the first fill.

## Where things are

| Folder or file | What it is |
| --- | --- |
| `docs/project-plan-and-functional-spec.md` | The full plan: decisions, fund rules, architecture, daily run, guardrails, data files, metrics, honesty rules, letters, weekly video, site functionality, operations, secrets, risks, next steps |
| `docs/name-theme-and-visual-design.md` | Naming, the four theme directions, the mood system, the cast, design elements, copy and voice samples |
| `docs/not-ai-design-rules.md` | The rulebook every design follows so nothing looks AI generated, with the A and B direction specs and a pre ship checklist |
| `docs/design-rules-summary.md` | Short version of the rules plus later additions: halftone everywhere, the Chairman's house portrait, the illustration review process |
| `docs/vibes-playbook.md` | How the Chairman turns headlines into trades: mood sets cash, conviction sizing, trade kinds, daily verdicts, when to sell. Approved and built |
| `docs/replay.md` | The private replay: running past days through the playbook to check its behavior. Results stay in `.replays/`, never published |
| `docs/decision-log.md` | Every decision made so far and what is still open. Read this first; it overrides older wording in the docs above |
| `docs/references.md` | The references and sources behind the design and the plan |
| `art/chairman/` | The Chairman's house portrait (SVG and previews) and the source that generates it |
| `design/mockups/` | All theme mockups as Claude Design artboards (A v1, A v2, A v3, B v1, C, D) |
| `design/sample-data.json` | The sample data every mockup uses |

## Live versions on claude.ai

These are private to William's account and are the editable originals. The files in this folder are snapshots from Nov 5, 2026.

- Project Plan and Functional Spec: https://claude.ai/artifact/2v9H586YPWYypPMSYfXPiR
- Name, Theme and Visual Design: https://claude.ai/artifact/5dwLyJ1SLvXqn84Ue2R955
- Not AI Design Rules: https://claude.ai/artifact/L5d6qNsrQ8k7QcgBADKfDm
- Theme mockups canvas: https://claude.ai/artifact/TAqu1fAGSiaPshGNC3yKM5
- Earlier plan (Jargon Index and Vibes Fund, superseded): https://claude.ai/artifact/6GbU3eMLo23kskeBRTEXGR

## How it will run (short version)

- GitHub Actions runs a morning trade at 9:40 AM ET and an evening record at 4:30 PM ET.
- Claude Code runs headless on the Claude subscription token (`CLAUDE_CODE_OAUTH_TOKEN`), with every tool turned off, and returns one JSON decision.
- Python validates every trade before any order reaches the Alpaca paper account.
- Results are written as JSON into the public site repo and read by static pages.
- Cost: $0 beyond the existing Claude plan.
- Results are kept honest with an adjusted NAV (slippage reserve, liquidity floor, dividends credited, no reruns).

Secrets (`ALPACA_KEY`, `ALPACA_SECRET`, `CLAUDE_CODE_OAUTH_TOKEN`) live only in GitHub Actions encrypted secrets. Never put them in this folder, in code, or in any committed file.
