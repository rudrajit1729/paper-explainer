"""An original background score, generated in code and cued to the animation (so nothing to license).

project.json → "music":
  "eighth": 0.35,                                   seconds per eighth note (0.35 ≈ 86 bpm)
  "chords": [[0, "C9"], [4.5, "Am9"], ...]          chord changes at animation times; "-dark" = muted, low
  "layers": [                                       plucked arpeggios and textures between animation times
     {"type": "arp", "from": 4.6, "to": 11.5, "rate": "quarter", "vel": 0.13},
     {"type": "arp", "from": 12.3, "to": 22.4, "rate": "eighth", "octave": 12, "pattern": [1,2,3,4,3,2]},
     {"type": "slowdown", "from": 22.4, "to": 26.8},     notes spread out and stop at "to" (a stall)
     {"type": "pulse", "from": 18.6, "to": 22.4}],       soft low heartbeat
  "swells": [4.5, 11.5],                            airy rise into a new scene
  "thuds": [26.8],                                  low muted hit (a stop, a problem)
  "end_bells": true                                 three bell tones as the video closes
"""
from __future__ import annotations
import numpy as np
from .project import Project
from .timing import anim_to_video

SR = 48000
CHORDS = {
    "C9": [48, 55, 64, 71, 74], "Am9": [45, 52, 60, 67, 71], "F7": [41, 48, 57, 64, 69], "Gsus": [43, 50, 57, 62, 67],
    "Dm9": [38, 50, 57, 64, 65], "Em7": [40, 52, 59, 62, 67], "Bbmaj7": [46, 53, 57, 62, 69], "A": [33, 45, 52],
    "C": [48, 55, 64, 67, 72], "G": [43, 50, 59, 62, 67], "Am": [45, 52, 60, 64, 69], "F": [41, 48, 57, 60, 65],
}


def _m2f(m): return 440 * 2 ** ((m - 69) / 12)


def _butter(x, fc, kind):
    from scipy.signal import butter, sosfilt
    return sosfilt(butter(2, fc, kind, fs=SR, output="sos"), x)


