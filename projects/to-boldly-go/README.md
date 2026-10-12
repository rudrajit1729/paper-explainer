# To Boldly Go (example project)

The explainer for *"To Boldly Go Where No One Has Gone Before": What Has AI Let Developers Unlock?*
by R. Choudhuri, J. L. Butler, C. Bird, C. Badea, B. Houck, A. Sarma.

- `output/To_Boldly_Go_voiceover.mp4` is the final version: Chris Bird's narrated cut.
- `narration/en.json` holds an earlier version of the English script. Paste the final script there
  (same line ids) so a rebuild reproduces the shipped video.
- `narration/es.json` is a Spanish narration to show the language support (machine-drafted; have a
  native speaker check it before sharing).
- `inject.json` holds the traced SVG paths of the figure's lobes and loop arrows.

```
explainer build projects/to-boldly-go --mode voice
explainer build projects/to-boldly-go --mode read --theme academic
explainer clip  projects/to-boldly-go --mode read --name loop-figure
```
