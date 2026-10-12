# Motion graphics recipes

All motion is a pure function of time, so scrubbing, previews and frame-by-frame rendering agree.
`at` = animation time (what you author in), `vt` = video time (real seconds).
Use `at` for anything tied to the story; use `vt` for ambient motion that should keep moving
during holds (a dot circling an icon, a ripple).

## Built-in effects (data attributes)

| Attribute | Does |
|---|---|
| `data-fx="rise" data-in="t"` | fades in while moving up 26 px over 0.6 s |
| `data-fx="fade"` | fades in |
| `data-out="t2"` | (with rise/fade) fades out at t2. Captions that replace each other use in/out pairs |
| `data-fx="bar" data-in data-dur` | scales from 0 to its CSS width (set `style="width:45%"`, `transform-origin:0 50%`) |
| `data-fx="count" data-val="45.0" data-decimals="1" data-unit="%"` | counts up |
| `data-fx="ring" data-val="45"` | SVG circle with `pathLength="100"` fills to the value |
| `data-dur="1.1"` | effect duration (default 0.6) |

Scenes crossfade with a slight zoom automatically (`data-scene="start,end"`).

## Helpers in project scripts

```js
const { $, clamp, easeIO, seg, lerp, win, V, D, onRender } = Explainer;
seg(t, a, d)     // eased 0→1 starting at a over d seconds
win(t, a, b, f)  // 1 between a and b, fading in and out over f
V(a)             // video time of animation time a (for vt-based motion)
onRender((at, vt) => { ... })   // called every frame
```

## Camera over a figure

Put the figure in `.viewport > .world` at its native pixel size (1640x900 in the example) and move
the world. Keyframes name the region to frame; zoom interpolates on a log scale so it feels even.
See `camera()` in both the starter and the example. Typical beats: open slightly zoomed in → full
figure → zoom to the part being narrated → pan → back to full before the scene ends.

## Spotlights on part of a figure

Stack copies of the same image. The base copy dims (`opacity`), and a copy clipped to the region of
interest stays bright:

```html
<img id="figBase" src="assets/fig.webp">
<img id="figNex" src="assets/fig.webp" style="clip-path:circle(94px at 820px 469px)">
<img id="figL0"  src="assets/fig.webp" style="clip-path:path('__INNER_CLIP__')">
```

Circles suit round elements; a traced path (below) lights an irregular shape exactly. Prefer circle
or traced highlights over boxes: boxes cut through neighbouring content.

## A dot that follows the figure's own lines

1. Trace the line in the figure's pixel space with `explainer.trace`:

```python
from explainer.trace import load, near_color, orange_like, region, outline_points, polar_to_xy, smooth_path, figure_eight, check
img = load("projects/x/assets/fig.webp", width=1640)
print(img[600, 600])                                   # sample a color at (x=600, y=600)
lobe_l = region(near_color(img, (78, 72, 64), 40), seed=(600, 600))
lobe_r = region(near_color(img, (63, 74, 85), 40), seed=(1040, 600))
rl, rr = outline_points(lobe_l, (610, 470)), outline_points(lobe_r, (1030, 470))
pts = figure_eight(rl, (610, 470), rr, (1030, 470), cross=(820, 470))
check("projects/x/assets/fig.webp", {"inner": pts})   # writes trace_check.png: look at it
d = smooth_path(pts)                                   # the SVG path
```

2. Store long paths in `inject.json` (`{"__INNER__": d}`) and reference `__INNER__` in the page.
3. Move a dot with `path.getPointAtLength(progress * path.getTotalLength())` inside `onRender`.
   Use `smooth_path` (Catmull-Rom) so the motion has no corners.
4. Hide the dot when it passes behind something round (fade by distance from the center).

`projects/to-boldly-go` grows the loop layer by layer (inner lobes, middle, outer arrows) with a
spotlight on the active layer, then slows the dot to a stop and turns it red when the loop "stalls".

## Slowing to a stop

```js
function travel(t, t0, speed, s1, s2){ /* constant speed until s1, then eases to a stop at s2 */ }
```

Stop exactly when the narration says it (the stall line's event `at`).

## Looping motifs

An ∞ (lemniscate) path with a dot and a growing trail closes the example. Drive it with `vt` so it
always completes as the video ends: `laps = clamp((vt - V(start)) / (D - V(start))) * 2`.

## Card metaphors (from the example)

- Faster: a dot circling the same zone quickly (`vt`-driven).
- Further: the zone grows outward, with a ripple that keeps reaching.
- Afresh: a new zone appears beside the old, joined by a dashed link.

Avoid rings or pies for shares that do not sum to 100%; a bar labelled "of responses" reads honestly.

## Timing feel

- Entrances 0.6 s, eased out. Stagger siblings by 0.15 to 0.5 s.
- Nothing important moves faster than about one loop per 4 seconds.
- Every pace change is eased by the engine (a short moving average on the time map).
