# Voices and languages

Every voice engine writes `build/<lang>/voice/<line>.wav` and `durations.json`. The time map then
paces the video to those durations, so any voice, speed or language fits automatically.

## 1. AI voice (default)

```
explainer build projects/x --mode voice                    # voice from narration/en.json
explainer build projects/x --mode voice --voice am_michael --speed 0.95
```

Kokoro: open model (Apache-2.0), runs offline on a laptop, downloads about 350 MB once to
`~/.cache/paper-explainer`. The voices are openly licensed, so the audio is free to publish.

| lang | default | others |
|---|---|---|
| en-us | af_heart | af_bella, af_nicole, am_michael, am_fenrir |
| en-gb | bf_emma | bf_isabella, bm_george, bm_lewis |
| es | ef_dora | em_alex |
| fr-fr | ff_siwis | |
| it | if_sara | im_nicola |
| pt-br | pf_dora | pm_alex |
| hi | hf_alpha | hm_omega |
| ja | jf_alpha | jm_kumo (needs `pip install misaki[ja]`) |
| cmn | zf_xiaobei | zm_yunxi (needs `pip install misaki[zh]`) |

Set `lang`, `voice` and `speed` in `narration/<lang>.json`. To choose by ear:
`explainer voices --lang en-us` writes one sample per voice into `voice-samples/`.

## 2. Your own voice, cloned

```
pip install -e ".[clone]"                    # Chatterbox (MIT) + PyTorch, about 2 GB
# record 10 to 30 s of yourself reading anything, quietly, as WAV:
#   projects/x/recordings/en/reference.wav
explainer build projects/x --mode voice --engine clone
```

Zero-shot cloning from the reference; no training run needed. English. Runs on Apple Silicon (mps),
CUDA or CPU (slow). Chatterbox adds an inaudible watermark to its output. Only clone a voice with
its owner's consent.

## 3. Your own recordings

Easiest: `explainer record projects/x --lang en` opens a recorder in the browser (localhost only).
It shows every line with Record, Play and Redo, a level meter, and Space / arrow keys; files save into
`recordings/en/<id>.wav`. Its second tab records `reference.wav` for cloning.

Or use any recorder: `explainer script projects/x --lang en` writes `build/en/recording_script.md`.
Record each line as `recordings/en/<id>.wav`, or the whole script as one `recordings/en/take.wav`
with a one-second pause between lines (it is split at the pauses), then:

```
explainer build projects/x --mode voice --engine recorded
```

Levels are normalized and silences trimmed. Any phone or laptop mic in a quiet room works.

## Another language

1. `explainer add-language projects/x es --page` creates `narration/es.json` (lines marked
   "TODO translate", lang and default voice set) and `index.es.html`. Use `--code fr-fr`, `pt-br`
   or `cmn` where the voice code differs from the file name.
2. Translate each narration line (keep the ids) and only the visible text in `index.es.html`
   (it is used automatically for `--lang es`). Check stills: translations
   run longer, so shorten rather than shrink the type.
3. `explainer build projects/x --mode voice --lang es`

Numbers: write them as words in the narration language. Names and the paper title can stay in English.

## Music only, no voice

`--mode read` paces the video for reading and adds the generated score. `--no-music` gives a
silent video for adding a soundtrack elsewhere.
