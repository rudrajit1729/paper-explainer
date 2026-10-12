"""Assemble the playable page: project HTML + engine + theme + time map + assets → build/<lang>/<mode>/index.html"""
from __future__ import annotations
import json, re, shutil
from pathlib import Path
from .project import Project, WEB, read_json

FONT_FACES = "".join(
    f"@font-face{{font-family:'Inter';font-weight:{w};font-display:block;"
    f"src:url('fonts/inter-latin-{w}-normal.woff2') format('woff2')}}\n" for w in (400, 500, 600, 700))


def theme_css(name: str) -> tuple[str, str]:
    path = WEB / "themes" / f"{name}.css"
    if not path.exists():
        names = ", ".join(p.stem for p in (WEB / "themes").glob("*.css"))
        raise SystemExit(f"Unknown theme '{name}'. Available: {names}")
    css = path.read_text()
    m = re.search(r"@font-link:\s*(\S+)", css)
    link = f'<link rel="stylesheet" href="{m.group(1)}">\n' if m else ""
    return css, link


def assemble(project: Project, lang: str, mode: str, theme: str | None = None, out: Path | None = None) -> Path:
    tm = read_json(project.build(lang) / f"timemap_{mode}.json")
    if not tm:
        raise SystemExit(f"No time map for {mode}. Run `explainer timing --mode {mode}` first.")
    html = project.page_source(lang).read_text()
    css, link = theme_css(theme or project.theme)
    head = (link + "<style>\n" + FONT_FACES + (WEB / "engine.css").read_text() + "\n" + css + "\n</style>")
    script = (f"<script>window.EXPLAINER_KEYS = {json.dumps(tm['keys'])};</script>\n"
              f"<script>\n{(WEB / 'engine.js').read_text()}\n</script>")
    if "<!-- @engine:head -->" not in html or "<!-- @engine:script -->" not in html:
        raise SystemExit("The page needs <!-- @engine:head --> near the top and <!-- @engine:script --> before its own script.")
    html = html.replace("<!-- @engine:head -->", head).replace("<!-- @engine:script -->", script)
    for key, value in (read_json(project.root / project.cfg.get("inject", "inject.json"), {}) or {}).items():
        html = html.replace(key, value)
    left = sorted(set(re.findall(r"__[A-Z][A-Z0-9_]+__", html)))
    if left:
        raise SystemExit(f"Placeholders with no value in inject.json: {', '.join(left)}")

    out = out or project.build(lang) / f"page_{mode}" / "index.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html)
    shutil.copytree(WEB / "fonts", out.parent / "fonts", dirs_exist_ok=True)
    if (project.root / "assets").exists():
        shutil.copytree(project.root / "assets", out.parent / "assets", dirs_exist_ok=True)
    return out


def publishable(project: Project, lang: str, mode: str, theme: str | None = None) -> Path:
    """One self-contained HTML file (assets inlined as data URIs), handy for sharing or hosting."""
    import base64, mimetypes
    page = assemble(project, lang, mode, theme)
    html = page.read_text()
    for ref in sorted(set(re.findall(r"""(?:src|url\()=?['"]?((?:assets|fonts)/[^'")\s>]+)""", html))):
        p = page.parent / ref
        if p.exists():
            mime = mimetypes.guess_type(p.name)[0] or ("font/woff2" if p.suffix == ".woff2" else "application/octet-stream")
            html = html.replace(ref, f"data:{mime};base64,{base64.b64encode(p.read_bytes()).decode()}")
    out = page.parent / "standalone.html"
    out.write_text(html)
    return out
