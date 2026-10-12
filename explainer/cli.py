"""explainer: turn a paper into an animated explainer video.

  explainer build projects/to-boldly-go --mode voice            whole pipeline → projects/<name>/output/*.mp4
  explainer build projects/to-boldly-go --mode read --preview   fast low-res check (12 fps, 960 px)

Run `explainer <command> -h` for the options of any step.
"""
from __future__ import annotations
import argparse, shutil, sys
from pathlib import Path
from .project import Project, PKG, read_json

LANG_HELP = "narration language file to use: narration/<lang>.json (default en)"


def _p(args) -> Project:
    return Project.load(args.project)


def _slug(s: str) -> str:
    return "".join(c if c.isalnum() else "_" for c in s).strip("_")


# ---------------------------------------------------------------- steps
def cmd_new(a):
    from .media import extract_paper
    src = PKG / "templates" / ("starter" if a.template == "starter" else "")
    if a.template != "starter":
        src = Path(a.template)
    dest = Path(a.dir) / a.name
    if dest.exists():
        raise SystemExit(f"{dest} already exists")
    shutil.copytree(src, dest, ignore=shutil.ignore_patterns("build", "output"))
    print(f"Created {dest}")
    if a.paper:
        info = extract_paper(Path(a.paper), dest / "source")
        print(f"  paper text → {info['text']}\n  {info['captions']} figure/table captions → {info['figures']}\n  images → {info['images']}")
    print("Next: edit narration/en.json and index.html, then `explainer build " + str(dest) + " --preview`")


def cmd_paper(a):
    from .media import extract_paper
    info = extract_paper(Path(a.pdf), Path(a.project) / "source")
    print(f"text: {info['text']}\ncaptions ({info['captions']}): {info['figures']}\nimages: {info['images']}")


def cmd_figure(a):
    from .media import figure_from_pdf
    crop = tuple(float(x) for x in a.crop.split(",")) if a.crop else None
    figure_from_pdf(Path(a.pdf), a.page, Path(a.out), crop=crop, transparent=not a.opaque, width=a.width)


def cmd_voice(a):
    from . import voice
    p = _p(a)
    if a.engine == "ai":
        d = voice.ai_voice(p, a.lang, a.voice, a.speed)
    elif a.engine == "clone":
        d = voice.clone_voice(p, a.lang, Path(a.reference) if a.reference else None)
    else:
        d = voice.recorded_voice(p, a.lang)
    print(f"{len(d)} lines, {sum(d.values()):.1f} s of speech → {p.voice_dir(a.lang)}")


def cmd_script(a):
    from .voice import recording_script
    print(recording_script(_p(a), a.lang))


def cmd_timing(a):
    from .timing import build_time_map
    tm = build_time_map(_p(a), a.mode, a.lang)
    print(f"{a.mode}: {tm['total']:.1f} s")


def cmd_page(a):
    from .page import assemble, publishable
    p = _p(a)
    out = publishable(p, a.lang, a.mode, a.theme) if a.standalone else assemble(p, a.lang, a.mode, a.theme)
    print(out)


def cmd_still(a):
    from .page import assemble
    from .render import still
    from .timing import anim_to_video
    p = _p(a)
    page = assemble(p, a.lang, a.mode, a.theme)
    keys = read_json(p.build(a.lang) / f"timemap_{a.mode}.json")["keys"]
    for t in a.at:
        out = p.build(a.lang) / f"still_{a.theme or p.theme}_{t:g}.png"
        still(page, out, anim_to_video(keys, t), width=a.width)
        print(out)


def cmd_render(a):
    from .page import assemble
    from .render import render
    p = _p(a)
    page = assemble(p, a.lang, a.mode, a.theme)
    out = p.build(a.lang) / f"silent_{a.mode}_{a.theme or p.theme}.mp4"
    fps, width = (12, 960) if a.preview else (a.fps, a.width)
    render(page, out, fps=fps, width=width, crf=26 if a.preview else 16)
    print(out)


