---
name: own-voice-render
description: >-
  Turn a finished script into an audio track in the user's own cloned voice
  (Hinglish, Hindi or English), rendered locally on their NVIDIA GPU with a
  fine-tuned IndicF5. Takes a script from another skill (faceless-vo-script
  03-script.json, an SRT, a JSON cue list) or any txt/md file; converts Roman
  Hinglish to Devanagari, fits timed cues to their windows, normalises loudness,
  and writes wav, m4a, srt and a QA report. Use when the user wants the voiceover
  "in my voice", "my own voice", "voice clone", or to turn a finished script or
  vocal track into audio. Do not use to write or edit the script, to clone anyone
  else's voice, or to call a hosted or paid TTS.
color: green
---

# Own-voice render

You turn a script that already exists into audio in **the user's own voice**. You do not write or rewrite the words. Another skill (usually `faceless-vo-script`) or the user supplies them. Your job is to get them spoken correctly, on time, and honestly reported.

The engine is IndicF5 (F5-TTS, 0.4B) fine-tuned on the user's own recordings, run locally. Nothing is uploaded. Read `references/engine.md` only when something is broken or the user wants to retrain.

## Hard rules

- **Own voice only.** The voice is the user's. Never use it for a script that impersonates a real person, and never train on or clone anyone else's audio.
- **Nothing leaves the machine.** No hosted or paid TTS, no uploading audio or scripts anywhere.
- **Never handle the Hugging Face token.** If the gated model needs a login, tell the user to run `hf auth login` in their own terminal. Never ask for, paste, print or store a token.
- **Do not edit the script's meaning.** You may convert spelling (Roman to Devanagari) and apply `lint --fix`. If a line is too long for its window, report it. Do not shorten it yourself unless the user asks; shortening belongs to the script skill.
- **You cannot hear the audio.** QA catches silence, clipping, runaway length and bad speaking rate. It cannot catch a mispronounced word. Say so, and send the clips to the user to listen to. Never claim a track "sounds right".
- **Performance notes are ignored.** This engine has no emotion, pace or emphasis control. Say so when the source has them.
- **Digits are blocked.** Spell numbers out in words before rendering.

## Run it

Always through the wrapper (right interpreter, UTF-8 mode):

```powershell
& "$env:USERPROFILE\.claude\skills\own-voice-render\ovr.ps1" <command> ...
```

(`ovr.ps1` runs `scripts/ovr.py` with `<your-indicf5-env>/python.exe -X utf8`. Bare `python` is a Store stub on this machine and will not work.)

| Command | Does |
| --- | --- |
| `doctor` | Preflight: GPU, VRAM, env, ffmpeg, model, checkpoint, references. Blocking problems exit 1. |
| `ingest <script> [--out DIR] [--lang auto\|hi\|en] [--english-as devanagari\|latin]` | Normalise any script into `plan.json`. English goes through Devanagari by default. |
| `draft <out>` | Fill Devanagari drafts from the lexicon. Unknown words become `[[word]]`. |
| `set-deva <out> <json>` | Save your final Devanagari: `{ "c01": "..." }`. Marks cues reviewed. |
| `review <out> --all` | Mark drafts reviewed after you have read them. |
| `lint <out> [--fix]` | Block on digits, Latin in Hindi, unresolved markers, characters the model never saw. |
| `render <out> [--only c02,c03] [--allow-overflow]` | Render, fit, normalise, write files. |
| `candidates <out> --cue c02 [--seeds 1-6] [--refs a,b]` | Alternate takes of one cue for the user to choose from. |
| `lock <out> --cue c02 --seed N [--ref name]` | Pin the chosen take. Survives edits to other cues. |
| `lexicon <roman> <deva> [--kind hindi\|loanword] [--approved]` | Save a spelling the user approved. |
| `calibrate` | Re-measure the user's speaking rate from the training clips. |
| `selftest` | One Hindi and one English line through the full pipeline. |

## Procedure

Follow the order. Each step gates the next.

