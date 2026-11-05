# Vibes Fund: Name, Theme and Visual Design

Nov 5, 2026 · @William

## The pick

Lead with **Mood Ring Capital**, styled as a 1970s fund brochure whose accent color changes every morning with the fund's mood. The mood ring was a 1975 fad, so the name, the era and the color system all tell the same joke: a fund run on feelings, measured by a novelty ring.

- **Name:** Mood Ring Capital. No investment firm by that name turned up in a search.
- **Theme:** "Mood Ring '75," warm cream paper, brown ink, chunky 70s serif, and one accent color set daily by the mood score.
- **Cast:** a calm, old money chairman who writes the trade log and letters, and a stressed out broker who has to explain the results on video every Friday.
- **Tagline:** "Past vibes are no guarantee of future vibes."

Three other complete directions follow if this one doesn't feel right.

## Naming

A good name here does four jobs: it tells the joke in one breath, works as a LinkedIn post title, suggests a look on its own, and can't be mistaken for a real firm.

| Name | The joke | Look it suggests | Watch out |
| --- | --- | --- | --- |
| **Mood Ring Capital** | A fund measured by a novelty ring | 70s brochure, color shifting accent | None found in a name search |
| Priced In Partners | "It's priced in," the most overused line in finance | Old money prospectus | Lands best with finance people; no firm found by that name |
| Sentimental Value Partners | A play on "fundamental value": the fund values stocks by how they make it feel | Soft, nostalgic, scrapbook | Shares a title with a 2025 film; still fine as a fund name |
| Headline Risk Capital | A real risk term turned into the whole strategy | Newspaper and terminal | Slightly dry |
| Hot Take Holdings | Every trade is a hot take | Cable finance TV | Sounds like a podcast |
| Gut Feeling Partners | Plain English, instant | Anything | Forgettable |
| Conviction Without Evidence Fund | Honest about the strategy | Legal document parody | Too long for a card or browser tab |
| Animal Spirits Fund | Keynes' term for emotion driven markets | Classic, scholarly | **Avoid:** a popular finance podcast already uses the name |

**Finalists: Mood Ring Capital and Sentimental Value Partners.** Sentimental Value is a pun on "fundamental value," and the pun is the point: Fundamental Value Partners is already a real asset manager in Hong Kong, so the straight version is off the table. Sentimental Value pairs best with direction B, an old money firm that is openly emotional about its holdings.

**Check before you commit:** search the final name plus "capital" or "fund," look it up on SEC's adviser search, and pick any fake ticker that isn't a real listed symbol.

