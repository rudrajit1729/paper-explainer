"""The time map: how long each moment of the animation lasts in the video.

The page is authored on animation time. Each timeline event names the narration line that goes
with it, the animation time it starts at, and when its motion has settled. `build_time_map`
stretches every event so the video stays on it long enough for its narration (voice mode) or
for reading (read mode), while entrances and transitions keep a natural speed.

Event fields (project.json → timeline.events):
  at        animation time the event starts (seconds)
  line      narration line id
  settle    animation time by which the event's motion is done (next event's `at` by default)
  entrance  optional: seconds of animation that play at entrance speed before the hold.
            Leave it out for continuous motion (a dot travelling a loop): then the whole
            stretch from `at` to `settle` is slowed evenly instead of paused.
  lead      seconds of video before the voice starts (default 0.12)
"""
from __future__ import annotations
import re
from .project import Project, read_json, write_json

DEFAULT_PACE = {
    "read":  {"entrance": 1.25, "transition": 1.4, "min_slope": 1.25, "pad": 0.2, "read_factor": 0.62},
    "voice": {"entrance": 1.3, "transition": 1.45, "min_slope": 1.4, "pad": 0.3},
    "fast":  {"entrance": 1.0, "transition": 1.0, "min_slope": 1.0, "pad": 0.0, "read_factor": 0.0},
}


def estimate_speech_seconds(text: str, lang: str) -> float:
    """Rough speaking time when no audio exists yet (about 160 words a minute)."""
    if lang.startswith(("ja", "zh", "cmn")):
        return len(re.sub(r"\s", "", text)) / 6.5
    return len(text.split()) / 2.65 + 0.3


def build_time_map(project: Project, mode: str, lang: str) -> dict:
    tl = project.cfg["timeline"]
    pace = {**DEFAULT_PACE.get(mode, DEFAULT_PACE["read"]), **tl.get("pace", {}).get(mode, {})}
    holds = tl.get("holds", {}).get(mode, {})
    final_hold = tl.get("final_hold", {}).get(mode, 4.0) if isinstance(tl.get("final_hold"), dict) else tl.get("final_hold", 4.0)
    events = tl["events"]

    # how long each line needs on screen
    if mode == "voice":
        durs = read_json(project.voice_dir(lang) / "durations.json")
        if not durs:
            raise SystemExit("No voice yet. Run `explainer voice` first (or use --mode read).")
    else:
        narration = project.narration(lang)
        durs = {e["line"]: estimate_speech_seconds(narration["lines"].get(e["line"], ""), narration.get("lang", lang))
                * pace.get("read_factor", 0.62) for e in events}

    ES, TS, MINU, PAD = pace["entrance"], pace["transition"], pace["min_slope"], pace["pad"]
    keys, voice = [(0.0, 0.0)], []
    v = a = 0.0
    for i, ev in enumerate(events):
        a0 = float(ev["at"])
        settle = float(ev.get("settle", events[i + 1]["at"] if i + 1 < len(events) else project.end))
        lead = float(ev.get("lead", 0.12))
        if a0 > a:                                   # transition into this event
            v += (a0 - a) * TS; a = a0; keys.append((v, a))
        need = durs.get(ev["line"], 0.0) + PAD + lead
        voice.append([ev["line"], round(v + lead, 3)])
        if "entrance" in ev:                         # play the entrance, then hold
            e = float(ev["entrance"])
            v += e * ES; a += e; keys.append((v, a))
            v += max(need - e * ES, (settle - a) * MINU); a = settle; keys.append((v, a))
        else:                                        # continuous motion: slow it evenly
            v += max((settle - a) * MINU, need); a = settle; keys.append((v, a))
        if holds.get(ev["line"]):                    # extra reading time, frozen
            v += float(holds[ev["line"]]); keys.append((v, a))
    v += (project.end - a) if mode == "fast" else float(final_hold)   # the closing stretch
    keys.append((v, project.end))

    clean = []
    for p in keys:
        p = (round(p[0], 3), round(p[1], 3))
        if not clean or p != clean[-1]:
            clean.append(p)
    data = {"mode": mode, "lang": lang, "keys": clean, "voice": voice, "total": round(v, 3)}
    write_json(project.build(lang) / f"timemap_{mode}.json", data)
    return data


def anim_to_video(keys: list, a: float) -> float:
    """Map an animation time to video time (first moment it is reached)."""
    for (v0, a0), (v1, a1) in zip(keys, keys[1:]):
        if a <= a1 and a1 > a0:
            return v0 + (v1 - v0) * (max(a, a0) - a0) / (a1 - a0)
    return keys[-1][0]
