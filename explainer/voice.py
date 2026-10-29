"""Narration audio, three ways. Every engine writes build/<lang>/voice/<line>.wav (48 kHz mono) and durations.json.

  ai        Kokoro (Apache-2.0, 82M parameters, runs offline on a laptop CPU). Dozens of voices, 8 languages.
  clone     Your own voice from a short reference recording, using Chatterbox (MIT; English).
            Record 10–30 s of yourself reading anything, save it as recordings/<lang>/reference.wav.
  recorded  You read the script yourself. Either one file per line (recordings/<lang>/<line>.wav)
            or a single take (recordings/<lang>/take.wav) that is split at the pauses.
"""
from __future__ import annotations
import json, os, urllib.request
from pathlib import Path
import numpy as np
from .project import Project, write_json

SR = 48000
CACHE = Path(os.environ.get("EXPLAINER_CACHE", Path.home() / ".cache" / "paper-explainer"))
KOKORO_FILES = {
    "kokoro-v1.0.onnx": "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx",
    "voices-v1.0.bin": "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin",
}
VOICE_PREFIX = {"en-us": "a", "en-gb": "b", "es": "e", "fr-fr": "f", "hi": "h", "it": "i", "pt-br": "p", "ja": "j", "cmn": "z"}
SAMPLE_TEXT = {"en-us": "Most studies ask how much faster AI makes developers. We asked what it lets them do.",
               "en-gb": "Most studies ask how much faster AI makes developers. We asked what it lets them do.",
               "es": "La mayoría de los estudios preguntan cuánto más rápido trabajan los desarrolladores con IA.",
               "fr-fr": "La plupart des études demandent à quel point l'IA rend les développeurs plus rapides.",
               "hi": "ज़्यादातर अध्ययन पूछते हैं कि एआई डेवलपर्स को कितना तेज़ बनाता है।",
               "it": "La maggior parte degli studi chiede quanto l'IA renda più veloci gli sviluppatori.",
               "pt-br": "A maioria dos estudos pergunta o quanto a IA torna os desenvolvedores mais rápidos.",
               "ja": "多くの研究は、AIで開発者がどれだけ速くなるかを問います。",
               "cmn": "大多数研究问的是，人工智能让开发者快了多少。"}
# a good default voice per language (see docs for the full list)
DEFAULT_VOICE = {"en-us": "af_heart", "en-gb": "bf_emma", "es": "ef_dora", "fr-fr": "ff_siwis", "hi": "hf_alpha",
                 "it": "if_sara", "pt-br": "pf_dora", "ja": "jf_alpha", "cmn": "zf_xiaobei"}