def cmd_music(a):
    from .music import compose
    p = _p(a)
    tm = read_json(p.build(a.lang) / f"timemap_{a.mode}.json")
    print(compose(p, tm, p.build(a.lang) / f"music_{a.mode}.wav"))


def cmd_build(a):
    """voice → timing → page → render → music → mix"""
    from .timing import build_time_map
    from .page import assemble
    from .render import render
    from .music import compose
    from .media import mux_music, mux_voice
    from . import voice
    p = _p(a)
    theme = a.theme or p.theme
    if a.mode == "voice" and not a.reuse_voice:
        print("1/5 voice"); cmd_voice(a)
    print("2/5 timing"); tm = build_time_map(p, a.mode, a.lang)
    print(f"     {tm['total']:.1f} s")
    print("3/5 render"); page = assemble(p, a.lang, a.mode, theme)
    fps, width = (12, 960) if a.preview else (a.fps, a.width)
    silent = render(page, p.build(a.lang) / f"silent_{a.mode}_{theme}.mp4", fps=fps, width=width, crf=26 if a.preview else 16)
    out_dir = p.root / "output"; out_dir.mkdir(exist_ok=True)
    name = f"{_slug(p.cfg.get('title', p.root.name))}_{a.lang}_{a.mode}" + ("" if theme == p.theme else f"_{theme}") + ("_preview" if a.preview else "")
    music = None
    if not a.no_music:
        print("4/5 music"); music = Path(compose(p, tm, p.build(a.lang) / f"music_{a.mode}.wav"))
    print("5/5 mix")
    out = out_dir / f"{name}.mp4"
    if a.mode == "voice":
        mux_voice(silent, voice.voice_track(p, a.lang, tm), music, out)
    elif music:
        mux_music(silent, music, out)
    else:
        shutil.copy(silent, out)
    print(f"Done → {out}")


def cmd_clip(a):
    from .media import cut
    from .timing import anim_to_video
    p = _p(a)
    theme = a.theme or p.theme
    tm = read_json(p.build(a.lang) / f"timemap_{a.mode}.json")
    src = p.build(a.lang) / f"silent_{a.mode}_{theme}.mp4"
    if not tm or not src.exists():
        raise SystemExit("Render first: explainer render <project> --mode " + a.mode)
    named = p.cfg.get("clips", {}).get(a.name or "", None)
    start, end = (named if named else (a.start, a.end))
    out = p.root / "output" / f"{_slug(p.cfg.get('title', 'clip'))}_{a.name or 'clip'}.mp4"
    out.parent.mkdir(exist_ok=True)
    print(cut(src, anim_to_video(tm["keys"], start), anim_to_video(tm["keys"], end), out))


def cmd_record(a):
    from .record import serve
    serve(_p(a), a.lang, port=a.port, open_browser=not a.no_browser)


def cmd_voices(a):
    """Audition voices: one sample WAV per voice for a language."""
    from . import voice
    import numpy as np, soundfile as sf
    try:
        from kokoro_onnx import Kokoro
    except ImportError:
        raise SystemExit("pip install kokoro-onnx soundfile")
    voice.ensure_kokoro()
    k = Kokoro(str(voice.CACHE / "kokoro-v1.0.onnx"), str(voice.CACHE / "voices-v1.0.bin"))
    prefix = voice.VOICE_PREFIX.get(a.lang)
    if not prefix:
        raise SystemExit(f"Unknown language '{a.lang}'. Use one of: {', '.join(voice.VOICE_PREFIX)}")
    names = [v for v in sorted(k.get_voices()) if v[0] in prefix]
    text = a.text or voice.SAMPLE_TEXT.get(a.lang, voice.SAMPLE_TEXT["en-us"])
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    for name in names:
        audio, sr = k.create(text, voice=name, speed=1.0, lang=a.lang)
        sf.write(out / f"{a.lang}_{name}.wav", np.asarray(audio), sr)
        print(f"  {out / (a.lang + '_' + name + '.wav')}")
    print(f"{len(names)} voices. Put the one you like in narration/<lang>.json as \"voice\".")


