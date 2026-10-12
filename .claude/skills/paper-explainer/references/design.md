# Design languages and house rules

## Themes

`explainer list` shows them; `docs/themes.png` shows the same slide in each. Use `--theme <name>` per build or `"theme"` in project.json.

| Theme | Look |
|---|---|
| google-apple (default) | Google's blue, red, yellow, green; Apple-style system type (Inter in exports); big rounded cards; white |
| fluent | Microsoft palette, Segoe UI (Windows) or Inter, small corners, light shadows |
| material | Google Material 3: Roboto Flex, tonal containers, large rounded shapes |
| academic | Serif display type with a sans body, muted inks, small corners: a conference-talk feel |
| editorial | Magazine-style: tight black headlines, toned-down accents, quiet grey cards |
| night | Dark stage, bright accents; figures sit on a white panel |

A theme is a CSS file in `explainer/web/themes/` that overrides tokens. To add one, copy a theme,
change the tokens, and add an `/* @font-link: <Google Fonts URL> */` line if it needs a web font.

Tokens: `--blue --red --yellow --green` (accents), `--*-ink` (accent text on white), `--*-tint`
(card fills), `--f` (body font), `--f-display` (headline font), `--s-bg --s-fg --s-muted --s-soft
--s-line --s-panel --s-chip --s-track` (stage surfaces), `--r-xl --r-lg --r-md --r-sm` (corners),
`--shadow-card`, `--figure-bg`, `--loop` (moving dot color).

Pages must use tokens, never literal colors, or themes will not restyle them.

## House rules (from the author's feedback on the first video)

- White background. No ambient color washes behind content.
- Colorful cards are welcome: tint each card with its accent, one accent per idea.
- No orange in the interface (the paper's figure may keep its own colors).
- No round colored dots as markers; use short pills (`.mk`). No brand logos.
- Clean sans type; a serif only in the academic theme.
- Highlights on a figure are circles or traced shapes, never boxes that cut through content.
- Moving elements along a figure's lines use the figure's own geometry, traced, with smooth curves.
- Slow enough to read: a viewer must finish every caption. Nothing should feel like it spins.
- Show a share as a filled bar "of responses", not a ring or pie, when shares overlap or do not sum to 100%.
- Each finding card gets a simple visual metaphor and 2 to 3 short example chips from the paper.
- The final slide carries the exact paper title and all authors.
- Writing: no em dashes; short declarative sentences; active voice.

## Layout

Stage is 1600x900. Side padding 110 px, top 90 px. Headlines 74 to 96 px, body 21 to 27 px,
minimum 18 px for anything meant to be read in a video. One idea per scene.