Sources: [Animal Spirits Podcast](https://podcasts.apple.com/us/podcast/id1310192007)

## Theme directions

Four complete looks. A is recommended; the others pair best with the names noted. All fonts listed are free on Google Fonts.

|  | **A. Mood Ring '75** (recommended) | **B. Old Money Prospectus** | **C. Trading Terminal** | **D. Cable Finance TV** |
| --- | --- | --- | --- | --- |
| Pairs with | Mood Ring Capital | Priced In Partners | Headline Risk Capital | Hot Take Holdings |
| Feeling | A warm 1975 fund brochure that takes itself very seriously | A private bank founded in 1921 | A trader's screen at 6 AM | A finance show where everything is breaking news |
| Palette | Cream #F4EBDD, ink brown #3B2A20, burnt orange #D9772B, avocado #7A8B3C, plus a daily mood accent | Paper #F6F1E4, banker green #1F4D3A, gold #B08D3C, ink #1C1C1C | Black #0B0B0C, amber #FFB000, signal green #33FF66, alert red #FF4D4D, grid #2A2A2A | Navy #0A1F44, alert red #E5202E, white #FFFFFF, chyron yellow #FFD400 |
| Type | Fraunces (soft, chunky display), IBM Plex Sans (body), IBM Plex Mono (numbers) | Cormorant Garamond (display), EB Garamond (body), old style numerals | JetBrains Mono for everything | Oswald (condensed headlines), Roboto Condensed (body) |
| Motifs | Rounded corners, a glossy mood stone as the logo, halftone photos, a rubber stamp reading "PAPER ONLY" | Engraved certificate borders, guilloche patterns, wax seal, letterhead | Dense panels, blinking cursor, function key labels, ASCII rules | Scrolling ticker, lower third chyrons, "BREAKING" banners, studio gradients |
| Signature moment | The whole page shifts to today's mood color on load, like a ring warming up | Each trade reason is set like a line in a ledger, signed by the chairman | Trades type themselves out line by line | A "BREAKING: FUND BUYS CEREAL" banner slams in on each new trade |
| Spreadsheet View | Ledger paper rows in cream and brown | Bound ledger with gold rule lines | Native fit | Ticker data as rows |
| Hacker View | Amber on brown, 70s computer printout | Telegraph tape | Native fit, the main look | Control room monitors |
| Boomer View | Printed brochure factsheet | Native fit, engraved annual report | Clean printout | Newspaper business page |
| Broker video style | Flat 70s cartoon, warm colors | Black and white newsreel | Pixel art on a monitor | Full cable news set |
| Risk | Needs care so the mood color never fights the data | Can feel too quiet | Hard to read for non technical visitors | Loud; can feel like a parody of a real network |

**See them:** [Vibes Fund theme mockups](https://claude.ai/artifact/TAqu1fAGSiaPshGNC3yKM5), one fund page per direction, all with sample data. Direction A has a mood switch in its Tweaks panel so you can see all five mood colors.

## Mood system

**What "mood" means here:** one fund, one mood per day. Each morning Claude reads the headlines and, along with its trades, returns a single score from −1 (the news feels terrible) to +1 (the news feels great). That score is already part of the plan's decision output. The mood is a readout of how the morning felt to the manager; it doesn't change the fund rules or trigger trades on its own. The five bands below are just display buckets that turn the number into a color and a word visitors can read at a glance. They are not investor types and not trading strategies.

Claude's daily mood score, from −1 to +1, picks one of five bands that follow the classic mood ring chart. That band sets the site's accent color, the mood label and the broker's posture.

| Band | Score | Ring color | Accent | Label examples |
| --- | --- | --- | --- | --- |
| Doom | −1.0 to −0.6 | Black | #2B2B2B | "Bunker mode" |
| Nervous | −0.6 to −0.2 | Amber | #C98A1B | "Checking the phone a lot" |
| Unbothered | −0.2 to +0.2 | Green | #4F8A5B | "Calm, possibly napping" |
| Optimistic | +0.2 to +0.6 | Blue | #2F6FA8 | "Cautiously euphoric" |
| Euphoric | +0.6 to +1.0 | Violet | #7B4FA8 | "Ordering the good champagne" |

**Rules that keep it readable**

- **Mood is decoration; performance is data.** The mood accent never colors a return. Gains and losses use ink color with ▲ and ▼ arrows and a + or − sign, so the mood ring's green for "unbothered" never reads as "up."
- **Always labeled.** The mood shows its word and score next to the color, so it works for colorblind visitors.
- **Contrast first.** Text on any accent meets WCAG AA; the dark bands use cream text, the light ones brown.
- **Motion:** on load, the accent eases from yesterday's color to today's over about a second, like a ring warming up. Visitors who prefer reduced motion get the final color instantly.
- **History:** a thin strip of daily mood colors under the NAV chart shows the fund's emotional history at a glance.

## Cast

Two original characters give the fund its comedy: one makes the calls with total calm, the other has to live with them. Neither is based on a real person, TV host or firm.

**The Chairman (writes the trade log and the Friday letter)**

- Old money, unflappable, signs every letter. A small, diminutive British gentleman: balding, thin wire spectacles, a long nose, impeccably dressed. Speaks in a posh British accent and never raises his voice. He describes a 9% loss as "a character building quarter."
- Name ideas: Sterling Haverford III, Preston Ashby, Whitmore T. Calloway.
- British name ideas: Sir Peregrine Ashby, Rupert Haverford, Lord Barnaby Whitmore.
- Appears as a formal portrait in the letter header and an ink signature. Optional cameo: a few seconds at the end of the Friday video, calmly signing off while the Broker panics, voiced with a posh British text to speech voice.
- The contrast is the joke: a tiny, perfectly composed Englishman making wild calls, and a big, sweaty American broker who has to explain them.

**The Broker (hosts the weekly video)**

- The guy on the desk who has to explain the Chairman's decisions every Friday. A gentle giant: huge, warm, simple and fiercely loyal, everyone's favorite guy on the floor. Overworked and slightly panicked, but never mean.
- The Chairman's exact opposite: towering where he is tiny, loud where he is quiet, a plain spoken American where he is a posh Englishman, sweating where he is composed. The Chairman makes the wild calls; the Broker trusts him completely and has to explain them. His design stays original: no wild beard or long overcoat that would read as a famous film character.
- Name ideas: Barry Kessler, Dougie Marchetti, Gary from the Desk.
- Look: short sleeve dress shirt, loosened tie, a little overweight, receding hairline, two phones, a mug that says #1 TRADER. Drawn flat in the theme's style.
- His build is part of the look, never the joke. The humor comes from his stress, not his body.

**Broker states, set by the week's return vs SPY**

| Week vs SPY | State | What changes |
| --- | --- | --- |
| Ahead by 3 points or more | Jubilant | Tie thrown over shoulder, confetti, one phone held up like a trophy |
| Ahead by 0 to 3 points | Relieved | Wipes brow, small smile, sips coffee |
| Behind by 0 to 3 points | Sweating | Sweat drops, both phones ringing, tie loosened further |
| Behind by 3 points or more | Meltdown | Tie around his head, bulging veins on his forehead, papers flying, mug empty. He keeps glancing at the Chairman's portrait on the wall, terrified |

A running gag across every state: the Broker is quietly terrified of the Chairman. The Chairman's framed portrait hangs on the set behind him, and the more the fund trails SPY, the more often he checks it.

The states give the video variety without new drawing each week: one character rig, four poses, and the script changes.

## Design elements

Every visual piece the site needs, with how direction A treats it. These become the first mockups in the design phase.

| Element | Job | Direction A treatment |
| --- | --- | --- |
| Wordmark and logo | Name the fund at a glance | "Mood Ring Capital" in Fraunces with a glossy oval mood stone; the stone takes today's accent |
| Favicon | Recognizable in a browser tab | The mood stone alone, recolored daily |
| Live card | Pull visitors in from the project list | Cream card, today's return vs SPY, mood word and stone, a tiny NAV vs SPY sparkline, "updated 4:30 PM" |
| Scoreboard | Answer "Are vibes beating SPY?" | Huge "YES" or "NOT YET" in Fraunces, the gap in points underneath, share of days ahead |
| NAV chart | Show the race | Two lines, fund in brown and SPY in a muted gray, with the daily mood strip underneath |
| Mood indicator | Show today's feeling | The stone, the band word, the score and Claude's label ("cautiously euphoric") |
| Key stats | The scorecard | A row of brochure style stat blocks with small caps labels and mono numbers |
| Holdings | What it owns and why | Cards with ticker, weight, gain with ▲▼, and the original buy reason in italics |
| Trade log | The comedy | Newest first; each line a typed memo with date, action stamp (BUY or SELL), ticker and the one liner |
| Compliance declined | Show rejected trades | A red rubber stamp across the struck out line |
| Friday letter | The voice | Letterhead with the Chairman's portrait and signature, set like a printed memo |
| Weekly video | The broker | 16:9 frame styled as a 70s TV set, captions on, hidden until approved |
| Factsheet | Printable summary | A single brochure page; doubles as Boomer View |
| Share card | LinkedIn and link previews | Scoreboard answer, return vs SPY and mood stone on cream, sized 1200 by 630 |
| Disclaimer bar | Keep it clearly fake | A thin stamp style bar: "Paper trading. Fake money. Real vibes. Not investment advice." |
| Empty and closed states | Weekends, holidays, missing data | "Market closed. The Chairman is at the club." and "Data unavailable, the intern is on it." |
| Three site views | Fit the rest of the site | Spreadsheet: ledger rows. Hacker: amber printout. Boomer: the factsheet |

## Copy and voice samples

The voice is total confidence about a ridiculous method. These samples set the tone for the prompts; real ones will name real companies and link the source headline.

**Taglines**

- "Past vibes are no guarantee of future vibes."
- "Investing on feelings since 2026."
- "Diversified across several strong feelings."
- "We read the room so you don't have to."

**Trade log lines**

- **BUY**, coffee chain: Lines are long and the vibes are caffeinated. We are in.
- **SELL**, airline: Three delay headlines before breakfast. The fund prefers to stay grounded.
- **BUY**, cereal maker: Shoppers are eating breakfast for dinner again. Conviction is high; evidence is cereal.
- **HOLD**: The news was loud but not convincing. The Chairman finished his tea.
- **COMPLIANCE DECLINED**: The Chairman tried to buy a company that does not exist. Inspiring, but no.

**Friday letter opener**

> Dear Investors, this week the fund trailed the S&P 500 by 2.1 points, which the Chairman describes as a character building week. Our conviction remains unshaken, mostly because we have not checked.

**Broker video opener**

> Hey everybody, Barry here from the desk. So. The Chairman bought cereal again.

**Disclaimers**

- Bar: "Paper trading. Fake money. Real vibes. Not investment advice."
- Video end card: "No real money was harmed in the making of this fund."
- Footer: "Mood Ring Capital is a fictional fund run by an AI on a paper trading account. Nothing here is a recommendation to buy or sell anything."

## Decisions and next steps

Three choices unlock the design phase; everything else in this doc follows from them.

- [ ] Pick the name: Mood Ring Capital or Sentimental Value Partners
- [ ] Pick the direction (lean: A, Mood Ring '75)
- [ ] Name the Chairman and the Broker
- [ ] Run the name checks: web search, SEC adviser search, fake ticker not a real symbol
- [ ] Mock up the Live card, scoreboard and fund page in the chosen direction
- [ ] Sketch the Broker in his four states and approve one look before any video work
- [ ] Fold the final name, voice and mood bands into the Claude prompts and the plan doc

Related: [Vibes Fund project plan](https://claude.ai/artifact/2v9H586YPWYypPMSYfXPiR)
