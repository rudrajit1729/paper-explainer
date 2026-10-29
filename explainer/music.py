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
    if project.cfg.get("music", {}).get("style") == "groove":
        return compose_groove(project, timemap, out_path)
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


# ---------------------------------------------------------------- groove
GROOVE_DOC = """A driving, warm score with drums, bass, pads and plucks (project.json → "music": {"style": "groove", ...}).

  "bpm": 104,
  "progression": ["Cmaj9", "Em7", "Am9", "Fmaj9"],   one chord per bar, looping
  "sections": [[0, 1], [5.5, 2], [41, 0], [44, 3]],  [animation time, level]: 0 pad only, 1 + plucks and hats,
                                                      2 + kick, clap and bass, 3 + four-on-the-floor and 16th hats
  "risers": [41, 44],                                 a noise rise that lands on these times
  "impacts": [44],                                    a soft boom on these times
  "end": 98                                           animation time where the band stops and the bells ring
"""
GCHORDS = {
    "Cmaj9": [48, 55, 59, 62, 64], "Em7": [40, 52, 55, 59, 62], "Am9": [45, 52, 55, 59, 60], "Fmaj9": [41, 53, 57, 60, 64],
    "G6": [43, 50, 55, 59, 64], "Dm9": [38, 50, 53, 57, 64], "Bbmaj9": [46, 53, 57, 60, 62],
}


