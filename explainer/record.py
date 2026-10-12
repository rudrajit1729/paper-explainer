"""A small recording studio in the browser: `explainer record <project> --lang en`.

Opens a local page that shows each narration line, records it from your microphone, and saves
recordings/<lang>/<id>.wav (and recordings/<lang>/reference.wav for voice cloning). Everything stays
on your computer; the page talks only to this local server.
"""
from __future__ import annotations
import json, subprocess, tempfile, threading, webbrowser
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse, parse_qs
from .project import Project, WEB

REFERENCE_TEXT = {
    "en": ("When I started this project, I wanted to understand how people actually do their work, "
           "not how we imagine they do it. So we listened. We asked open questions, read every answer, "
           "and looked for the patterns that kept coming back. Some of them surprised us. Most of them "
           "made us rethink what good tools should do, and what they should leave to people."),
    "es": ("Cuando empecé este proyecto, quería entender cómo trabajan realmente las personas. "
           "Así que escuchamos. Hicimos preguntas abiertas, leímos cada respuesta y buscamos los patrones "
           "que se repetían. Algunos nos sorprendieron, y muchos nos hicieron repensar qué deberían hacer "
           "las buenas herramientas."),
}


def serve(project: Project, lang: str, port: int = 8765, open_browser: bool = True):
    n = project.narration(lang)
    folder = project.root / "recordings" / lang
    folder.mkdir(parents=True, exist_ok=True)
    rel = project.root.name
    data = {
        "lang": lang,
        "folder": f"projects/{project.root.name}/recordings/{lang}",
        "lines": [{"id": cid, "text": n["lines"].get(cid, "")} for cid in project.line_ids()],
        "reference_text": REFERENCE_TEXT.get(lang.split("-")[0], REFERENCE_TEXT["en"]),
        "build_cmd": f"explainer build projects/{rel} --mode voice --engine recorded --lang {lang}",
        "clone_cmd": f"explainer build projects/{rel} --mode voice --engine clone --lang {lang}",
    }
    page = (WEB / "recorder.html").read_text().replace(
        "<script>\nconst DATA", f"<script>window.RECORDER_DATA = {json.dumps(data, ensure_ascii=False)};</script>\n<script>\nconst DATA", 1)

    def seconds(p: Path) -> float:
        import soundfile as sf
        info = sf.info(p)
        return round(info.frames / info.samplerate, 2)

    class H(BaseHTTPRequestHandler):
        def log_message(self, *a): pass

        def _send(self, body: bytes, ctype: str, code: int = 200):
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            u = urlparse(self.path); q = parse_qs(u.query)
            if u.path in ("/", "/index.html"):
                return self._send(page.encode(), "text/html; charset=utf-8")
            if u.path.startswith("/fonts/"):
                f = WEB / "fonts" / Path(u.path).name
                if f.exists():
                    return self._send(f.read_bytes(), "font/woff2")
            if u.path == "/status":
                s = {p.stem: seconds(p) for p in folder.glob("*.wav")}
                return self._send(json.dumps(s).encode(), "application/json")
            if u.path == "/audio":
                f = folder / f"{Path(q.get('id', [''])[0]).name}.wav"
                if f.exists():
                    return self._send(f.read_bytes(), "audio/wav")
            self._send(b"not found", "text/plain", 404)

        def do_POST(self):
            u = urlparse(self.path); q = parse_qs(u.query)
            if u.path != "/save":
                return self._send(b"not found", "text/plain", 404)
            cid = Path(q.get("id", [""])[0]).name
            body = self.rfile.read(int(self.headers.get("Content-Length", 0)))
            if not cid or not body:
                return self._send(json.dumps({"ok": False, "error": "Empty recording"}).encode(), "application/json")
            with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as tmp:
                tmp.write(body)
            out = folder / f"{cid}.wav"
            r = subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", tmp.name, "-ac", "1", "-ar", "48000", str(out)])
            Path(tmp.name).unlink(missing_ok=True)
            if r.returncode != 0:
                return self._send(json.dumps({"ok": False, "error": "ffmpeg could not read the recording"}).encode(), "application/json")
            print(f"  saved {out.relative_to(project.root)} ({seconds(out)} s)", flush=True)
            self._send(json.dumps({"ok": True, "seconds": seconds(out)}).encode(), "application/json")

    httpd = ThreadingHTTPServer(("127.0.0.1", port), H)
    url = f"http://localhost:{port}/"
    print(f"Recorder running at {url}  (Ctrl+C to stop)\nSaving into {folder}")
    if open_browser:
        threading.Timer(0.5, lambda: webbrowser.open(url)).start()
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()
    return httpd