def cmd_add_language(a):
    """Scaffold a new narration language (and optionally a translated page)."""
    import json
    from .voice import DEFAULT_VOICE
    p = _p(a)
    src = p.root / "narration" / f"{a.source}.json"
    dst = p.root / "narration" / f"{a.lang}.json"
    if dst.exists() and not a.force:
        raise SystemExit(f"{dst} exists (use --force to overwrite)")
    n = json.loads(src.read_text())
    n["lang"] = a.code or a.lang
    n["voice"] = a.voice or DEFAULT_VOICE.get(n["lang"], n.get("voice"))
    n["lines"] = {k: f"TODO translate: {v}" for k, v in n["lines"].items()}
    dst.write_text(json.dumps(n, indent=1, ensure_ascii=False))
    print(f"Created {dst}: translate each line (keep the ids), then remove the TODO prefixes.")
    if a.page:
        page = p.root / f"index.{a.lang}.html"
        shutil.copy(p.root / p.cfg.get("page", "index.html"), page)
        print(f"Created {page}: translate only the visible text, then check with `explainer still --lang {a.lang}`.")
    print(f"Build: explainer build {a.project} --mode voice --lang {a.lang}")


def cmd_list(a):
    from .page import theme_css
    from .voice import DEFAULT_VOICE
    themes = sorted(x.stem for x in (PKG / "web" / "themes").glob("*.css"))
    print("Themes:")
    for t in themes:
        first = (PKG / "web" / "themes" / f"{t}.css").read_text().splitlines()[0].strip("/* ").rstrip(" */")
        print(f"  {first}")
    print("\nAI voice languages (narration 'lang') and a default voice for each:")
    for k, v in DEFAULT_VOICE.items():
        print(f"  {k:6s} {v}")
    print("\nMore Kokoro voices: af_bella af_nicole am_michael am_fenrir bf_isabella bm_george bm_lewis em_alex ff_siwis im_nicola pm_alex jm_kumo zm_yunxi")


