# Vibes Fund: The Vibes Playbook

Nov 5, 2026 · Approved by William and built (prompt version 2026-11-05.2)

## Summary

The playbook is how a morning of headlines becomes trades. Today the prompt only states the rules, so Claude improvises everything else. In the one real test it put 27% of the fund to work and left 73% in cash. This draft gives the Chairman a method he follows every morning, and moves the parts that should be consistent (sizing, how invested to be) into code.

The method in one line: **read the room, review the book, find the story, size by conviction.**

Vibes only. No price charts, momentum, stop losses or backtests. The fund reacts to the news and nothing else, and it never sells because a price fell, only because the vibe changed.

## Decisions (all approved Nov 5)

- [x] **Mood sets how invested the fund is** (section 1). This changes the decision log, where mood is display only. Recommended: yes, since it gives the mood ring a real job.
- [x] **Code sizes every trade from a conviction level** (section 4), instead of Claude picking dollar amounts. Recommended: yes.
- [x] **Leaps:** allow second-order trades, at most 2 a day (section 3). Recommended: yes, since that's where most of the comedy is.
- [x] **Book review:** Claude gives every holding a one-word verdict each morning (section 2). Recommended: yes; it costs little and gives the site a "still believes" column.
- [x] **Fading vibes:** a holding with no supporting headline for 15 trading days must be reaffirmed or trimmed (section 5). Recommended: yes, so the book doesn't go stale.

## 1. Read the room

Claude reads all the headlines first and sets the morning's mood before looking at any single story. It returns a score from -1 to +1, as now.

**Proposal: the mood sets how much cash the fund keeps.**

| Mood | Score | Most cash allowed | In words |
| --- | --- | --- | --- |
| Doom | -1.0 to -0.6 | 30% | Battens down. The only band where a big cash pile is in character |
| Nervous | -0.6 to -0.2 | 20% | Keeps some powder dry |
| Unbothered | -0.2 to +0.2 | 10% | Business as usual |
| Optimistic | +0.2 to +0.6 | 5% | Nearly all in |
| Euphoric | +0.6 to +1.0 | 5% | All in, with a small reserve for dignity |

- The 30% cap in the fund rules stays the hard limit. The band sets a target under it.
- Code can't force buys, since Claude picks every trade. So when cash ends above the band's limit, the trade log shows it as a flagged line, for example: "The Chairman felt Euphoric and remained 41% in cash." It's honest, and it's a joke the fund earned.
- During the first week the targets are not checked, since 4 trades a day can't fill the book on day 1.

If you'd rather keep mood display only, the fallback is one fixed rule: at least 70% invested after the first week, whatever the mood.

## 2. Review the book

Before any new idea, the Chairman reviews what he already owns. To do this, each holding in the prompt gains three fields it doesn't have today:

- **Thesis:** the reason it was bought, in the Chairman's own words from the trade log
- **Held:** trading days since it was bought
- **Last support:** the last day a headline backed it up

Then each holding gets one verdict, returned in a new `book` field:

| Verdict | Meaning | What happens |
| --- | --- | --- |
| Intact | Nothing today changes the thesis | Hold |
| Strengthened | Today's news backs it up | Hold or add, up to the 20% cap |
| Weakened | The news has cooled on it | Trim, or note it and hold |
| Dead | Today's news contradicts the thesis | Sell all |

The site can show the verdicts as a "Still believes?" column in Holdings.

## 3. Find the story

The Chairman picks the headlines that move him, 1 to 3 on most days. Each trade is one of three kinds, and Claude labels which:

| Kind | Rule | Example |
| --- | --- | --- |
| Direct | The company is in the headline | A chipmaker beats earnings: buy the chipmaker |
| Sector | The story is about an industry, not one company | Oil supply worries: buy the energy sector fund |
| Leap | One logical step from the story, explainable in one sentence | Record coffee prices: buy the biggest tea seller, since the nation will switch |

