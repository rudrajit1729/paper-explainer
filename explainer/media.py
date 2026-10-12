"""Mixing, clips, and getting figures and text out of a paper (ffmpeg and poppler do the work)."""
from __future__ import annotations
import re, shutil, subprocess
from pathlib import Path


def _ff(*args):
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *map(str, args)], check=True)


def need(tool: str, hint: str):
    if not shutil.which(tool):
        raise SystemExit(f"'{tool}' is not installed. {hint}")


# ---------------------------------------------------------------- audio + video
def mux_music(video: Path, music: Path, out: Path) -> Path:
    """Video + music at a presentation-friendly level (-19 LUFS)."""
    _ff("-i", video, "-i", music, "-filter_complex", "[1:a]loudnorm=I=-19:TP=-1.5:LRA=11,aresample=48000[a]",
        "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", out)
    return out


def mux_voice(video: Path, voice: Path, music: Path | None, out: Path) -> Path:
    """Video + narration (-16 LUFS), with the music ducking under the voice."""
    if music is None:
        _ff("-i", video, "-i", voice, "-filter_complex", "[1:a]loudnorm=I=-16:TP=-1.5:LRA=7,aresample=48000[a]",
            "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", out)
        return out
    graph = ("[1:a]loudnorm=I=-16:TP=-1.5:LRA=7,aresample=48000,asplit=2[v1][v2];"
             "[2:a]loudnorm=I=-25:LRA=11,aresample=48000[m];"
             "[m][v1]sidechaincompress=threshold=0.04:ratio=5:attack=20:release=450[md];"
             "[md][v2]amix=inputs=2:normalize=0,alimiter=limit=0.9[a]")
    _ff("-i", video, "-i", voice, "-i", music, "-filter_complex", graph,
        "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", out)
    return out


def cut(video: Path, start: float, end: float, out: Path, fade: float = 0.45, keep_audio: bool = False) -> Path:
    """A clip between two video times, fading in and out of white."""
    dur = end - start
    vf = f"fade=t=in:st=0:d={fade}:color=white,fade=t=out:st={max(0, dur - fade):.2f}:d={fade}:color=white,format=yuv420p"
    args = ["-ss", f"{start:.3f}", "-i", video, "-t", f"{dur:.3f}", "-vf", vf, "-c:v", "libx264", "-preset", "slow",
            "-crf", "16", "-movflags", "+faststart"]
    args += (["-c:a", "aac", "-b:a", "192k"] if keep_audio else ["-an"])
    _ff(*args, out)
    return out


def gif(video: Path, out: Path, width: int = 960, fps: int = 15) -> Path:
    """A GIF for a README or a slide that can't play video."""
    _ff("-i", video, "-vf", f"fps={fps},scale={width}:-1:flags=lanczos,split[a][b];[a]palettegen=stats_mode=diff[p];[b][p]paletteuse=dither=bayer:bayer_scale=4",
        out)
    return out


# ---------------------------------------------------------------- papers
def extract_paper(pdf: Path, dest: Path) -> dict:
    """Pull the text, the figure captions and the embedded images out of a paper PDF."""
    need("pdftotext", "Install poppler (macOS: brew install poppler; Ubuntu: apt install poppler-utils).")
    dest.mkdir(parents=True, exist_ok=True)
    subprocess.run(["pdftotext", "-layout", str(pdf), str(dest / "paper.txt")], check=True)
    text = (dest / "paper.txt").read_text(errors="ignore")
    caps = re.findall(r"^\s*((?:Fig\.|Figure|TABLE|Table)\s+[IVX\d]+\b[.:]?.{0,220})", text, re.M)
    (dest / "figures.md").write_text("# Figures and tables found in the paper\n\n" + "\n".join(f"- {c.strip()}" for c in caps))
    img = dest / "images"; img.mkdir(exist_ok=True)
    subprocess.run(["pdfimages", "-png", "-p", str(pdf), str(img / "img")], check=False)
    return {"text": dest / "paper.txt", "figures": dest / "figures.md", "images": img, "captions": len(caps)}


def figure_from_pdf(pdf: Path, page: int, out: Path, crop: tuple | None = None, transparent: bool = True,
                    dpi: int = 300, width: int = 1640) -> Path:
    """Get a figure: the largest image embedded on `page`, or the page rendered at `dpi` and cropped.

    crop is (x0, y0, x1, y1) as fractions of the page, e.g. (0.08, 0.1, 0.92, 0.45).
    transparent=True turns the white background see-through so the figure sits on any theme.
    """
    from PIL import Image
    import numpy as np, tempfile
    need("pdfimages", "Install poppler (macOS: brew install poppler).")
    tmp = Path(tempfile.mkdtemp())
    im = None
    if crop is None:
        subprocess.run(["pdfimages", "-png", "-f", str(page), "-l", str(page), str(pdf), str(tmp / "e")], check=True)
        imgs = [p for p in tmp.glob("e-*.png")]
        masks = {p for p in imgs if Image.open(p).mode in ("L", "1") and len(imgs) > 1}
        cands = sorted(set(imgs) - masks, key=lambda p: Image.open(p).size[0] * Image.open(p).size[1], reverse=True)
        if cands:
            im = Image.open(cands[0]).convert("RGB")
    if im is None:
        subprocess.run(["pdftoppm", "-png", "-r", str(dpi), "-f", str(page), "-l", str(page), str(pdf), str(tmp / "p")], check=True)
        im = Image.open(next(tmp.glob("p*.png"))).convert("RGB")
        if crop:
            W, H = im.size
            im = im.crop((int(crop[0] * W), int(crop[1] * H), int(crop[2] * W), int(crop[3] * H)))
    if width and im.size[0] > width:
        im = im.resize((width, round(im.size[1] * width / im.size[0])), Image.LANCZOS)
    if transparent:
        a = np.asarray(im).astype(float)
        alpha = np.clip((255 - a.min(axis=2)) / 9.0, 0, 1) * 255
        im = Image.fromarray(np.dstack([a, alpha]).astype(np.uint8), "RGBA")
    out.parent.mkdir(parents=True, exist_ok=True)
    im.save(out, "WEBP", quality=88, method=6)
    print(f"  {out}  {im.size[0]}x{im.size[1]}")
    return out
