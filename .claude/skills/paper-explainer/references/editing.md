# Changing an existing explainer

Find the right file first:

| Change | Where |
|---|---|
| Words on screen | `index.html` (or `index.<lang>.html` for a translated page) |
| What the voice says | `narration/<lang>.json` |
| When something appears | `data-in` in `index.html`, and the matching event `at` in `project.json` |
| How long a moment lasts | `project.json` → `timeline` (`pace`, `holds`, `final_hold`) |
| Colors, fonts, corners | `--theme` or `project.json` `theme`; per-project overrides in the page `<style>` |
| Music | `project.json` → `music` |
| A figure | `assets/` (keep the same pixel size, or update coordinates in the page script) |

After any change: `explainer still ... --at <times>` to look, then rebuild. Narration changes need
`--mode voice` without `--reuse-voice` so the audio is regenerated.

## Common requests

**"Too fast to read."** Raise `pace.read.read_factor` (more time per line), `pace.*.min_slope`
(slower continuous motion), or add `holds` for the dense lines. The opening of a scene can also
start later relative to its narration with a larger `lead`.

**"The dot or camera spins my eyes."** Raise `min_slope` for that mode, or give the scene's events
more animation time (move later events' `at` and `data-in` values later).

**"Make the video N seconds."** Run `explainer timing` and read the total, then scale `min_slope`,
`read_factor` and `holds` until it matches. Voice mode is bounded below by the narration length.

**"Change a number."** Update every place it shows: the text, `data-val` on a `count` element,
the `width:` of a bar, and the narration.

**"Move this line after that."** Change `data-in` values in the page and the event `at` values,
keeping each event's `at` equal to when its thing appears.

**"Shorter / longer scene."** Shift every later `data-in`, `data-scene`, event `at`/`settle`, camera
keyframe and music time by the same amount. A small script is safer than editing by hand:
`re.sub(r'data-in="([\d.]+)"', ...)` over the page and the same shift over project.json.

**"Different wording in the final video than the script."** Keep `narration/<lang>.json` as the
single source of truth so a rebuild reproduces the shipped video.

**"Restyle."** `--theme fluent|material|academic|night|google-apple`. For one project, override tokens
in the page `<style>`: `:root{ --blue:#0B57D0; --r-xl:16px }`.

## Things that look like bugs

- An element visible at the start: its `data-in` is negative or 0. Scene 1 elements use `-1` on purpose.
- A hold that freezes mid-animation: an entrance spans two events. Re-stagger so each entrance ends
  before the next event's `at`, or make that event continuous (remove `entrance`).
- Text clipped in a card: shorten the text first; enlarge the card second.
- Fonts look different in the video: the renderer uses bundled Inter for the default theme and
  Google Fonts for others (needs internet while rendering).