# ---------------------------------------------------------------- helpers
def _resample(a: np.ndarray, sr: int) -> np.ndarray:
    if sr == SR:
        return a
    from scipy.signal import resample_poly
    from math import gcd
    g = gcd(sr, SR)
    return resample_poly(a, SR // g, sr // g)


def _trim(a: np.ndarray, thresh: float = 0.01, head: float = 0.03, tail: float = 0.12) -> np.ndarray:
    idx = np.nonzero(np.abs(a) > thresh * max(1e-9, np.abs(a).max()))[0]
    if not len(idx):
        return a
    return a[max(0, idx[0] - int(head * SR)): idx[-1] + int(tail * SR)]


def _level(a: np.ndarray, target_rms: float = 0.08) -> np.ndarray:
    rms = np.sqrt(np.mean(a ** 2)) or 1.0
    a = a * (target_rms / rms)
    peak = np.abs(a).max()
    return a / peak * 0.95 if peak > 0.95 else a


def _mono(a: np.ndarray) -> np.ndarray:
    return a.mean(axis=1) if a.ndim == 2 else a


def _save_all(project: Project, lang: str, clips: dict[str, np.ndarray]) -> dict:
    import soundfile as sf
    out = project.voice_dir(lang)
    durs = {}
    for cid, a in clips.items():
        a = _level(_trim(a))
        sf.write(out / f"{cid}.wav", a.astype(np.float32), SR)
        durs[cid] = round(len(a) / SR, 3)
    write_json(out / "durations.json", durs)
    return durs


def ensure_kokoro():
    """Download the Kokoro model once (about 350 MB) into the cache."""
    CACHE.mkdir(parents=True, exist_ok=True)
    for name, url in KOKORO_FILES.items():
        if not (CACHE / name).exists():
            print(f"  downloading {name} (one time)…", flush=True)
            urllib.request.urlretrieve(url, CACHE / name)


# ---------------------------------------------------------------- engines
def ai_voice(project: Project, lang: str, voice: str | None = None, speed: float | None = None) -> dict:
    """Synthesize every line with Kokoro."""
    try:
        from kokoro_onnx import Kokoro
    except ImportError:
        raise SystemExit("Kokoro is missing: pip install kokoro-onnx soundfile")
    ensure_kokoro()
    n = project.narration(lang)
    code = n.get("lang", "en-us")
    voice = voice or n.get("voice") or DEFAULT_VOICE.get(code, "af_heart")
    speed = speed or float(n.get("speed", 1.0))
    k = Kokoro(str(CACHE / "kokoro-v1.0.onnx"), str(CACHE / "voices-v1.0.bin"))
    clips = {}
    for cid in project.line_ids():
        text = n["lines"].get(cid, "").strip()
        if not text:
            clips[cid] = np.zeros(int(0.1 * SR)); continue
        # narration "voices" maps a line id to its own voice (a second character); others use the default
        a, sr = k.create(text, voice=n.get("voices", {}).get(cid, voice), speed=speed, lang=code)
        clips[cid] = _resample(np.asarray(a, dtype=np.float64), sr)
        print(f"  {cid}: {text[:60]}", flush=True)
    return _save_all(project, lang, clips)


def clone_voice(project: Project, lang: str, reference: Path | None = None, exaggeration: float = 0.5) -> dict:
    """Speak every line in your own voice, cloned from a short reference recording (Chatterbox)."""
    try:
        import torch
        from chatterbox.tts import ChatterboxTTS
    except ImportError:
        raise SystemExit("Voice cloning needs Chatterbox: pip install chatterbox-tts  (about 2 GB with PyTorch)")
    ref = reference or project.root / "recordings" / lang / "reference.wav"
    if not ref.exists():
        raise SystemExit(f"Record 10–30 s of yourself reading anything and save it as {ref}")
    device = "cuda" if torch.cuda.is_available() else ("mps" if torch.backends.mps.is_available() else "cpu")
    model = ChatterboxTTS.from_pretrained(device=device)
    n = project.narration(lang)
    clips = {}
    for cid in project.line_ids():
        text = n["lines"].get(cid, "").strip()
        if not text:
            clips[cid] = np.zeros(int(0.1 * SR)); continue
        wav = model.generate(text, audio_prompt_path=str(ref), exaggeration=exaggeration)
        clips[cid] = _resample(wav.squeeze(0).cpu().numpy().astype(np.float64), model.sr)
        print(f"  {cid}: {text[:60]}", flush=True)
    return _save_all(project, lang, clips)


def recorded_voice(project: Project, lang: str) -> dict:
    """Use your own recordings: one file per line, or one take split at the pauses."""
    import soundfile as sf
    rec = project.root / "recordings" / lang
    ids = project.line_ids()
    clips = {}
    if all((rec / f"{cid}.wav").exists() for cid in ids):
        for cid in ids:
            a, sr = sf.read(rec / f"{cid}.wav")
            clips[cid] = _resample(_mono(a), sr)
    elif (rec / "take.wav").exists():
        a, sr = sf.read(rec / "take.wav")
        parts = split_take(_resample(_mono(a), sr), len(ids))
        clips = dict(zip(ids, parts))
    else:
        missing = [cid for cid in ids if not (rec / f"{cid}.wav").exists()]
        raise SystemExit(f"Put one WAV per line in {rec}/ (missing: {', '.join(missing[:6])}…) "
                         f"or a single take as {rec}/take.wav. `explainer script` prints what to read.")
    return _save_all(project, lang, clips)


def split_take(a: np.ndarray, count: int) -> list[np.ndarray]:
    """Cut one long recording into `count` lines at its longest pauses."""
    hop = int(0.02 * SR)
    frames = np.sqrt(np.convolve(a ** 2, np.ones(hop) / hop, mode="same"))[::hop]
    quiet = frames < max(frames.max() * 0.04, 1e-4)
    gaps, i = [], 0
    while i < len(quiet):                       # find silent runs
        if quiet[i]:
            j = i
            while j < len(quiet) and quiet[j]:
                j += 1
            if i > 0 and j < len(quiet):
                gaps.append((j - i, (i + j) // 2))
            i = j
        else:
            i += 1
    if len(gaps) < count - 1:
        raise SystemExit(f"Found {len(gaps) + 1} phrases but the script has {count} lines. "
                         "Leave a clear one-second pause between lines, or record one file per line.")
    cuts = sorted(c for _, c in sorted(gaps, reverse=True)[: count - 1])
    bounds = [0] + [c * hop for c in cuts] + [len(a)]
    return [a[s:e] for s, e in zip(bounds, bounds[1:])]


def recording_script(project: Project, lang: str) -> Path:
    """A printable script for recording your own voice."""
    n = project.narration(lang)
    lines = [f"# Recording script ({lang})", "",
             "Read each line in a natural voice. Either save each one as its own file",
             f"(recordings/{lang}/<id>.wav) or record all of them in one take",
             f"(recordings/{lang}/take.wav) with a one-second pause between lines.", ""]
    for cid in project.line_ids():
        lines += [f"**{cid}**  {n['lines'].get(cid, '')}", ""]
    out = project.build(lang) / "recording_script.md"
    out.write_text("\n".join(lines))
    return out


def voice_track(project: Project, lang: str, timemap: dict) -> Path:
    """Place every line at its start time in one WAV for the whole video."""
    import soundfile as sf
    vdir = project.voice_dir(lang)
    track = np.zeros(int((timemap["total"] + 1) * SR))
    for cid, start in timemap["voice"]:
        p = vdir / f"{cid}.wav"
        if p.exists():
            a, _ = sf.read(p)
            i = int(start * SR)
            track[i:i + len(a)] += a[: max(0, len(track) - i)]
    out = project.build(lang) / "voice_track.wav"
    sf.write(out, track[: int(timemap["total"] * SR)].astype(np.float32), SR)
    return out
