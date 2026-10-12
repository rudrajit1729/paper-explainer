"""A project is a folder:

    projects/<name>/
      project.json          timeline events, pacing, music cues, theme, clips
      index.html            the animated page (scenes on animation time)
      index.<lang>.html     optional translated page for a language
      inject.json           optional {"__PLACEHOLDER__": "value"} pasted into the page (long SVG paths etc.)
      narration/<lang>.json the narration lines, plus voice settings for that language
      recordings/<lang>/    your own voice: <line-id>.wav per line, or one take.wav
      assets/               figures and images the page uses
      build/<lang>/         everything generated (safe to delete)
"""
from __future__ import annotations
import json
from dataclasses import dataclass
from pathlib import Path

PKG = Path(__file__).resolve().parent
WEB = PKG / "web"


@dataclass
class Project:
    root: Path
    cfg: dict

    @classmethod
    def load(cls, path: str | Path) -> "Project":
        root = Path(path).resolve()
        if root.is_file():
            root = root.parent
        cfg_path = root / "project.json"
        if not cfg_path.exists():
            raise SystemExit(f"No project.json in {root}")
        return cls(root, json.loads(cfg_path.read_text()))

    # ---- paths -------------------------------------------------------------
    def build(self, lang: str) -> Path:
        p = self.root / "build" / lang
        p.mkdir(parents=True, exist_ok=True)
        return p

    def voice_dir(self, lang: str) -> Path:
        p = self.build(lang) / "voice"
        p.mkdir(parents=True, exist_ok=True)
        return p

    def page_source(self, lang: str) -> Path:
        translated = self.root / f"index.{lang}.html"
        return translated if translated.exists() else self.root / self.cfg.get("page", "index.html")

    # ---- narration ---------------------------------------------------------
    def narration(self, lang: str) -> dict:
        p = self.root / "narration" / f"{lang}.json"
        if not p.exists():
            raise SystemExit(f"No narration for '{lang}'. Create {p.relative_to(self.root)} "
                             f"(copy narration/en.json and translate the lines).")
        n = json.loads(p.read_text())
        n.setdefault("lines", {})
        return n

    def line_ids(self) -> list[str]:
        return [e["line"] for e in self.cfg["timeline"]["events"]]

    @property
    def theme(self) -> str:
        return self.cfg.get("theme", "google-apple")

    @property
    def end(self) -> float:
        return float(self.cfg["timeline"].get("end", 40))


def read_json(path: Path, default=None):
    return json.loads(path.read_text()) if path.exists() else default


def write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=1, ensure_ascii=False))
