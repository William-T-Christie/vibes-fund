# Vibes Fund: Project Plan and Functional Spec

Nov 5, 2026 · @William

## Summary

The Vibes Fund is a $100,000 paper portfolio that Claude trades once each weekday from the morning's headlines, tracked live against SPY, for $0 a year. It runs on GitHub Actions, places paper orders through Alpaca, and calls Claude through your existing subscription instead of a paid API key.

**The question:** can a fund run on nothing but good vibes beat SPY, the 500 biggest companies in America? Every page, stat and letter answers that one question.

- **What visitors see:** a fund page that opens on an "Are vibes beating SPY?" scoreboard, then the NAV line vs SPY, holdings, a deadpan trade log, Friday letters to investors, a quarterly factsheet, and a weekly cartoon broker video once it looks presentable.
- **What it costs:** nothing beyond the Claude plan you already pay for.
- **What it takes:** a few Claude Code sessions to build the pipeline and the site. It goes live as soon as both work, with no waiting period.
- **What comes next:** design, then implementation. This doc defines what the fund does; how it looks is the next phase.

## Decisions

Nine decisions are locked and two are still open.

| Decision | Choice | Why |
| --- | --- | --- |
| Signal | Vibes from news headlines, not personal inputs | Keeps the joke simple: the fund reacts to the world, and the reasoning is the punchline |
| Claude access | Claude Code in GitHub Actions on your subscription token | Makes the fund free and keeps all trading logic in tested code |
| Model | Claude Sonnet 5.5 | Strong enough for the voice, light on usage limits |
| Broker | Alpaca Paper Trading API | Free, real market fills, no brokerage account needed |
| Hosting | JSON in the public site repo, read by static pages | No server or database to pay for |
| Format | Vibes only, no Billy Joel rival fund | Keeps the project focused on one fund and one joke |
| Weekly video | Original cartoon broker, animated in code by Claude and rendered to MP4 each Friday | Free and automatic; no video model available on either subscription; no real person's likeness |
| Go live | As soon as the pipeline and site work; no quiet run, no launch date | It's supposed to be crazy; a crash to $15 or a run to $1 million are both good content |
| Fairness | Adjusted NAV: slippage reserve, liquidity floor, dividends credited, no reruns | Fake money, but results must be what real money would have done; no free win vs SPY |

**Open:**

- [x] Vibes only, or Vibes vs the Billy Joel Fund head to head on one chart
- [ ] Headline source: free RSS feeds only, or Alpaca's news feed if the free plan includes it (checked during setup)
- [ ] Fund name and persona for the site (Vibes Capital Management is the working name)
- [x] Optional: a weekly recap from an original character, a stressed out, a little overweight stockbroker. Free path: a cartoon drawn in code that sweats harder as the fund falls, reading Claude's Friday script in the browser's built in voice, fully automatic. Paid path: Google AI Pro ($19.99 a month) includes Veo video in its Flow tool, about 8 second clips made by hand each week. The host announces what the fund did, never tells viewers to buy or sell.

**Headline source options**

|  | Free RSS feeds | Alpaca news feed |
| --- | --- | --- |
| Pros | No account; mix of business and general news gives broader vibes; easy to add or swap sources | Same keys as trading; every story is tagged with tickers, so fewer made up or wrong tickers; one clean, timestamped format; history back to 2015 for testing the prompt |
| Cons | Feeds break or move without notice; no ticker tags, so Claude must map stories to companies; timestamps and formats vary by publisher | One source (Benzinga), market news only, so vibes skew toward finance headlines; free access needs confirming on the Basic plan |

Lean: Alpaca as the main feed if it's free, plus one or two general RSS feeds so the fund can still react to the wider world.