# ---------------------------------------------------------------- parser
def main(argv=None):
    ap = argparse.ArgumentParser(prog="explainer", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    def proj(sp, mode=True, theme=False):
        sp.add_argument("project", help="project folder, e.g. projects/to-boldly-go")
        sp.add_argument("--lang", default="en", help=LANG_HELP)
        if mode:
            sp.add_argument("--mode", default="read", choices=["read", "voice", "fast"],
                            help="read: paced for reading with music; voice: paced to the narration; fast: original speed")
        if theme:
            sp.add_argument("--theme", default=None, help="design language (see `explainer list`); default from project.json")

    s = sub.add_parser("new", help="start a project from the starter (optionally pulling in a paper)")
    s.add_argument("name"); s.add_argument("--dir", default="projects"); s.add_argument("--paper", help="paper PDF to extract")
    s.add_argument("--template", default="starter", help="'starter' or a path to an existing project to copy")
    s.set_defaults(fn=cmd_new)

    s = sub.add_parser("paper", help="extract a paper's text, captions and images into <project>/source")
    s.add_argument("pdf"); s.add_argument("project"); s.set_defaults(fn=cmd_paper)

    s = sub.add_parser("figure", help="get one figure out of a PDF as a web image")
    s.add_argument("pdf"); s.add_argument("--page", type=int, required=True); s.add_argument("--out", required=True)
    s.add_argument("--crop", help="x0,y0,x1,y1 as page fractions, to cut a vector figure out of the rendered page")
    s.add_argument("--opaque", action="store_true", help="keep the white background"); s.add_argument("--width", type=int, default=1640)
    s.set_defaults(fn=cmd_figure)

    def voice_opts(s):
        s.add_argument("--engine", default="ai", choices=["ai", "clone", "recorded"], help="ai voice, your cloned voice, or your recordings")
        s.add_argument("--voice", help="AI voice name (see `explainer list`)"); s.add_argument("--speed", type=float)
        s.add_argument("--reference", help="clone: a 10–30 s recording of your voice (default recordings/<lang>/reference.wav)")

    s = sub.add_parser("voice", help="make the narration audio"); proj(s, mode=False); voice_opts(s); s.set_defaults(fn=cmd_voice)
    s = sub.add_parser("script", help="write a recording script for reading it yourself"); proj(s, mode=False); s.set_defaults(fn=cmd_script)
    s = sub.add_parser("timing", help="build the time map"); proj(s); s.set_defaults(fn=cmd_timing)
    s = sub.add_parser("page", help="assemble the playable page"); proj(s, theme=True)
    s.add_argument("--standalone", action="store_true", help="one HTML file with images inlined"); s.set_defaults(fn=cmd_page)
    s = sub.add_parser("still", help="PNG frames at animation times, to check a layout or theme"); proj(s, theme=True)
    s.add_argument("--at", type=float, nargs="+", required=True); s.add_argument("--width", type=int, default=1600); s.set_defaults(fn=cmd_still)
    s = sub.add_parser("render", help="render the silent video"); proj(s, theme=True)
    s.add_argument("--fps", type=int, default=30); s.add_argument("--width", type=int, default=1920)
    s.add_argument("--preview", action="store_true", help="12 fps at 960 px, fast"); s.set_defaults(fn=cmd_render)
    s = sub.add_parser("music", help="compose the score for a time map"); proj(s); s.set_defaults(fn=cmd_music)

    s = sub.add_parser("build", help="the whole pipeline"); proj(s, theme=True); voice_opts(s)
    s.add_argument("--fps", type=int, default=30); s.add_argument("--width", type=int, default=1920)
    s.add_argument("--preview", action="store_true"); s.add_argument("--no-music", action="store_true")
    s.add_argument("--reuse-voice", action="store_true", help="keep the narration audio already in build/<lang>/voice")
    s.set_defaults(fn=cmd_build)

    s = sub.add_parser("clip", help="cut a clip out of a rendered video by animation time"); proj(s, theme=True)
    s.add_argument("--name", help="a named clip from project.json 'clips', or a name for this one")
    s.add_argument("--start", type=float); s.add_argument("--end", type=float); s.set_defaults(fn=cmd_clip)

    s = sub.add_parser("record", help="record your own narration in the browser, line by line"); proj(s, mode=False)
    s.add_argument("--port", type=int, default=8765); s.add_argument("--no-browser", action="store_true"); s.set_defaults(fn=cmd_record)

    s = sub.add_parser("voices", help="audition every AI voice for a language")
    s.add_argument("--lang", default="en-us", help="en-us, en-gb, es, fr-fr, hi, it, pt-br, ja, cmn")
    s.add_argument("--text", help="what the samples say"); s.add_argument("--out", default="voice-samples")
    s.set_defaults(fn=cmd_voices)

    s = sub.add_parser("add-language", help="start narration (and optionally the page) in a new language")
    s.add_argument("project"); s.add_argument("lang", help="file name, e.g. es, fr, ja")
    s.add_argument("--code", help="voice language code if different from the file name (e.g. fr-fr, pt-br, cmn)")
    s.add_argument("--voice"); s.add_argument("--source", default="en"); s.add_argument("--page", action="store_true", help="also copy index.html to index.<lang>.html")
    s.add_argument("--force", action="store_true"); s.set_defaults(fn=cmd_add_language)

    s = sub.add_parser("list", help="themes, languages and voices"); s.set_defaults(fn=cmd_list)

    a = ap.parse_args(argv)
    a.fn(a)


if __name__ == "__main__":
    main()