- **Leaps:** at most 2 a day, and one step only. "Rain in Brazil, so coffee, so cafés, so the landlords of cafés" is three steps and gets declined.
- **General news** (BBC, NPR) usually becomes Sector or Leap trades, since it rarely names a company.
- **Where to look:** large US companies and the standard sector funds come first, so trades clear the liquidity floor. The prompt lists the sector funds so Claude uses the same ones every time: XLK tech, XLF financials, XLE energy, XLV health care, XLY consumer discretionary, XLP consumer staples, XLI industrials, XLB materials, XLU utilities, XLRE real estate, XLC communication, GLD gold.
- **Stories about harm to people** produce no trade and no joke. This rule is unchanged.

## 4. Size by conviction

Claude stops choosing dollar amounts. It picks a conviction level, and code turns that into dollars from the morning's NAV.

| Conviction | Share of NAV | Trade log label |
| --- | --- | --- |
| Mild | 5% | "a mild conviction" |
| Firm | 10% | "a firm conviction" |
| Strong | 15% | "a strong conviction" |
| Total | 20% (the cap) | "total conviction" |

- **Adding** to a holding: the conviction is the size of the addition, and the 20% cap still applies to the result.
- **Selling:** a sell is a Trim (half the position) or an Exit (all of it). No dollar amounts.
- **Short on cash:** buys are placed strongest first. If cash runs out, the last buy shrinks to the cash left, as long as that's still at least $1,000. Otherwise it's declined. This is a fixed rule, not a guess, so it fits "never fixed by guessing."
- **Rounding:** dollars round down to the nearest $100, so the log reads cleanly.

The labels go into the trade log, so a reason reads like: "Bought XLE on a firm conviction that the world will need more oil than it admits."

## 5. When to sell

- A **Dead** verdict always means Exit.
- A **Weakened** verdict means Trim, unless the Chairman says in one sentence why he's holding.
- **Fading vibes:** a holding with no supporting headline in 15 trading days is flagged in the prompt as fading. The Chairman must reaffirm it, which counts as a verdict with a sentence, or trim it. This keeps the book from turning into a quiet index fund.
- **Making room:** at 10 holdings, a new idea needs an Exit first.
- **The 5 holding minimum:** an Exit is allowed when new names bought the same morning keep the fund at 5 or more, or when the fund is already under 5 and the morning still leaves it with more names than it started.
- **Never on price alone.** A falling price is not news. "The share price has fallen" is not an allowed reason; Compliance declines it.

## 6. Quiet mornings

- If no headline reaches Firm conviction, the fund makes no new buys. The book review still runs, so Dead verdicts still sell.
- Holding still is a fine outcome and gets one line in the log, as now.

## 7. The first week

- **Day 1:** up to 4 buys, Firm or Strong, so the fund opens 40 to 60% invested.
- **Days 2 to 5:** keep building toward 5 holdings and the mood's cash target.
- **From day 6:** the 5 holding minimum and the mood cash targets apply.

## What changes in the code

| Where | Change |
| --- | --- |
| `prompts/manager.md` | Rewritten around the four steps, the trade kinds, conviction labels, sector fund list and verdicts. Version bumped and dated |
| `decide.py` schema | Trades gain `kind` and `conviction`, sells use `trim` or `exit` instead of dollars, and there's a new `book` list of verdicts |
| `morning.py` prepare | Each holding carries its thesis, days held and last support, taken from `trades.json` |
| `validate.py` | Dollars come from conviction and NAV. New checks: at most 2 leaps, a valid conviction, no price-only reasons, and a short-cash buy shrinks to fit |
| `record.py` / `summary.json` | Logs whether the fund hit the mood's cash target, plus the day's verdicts for the site |
| Tests | New fixtures for each rule above |

## Not in this playbook

- No price, chart or momentum signals. That would stop being vibes.
- No stop losses. The Chairman's convictions don't come with exits.
- No backtests or tuning against past news, per the honesty rules. Every prompt change is dated and listed on the methodology page instead.