Source: [Alpaca News API](https://alpaca.markets/docs/news-api)

**Name and persona ideas**

The name should work as a LinkedIn post title and as the joke in one line. Shortlist:

| Name | Why it works | Watch out |
| --- | --- | --- |
| Mood Ring Capital | The daily mood score becomes a color, so the site literally changes color with the fund's feelings; strongest visual hook | Needs the design to lean into color |
| Priced In Partners | Finance people instantly get the joke; every trade reason can end with "and it's not priced in yet" | Lands less with non finance visitors |
| Headline Risk Capital | A real finance term turned into a strategy; says exactly what the fund does | Slightly dry |
| Gut Feeling Partners | Plain English, anyone gets it in a second | Generic; easy to forget |
| Read the Room Capital | Fits a fund that trades on the room's mood each morning | Weaker as a short name |
| Hot Take Holdings | Every trade is a hot take; great for share cards ("Today's hot take: sell the airlines") | Sounds more like a podcast than a fund |
| Conviction Without Evidence Fund | The funniest as a full title; honest about the strategy | Too long for a card or tab |
| Vibes Capital Management | Current working name; clear and safe | The least memorable |

**Persona options**

- **An old money portfolio manager** with a full name and a portrait, who takes vibes with total seriousness. Highest comedy, most shareable.
- **"The Desk"**, an unnamed institutional voice ("The Desk notes rising optimism in the cereal sector"). Dry and polished.
- **Openly Claude as PM**, framed as an AI experiment. Most honest and the best recruiter story, least funny on its own.

**Tagline ideas:** "Past vibes are no guarantee of future vibes." "Investing on feelings since 2026." "Fake money. Real conviction."

Lean: Mood Ring Capital with the old money manager, since the color shifting site gives the design phase a clear direction. Check that any fake ticker you give it isn't a real listed symbol.

## Fund rules

The fund is long only and concentrated, so the chart moves and every trade is easy to explain. Code enforces every rule; Claude is told the rules but never trusted to follow them.

| Rule | Setting |
| --- | --- |
| Starting capital | $100,000 paper; inception day is go live day |
| What it can buy | US listed stocks and ETFs only, plus an approved list of leveraged index funds gated by the mood (added Nov 6). No options, crypto, shorts, or margin |
| Positions | 3 to 6 holdings after the first week (changed Nov 6; see the decision log) |
| Position cap | 35% of NAV per name (changed Nov 6) |
| Cash | 0% to 30% of NAV; above 30% counts as a "defensive" call and must be explained |
| Trades per day | Up to 4 buys or sells, so the log stays readable |
| Order type | Market orders, sized in dollars, placed once a day at 9:40 AM ET |
| Holding period | No minimum; Claude can flip a name the next day if the vibes turn |
| Benchmark | SPY, total return from the same inception day |

## Architecture

Claude only picks trades; plain Python running in GitHub Actions does the reading, checking, trading and publishing.

&#91;embedded content: architecture · 2 daily runs, 3 outside services\]

Only the morning run calls Claude. The evening run is pure code, so a Claude outage never breaks the chart.

**Repo layout**

```text
.github/workflows/  morning.yml, evening.yml, letter.yml, healthcheck.yml
vibes/              fetch_news.py, decide.py, validate.py, trade.py, record.py, metrics.py
vibes/prompts/      manager.md, letter.md, video_script.md
vibes/video/        broker animation, voice and render scripts
data/vibes/         the JSON the site reads, plus logs/
tests/              validation and metrics tests on fixture data
```

## Daily run

Each trading day has two runs: a morning trade and an evening record. Splitting them means the published NAV uses full market closing prices, since Alpaca's free plan only shows the whole market on a 15 minute delay.

**Morning trade, 9:40 AM ET**

1. **Gate.** Ask Alpaca's market clock whether the market is open today. Holidays and weekends end the run quietly. If Alpaca already shows orders from today, or it's past 11:00 AM ET, stop, so a retry never trades twice and a late run never trades on stale news.
2. **Read the news.** Pull headlines published between yesterday's close and the moment the run started. Drop duplicates, keep title, source, link and time, cap at about 60 items.
3. **Load the book.** Pull current positions, cash and buying power from the Alpaca paper account.
4. **Decide.** Run Claude Code headless, with every tool turned off, on the headlines, the book and the fund rules. It returns one JSON object: trades, sizes, reasons, and today's mood.
5. **Validate.** Code checks every ticker, size and rule (see Guardrails). Invalid trades are dropped and logged, never fixed by guessing.
6. **Trade.** Place the surviving orders as market orders, then wait for fills.
7. **Save.** Commit the decision and raw Claude output before orders fill, then commit the fills, so the git history proves nothing was changed afterward.

**Evening record, 4:30 PM ET**

1. **Mark.** Read account equity, positions and SPY's close.
2. **Compute.** Update NAV history, returns and every metric the site shows.
3. **Publish.** Commit the JSON files. The site reads them on next load.

**When something breaks**

| Failure | What happens |
| --- | --- |
| No headlines came back | Hold all positions; log "Quiet morning. The fund meditated." |
| Claude call fails or times out | Retry once, then hold; log "Manager out of office." |
| Claude returns broken JSON | Retry once with the error attached, then hold |
| A ticker fails validation | Drop that trade only; the rest go through |
| Alpaca rejects an order | Log the reason; no retry until tomorrow |
| The run starts late | Trade if it starts before 11:00 AM ET; later, hold and log "The manager overslept." |
| Evening run fails | Next evening run backfills the missed day |

## Claude's job

Claude does one thing: read the morning, pick the trades, and explain each in one sentence. Everything else is code.

**What it gets**

- Today's date and the fund's day number since inception
- Headlines with source, link and time
- Current holdings with cost basis, today's weight and gain or loss
- Cash and NAV
- The fund rules, written out in plain words
- The last 5 trade reasons, so it stays consistent and doesn't repeat jokes

**What it returns**

```json
{
  "mood": { "label": "cautiously euphoric", "score": 0.6 },
  "summary": "One sentence on the morning as the fund sees it.",
  "trades": [
    {
      "action": "buy",
      "ticker": "XYZ",
      "dollars": 12000,
      "reason": "One deadpan sentence in the fund manager voice.",
      "headline_link": "https://..."
    }
  ],
  "holds": "Optional one sentence on why nothing else moved."
}
```

**The voice**

"Voice" here means the writing tone of trade reasons and letters. There is no video presenter in the plan.

- A serious fund manager who takes vibes with total conviction. The joke is the confidence, not wacky language.
- One sentence per trade. Paraphrase the headline in its own words and link the source; never quote it.
- Jokes land on the fund, never on real people, tragedies, or anyone's misfortune. Bad news about people means no trade and no joke.
- Mood score runs from −1 (doom) to +1 (euphoria) and becomes the "today's mood" stat on the site.

**How it runs**

The workflow installs Claude Code, then calls it in headless mode with the prompt and data files, asking for JSON output on the Sonnet 5.5 model. Auth comes from the `CLAUDE_CODE_OAUTH_TOKEN` GitHub Actions secret. Every Claude Code tool is turned off, so Claude can only read the prompt and return text. The prompt lives in the repo as a versioned file, so every change to the manager's personality has a history.

## Guardrails

All money here is fake: a $100,000 paper account, no real funds ever touched. The guardrails exist so the experiment behaves like a real fund and the result vs SPY stays fair.

Every trade passes these checks in code before any order is sent. A failed check drops that trade and writes the reason to the log, which the site can show as part of the joke ("Compliance declined.").

| Check | Rule |
| --- | --- |
| Ticker exists | On Alpaca's asset list, active and tradable |
| Allowed type | US stock or ETF; no leveraged or inverse ETFs, no OTC names |
| Sells | Only names the fund holds, never more than held |
| Buys | Fit within cash after sells settle in the same run |
| Position cap | No name above 20% of NAV after the trade |
| Count | Holdings stay between 5 and 10; trades per day at most 4 |
| Minimum size | Each order at least $1,000, so tiny trades don't clutter the log |
| Reason | Present, one sentence, under 200 characters, with a source link |
| Repeat run | Alpaca is checked for today's orders, and every order ID is unique to the date and ticker, so a second run that day places nothing |
| Liquidity | At least $50M traded per day on average, and no order above 1% of that day's volume |

**Kill switch:** a `PAUSED` file in the repo stops all trading. The evening record keeps running so the chart stays honest.

## Data files

The site reads a handful of small JSON files from `data/vibes/`; nothing else talks to the outside world. Raw logs live alongside them so every number can be traced back.

| File | Holds | Written by |
| --- | --- | --- |
| `summary.json` | Today's NAV, returns vs SPY, mood, key stats, last updated time | Evening run, morning run updates mood |
| `nav.json` | One row per trading day: date, NAV, SPY close, both indexed to 100 | Evening run |
| `holdings.json` | Current positions: ticker, shares, weight, cost, gain, date bought, buy reason | Evening run |
| `trades.json` | Every trade ever: date, action, ticker, dollars, fill price, reason, link, outcome so far | Morning run, outcome updated each evening |
| `letters/YYYY-MM-DD.md` | Each Friday letter | Friday run |
| `video/YYYY-MM-DD.mp4` | Weekly broker video, latest 4 only, plus its script and captions; shown only when show\_video is on | Friday run |
| `factsheets/YYYY-QN.json` | Quarterly factsheet data | Quarter end run |
| `logs/YYYY-MM-DD/` | Links and sources of headlines used (not the headline text, since the repo is public), prompt version, raw Claude output, validation results, Alpaca responses | Both runs |

## Metrics

The evening run computes every number the site shows, so the frontend only displays. Each carries an as of date.

| Metric | Definition |
| --- | --- |
| NAV | Adjusted NAV: Alpaca paper account equity at the close, plus dividends credited, minus the slippage reserve |
| Return since inception | NAV vs $100,000 |
| Today's return | NAV vs prior close, with SPY's for comparison |
| Gap vs SPY | Fund return minus SPY return since inception, in percentage points |
| Volatility | Annualized standard deviation of daily returns, shown once there are 20 trading days |
| Max drawdown | Largest fall from a peak NAV |
| Win rate | Share of closed trades that made money |
| Best and worst trade | By percent return, closed or still open |
| Longest held | The name the fund has believed in the longest |
| Turnover | Dollars traded over the last 30 days vs average NAV |
| Today's mood | Claude's label and score from the morning run |
| Mood vs return | Correlation of mood score with next day return, shown after 30 days; it will probably be near zero, which is the joke |
| Beating SPY? | Yes or Not yet since inception, plus the share of trading days the fund closed ahead of SPY; this is the headline number |

## Keeping it honest

No real money is invested, but every price is real: Alpaca's paper engine fills each order against the live market quote at that moment. Alpaca's own docs list what the simulation leaves out, and the fund corrects for each one so vibes never get a free win.

| What paper trading misses | Which way it bends results | How the fund corrects it |
| --- | --- | --- |
| Slippage, market impact, regulatory fees | Flatters the fund | Every trade is charged a 0.10% "slippage reserve," deliberately more than a liquid large cap costs to trade, and subtracted from NAV |
| Thinly traded stocks | Flatters the fund, since paper fills at the quote no matter the size | Only names with at least $50M traded per day, and no order above 1% of a day's volume |
| Dividends | Hurts the fund, since SPY's total return includes them | The evening run credits dividends on holdings from Alpaca's corporate actions data, so both sides are total return |
| Interest on cash | Hurts the fund slightly | Left as is; cash earning nothing is a fair cost of a cautious mood |

**No hindsight, no do overs**

- Only headlines published before the run starts are used.
- Each morning's decision is committed to the public repo before the orders fill, so the git history proves nothing was edited after the fact.
- One fund, one inception date, never reset after go live. No backtests, no backfilled days, no reruns for a better answer. Bad days stay on the chart.
- Every change to the manager's prompt is dated and listed on the methodology page.
- The site shows adjusted NAV; raw Alpaca equity, dividends credited and the slippage reserve are all published alongside it so anyone can check the math.

## Letters and factsheets

One extra Claude call a week, plus one a quarter, gives the fund a voice beyond the trade log.

**Friday letter to investors** (runs after Friday's evening record)

- 150 to 250 words in the same manager voice, opening "Dear Investors,"
- Covers the week's return vs SPY, the best and worst call, and one "lesson learned" that learns nothing
- Built only from the week's JSON, so every number in it is real
- Saved as Markdown and listed newest first on the site

**Quarterly factsheet** (first trading day after quarter end)

- One page: returns vs SPY by month, top holdings, sector mix, volatility, drawdown, number of trades
- Plus a short manager commentary paragraph
- Doubles as the printable Boomer View page

The first letter ships on the first Friday after go live, and the first factsheet covers the first full quarter after go live.

## Weekly recap video

Every Friday an original cartoon stockbroker, stressed out and a little overweight, delivers the week's results in a short video. It is built entirely with Claude and free tools, so it costs $0, and it stays off the site until it looks presentable.

**How it's made**

1. The Friday run has Claude write a 30 to 45 second script from the week's JSON, in the same deadpan voice as the letter.
2. The broker is a cartoon drawn in code (SVG), with moods tied to performance: calm when the fund is up, sweating, loosened tie and ringing phones when it's down.
3. An open source text to speech model reads the script; the animation is timed to the audio.
4. A headless browser records the animation frame by frame and ffmpeg turns it into an MP4.
5. The video lands on the fund page next to the Friday letter, with captions on by default.

**Rules for the broker**

- An original character with his own name and look; never modeled on a real person or TV host.
- He reports what the fund did and how it did vs SPY. He never tells viewers to buy or sell.
- The "Paper trading. Fake money. Not investment advice." line appears on screen in every video.

**Quality gate before it goes public**

- Videos render every Friday from day one, but stay hidden behind a `show_video` switch.
- You review the character design and a few rendered episodes; the switch flips only when you sign off.
- Until then, the Friday letter carries the recap on its own.

**Storage:** the latest 4 videos live in the site repo; older ones move to GitHub release files so the repo stays small.

## Site functionality

This is what the site must do; how it looks is the design phase. Every view reads the same JSON files.

**Live card on the project list**

- Today's return vs SPY, today's mood, and an "updated" time
- A small sparkline of NAV vs SPY since inception
- Links to the fund page

**Fund page**

- **Scoreboard:** one big answer to "Are vibes beating SPY?" (Yes or Not yet), with the gap in percentage points and the share of days the fund has been ahead
- **Hero:** NAV line vs SPY since inception, with range buttons (1M, 3M, all)
- **Key stats:** return since inception, gap vs SPY, volatility, max drawdown, win rate, today's mood
- **Holdings:** current positions with weight, gain, and the reason it was bought
- **Trade log:** newest first, one line each, filter by ticker and by buy or sell, link to source
- **Letters:** Friday archive, newest first
- **Weekly video:** the latest broker recap beside the Friday letter, captions on; hidden until you approve his look
- **Factsheet:** latest quarter, printable
- **How it works:** a short plain English methodology, the fund rules, and a link to the code
- **Disclaimer bar:** visible on every view

**Hooks into the three site views**

| View | What the fund adds |
| --- | --- |
| Spreadsheet View | `=VIBES()` returns today's NAV; a Portfolio tab shows live holdings and the trade log as rows |
| Hacker View | The trade log as a terminal feed, with validation messages and "Compliance declined" lines |
| Boomer View | The printable one page factsheet |

**Behavior**

- Shows an "as of" time on every number and a "market closed" state on weekends and holidays
- Works if one file is missing: that section shows "data unavailable" rather than breaking the page
- Loads fast on phones; the JSON stays small by keeping full logs out of what the page loads

## Operations

The fund should run for months without attention, so the weak points are timing, tokens and silent failures.

| Risk to uptime | Handling |
| --- | --- |
| GitHub cron runs in UTC, so 9:40 AM ET shifts with daylight saving | Schedule both 13:40 and 14:40 UTC for the morning run, and 20:30 and 21:30 UTC for the evening run. A gate checks the real ET time, and one shared concurrency group means two fund runs can never overlap |
| Scheduled runs can start late at busy times | Schedule off the hour (already at :40) and log the actual start. Trade only until 11:00 AM ET; a later start holds and logs "The manager overslept." Headlines are cut off at the real start time, so a late run never sees news it shouldn't |
| GitHub disables schedules in public repos after 60 days with no activity | Not a risk here: the daily data commits count as activity |
| Subscription token expires or breaks after a plan change | A Sunday health check calls Claude with a tiny prompt and fails loudly, so a broken token gets fixed before Monday. Note the token's expiry at setup and renew it early |
| A run fails silently | GitHub emails you on any failed run; the page shows a "last updated" time and flags any data older than one trading day as stale |
| Usage limits | One short call per weekday plus a letter and a video script each Friday, far below plan limits. If your own heavy use that morning hits the limit, the fund holds for the day instead of failing |
| A run crashes after placing orders but before committing, and a retry trades twice | Every order carries an ID built from the date and ticker, which Alpaca rejects if reused, and the run checks Alpaca for today's orders before trading. The trade file alone is not trusted |
| Orders fill partly or not at all | Unfilled orders are canceled 30 minutes after placing; the evening run records actual positions, not intended ones |
| A fund run and your own site edits push at the same time | The bot only writes inside data/vibes/, rebases before pushing, and retries once |
| A holding is acquired, renamed or delisted | The evening run compares positions with the day before, logs any change it can't explain, and pauses trading in that name |
| Alpaca's API is down | Retry once, then hold for the day; the next evening run backfills |

Secrets are GitHub Actions encrypted secrets, never files in the repo: `ALPACA_KEY`, `ALPACA_SECRET` (paper keys only) and `CLAUDE_CODE_OAUTH_TOKEN`. Every workflow also has a manual run button.

**Keeping secrets secret**

- Nothing secret ever goes in code, `.env` files, JSON or logs. `.env` is gitignored, and GitHub secret scanning with push protection blocks any commit that contains a key.
- Each secret goes only to the step that needs it: Alpaca keys to the trade and record steps, the Claude token to the decide step. The Claude step never sees the Alpaca keys.
- Claude runs with every tool turned off (no shell, no files, no web), so text planted in a headline can't make it run commands or read secrets. Its output is plain data that code validates.
- Workflows run only on a schedule or a manual run, never on pull requests, so a stranger's fork or pull request can't reach the secrets.
- Third party actions are pinned to exact versions, and each workflow gets the least permission it needs: write access to repo contents, nothing else.
- Before every commit, a scrub step scans the data and logs for anything shaped like a key and fails the run if it finds one.
- Paper keys only. Never create live trading keys for this project; a leaked paper key can only move fake money.
- The Claude token is tied to your subscription, so treat it like a password. If it ever appears anywhere public, revoke it and generate a new one immediately.
- Two factor login on your GitHub account, and you are the only person with write access to the repo.

## Risks

The biggest risk is a boring chart; the most serious is looking like real investment advice.

| Risk | Fix |
| --- | --- |
| Looks like advice | "Paper trading. Fake money. Real vibes. Not investment advice." on every view; no "buy this" language; never invite people to copy trades |
| Boring chart that hugs SPY | 5 to 10 names and a 20% cap; the trade log carries the comedy even on flat days |
| Bad model output | Code validates everything; raw output is logged; Claude can't place an order directly |
| Headline copyright | Trade reasons paraphrase and link out; headline text is never stored or shown |
| Jokes about real tragedies | Voice rules forbid it; no trade on news about harm to people |
| Subscription terms change | The decision step is one swappable function; switching to a paid API key is a one line change at about $20 a year |
| Weekly video looks amateur | Renders from day one but stays hidden behind the show\_video switch until you approve the character and a few episodes |
| Broker or name reads as a real person or firm | Original character and original fund name only; any fake ticker checked against real listed symbols |

## Phases and cost

The fund goes live as soon as the pipeline and the site both work. There is no waiting period: go live day is inception day, and whatever happens after that, from $15 to $1 million, is the show.

1. **Accounts and tokens:** Alpaca paper account, Claude token, GitHub Actions secrets, secret scanning on
2. **Build the pipeline** with Claude Code
3. **Dry run** a few mornings to catch bugs, then reset the paper account to $100,000
4. **Design** the Live card and the fund page
5. **Build the site** with Claude Code
6. **Prototype the broker video** with Claude Code; it renders weekly but stays hidden until you approve it, so it never blocks go live
7. **Go live:** the first real trade sets inception day

Design works from the dry run data, so the pages are built against real numbers instead of a mockup.

| Item | Cost per year |
| --- | --- |
| Alpaca paper trading and market data, Basic plan | $0 |
| News feeds | $0 |
| GitHub Actions and Pages, public repo | $0 |
| Claude, through your existing subscription | $0 extra |
| Weekly video, open source voice and video tools | $0 |
| **Total** | **$0** |

## Next steps

- [x] Decide Vibes only or Vibes vs Billy Joel
- [ ] Open an Alpaca paper trading account and generate paper API keys
- [ ] Run `claude setup-token` and save the token as a GitHub Actions secret
- [ ] Confirm the site repo is public
- [ ] Turn on GitHub secret scanning, push protection and two factor login
- [ ] Pick the fund name and persona (lean: Mood Ring Capital with the old money manager)
- [ ] Check whether Alpaca's news feed is free on the Basic plan; otherwise pick 3 to 5 RSS feeds
- [ ] Start the design phase: Live card, fund page, and the three view hooks
- [ ] Prototype the broker character and approve his look before the video goes public
- [ ] Dry run a few mornings, reset the paper account to $100,000, and go live

## Sources

- [Claude Code GitHub Actions](https://code.claude.com/docs/en/github-actions)
- [Alpaca Market Data API plans](https://docs.alpaca.markets/us/docs/about-market-data-api)
- [Alpaca News API](https://alpaca.markets/docs/news-api)
- [Alpaca Paper Trading API](https://alpaca.markets/blog/paper-trading-api/)
- [GitHub: disabling and enabling workflows](https://docs.github.com/en/actions/how-tos/manage-workflow-runs/disable-and-enable-workflows)
- [Earlier plan: Jargon Index and Vibes Fund](https://claude.ai/artifact/6GbU3eMLo23kskeBRTEXGR)
- [Alpaca paper trading rules and limits](https://docs.alpaca.markets/docs/trading/paper-trading/)
- [Sora shutdown timeline (Wikipedia)](<https://en.wikipedia.org/wiki/Sora_(text-to-video_model)>)
