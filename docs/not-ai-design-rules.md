# Vibes Fund: Not AI Design Rules

Nov 5, 2026 · @William

## Why AI design looks like AI

AI tools default to the most common choices in their training data, so unguided output converges on the same look. Anthropic calls this distributional convergence. Avoiding it means making every decision on purpose and writing those decisions down before any screen is drawn.

This doc is the rulebook for every Vibes Fund design: the site, the Live card, letters, factsheets and the weekly video. Any design Claude produces for the project must follow it, and any rule broken must be broken on purpose with a written reason.

Two layers of tells matter here:

- **First wave, now widely mocked:** purple gradients, Inter, three icon cards, glow effects, emoji icons.
- **Second wave, harder to see:** the "tasteful" defaults AI reaches for once told to avoid the first wave. That means a cream background with a serif display and a warm orange accent, Fraunces and IBM Plex, mono eyebrow labels, dot separators, pill badges, and every section boxed in a rounded card. The first A and B mockups hit this second wave.

## The rules

Every value below is fixed. A value not on these lists is a mistake.

**1. Start from real references**

- Each direction is designed from 3 to 5 real printed or built artifacts of its era or genre, studied before any screen is drawn. A style description ("70s vibe") is not a reference.
- Borrow the genre's actual conventions (how a 1970s annual report sets a highlights table, how a stock certificate frames its text), not a modern web layout dressed in period colors.

**2. Type**

- One family for text. At most one second face, used only for display, and only if the first can't do the job.
- No Inter, Roboto, Arial, Open Sans, Lato, system fonts, Space Grotesk, Fraunces, IBM Plex or JetBrains Mono. These are the faces AI reaches for first.
- No script fonts faking signatures. Typeset the name, or use a real scanned signature.
- Six type sizes for the whole page, with big jumps between them (display at least 3x body). Tabular figures for every number in a table.

**3. Color**

- One ink for text, one paper, one accent. The accent has a single job and is not used for anything else.
- No gradients, glows or tinted blobs. No cream plus serif plus orange combination.
- Any color that carries meaning is labeled in words too.

**4. Layout**

- A real grid (12 columns, fixed gutters), used asymmetrically. Empty columns are allowed and encouraged.
- One dominant element per screen. Sections differ in weight; most are quiet.
- Group with whitespace and rules (1px hairlines, one heavy rule weight), not boxes.
- Spacing scale: 4, 8, 16, 24, 32, 48, 64, 96, 128. Nothing in between.

**5. Components**

- No cards by default. A box must earn its border by being a separate, actionable object.
- Corner radius: 0 everywhere, except where the subject is round (the mood ring).
- No shadows.
- No eyebrow labels, dot separated lists, pill badges or decorative status dots.

**6. Imagery**

- One illustration or image style per direction, with written rules (line weight, texture, palette).
- No clip art built from circles and ellipses in flat fills. Prefer typography, real photos, scanned texture, or an honest labeled placeholder.
- Characters (the Chairman, the Broker) are drawn once, properly, in a single style, and reused.

**7. Copy**

- Specific to this fund. If a competitor could reuse the line, rewrite it.
- At most one joke per section, and no repeated joke formula.
- No clipped two beat slogans in the "X. Real Y." rhythm.

**8. Data**

- Use the genre's real data conventions: a highlights table, a schedule of investments, footnotes.
- Every number shows its date. Sample data is labeled once, plainly, not with a badge on every block.

**9. Motion**

- At most one motion moment per page (the mood color settling on load), and none for users who prefer reduced motion.

## Banned list

Each of these reads as AI on sight. The right column is what to do instead.

| Tell | Instead |
| --- | --- |
| Purple or indigo gradients, glows, blurred blobs | One flat accent with one job |
| Cream background, serif display, warm orange accent | A palette taken from the reference artifacts |
| Inter, Space Grotesk, Fraunces, IBM Plex, JetBrains Mono | A family chosen for the genre, off the AI shortlist |
| Small uppercase eyebrow over every heading | A plain heading; labels only where a category is needed |
| Dot separated metadata ("Day 62 · Thursday") | A sentence, or a table column |
| Pill badges ("SAMPLE DATA", "PREVIEW") | One plain line of text where it matters |
| Every section in a bordered rounded card | Whitespace and rules |
| A row of identical stat tiles | A ruled highlights table |
| Many corner radii | Zero, except round subjects |
| Rotated rubber stamps and kitsch props | A plain marginal note |
| Clip art made of circles and ellipses | Typography, texture, or a labeled placeholder |
| Script fonts as signatures | A typeset name or a real scan |
| Even rhythm, every section the same weight | One dominant element; the rest quiet |
| Repeated joke formulas, "X. Real Y." slogans | Specific lines, one joke per section at most |
| Mono labels sprinkled on a non technical page | Mono only where the genre uses it (a terminal) |