1. **`doctor`.** Fix any FAIL with `references/troubleshooting.md`. The GPU is an 8 GB laptop card: if VRAM is low, ask the user to close DaVinci, browsers or training runs.
2. **`ingest`.** Read the summary: mode (`timed` when the source has cue windows, otherwise `sequential`), cue count, Hindi vs English split, warnings. A source with `status: draft` or `[FACT:]` holes must not be rendered as final. Stop and tell the user. See `references/input-contract.md` for what each source format maps to.
3. **Devanagari, for every Hindi or Hinglish cue.** This is your job, not the script's.
   - Run `draft`, open `needs-deva.md`, and write the final Devanagari for each cue following `references/devanagari.md`. Resolve every `[[word]]` and every ambiguous word (`ki`, `to`, `main`, `is`) from context.
   - Write the result as a JSON map and run `set-deva`. Do not just run `review --all` on a draft you did not read.
   - **English cues are written in Devanagari too** (Indian-accented English in the user's voice). `ingest` marks them `from_english` and sends them down the Hindi path with the Hindi reference. Transliterate the whole sentence phonetically ("Most players lose" -> `मोस्ट प्लेयर्स लूज़`). The user compared this against Latin text with other seeds and references and chose it. Use `ingest --english-as latin` only if the user asks for it.
   - No cue contains Latin letters (except the allowed acronyms) unless it was ingested with `--english-as latin`.
   - Keep approved spellings. `waste` is `वेस्ट`. Never change one the user approved.
4. **`lint --fix`, then `lint`.** Exit 0 is required before rendering. Do not loosen the linter to get past an error.
5. **`render`.** One model load, then cached. First run on a cold machine takes a minute or two to load the model. Reruns of unchanged text are instant from the cache.
6. **Read the exit code and `report.json`.**

   | Code | Meaning | You do |
   | --- | --- | --- |
   | 0 | clean | Send the audio. Still ask the user to listen. |
   | 2 | rendered, needs a human listen (QA flags, or a cue was truncated) | Name the flagged cues. Offer `candidates`. |
   | 3 | timing overflow or collision | Report each cue and by how many seconds. Ask for a shorter line. Do not fake it. |
   | 1 | blocked or error | Fix the cause. |

7. **Deliver.** Send `voice.wav` (or `voice.m4a`) to the user with `SendUserFile`, then say plainly that only they can judge pronunciation.
8. **Fix loop for a word that sounds wrong.** Escalate in this order, one step at a time:
   1. Try another spelling and re-render that cue (`references/devanagari.md`, "when a word sounds off").
   2. `candidates --seeds 1-6`, send them, the user picks, then `lock`.
   3. `candidates --refs ...` with other reference clips (`references/qa.md`). A reference where the user says the word correctly fixes what seeds cannot.
   4. If it is a pattern the model never learned, tell the user it needs more recordings of that word in context and a retrain (`references/engine.md`). Do not retrain unasked: it takes the GPU for about 30 minutes.

## Outputs

In the output folder (next to the script, or `--out`):

| File | What |
| --- | --- |
| `voice.wav` | 48 kHz mono 16-bit, loudness-normalised to -16 LUFS, true peak under -1.5 dB |
| `voice.m4a` | AAC 192k copy |
| `voice.srt` | Cue-level captions with the real spoken timings |
| `report.json` | Per-cue seeds, references, QA flags, tempo, placements, loudness, issues |
| `plan.json`, `locks.json` | The normalised script and the pinned takes |
| `cues/`, `candidates/` | Per-cue wavs and alternates |

When the source is a `faceless-vo-script` package, `07-voice.m4a` and `07-voice-report.json` are also written beside `03-script.json` in the same shape that skill produces, so its downstream steps work unchanged.

## Timing law

- Timed sources place each cue at `in_sec`. A cue that reads longer than its window is sped up by at most **1.12x**. Past that it is an **overflow**: exit 3, with the number of seconds over. No silent trimming.
- `--allow-overflow` truncates with a short fade and marks the cue `truncated` (exit 2). Use it only when the user asks to hear the draft anyway.
- Sequential sources get 0.30 s between cues and 0.60 s at paragraph breaks.
- The audio length equals `video_duration_sec` when the source gives one.

## Done

You are done only when:

- `doctor` passed, `lint` exited 0, and `render` produced files
- the exit code and every QA flag, truncation or overflow is stated in your reply
- the clip was sent to the user, and you said that pronunciation needs their ear
- any spelling the user approved is saved with `lexicon --approved`

Reply with: the output path, the duration, the cues that were sped up, flagged or locked, and one line on what the user should listen for. Do not paste the whole script.

## References

- `references/input-contract.md`: formats, field mapping, what upstream skills should write
- `references/devanagari.md`: conversion rules, numbers, English words, when a word sounds off
- `references/qa.md`: what QA can and cannot see, the listen protocol, candidates and locks
- `references/engine.md`: how the voice was built, files, retraining, limits
- `references/troubleshooting.md`: symptom to fix
