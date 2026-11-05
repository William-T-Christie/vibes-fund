# Vibes Fund: Decision Log

Snapshot as of Nov 5, 2026. Where this log and an older doc disagree, this log is current.

## Concept

- The fund trades on vibes from news headlines, not on personal inputs about an individual.
- Vibes only. No Billy Joel rival fund.
- The core question is whether a fund trading on nothing but vibes can beat SPY.
- All money is fake: a $100,000 Alpaca paper account. Results must still be what real money would have done, with no free wins. That is why the plan uses adjusted NAV, a 0.10% slippage reserve, a liquidity floor, dividends credited, and no reruns or backtests.
- It goes live as soon as the pipeline and site work. There is no quiet run and no launch date. A crash to $15 or a run to $1 million are both good content.

## How it runs

- Claude Code runs in GitHub Actions on William's Claude subscription token, not a paid API key, so the fund costs $0.
- Claude only picks trades and returns JSON. Code validates every trade and places every order.
- Order IDs are unique per date and ticker, so a retry can never trade twice. No trading happens after 11:00 AM ET.
- Each morning's decision is committed before orders fill, so the git history proves nothing was edited afterward.
- Secrets live only in GitHub Actions encrypted secrets.
  - Each secret goes only to the step that needs it.
  - Workflows never run on pull requests.
  - A scrub step blocks anything shaped like a key.
  - Paper keys only.
- Development timelines are not estimated. Building is done with Claude Code, not by hand.

## Vibes playbook

- Approved Nov 5 and built (prompt version 2026-11-05.2): mood sets cash, code sizes trades from a conviction level (Mild 5%, Firm 10%, Strong 15%, Total 20%), sells are Trim or Exit, trades are labeled Direct, Sector or Leap (at most 2 leaps a day), every holding gets a daily verdict, and a holding with no supporting headline for 15 trading days must be reaffirmed or trimmed.
- Never sells on price alone; Compliance declines reasons about a falling share price.

## Name

- The finalists are **Mood Ring Capital** and **Sentimental Value Partners**.
- "Fundamental Value Partners" is already a real firm, so the pun version is used instead.
- "Animal Spirits" is avoided because a popular podcast uses it.
- Mood Ring Capital is the working name in the current mockups.

## Theme

- The choice is narrowed to **A (Mood Ring Capital)** or **B (Sentimental Value Partners)**. C (Trading Terminal) and D (Cable Finance TV) are parked.
- **A v3 is the current lead.** It is a 1970s two color annual report: black ink plus one spot color, the day's mood ink.
  - Chivo only. Paper #F4F3EE, ink #161513.
- Changes made to A v3 on Nov 5:
  - **Halftone everywhere:** every mood color on the page is printed with the white dot screen, never flat.
  - **"Ahead or behind, day by day":** an interactive bar chart of the fund's lead over the S&P 500. Bars are printed in each morning's mood. Pointing at a day shows its numbers in a readout under the chart, and there are jump links to key moments.
  - **Investor letter:** rewritten longer, to fill its space, in the Chairman's dry voice, with a P.S. and a P.P.S. and a drawn signature.
  - **Board height:** the canvas board was made taller so the feedback coupon shows in full.
- B v2 has not been built yet. It is next in the design queue, built on the B spec in the rules doc.

## Mood system

- There is one mood per day: a score from -1 to +1 that Claude returns with its trades.
- Changed Nov 5: the mood now sets how much cash the fund may keep once the first week is over (Doom 30%, Nervous 20%, Unbothered 10%, Optimistic and Euphoric 5%). Code can't force buys, so a miss is printed in the trade log. See `docs/vibes-playbook.md`.
- The score falls into one of five bands:

| Band | Score | Color |
| --- | --- | --- |
| Doom | -1.0 to -0.6 | #2B2B2B |
| Nervous | -0.6 to -0.2 | #C98A1B |
| Unbothered | -0.2 to +0.2 | #4F8A5B |
| Optimistic | +0.2 to +0.6 | #2F6FA8 |
| Euphoric | +0.6 to +1.0 | #7B4FA8 |

## Cast

**The Chairman, Sir Peregrine Ashby.** He writes the trade log and the Friday letters.
- Small, diminutive, posh and British.
- Balding, with thin round spectacles and a long nose.
- Unimpressed and unflappable.
- The house portrait is final for now: `art/chairman/chairman-portrait.svg`. Reuse it rather than redrawing him.

**The Broker, Barry Kessler.** He hosts the Friday video.
- A gentle giant, the Chairman's opposite: "a Hagrid to the Chairman's Dumbledore."
- He has an original look, with no wild beard or long coat.
- He is terrified of the Chairman, and in the Meltdown state he has bulging veins.
- His character design has not been drawn yet.

## Weekly video

- The cartoon broker is animated in code by Claude and rendered to MP4. No video model is used.
- It stays hidden behind a `show_video` switch until William approves the character and a few episodes.

## Design process

- Every design follows the Not AI Design Rules. William adds rules over time as he spots new AI tells.
- Illustrations are not patched by editing coordinates and judging from code. The process is:
  1. Plan the pose and composition.
  2. Build hard parts as large studies first.
  3. Render each round at enlarged size and at page size.
  4. Get a fresh reviewer critique against the brief.
  5. Publish only after the review passes.

## Open

- [ ] Final name: Mood Ring Capital or Sentimental Value Partners.
- [ ] Final direction: A or B. This needs B v2 for a fair comparison.
- [ ] Design and approve the Broker, Barry Kessler.
- [ ] Headline source: free RSS, the Alpaca news feed, or both.
- [ ] Run name checks: web search, SEC adviser search, and a fake ticker that isn't a real symbol.
- [ ] Accounts: open the Alpaca paper account, run `claude setup-token`, and store the GitHub Actions secrets with secret scanning and two factor login turned on.
- [ ] Build the pipeline, dry run it, reset the paper account to $100,000, build the site, and go live.
