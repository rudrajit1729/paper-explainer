# Building a new explainer from a paper

## 1. Start the project and read the paper

```
explainer new my-paper --paper path/to/paper.pdf
```

This copies the starter into `projects/my-paper/` and extracts `source/paper.txt`,
`source/figures.md` (captions found) and `source/images/` (embedded images, `img-<page>-<n>.png`).
Read the abstract, the research questions, the main results table and the key figure's caption.

## 2. Plan the story (agree it with the author before building)

Aim for 4 to 6 scenes and 60 to 100 seconds narrated. A shape that works:

| Scene | Job | Typical visual |
|---|---|---|
| Question | The gap: what others ask vs what this paper asks | Two big lines of type, the second in an accent color |
| Answer / findings | The 3 headline results with their numbers | Cards with a visual metaphor, a bar that fills, 2 to 3 example chips each |
| Mechanism | How or why it works, using the paper's own main figure | The figure with a camera, spotlights and motion on its own lines |
| Implication | What people should do | Cards or columns, one per recommendation |
| Takeaway | One memorable line and the citation | Big type, a small looping motif, full title and authors |

Write the plan as a short table (scene, on-screen text, narration, visual) and show it to the author.

## 3. Get the figure

```
explainer figure paper.pdf --page 8 --out projects/my-paper/assets/fig1.webp
```

It takes the largest embedded image on that page. For a vector figure, render and crop the page:
`--crop 0.08,0.10,0.92,0.48` (fractions of the page). The white background is made transparent so
the figure sits on any theme (`--opaque` keeps it). Draw it in the page at 1640 px wide.

## 4. Write the narration

`narration/en.json` holds one short line per id. Spoken style: short sentences, numbers written as
words ("three hundred and thirty-one"), no parentheses or abbreviations the voice would trip on.
About 2.6 words per second; a 90-second video is about 230 words.

## 5. Build the page

Edit `index.html` (start from the starter, borrow patterns from `projects/to-boldly-go/index.html`):

- Each scene: `<section class="scene" data-scene="start,end" data-chip="Name" data-chip-color="b">`.
  Neighbouring scenes overlap by about 0.2 s so they crossfade.
- Each element that appears: `data-fx="rise" data-in="t"` (see `motion.md` for all effects).
- Custom motion goes in the project script with `Explainer.onRender((at, vt) => { ... })`.

Then add one timeline event per narration line in `project.json` (`timeline.events`):

```json
{"at": 7.0, "line": "c6", "entrance": 1.4, "settle": 8.6, "note": "Further card"}
```

- `at`: animation time the thing the line talks about appears.
- `entrance`: seconds of animation that play at normal speed (the card rising, its bar filling),
  after which the picture holds until the narration finishes. Leave it out for continuous motion
  (a dot travelling a path) so that motion slows evenly instead of freezing.
- `settle`: when this event's motion is done; defaults to the next event's `at`.
- `holds.read` / `holds.voice`: extra frozen seconds after a line, for dense slides.

Stagger elements so one event's entrance finishes before the next event starts (card 1 and its
chips and bar by 6.8, card 2 starting at 7.0). Interleaved entrances make holds look half-finished.

## 6. Check, then render

```
explainer timing projects/my-paper --mode read
explainer still projects/my-paper --at 3 9 16 25 --mode read     # look at every scene
explainer build projects/my-paper --mode read --preview          # watch it once
explainer build projects/my-paper --mode voice                   # narrated, full quality
```

Read the PNGs and the preview critically: text overflow, overlaps, anything hard to read, a hold that
looks unfinished, motion that is too fast. Then fix and repeat.

## 7. Extras

- `explainer clip projects/my-paper --name figure --mode read` cuts a named clip (`clips` in project.json).
- `explainer page projects/my-paper --mode read --standalone` writes one self-contained HTML file to share.
- `python -c "from explainer.media import gif; ..."` for a README GIF.