def compose(project: Project, timemap: dict, out_path) -> str:
    from scipy.io import wavfile
    from scipy.signal import fftconvolve
    spec = project.cfg.get("music", {})
    keys, T = timemap["keys"], timemap["total"]
    V = lambda a: T if a == "end" else anim_to_video(keys, float(a))
    N = int(SR * T)
    rng = np.random.default_rng(7)
    E = float(spec.get("eighth", 0.35))
    buf = lambda: np.zeros(N)

    def add(bus, start, sig):
        i = int(start * SR)
        if 0 <= i < N:
            j = min(N, i + len(sig)); bus[i:j] += sig[: j - i]

    # chords → video time
    raw = spec.get("chords", [[0, "C9"]])
    chords = []
    for k, (a, name) in enumerate(raw):
        s = V(a); e = V(raw[k + 1][0]) if k + 1 < len(raw) else T
        dark = name.endswith("-dark")
        chords.append((s, e, CHORDS[name.replace("-dark", "")], dark))

    def chord_at(t):
        for s, e, n, _ in chords:
            if s <= t < e:
                return n
        return chords[-1][2]

    # pad
    pad, dark = buf(), buf()
    for s, e, notes, is_dark in chords:
        L = e - s + 2.2; t = np.arange(int(L * SR)) / SR
        env = np.minimum(1, t / 1.1) * np.clip((e - s + 0.9 - t) / 1.3, 0, 1)
        for k, mn in enumerate(notes):
            f = _m2f(mn); v = 0.11 if k else 0.15
            tone = sum(a * np.sin(2 * np.pi * f * h * t * (1 + d)) for d in (-0.0023, 0.0023)
                       for h, a in ((1, 1), (2, .35), (3, .16), (4, .07)))
            add(dark if is_dark else pad, max(0, s - 0.2), v * tone * env)
    pad = _butter(pad, 2200, "low") * 0.32
    dark = _butter(dark, 520, "low") * 0.22

    def pluck(f, dur=1.1, vel=1.0):
        t = np.arange(int(dur * SR)) / SR
        x = np.sin(2 * np.pi * f * t) + .32 * np.sin(4 * np.pi * f * t) + .12 * np.sin(6 * np.pi * f * t)
        return vel * x * np.minimum(1, t / 0.004) * np.exp(-t * 4.2)

    arp, high, pulse, air, thud, bell = buf(), buf(), buf(), buf(), buf(), buf()
    for L in spec.get("layers", []):
        a, b = V(L["from"]), (T - 1.5 if L["to"] == "end" else V(L["to"]))
        vel = float(L.get("vel", 0.13)); octv = int(L.get("octave", 12)); pat = L.get("pattern", [1, 2, 3, 4, 3, 2])
        layer = high if octv >= 24 else arp
        if L["type"] == "arp":
            step = E * (2 if L.get("rate", "quarter") == "quarter" else 1)
            tt, i = a, 0
            while tt < b - 0.05:
                n = chord_at(tt); m = n[pat[i % len(pat)] % len(n)] + octv
                add(layer, tt, pluck(_m2f(m), vel=vel * (1.0 if i % 4 == 0 else .72)))
                tt += step; i += 1
        elif L["type"] == "slowdown":
            tt, i = a, 0
            while tt < b - 0.05:
                n = chord_at(tt); m = n[(1, 2, 3, 4)[i % 4]] + octv; r = (tt - a) / max(1e-6, b - a)
                add(arp, tt, pluck(_m2f(m), vel=vel * (1 - 0.5 * r)))
                i += 1; tt += E * (1 + r ** 1.6 * 3.2)
        elif L["type"] == "pulse":
            tt = a
            while tt < b:
                t = np.arange(int(.5 * SR)) / SR; f = 60 * np.exp(-t * 6) + 41
                add(pulse, tt, .28 * np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 7)); tt += E * 2
    arp = _butter(arp, 5200, "low"); high = _butter(high, 7000, "low")

    for c in spec.get("swells", []):
        L = 1.6; t = np.arange(int(L * SR)) / SR
        env = np.where(t < 1.1, (t / 1.1) ** 2, np.exp(-(t - 1.1) * 9))
        add(air, V(c) - 1.1, .05 * rng.standard_normal(len(t)) * env)
    air = _butter(_butter(air, 6000, "low"), 900, "high")
    for c in spec.get("thuds", []):
        t = np.arange(int(1.6 * SR)) / SR
        add(thud, V(c), .32 * np.sin(2 * np.pi * np.cumsum(70 * np.exp(-t * 3) + 44) / SR) * np.exp(-t * 2.6))
    if spec.get("end_bells", True):
        def chime(f, start, v):
            t = np.arange(int(3 * SR)) / SR
            x = sum(a * np.sin(2 * np.pi * f * r * t) * np.exp(-t * dk) for r, a, dk in ((1, 1, 1.6), (2.76, .35, 3.5), (5.4, .12, 6), (2, .25, 2.4)))
            add(bell, start, v * x * np.minimum(1, t / 0.003))
        chime(_m2f(76), T - 1.45, .16); chime(_m2f(83), T - 1.2, .10); chime(_m2f(72), T - 0.95, .13)

    dry = pad + dark + arp + high + pulse + air + thud + bell

    def ir(seed):
        r = np.random.default_rng(seed); t = np.arange(int(2.4 * SR)) / SR
        return _butter(r.standard_normal(len(t)) * np.exp(-t / 0.55), 5000, "low") * 0.02
    Lc = dry + np.roll(arp, int(.011 * SR)) * .25 + np.roll(high, int(.017 * SR)) * .3
    Rc = dry + np.roll(arp, int(.007 * SR)) * .25 - np.roll(high, int(.013 * SR)) * .1
    out = np.stack([Lc * .78 + fftconvolve(Lc, ir(1))[:N] * .9, Rc * .78 + fftconvolve(Rc, ir(2))[:N] * .9], 1)
    t = np.arange(N) / SR
    out *= np.minimum(1, t / 0.6)[:, None] * np.clip((T - t) / 1.4, 0, 1)[:, None]
    out = np.tanh(out * 0.8) / np.tanh(0.8)
    out /= np.max(np.abs(out)) / 0.85
    wavfile.write(str(out_path), SR, (out * 32767).astype(np.int16))
    return str(out_path)
