"""Turn shapes in a figure into SVG paths, so motion can follow the figure's own lines.

Typical use (see .claude/skills/paper-explainer/references/motion.md):

    from explainer.trace import load, near_color, region, outline_points, stroke_points, smooth_path, figure_eight
    img = load("assets/fig.webp", width=1640)                 # same size the page draws it at
    lobe = region(near_color(img, (78, 72, 64), 40), seed=(600, 600))
    r = outline_points(lobe, center=(610, 470))              # radius of the outline at every degree
    d = smooth_path(polar_to_xy(r, (610, 470), range(24, 337, 6)))

All coordinates are in the figure's pixel space at the width you load it at.
"""
from __future__ import annotations
import math
import numpy as np


def load(path, width: int | None = None) -> np.ndarray:
    from PIL import Image
    im = Image.open(path).convert("RGBA")
    if width and im.size[0] != width:
        im = im.resize((width, round(im.size[1] * width / im.size[0])), Image.LANCZOS)
    a = np.asarray(im).astype(float)
    rgb, alpha = a[..., :3], a[..., 3:4] / 255
    return (rgb * alpha + 255 * (1 - alpha)).astype(int)        # flatten onto white


def near_color(img: np.ndarray, rgb, tol: float = 30) -> np.ndarray:
    """Mask of pixels within `tol` of a color. Sample colors with img[y, x]."""
    return np.sqrt(((img - np.array(rgb)) ** 2).sum(2)) < tol


def orange_like(img: np.ndarray) -> np.ndarray:
    """Mask for saturated warm strokes (arrows, highlights). Adjust the thresholds for other hues."""
    r, g, b = img[..., 0], img[..., 1], img[..., 2]
    return (r > 140) & (g > 60) & (g < 160) & (b < 110) & (r - b > 90) & (r - g > 40)


def region(mask: np.ndarray, seed, close: int = 3) -> np.ndarray:
    """The connected shape in `mask` that contains `seed` (x, y), with holes filled."""
    from scipy import ndimage as nd
    m = nd.binary_closing(mask, iterations=close)
    lab, _ = nd.label(m)
    return nd.binary_fill_holes(lab == lab[seed[1], seed[0]])


def outline_points(mask: np.ndarray, center, smooth: int = 5, stop=None) -> np.ndarray:
    """Outer radius of a shape from `center` at each degree 0..359, smoothed.
    `stop(x, y)` can end a ray early (for example at another shape)."""
    H, W = mask.shape
    cx, cy = center
    r = np.full(360, np.nan)
    for k in range(360):
        a = math.radians(k); best = None
        for rr in range(1, max(H, W)):
            x = int(round(cx + rr * math.cos(a))); y = int(round(cy + rr * math.sin(a)))
            if x < 0 or y < 0 or x >= W or y >= H or (stop and stop(x, y)):
                break
            if mask[y, x]:
                best = rr
        if best:
            r[k] = best
    idx = np.arange(360); good = ~np.isnan(r)
    r = np.interp(idx, np.concatenate([idx[good] - 360, idx[good], idx[good] + 360]), np.tile(r[good], 3))
    for _ in range(2):
        pad = np.concatenate([r[-smooth:], r, r[:smooth]])
        r = np.convolve(pad, np.ones(2 * smooth + 1) / (2 * smooth + 1), mode="valid")
    return r


def polar_to_xy(r: np.ndarray, center, degrees, offset: float = 0):
    return [(center[0] + (r[k % 360] + offset) * math.cos(math.radians(k)),
             center[1] + (r[k % 360] + offset) * math.sin(math.radians(k))) for k in degrees]


def smooth_path(points, closed: bool = False) -> str:
    """Catmull-Rom spline through the points, as an SVG path `d` string (no corners)."""
    P = list(points); n = len(P)
    d = f"M{P[0][0]:.1f},{P[0][1]:.1f}"
    for i in range(n - 1):
        p0 = P[i - 1] if i > 0 else P[i]; p1 = P[i]; p2 = P[i + 1]; p3 = P[i + 2] if i + 2 < n else P[i + 1]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        d += f" C{c1[0]:.1f},{c1[1]:.1f} {c2[0]:.1f},{c2[1]:.1f} {p2[0]:.1f},{p2[1]:.1f}"
    return d + (" Z" if closed else "")


def figure_eight(left_r, left_c, right_r, right_c, cross, k0: int = 24, step: int = 6, offset: float = 0):
    """One loop around a left shape, through the crossing point, one loop around a right shape."""
    P = [cross]
    P += polar_to_xy(left_r, left_c, range(k0, 360 - k0 + 1, step), offset)
    P.append(cross)
    P += polar_to_xy(right_r, right_c, range(180 - k0, -(180 - k0) - 1, -step), offset)
    P.append(cross)
    return P


def check(img_path, paths: dict, out="trace_check.png", width: int = 1640):
    """Draw paths over the figure to see that they sit on the right lines."""
    from PIL import Image, ImageDraw
    im = Image.fromarray(load(img_path, width).astype(np.uint8)); dr = ImageDraw.Draw(im)
    colors = [(66, 133, 244), (52, 168, 83), (234, 67, 53), (251, 188, 4)]
    for i, pts in enumerate(paths.values()):
        dr.line(list(pts), fill=colors[i % 4], width=4)
    im.save(out)
    return out