def compose_groove(project: Project, timemap: dict, out_path) -> str:
    from scipy.io import wavfile
    from scipy.signal import fftconvolve
    spec = project.cfg["music"]
    keys, T = timemap["keys"], timemap["total"]
    V = lambda a: anim_to_video(keys, float(a))
    N = int(SR * T); rng = np.random.default_rng(11)
    beat = 60.0 / float(spec.get("bpm", 104)); bar = 4 * beat
    prog = [GCHORDS[c] for c in spec.get("progression", ["Cmaj9", "Em7", "Am9", "Fmaj9"])]
    secs = sorted((V(a), int(l)) for a, l in spec.get("sections", [[0, 2]]))
    end = V(spec["end"]) if "end" in spec else T - 2.0
    level = lambda t: ([l for s0, l in secs if s0 <= t] or [secs[0][1]])[-1] if t < end else -1
    buses = {k: np.zeros(N) for k in ("kick", "clap", "hat", "bass", "pad", "pluck", "fx")}

    def add(bus, start, sig):
        i = int(start * SR)
        if i < 0: sig, i = sig[-i:], 0
        if i < N:
            j = min(N, i + len(sig)); buses[bus][i:j] += sig[: j - i]

    tt = lambda d: np.arange(int(d * SR)) / SR
    def kick():
        t = tt(.42); f = 46 + 110 * np.exp(-t * 38)
        return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 7.5) + .07 * rng.standard_normal(len(t)) * np.exp(-t * 300)
    def clap():
        t = tt(.32); n = rng.standard_normal(len(t))
        env = sum(np.exp(-np.maximum(0, t - o) * 60) * (t >= o) for o in (0, .011, .022)) / 3 + .6 * np.exp(-t * 14)
        return _butter(_butter(n * env, 900, "high"), 5200, "low") + .3 * np.sin(2 * np.pi * 190 * t) * np.exp(-t * 30)
    def hat(open_=False):
        t = tt(.18 if open_ else .05)
        return _butter(_butter(rng.standard_normal(len(t)) * np.exp(-t * (18 if open_ else 90)), 6500, "high"), 11000, "low")
    def pluck(f, d=.5):
        t = tt(d); x = np.sin(2 * np.pi * f * t) + .45 * np.sin(4 * np.pi * f * t) * np.exp(-t * 9) + .2 * np.sin(6 * np.pi * f * t) * np.exp(-t * 14)
        return x * np.minimum(1, t / .003) * np.exp(-t * 6.5)
    def bassnote(f, d):
        t = tt(d); saw = 2 * ((f * t) % 1) - 1
        return (np.sin(2 * np.pi * f * t) * .8 + _butter(saw, 700, "low") * .35) * np.minimum(1, t / .008) * np.exp(-t * 2.2)

    nbars = int(T / bar) + 2
    side = np.ones(N)                                     # sidechain envelope from the kick
    for b in range(nbars):
        t0 = b * bar; ch = prog[b % len(prog)]
        L = level(t0 + .01)
        if L < 0: continue
        # pad: detuned, slow attack, one bar
        t = tt(bar + .4); env = np.minimum(1, t / .5) * np.clip((bar + .4 - t) / .5, 0, 1)
        padsig = sum(np.sin(2 * np.pi * _m2f(m) * (1 + d) * t) + .3 * np.sin(4 * np.pi * _m2f(m) * (1 + d) * t) for m in ch[1:] for d in (-.003, 0, .003))
        add("pad", t0, padsig * env * (.075 if L else .04))
        for q in range(16):                                # sixteenth steps
            ts = t0 + q * beat / 4; Lq = level(ts)
            if Lq < 0: continue
            if Lq >= 1 and q % 2 == 0:
                m = ch[1:][(q // 2) % 4] + (12 if q % 8 < 4 else 24)
                add("pluck", ts, pluck(_m2f(m)) * (.2 if q % 4 == 0 else .13))
            if Lq >= 1 and q % 4 == 2: add("hat", ts, hat(q % 8 == 6 and Lq >= 2) * .055)
            if Lq >= 3 and q % 2 == 1: add("hat", ts, hat() * .025)
            if Lq >= 2 and (q in (0, 8) or (Lq >= 3 and q % 4 == 0)):
                add("kick", ts, kick() * .9); i = int(ts * SR); w = int(.25 * SR)
                if i < N: side[i:i + w] = np.minimum(side[i:i + w], .35 + .65 * (np.arange(min(w, N - i)) / w) ** .6)
            if Lq >= 2 and q in (4, 12): add("clap", ts, clap() * .26)
            if Lq >= 2 and q % 2 == 0 and q not in (6, 14):
                add("bass", ts, bassnote(_m2f(ch[0] - 12 + (12 if q in (10,) else 0)), beat * .55) * .32)
    for c in spec.get("risers", []):
        t = tt(2.2); f = 400 * np.exp(t * 1.4); n = rng.standard_normal(len(t))
        add("fx", V(c) - 2.2, _butter(n, 1200, "high") * (t / 2.2) ** 2.4 * .14 + np.sin(2 * np.pi * np.cumsum(f) / SR) * (t / 2.2) ** 3 * .03)
    for c in spec.get("impacts", []):
        t = tt(2.0)
        add("fx", V(c), np.sin(2 * np.pi * np.cumsum(38 + 70 * np.exp(-t * 6)) / SR) * np.exp(-t * 2.2) * .5 + _butter(rng.standard_normal(len(t)) * np.exp(-t * 3), 3000, "low") * .08)
    # sound effects, cued in animation time: [time, name, gain, duration, pitch semitones]
    def sfx(name, d=1.0, pitch=0.0):
        pf = 2 ** (pitch / 12)
        if name == "whoosh":
            t = tt(.85); n = rng.standard_normal(len(t)); env = np.sin(np.pi * np.clip(t / .85, 0, 1)) ** 2
            lo = _butter(n, 2400 * pf, "low"); hi = _butter(n, 600 * pf, "high")
            return (_butter(lo, 300, "high") * .6 + hi * .25 * np.clip(t / .85, 0, 1)) * env * .5
        if name == "tick":
            t = tt(.25); f = 1050 * pf
            return (np.sin(2 * np.pi * f * t) + .4 * np.sin(2 * np.pi * f * 3.9 * t) * np.exp(-t * 40)) * np.exp(-t * 22) * .35
        if name == "tap":
            t = tt(.12); return (rng.standard_normal(len(t)) * np.exp(-t * 160) * .4 + np.sin(2 * np.pi * 180 * t) * np.exp(-t * 35)) * .5
        if name == "clink":
            t = tt(.6); return (np.sin(2 * np.pi * 2480 * t) + .6 * np.sin(2 * np.pi * 3720 * t)) * np.exp(-t * 9) * .12
        if name == "thunk":
            t = tt(.4); return np.sin(2 * np.pi * np.cumsum(70 + 90 * np.exp(-t * 30)) / SR) * np.exp(-t * 9) * .7
        if name == "chunk":
            t = tt(.35)
            return (np.sin(2 * np.pi * np.cumsum(90 + 160 * np.exp(-t * 40)) / SR) * np.exp(-t * 12) * .8
                    + _butter(rng.standard_normal(len(t)) * np.exp(-t * 90), 2500, "low") * .3)
        if name == "slap":
            t = tt(.16); return _butter(_butter(rng.standard_normal(len(t)) * np.exp(-t * 45), 700 * pf, "high"), 5000 * pf, "low") * .5
        if name == "ping":
            t = tt(.8); f = 1760 * pf
            return (np.sin(2 * np.pi * f * t) + .45 * np.sin(2 * np.pi * f * 1.5 * t)) * np.minimum(1, t / .004) * np.exp(-t * 6) * .16
        if name == "flip":
            out = np.zeros(int(d * SR))
            for k in range(int(d * 26)):
                i = int((k / 26 + rng.uniform(0, .01)) * SR); c = tt(.03)
                seg = _butter(rng.standard_normal(len(c)), 1800, "high") * np.exp(-c * 200) * .35
                out[i:i + len(seg)] += seg[: max(0, len(out) - i)]
            return out
        if name == "lamp":
            t = tt(.08); return _butter(rng.standard_normal(len(t)), 1500, "high") * np.exp(-t * 120) * .4
        if name == "heart":
            t = tt(.5); b = lambda o: np.sin(2 * np.pi * 52 * (t - o)) * np.exp(-np.maximum(0, t - o) * 14) * (t >= o)
            return (b(0) + .7 * b(.18)) * .9
        if name == "pop":
            t = tt(.12); return np.sin(2 * np.pi * np.cumsum(500 * pf + 900 * np.exp(-t * 60)) / SR) * np.exp(-t * 30) * .2
        if name == "shimmer":
            out = np.zeros(int(d * SR))
            for k in range(int(d * 18)):
                f = _m2f(int(rng.choice([84, 86, 88, 91, 93, 96]))); c = tt(.6); i = int(rng.uniform(0, d - .6) * SR)
                seg = np.sin(2 * np.pi * f * c) * np.sin(np.pi * c / .6) ** 2 * .03
                out[i:i + len(seg)] += seg[: max(0, len(out) - i)]
            return out
        if name == "rise":
            t = tt(d); return _butter(rng.standard_normal(len(t)), 900, "high") * (t / d) ** 2 * .16
        if name == "type":
            out = np.zeros(int(d * SR)); k = 0.0
            while k < d - .05:
                c = tt(.04); seg = (_butter(rng.standard_normal(len(c)), 2000, "high") * .25 + np.sin(2 * np.pi * 240 * c) * .3) * np.exp(-c * 140)
                i = int(k * SR); out[i:i + len(seg)] += seg[: max(0, len(out) - i)]; k += rng.uniform(.07, .13) + (.18 if rng.random() < .12 else 0)
            return out * .55
        if name == "roll":
            out = np.zeros(int(d * SR)); k = 0.0; step = .045
            while k < d - .03:
                c = tt(.03); seg = np.sin(2 * np.pi * 2200 * c) * np.exp(-c * 180) * .12
                i = int(k * SR); out[i:i + len(seg)] += seg[: max(0, len(out) - i)]; k += step; step *= 1.03
            return out
        if name == "clap":
            return clap() * .35
        if name == "sting":
            t = tt(2.6)
            return sum(np.sin(2 * np.pi * _m2f(m) * t) * np.exp(-t * 1.8) * .1 for m in (60, 67, 72, 76, 79)) * np.minimum(1, t / .005)
        return np.zeros(10)
    for cue in spec.get("sfx", []):
        tm, name = cue[0], cue[1]; g = cue[2] if len(cue) > 2 else 1.0; d = cue[3] if len(cue) > 3 else 1.0; pitch = cue[4] if len(cue) > 4 else 0.0
        add("fx", V(tm), sfx(name, d, pitch) * g)
    def chime(f, start, v):
        t = tt(3.2)
        x = sum(a * np.sin(2 * np.pi * f * r * t) * np.exp(-t * dk) for r, a, dk in ((1, 1, 1.4), (2.76, .3, 3.2), (5.4, .1, 6), (2, .22, 2.2)))
        add("fx", start, v * x * np.minimum(1, t / .003))
    for k, m in enumerate((72, 76, 79, 84)): chime(_m2f(m), end + k * .22, .12)
    pad = _butter(buses["pad"], 2400, "low") * side
    bass = _butter(buses["bass"], 900, "low") * (.4 + .6 * side)
    dry = buses["kick"] + buses["clap"] * .9 + buses["hat"] + bass + pad + buses["pluck"] * (.7 + .3 * side) + buses["fx"]
    def ir(seed):
        r = np.random.default_rng(seed); t = np.arange(int(2.2 * SR)) / SR
        return _butter(r.standard_normal(len(t)) * np.exp(-t / .5), 6000, "low") * .018
    wet = buses["pluck"] + buses["clap"] * .6 + pad * .6 + buses["fx"] * .5
    Lc = dry + fftconvolve(wet, ir(3))[:N] + np.roll(buses["pluck"], int(.012 * SR)) * .2
    Rc = dry + fftconvolve(wet, ir(4))[:N] + np.roll(buses["pluck"], int(.008 * SR)) * .2
    out = np.stack([Lc, Rc], 1)
    t = np.arange(N) / SR
    out *= np.minimum(1, t / .4)[:, None] * np.clip((T - t) / 1.2, 0, 1)[:, None]
    out = np.tanh(out * 1.1) / np.tanh(1.1)
    out /= np.max(np.abs(out)) / .9
    wavfile.write(str(out_path), SR, (out * 32767).astype(np.int16))
    return str(out_path)
