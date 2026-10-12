"""Render the page to a silent MP4, frame by frame, so motion is smooth and identical every time."""
from __future__ import annotations
import subprocess
from pathlib import Path

CAPTURE_CSS = """
.wrap{max-width:none!important;padding:0!important;gap:0!important}
.head,.controls,.chips{display:none!important}
.screen{border-radius:0!important;box-shadow:none!important;width:%(w)dpx!important;height:%(h)dpx!important;aspect-ratio:auto!important}
html,body{margin:0!important;background:#fff!important}
"""


def render(page: Path, out: Path, fps: int = 30, width: int = 1920, start: float = 0.0, end: float | None = None,
           crf: int = 16, progress: bool = True) -> Path:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        raise SystemExit("Playwright is missing: pip install playwright && playwright install chromium")
    w, h = width, round(width * 9 / 16 / 2) * 2
    out.parent.mkdir(parents=True, exist_ok=True)
    ff = subprocess.Popen(
        ["ffmpeg", "-y", "-loglevel", "error", "-f", "image2pipe", "-framerate", str(fps), "-c:v", "png", "-i", "-",
         "-vf", "format=yuv420p", "-c:v", "libx264", "-preset", "slow", "-crf", str(crf), "-movflags", "+faststart", str(out)],
        stdin=subprocess.PIPE)
    with sync_playwright() as p:
        browser = p.chromium.launch()
        pg = browser.new_page(viewport={"width": w, "height": h})
        pg.goto(page.resolve().as_uri())
        pg.add_style_tag(content=CAPTURE_CSS % {"w": w, "h": h})
        pg.wait_for_function("window.__D !== undefined")
        pg.evaluate("document.fonts.ready")
        pg.wait_for_timeout(600)
        D = pg.evaluate("window.__D")
        end = D if end is None else min(end, D)
        n = max(1, int(round((end - start) * fps)))
        for i in range(n):
            t = end if i == n - 1 else start + i / fps
            pg.evaluate(f"window.__seek({t:.4f})")
            ff.stdin.write(pg.screenshot(clip={"x": 0, "y": 0, "width": w, "height": h}))
            if progress and i % (fps * 5) == 0:
                print(f"  rendering {t:5.1f}s / {end:.1f}s", flush=True)
        browser.close()
    ff.stdin.close()
    if ff.wait() != 0:
        raise SystemExit("ffmpeg failed while encoding the video")
    return out


def still(page: Path, out: Path, t: float, width: int = 1920) -> Path:
    """One frame as a PNG: quick for checking a layout or a theme."""
    from playwright.sync_api import sync_playwright
    w, h = width, round(width * 9 / 16)
    with sync_playwright() as p:
        browser = p.chromium.launch()
        pg = browser.new_page(viewport={"width": w, "height": h})
        pg.goto(page.resolve().as_uri())
        pg.add_style_tag(content=CAPTURE_CSS % {"w": w, "h": h})
        pg.wait_for_function("window.__D !== undefined")
        pg.evaluate("document.fonts.ready")
        pg.wait_for_timeout(600)
        pg.evaluate(f"window.__seek({t:.4f})")
        pg.screenshot(path=str(out), clip={"x": 0, "y": 0, "width": w, "height": h})
        browser.close()
    return out
