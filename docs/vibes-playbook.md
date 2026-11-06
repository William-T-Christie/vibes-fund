# Vibes Fund: The Vibes Playbook

Nov 6, 2026 · Approved by William and built (prompt version 2026-11-06.1). Sections 1 to 7 below are the original Nov 5 draft; the revision sections above them override any number that differs.

## Summary

The playbook is how a morning of headlines becomes trades. Today the prompt only states the rules, so Claude improvises everything else. In the one real test it put 27% of the fund to work and left 73% in cash. This draft gives the Chairman a method he follows every morning, and moves the parts that should be consistent (sizing, how invested to be) into code.

The method in one line: **read the room, review the book, find the story, size by conviction.**

Vibes only. No price charts, momentum, stop losses or backtests. The fund reacts to the news and nothing else, and it never sells because a price fell, only because the vibe changed.

## Revision after the first replay (prompt 2026-11-05.3)

A private 100-day replay (`docs/replay.md`) showed three behavior problems. These changes fix how the fund reads the news and stop losses it caused itself. They were not tuned to raise the replayed return.

| Problem in the replay | Change |
| --- | --- |
| Trims pushed cash over the 5% target, so the fund bought the same names back: 25 trims, 22 adds, only 4 exits, 3.7x turnover | Sale proceeds from the last 3 trading days don't count against the mood's cash limit. Adds need a Strengthened verdict that morning, enforced in code |
| The mood ran only from -0.35 to +0.4, so the site would be blue or green 92 days in 100 | The prompt gives anchors for -0.8, -0.4, 0, +0.4 and +0.8, scores the news before the book, and says to use the whole scale |
| 7 of 36 buys followed analyst notes rather than news | Events outrank opinions: a reason built on a rating or price target is capped at Mild and can never be an add, enforced in code |

## Earnings drift (prompt 2026-11-05.4)

After a company beats estimates and raises guidance, its price tends to keep drifting the way of the news for weeks. It is the best documented news effect there is, and it is still trading on the news. Approved by William Nov 5.

- Every trade carries a `catalyst`: `earnings_beat`, `earnings_miss`, `event` or `opinion`.
- Total conviction is reserved for an earnings beat. The fund never buys on an earnings miss.
- A position opened on an earnings beat has a 30 trading day drift window. Inside it, the position can only be sold on a Weakened or Dead verdict, and the fading clock doesn't run.
- An earnings miss on a holding is Weakened at least; a guidance cut is Dead.
- Any trim needs that morning's verdict to be Weakened or Dead. Exits to make room, or to end a fading holding, need no verdict.

**What the private replays showed** (`docs/replay.md`; one run each, descriptive only):

| Run | Window | Prompt | Fund vs SPY | Trims | Adds | New positions | Exits | Mood range |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | Jun 15 to Nov 4 | .2 | -7.3% vs +2.5% | 25 | 22 | 14 | 4 | -0.35 to +0.40 |
| 2 | Jun 15 to Nov 4 | .3 | -0.4% vs +2.5% | 28 | 19 | 15 | 5 | -0.40 to +0.35 |
| 3 | Jan 21 to Jun 12 | .4 | +1.3% vs +9.4% | 9 | 11 | 23 | 13 | -0.55 to +0.55 |

- The churn is fixed by the trim rule, not by the cash exemption: run 3 rotated (22 names, 13 exits) instead of trimming and rebuying.
- Drift did not pay in run 3: names opened on an earnings beat lost $4,257 in all, while names opened on other events made $5,998. Eleven names in one run is far too few to judge the effect either way.
- The fund held up better than SPY in the March selloff and lagged the April to June rebound.
- The mood still never reached Doom or Euphoric. The live fund also reads general news, which may widen it; revisit after the dry run.

## High conviction and leverage (prompts 2026-11-05.5 and 2026-11-06.1)

William asked for more volatility: a fund that clearly beats or clearly trails SPY, and makes the occasional crazy bet, is a better show than one that drifts a few points behind. More volatility does not raise the expected result; it widens the range of outcomes. Approved Nov 5 and 6.

| Rule | Before | Now |
| --- | --- | --- |
| Holdings | 5 to 10 | 3 to 6 (a leveraged fund doesn't count toward the 6) |
| Most in one name | 20% | 35% |
| Mild, Firm, Strong, Total | 5, 10, 15, 20% | 10, 20, 30, 35%; Strong is the normal size for a real event |
| Most cash by mood | Doom 30% to Euphoric 5% | Doom 50%, Nervous 30%, Unbothered 15%, Optimistic 5%, Euphoric 0% |
| Leaps | 2 a day | 3 a day, plus one wild card a week, played by Friday, up to Strong |
| Liquidity floor | $50M a day | $20M a day |
| Slippage reserve | 0.10% | 0.10%, or 0.25% for names under $200M a day |

**Leveraged funds.** Only an approved list of broad and sector index funds (bull: QLD, SSO, TQQQ, UPRO, SPXL, TNA, SOXL, TECL, FAS, ERX, LABU; bear: PSQ, SH, QID, SDS, SQQQ, SPXU, SPXS, TZA, SOXS, FAZ, LABD). Single-stock leveraged funds and volatility products stay banned. Bull funds only on mornings at +0.4 or better, bear funds at -0.4 or worse; one at a time, Mild or Firm. When the mood crosses zero the other way, Compliance sells it. On an extreme morning the Chairman is expected to buy one; if he doesn't, the trade log prints "The Chairman felt Doom and declined the bear fund."

**Shorts** stay out for now: losses are uncapped, Alpaca's paper account doesn't charge borrow fees (so it would flatter results), and it needs margin. The bear funds cover the downside bet.

**Replays.** Run 4 (prompt .5, Jan 21 to Jun 12) doubled volatility to 31% against SPY's 14%, with a -15.6% drawdown, but never used a leveraged fund or the wild card, even with 12 mornings at -0.4 or worse. Prompt .6 makes both expected rather than optional. Run 5 (prompt .6, same window) used them: 6 leveraged trades, no leverage declined, 16 wild cards, and the first Doom and Euphoric mornings (range -0.65 to +0.65). It finished +11.6% against SPY's +9.4%, the first run ahead, but was ahead on only 12 of 100 days, swung at 32% volatility with a -13.3% drawdown, and turned over 11.9 times its value ($1,278 of slippage reserve). The lead came from one stock: Sandisk, bought on an earnings beat, made $21,800, while leveraged funds lost $4,600, wild cards $2,800 and other events $2,300. A wilder fund, not yet a better one.

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
