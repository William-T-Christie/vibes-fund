# Vibes Fund: Private Replay

Nov 5, 2026

The replay runs past trading days through the current playbook to check how it **behaves**: whether it stays invested, how often Compliance says no, whether verdicts rotate the book, and whether the jokes repeat. It is not a track record, and it is never published.

## How it works

For each past session, in order:

1. **Morning.** Alpaca headlines from the prior close to 9:40 ET that day, nothing later. Claude decides with the real prompt, and the real Compliance code checks it.
2. **Fills.** Accepted orders fill at that morning's real 9:40 price on a simulated paper account (cash only, never margin), with the 0.10% slippage reserve charged.
3. **Evening.** The book is marked at the real close, dividends are credited, SPY is tracked with dividends reinvested, and the mood's cash target is checked.

The book carries forward day to day. Each run is saved under `.replays/<name>/`, which is gitignored: `state.json`, one Claude reply per day in `claude/`, and `report.md` plus `report.json` at the end. Rerunning the same name resumes where it stopped and reuses Claude's earlier replies, so a crash costs nothing.

## Why the result vs SPY isn't a verdict on the playbook

- **Claude may already know** how some of these days turned out, if they fall inside its training data. That would make its picks look smarter than real-time calls. Start the window after the model's training cutoff where you can.
- **One run is one sample.** Run it again under a different name to see the spread.
- **100 days is short**, even for a real fund.
- **Market news only.** Alpaca keeps news history; the BBC and NPR feeds don't. So a replay misses the general world news that drives many Sector and Leap trades.

## The rules

- Results never go into `data/vibes/`, onto the site, or into a commit.
- Change the prompt only to fix behavior (always in cash, the same joke twice, broken leaps), never to raise the replayed return. Otherwise the live fund's record stops being a fair test.

## Running it

One-time: store the Alpaca **paper** keys in the macOS Keychain. Each command prompts for the value and shows nothing:

```bash
security add-generic-password -a "$USER" -s vibes-alpaca-key -w
```

```bash
security add-generic-password -a "$USER" -s vibes-alpaca-secret -w
```

Start small to check that the news history works on the free plan (5 Claude calls):

```bash
scripts/with-keys.sh uv run vibes replay --name first-look --days 5
```

Then the full run (about 100 Claude calls on your subscription, run one after another; expect an hour or two):

```bash
scripts/with-keys.sh uv run vibes replay --name run-1 --days 100
```

Options: `--end YYYY-MM-DD` (default yesterday) and `--start YYYY-MM-DD` to pin the window, for example to begin after the model's training cutoff. Use a new `--name` for each extra run.
