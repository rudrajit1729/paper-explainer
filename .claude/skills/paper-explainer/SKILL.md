---
name: paper-explainer
description: Turn a research paper into a short animated explainer video (HTML motion graphics rendered to MP4) with music, an AI voice, a cloned voice, or the author's own recordings, in any of several design languages and narration languages. Use when asked to make, edit, re-time, restyle, translate, narrate or export a paper explainer, a figure animation, or a project in this repo's projects/ folder.
---

# Paper explainer

This repo turns a paper into a 1 to 2 minute animated explainer. A project is one folder in `projects/`.
The page is HTML on a fixed 1600x900 stage, written on **animation time**. The toolkit stretches
animation time into **video time** so every moment lasts as long as its narration or its reading needs,
then renders frame by frame and mixes music and voice.

```
explainer build projects/<name> --mode read  --preview     # quick low-res check (music, paced for reading)
explainer build projects/<name> --mode voice               # narrated, full quality
explainer build projects/<name> --mode voice --engine clone   # in the author's cloned voice
explainer build projects/<name> --theme academic --lang es    # other design language, Spanish narration
explainer record projects/<name>                                # author records the narration in the browser
```

Outputs land in `projects/<name>/output/`. Everything in `build/` is regenerated.

## Pick the guide for the job

| Task | Read |
|---|---|
| New video from a paper (plan scenes, write narration, build the page) | `references/build.md` |
| Change text, timing, pacing, colors, a scene, the music | `references/editing.md` |
| Motion graphics: figure camera, spotlights, a dot following the figure's lines, counters, loops | `references/motion.md` |
| AI voice, cloned voice, own recordings, other languages | `references/voice-and-languages.md` |
| Design languages (themes) and the house design rules | `references/design.md` |

`projects/to-boldly-go/` is the worked example that uses every technique. Read its `index.html`
and `project.json` before writing a new page; copy patterns from it rather than inventing new ones.

## Rules that always apply

1. **Never edit `build/`.** Edit `index.html`, `project.json`, `narration/<lang>.json`, `assets/`.
2. **Check with stills before rendering.** `explainer still <project> --at 5 12 20` writes PNGs at
   animation times. Look at them. A full render takes minutes; a still takes seconds.
3. **Preview before full quality.** `--preview` renders at 12 fps and 960 px.
4. **Every narration line has a timeline event** with the same id, and the event's `at` is when the
   matching thing appears on screen. That pairing is what keeps voice and picture in sync.
5. **Keep facts from the paper.** Numbers, quotes, names and the title come from the paper, exactly.
   Ask the author before rewording a claim.
6. **One idea per scene, one sentence per caption.** If text needs more than about 4 seconds to read, split it.
7. **Respect the author's design preferences** in `references/design.md` (they came from real feedback).
8. Before publishing a video or repo of an **unpublished or under-review** paper, check with the author:
   double-blind venues forbid revealing authors.

## Requirements

Python 3.10+, `pip install -e .`, `playwright install chromium`, ffmpeg, and poppler (`pdftotext`,
`pdfimages`) for reading papers. Voice cloning adds `pip install -e ".[clone]"`.