## Direction A v2: Mood Ring Capital

The page is a 1970s two color annual report: black ink plus one spot color, and the spot color is today's mood. Color has exactly one job on the page: telling you how the fund feels.

**References to work from**

- 1970s mutual fund annual reports and shareholder letters: financial highlights tables, ruled schedules of investments, the chairman's letter set in columns.
- Swiss style corporate reports of the same era: strict grids, flush left type, big numerals, lots of empty space.
- Two color offset printing: one spot ink over black, halftone dot screens.
- Original mood ring packaging and the "what your color means" chart card.

**System**

| Element | Setting |
| --- | --- |
| Type | Chivo only. 900 for display and numerals, 400 and 700 for text, tabular figures in tables |
| Type sizes | 13, 16, 20, 32, 64, 200 px |
| Paper | #F4F3EE, a neutral off white, not cream |
| Ink | #161513 for all text and rules |
| Spot color | The mood ink of the day: Doom #2B2B2B, Nervous #C98A1B, Unbothered #4F8A5B, Optimistic #2F6FA8, Euphoric #7B4FA8. Used for large shapes only, never for body text |
| Grid | 12 columns, 24 px gutters, max width 1280 px |
| Rules | 1 px hairlines, 8 px heavy rule. Nothing else |
| Radius and shadow | None, except the mood ring itself |
| Texture | A halftone dot screen on spot color areas, like offset printing |

**Signature moment**

The hero is a large printed swatch of today's mood ink, screened with halftone dots, beside the one word answer to the fund's question. When the mood changes, the whole report reprints in a new spot color.

## Direction B v2: Sentimental Value Partners

The page is one engraved certificate followed by a bound ledger. The certificate is the dominant element; everything after it is quiet, ruled and typeset like a private bank's books.

**References to work from**

- Engraved stock and bond certificates: guilloche borders, vignettes, serial numbers, engraved roman capitals.
- Private bank letterheads and correspondence from the early 1900s.
- Bound ledger books: ruled columns, red margin lines, handwritten style entries set in type.
- Banknote line engraving for any portrait: hatching and cross hatching, never flat fills.

**System**

| Element | Setting |
| --- | --- |
| Type | Old Standard TT only, a 19th century modern face. Capitals with wide spacing for engraved titles |
| Type sizes | 14, 17, 21, 30, 56, 120 px |
| Paper | #F1EEE6 |
| Ink | #1C1B19 for text and rules |
| Accent | Banknote green #2E5A44, used only for engraved borders and the certificate |
| Grid | 12 columns, centered certificate, ledger on full width |
| Rules | 1 px hairlines, a double rule for section breaks, a ledger margin line |
| Radius and shadow | None |
| Imagery | Line engraving only. The Chairman's portrait is drawn properly in hatching, or shown as a labeled placeholder until it can be |

**What changes from v1:** no script signatures, no rotated stamps, no clip art figures, no barometer built from colored arcs, no mono or small caps labels sprinkled through the page. The wax seal stays only as a blind embossed outline, the way real certificates carry one.

## Pre ship checklist

Run this on every design before it is called done.

- [ ] Zoom to 25%. One element dominates and the sections don't look like the same gray block.
- [ ] List every corner radius, shadow, gap and font size in the code. Anything off the scales above gets fixed.
- [ ] Count typefaces. One, or two with a written reason.
- [ ] Search the page for eyebrows, " · " separators, pills and badges. Remove them.
- [ ] Count boxes. Every bordered container is a separate, actionable object.
- [ ] Read every line of copy. Could a competitor use it unchanged? Is any joke formula repeated?
- [ ] Every illustration follows the direction's one written style.
- [ ] Swap in another fund's name. If the page still works, add something only this fund could say.
- [ ] Text contrast is at least 4.5:1, and color never carries meaning alone.
- [ ] Final human pass on spacing, type and color.

## Sources

- [Improving frontend design through Skills (Anthropic)](https://claude.com/resources/articles/improving-frontend-design-through-skills)
- [AI slop website checklist (Illos)](https://illos.dev/guides/ai-slop-website-checklist)
- [7 Signs a UI Has Been Vibe Coded (Fountain Institute)](https://www.thefountaininstitute.com/blog/signs-vibe-coded-ui)
- [AI Slop Fonts and Gradients (925 Studios)](https://www.925studios.co/blog/ai-slop-design-tells)
- [10 signs your website was made by AI (Noqode)](https://www.noqode.fr/en/blog/design-ia-generique)
- [How to Make AI UI Look Less Generic (Superdesign)](https://superdesign.dev/blog/how-to-make-ai-ui-look-less-generic)
- [Claude Design tips to look less AI generated (note.com)](https://note.com/it_audit/n/na94228399197?hl=en)
