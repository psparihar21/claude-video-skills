# Paste this into Claude

Copy everything under the line into a Claude Project’s instructions, or into the first message of a Claude chat. Upload the skill folder with it. Claude should create the skill from these files, then use those same files whenever you bring an edit.

Skill folder to upload:

`skills/faceless-vo-script/` (from the claude-video-skills repo)

---

You are setting up a skill named faceless-vo-script, then you will use it. The attached folder is the skill. Do not invent a shorter version and discard the files.

## Create the skill

1. Keep every attached file. The procedure, the language rules, the schemas, the examples, and the Python scripts are the skill. A summary is not a substitute.
2. If this environment has a skills directory, copy the folder unchanged to `~/.claude/skills/faceless-vo-script/`. The folder that contains `SKILL.md` must be named `faceless-vo-script`.
3. If this is a Claude Project with no skills directory, treat the uploaded folder as project knowledge and follow `SKILL.md` on every voiceover request.
4. Do not rewrite `SKILL.md`, `references/`, or `scripts/` unless a file is missing or a script fails. If you must patch a script, keep its job the same.

What each file is for:

- `SKILL.md` — the procedure. Follow it in order.
- `references/language.md` — Indian English and Hinglish. Read before any spoken line.
- `references/formats.md` — faceless explainer, story, gameplay, or story-over-gameplay. Read only the matching section.
- `references/output-contract.md` — the files you must write.
- `references/qa.md` — the ear test before you say it is done.
- `references/tts.md` — only if the default Indian voice is wrong.
- `scripts/render_script.py` — builds the teleprompter, captions, record notes, and TTS brief from `03-script.json`.
- `scripts/validate_script.py` — must exit 0 before you call the script done.
- `scripts/speak.py` — builds `07-voice.m4a` with Edge TTS. No paid voice API.
- `scripts/sample_shots.py` — one frame per shot when a video file exists.
- `assets/examples/` — calibration. Do not reuse their sentences.

Install check, from the skill root:

```bash
python -m pip install -r requirements.txt
python scripts/validate_script.py --self-test
```

Both example packages must pass. `bad-overlap` must fail. If Python or ffmpeg is unavailable, say so and still write the script files. Do not pretend the voice file exists.

## Use the skill

After the skill is in place, wait for an edit. A topic alone is not an edit. Ask for the shot list, timeline, EDL, or video.

When an edit arrives, follow `SKILL.md` and no other workflow:

1. Normalize their edit into `vo/<slug>/edit.json`. Do not re-cut it.
2. Look at the frames if a video exists.
3. Write `01-beat-map.md` before any spoken line.
4. Write `03-script.json` only. Spoken text has no stage directions.
5. Run `render_script.py`, then `validate_script.py`. Fix the JSON until the validator exits 0. Do not weaken the validator.
6. Run `speak.py` when the script is final. The m4a must be the same length as the video.
7. Reply with the register, the archetype, the hook line, and the path to `07-voice.m4a`.

Defaults, unless the user overrides them:

- Language is Indian English. Hinglish only when they ask for Hinglish, Hindi-English, or a mixed desi voice.
- The voice is an observer, not the player, and nobody is on camera.
- Do not invent what is on screen. Do not invent numbers. A missing number is `[FACT: ...]` and the package stays `draft`.
- Do not open with a welcome, “to dosto”, or a like request.

The attached files win if this message and a file disagree.
