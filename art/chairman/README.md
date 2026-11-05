# The Chairman: house portrait

Sir Peregrine Ashby, Chairman of Mood Ring Capital. This is the official drawing. Reuse it in the letters, the fund page, the Friday show and anywhere else he appears, rather than redrawing him.

## Files

| File | What it is |
| --- | --- |
| `chairman-portrait.svg` | The portrait as a standalone SVG (400 x 500). The chair and carnation are printed in Optimistic blue #2F6FA8 with the halftone dot screen |
| `chairman-portrait-preview.png` | Enlarged render of the whole portrait |
| `chairman-face-detail.png` | Close-up of the face |
| `chairman-portrait-page-size.png` | How it reads at the size it appears on the page (about 232 px wide) |
| `source/portrait.py`, `source/cupset.py` | The generator. `portrait.py` draws the chair, figure and face; `cupset.py` draws the teacup, saucer and both hands |

## The drawing

- **Style:** classic mid-century magazine gag cartoon in pen and ink, with fine line, cross hatching for shadow and solid blacks. Two colors only: ink #161513 on paper #F4F3EE, plus the day's mood ink, always halftone screened.
- **Pose:** a small man sitting in an enormous tufted wingback chair, with his feet dangling over the front of the seat. The chair dwarfing him is the joke.
- **Face:** profile, bald dome with a few combed strands and a white fringe, a very long nose and a downturned, unimpressed mouth. Round wire spectacles show the near lens only, with the bridge resting on the nose.
- **Dress:** black suit, wing collar, bow tie, hatched waistcoat, and a carnation in the mood ink.
- **Hands:** one hand pinches the teacup handle with the thumb on top; the other holds the saucer palm up beneath it.

## Changing the day's mood color

In the page, the chair and carnation use `{{accent}}`, filled with the day's mood ink and the dot pattern `a3-screen`, or `a3-screen-sm` for small marks. To recolor the standalone SVG, replace `#2F6FA8` with another mood ink:

| Mood | Color |
| --- | --- |
| Doom | #2B2B2B |
| Nervous | #C98A1B |
| Unbothered | #4F8A5B |
| Euphoric | #7B4FA8 |

## Regenerating

Run `python3 source/portrait.py`. It writes `source/portrait.svgfrag`, the SVG with `{{accent}}` placeholders, ready to paste into a page that defines the `a3-screen` and `a3-screen-sm` patterns.

Follow the illustration process in `docs/design-rules-summary.md` for any change:
1. Build hard parts as large studies first.
2. Render at enlarged size and at page size.
3. Get a fresh critique against the brief.
4. Publish only after it passes.
