# Video analysis

How to study a reference video so the new video can cover the same topic with the same pull, in the user's voice. Output feeds `craft-brief.md`. Nothing measured or captured here may appear in the new video.

## Contents
- Getting the material
- Run the analyzer
- Read the numbers
- Read the frames
- Topic map (same topic, new video)
- After the brief

## Picking a reference (optional)

When the user asks what to remake, rank candidates by how far each video beat its own channel, not by raw views: collect public listings (at least four videos per channel; channel page or the browser, never a logged-in session) into `[{"channel","title","views","url","duration"}]` and run `python3 ${CLAUDE_SKILL_DIR}/scripts/swipe.py collected.json --min 2.0`. Show the top five with their multiples and formula labels, and say the formula is a judgement about the title, not why it worked. Then the user picks one reference.

## Getting the material

| Reference given as | Do this |
|---|---|
| Video file (attached or a path) | Run `analyze_reference.py` on it. Best case. |
| YouTube link | Read the transcript through the browser (video page → "Show transcript", read with page-text tools) and save it to `reference/transcript.txt`. Watch the first 15 s and one moment per minute with the browser and take screenshots to study framing, text, and edit style; do not save them as assets. Then ask once: "If you can share the file, I can measure cut rhythm and pacing exactly." |
| Transcript only | Use it for structure and pace estimate; mark visual and rhythm fields `unknown (no video)`. |

Never download the reference's picture or sound for use. If the user wants exact measurements from a link and no file exists, a study-only download (yt-dlp, if installed, with the user's yes) into `reference/` is the only exception: note it in `intake.md`, delete the file after the craft brief, and never cut from it.

## Run the analyzer

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/analyze_reference.py <video> productions/<slug> [--language hi|en|auto] [--scene 0.30]
```

(Relative to `SKILL.md`: `scripts/analyze_reference.py`.) Needs ffmpeg and ffprobe. It transcribes with faster-whisper when the interpreter has it; on the user's machine run it with the video-timeline-copilot Python (see `connectors.md`). Otherwise pass `--no-transcribe` and supply a transcript.

`--scene`: 0.30 suits most edits. Raise to 0.4 for handheld or gameplay footage that triggers false cuts; lower to 0.2 if obvious cuts are missed (soft fades, similar-looking shots). Check `shots.csv` against the sheets once.

Outputs in `reference/`: `analysis.md` (read first), `metrics.json`, `shots.csv`, `transcript.txt` / `.json`, `sheets/`, `hook/hook_sheet.jpg`.

## Read the numbers

| Measure | What it tells you | How to use it |
|---|---|---|
| cuts/min, avg and median shot | Picture-change rhythm | New shot list lands within about ±30% of this unless the style card says slower or faster. |
| cuts per 30 s | Where the edit speeds up or rests | Dense windows are interrupts or reveals; a long sparse window is an attention risk or a deliberate breather. Map both to beats. |
| shots over 8 s | Long holds | Usually talking head or screen demo; note what keeps them alive (zoom, text, motion). |
| wpm, wpm per 30 s | Spoken density | Compare with the style card pace. The script follows the user's pace, not theirs. |
| hook (first 15 s) | What the opening does | Name the device and the promise; never reuse the words. |
| pauses over 1 s | Planned beats or dead air | Planned pauses before a reveal are craft; dead air is a gap to beat. |
| LUFS / LRA | Mix target | Delivery targets about −14 LUFS whatever the reference measured. |
| questions | Viewer-address habit | Count only; write the user's own questions. |

## Read the frames

Open `hook/hook_sheet.jpg` and every `sheets/sheet_NN.jpg` with the image reader. Record, as mechanisms:

- **Visual grammar:** share of talking head, screen or gameplay capture, B-roll, graphics, text cards. Roughly, by shot count.
- **Text on screen:** how often, how many words, position, case, whether it repeats the voice or adds to it.
- **Captions:** burned word-by-word, sentence captions, or none.
- **Framing moves:** punch-ins, zooms, split screens, picture-in-picture, arrows or highlights.
- **Colour and look:** palette, contrast, overall energy.
- **First frame:** what the viewer sees before a word is spoken.

Do not copy layouts, graphics, thumbnail compositions, or characters. The new video takes these as targets ("a visual change every ~5 s", "text card at every claim"), filled with the user's look from the style card.

## Topic map (same topic, new video)

The topic is open to anyone; the reference's take on it is not. Build a short topic map in the craft brief:

1. **Questions the video answers.** Phrase as viewer questions ("Is X worth it in 2026?"), not their lines.
2. **Claims and facts it relies on.** List each as a topic to re-check, not as wording. Research every one fresh with an available research tool; prefer primary sources; note anything outdated or wrong.
3. **What is missing or weak.** Unanswered questions, no proof, stale data, no counter-case, no demo, no personal test.
4. **Angle options for the user.** Two or three, for example: newer (what changed since it was made), deeper (the part they skimmed), contrarian (the claim they got wrong), practical (a step-by-step they never showed), personal test (the user tried it). The user picks or supplies their own in the question batch.

The script then covers the same topic with the user's angle, their own examples, freshly sourced facts, and a different running order. `originality-rules.md` still applies in full.

## After the brief

- Keep `metrics.json`, `shots.csv`, and the craft brief.
- `transcript.txt` stays only for `similarity_guard.py`; do not reread it for wording.
- Frames and sheets are never sources. `check_package.py` fails any row that points into `reference/`.
- If a study-only download was made, delete it now and note the deletion in `intake.md`.
