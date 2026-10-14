---
name: faceless-vo-script
description: >-
  Write a timed Hinglish or Indian English voiceover for a faceless video or
  faceless gameplay edit, then render the teleprompter, emotion map, TTS brief,
  captions, and an Indian voice track lined up to the cut. Use when the user
  has a locked edit, shot list, EDL, timeline, or video from an editing skill
  and wants narration, commentary, a vocal script, or a voice to lay on the
  picture. Do not use for niche research, thumbnails, or re-cutting the video.
color: orange
---

# Faceless voiceover script

You write the vocal track for a video that is already edited. The picture, the cuts, and the on-screen text are locked. Your job is the words a person will say, timed so they can be recorded or dropped into TTS and laid on a faceless video or faceless gameplay.

Default register is **Indian English**. Switch to **Hinglish** when the user asks for Hinglish, Hindi-English, or a mixed desi voice. "Majorly Indian English" means Indian English.

Before you write a spoken line, read `references/language.md` and the one section of `references/formats.md` that matches the format. Before you write files, read `references/output-contract.md`. Before you tell the user it is done, read `references/qa.md` and run the validator. Read `references/field-notes.md` only when you are changing this skill, not when you are writing a script.

## What you produce

A folder `vo/<slug>/` next to the edit:

| File | Who writes it |
| --- | --- |
| `01-beat-map.md` | You, after you have seen the cut |
| `03-script.json` | You. This is the only script |
| `02-script.md`, `04-captions.srt`, `05-record-notes.md`, `06-tts-brief.md` | `scripts/render_script.py` |
| `07-voice.m4a` | `scripts/speak.py`, after validation |

The teleprompter, the captions, the record notes, and the TTS brief are renders. Do not hand-write a second version of the words. The brief is the emotion map plus the paste-ready engine settings. The m4a is an Indian neural voice already shifted onto each cue, so it can sit on the faceless picture.

## What you never do

- Do not re-cut, re-order, or "improve" the edit. If a line cannot fit, write a shorter line. Put a recut request in `recut_requests` and keep writing to the locked cut.
- Do not invent what is on screen. If you did not see it in a frame, an editor note, or on-screen text, you do not know it.
- Do not invent facts, stats, prices, patch notes, or loot numbers. A number with no source becomes `[FACT: what you still need]`, and that cue cannot ship as final.
- Do not welcome people. No "in this video", "hey guys", "to dosto", "bhai log", "smash the like", "buckle up", "let's dive in".
- Do not narrate a face, a creator, or "as you can see me". Nobody is on camera. The voice is an observer, not a vlogger.
- Do not send the script to a paid voice API. The local voice file comes from `scripts/speak.py` (Edge TTS, Indian English voices, no key). ElevenLabs settings live in the brief for the user to paste themselves.

## Inputs

Accept whatever the editing skill actually wrote. Then normalize it into an edit package. The shape is `assets/edit-package.schema.json`.

Look, in this order:

1. A path or file the user pointed at.
2. An edit package already named `edit.json`, `edit-package.json`, `timeline.json`, or `*.edl` in the working folder.
3. The latest shot list, chapter list, or caption track that skill wrote (markdown tables, CSV, JSON, SRT).
4. The video file alone.

Map their fields onto shots with `in_sec`, `out_sec`, `visual`, `on_screen_text`, `cut_type`, and `energy`. Keep their wording in `visual`. Do not decorate it.

If there is no video and the shot notes are vague ("gameplay", "b-roll", "clip"), still write the script, mark those shots `confidence: low` in the beat map, and keep the line generic. Say that limit in the reply to the user.

Set `format` to one of:

- `faceless-explainer` — teaching, finance, facts, listicles, no host on camera
- `faceless-story` — storytime over stock or gameplay wallpaper
- `faceless-gameplay` — the game is the subject
- `story-over-gameplay` — the story is the subject, the game is wallpaper

If they did not say, infer it. Story over a driving/parkour/farming clip is `story-over-gameplay`, not gameplay commentary.

## Register

| They said | You write |
| --- | --- |
| Nothing about language | `indian-english` |
| Hinglish, Hindi-English, desi mix | `hinglish` |
| Hindi | `hinglish`, and tell them this skill stays mixed on purpose |
| A city flavor | Pan-India base plus that flavor, lightly |

Persona defaults, unless they overrode them:

- Observer, not the player. Do not say "main push karta hoon" or "I am playing".
- Pan-India, late 20s, close-mic, slight smile, no shout, no news-anchor.
- Clean. No slur, no "tu", no piled "bhai / yaar / bro".
- Gender-neutral. If the voice must say "I", use English "I" so the verb does not pick a gender. First-person Hindi only after they name the voice gender.

## Procedure

Follow this order. Do not draft the spoken track in your head and then assign timestamps.

1. **Normalize the edit.** Write `vo/<slug>/edit.json` in the edit-package shape, even if you only copied their file. `video_duration_sec` comes from ffprobe when a file exists, not from a guess.
2. **See the picture.** When `video_path` is set, run:

   ```bash
   python .cursor/skills/faceless-vo-script/scripts/sample_shots.py \
     --edit vo/<slug>/edit.json \
     --out vo/<slug>/frames
   ```

   Shorts and anything under 90 seconds: look at every frame. Longer videos: look at hooks, payoffs, text cards, and any shot whose `visual` is under eight words. Cap a pass at 40 frames, then sample the next batch only where the script is still unsure.
3. **Write `01-beat-map.md` before any cue.** One block per shot:

   - time range and shot id
   - what the viewer sees (only what you actually have)
   - what they already understand from the picture
   - what the voice is allowed to add
   - what the voice must not repeat (burned-in text, obvious action)
   - spoken room, in seconds, after the air rules below
   - `confidence`: high (frame or specific note), medium (detailed note, no frame), low (vague)
4. **Write `03-script.json`.** One cue per spoken breath. Schema: `assets/script-package.schema.json`. Spoken text is the only thing that will be said. Performance notes live in `performance`, never inside `spoken`.
5. **Render.**

   ```bash
   python .cursor/skills/faceless-vo-script/scripts/render_script.py \
     --script vo/<slug>/03-script.json \
     --out vo/<slug>
   ```

6. **Validate.** Exit 0 is required before you call it done.

   ```bash
   python .cursor/skills/faceless-vo-script/scripts/validate_script.py \
     --edit vo/<slug>/edit.json \
     --script vo/<slug>/03-script.json
   ```

   Fix the script. Do not relax the validator to make a long line pass.
7. **Speak.** When status is `final`, build the voice file. Skip this only when the machine cannot reach the speech service, and say so.

   ```bash
   python .cursor/skills/faceless-vo-script/scripts/speak.py \
     --script vo/<slug>/03-script.json \
     --out vo/<slug>
   ```

   Needs `edge-tts` (`python3 -m pip install edge-tts`) and ffmpeg. Read `references/tts.md` only if you need to change the voice.
8. **Reply** with the register, the archetype, where the files are, and any low-confidence shots, `[FACT:]` holes, or recut requests. Paste the hook line and the path to `07-voice.m4a`. Do not paste the whole teleprompter unless they asked.

## Timing law

Indian delivery sits a little slower than American commentary. Write for a clear close-mic read, not a shouted dub.

| | Target | Hard ceiling |
| --- | --- | --- |
| Words per second | 2.2–2.6 | 2.85 |
| Sentence length | under 18 words | 22 |
| Air after a hard cut | start ≥ 0.10s after the cut | |
| Air before the next hard cut | end ≥ 0.15s before it | |
| Comma or full stop | every 12–16 words | |

Count words the way the validator counts them: whitespace and hyphens split.

- A punch word may land on the cut. End the cue at the cut. Do not spill into the next shot.
- One cue stays inside one shot. A line that needs two shots is two cues, or one cue if the beat map calls those shots a single breath. Three shots is always wrong.
- `hold_for_read` is silence. The viewer is reading. Cover that window with `intentional_silence`. Do not talk, and do not read the card aloud unless the card is the joke and the beat map says to land it before the hold.
- Shorts, Reels, and TikTok: the first spoken cue starts by 0.35s and its role is `hook`. No cold welcome.
- YouTube longform: first words by 5 seconds unless the open is a deliberate silent visual, which you mark in `intentional_silence`. If the video is longer than four minutes, land a new stake between 2:30 and 3:30. The validator warns when that window is empty.
- Leave a hole over a kill-feed, a punchline SFX, or a music sting the edit marked. Say less when the bed is already loud. Note ducking in `mix_note` on that cue.

Roles are `hook`, `setup`, `turn`, `payoff`, `breather`, `cta`. Default is no CTA. A CTA exists only when the edit has a CTA card, it is the last cue, and it is one sentence.

## Truth law

Every digit, currency amount, or quantity word (`twenty`, `lakh`, `crore`, `hundred`, `thousand`) needs `fact_source` on that cue. Point it at a shot field (`s04.on_screen_text`), an editor note, or `brief:<what the user told you>`.

If the source does not exist, the spoken line uses `[FACT: ...]` and `status` on the package stays `draft`. Never pick a plausible number.

Names, ranks, and patch claims follow the same rule. "He is a pro player" is a claim. "Yeh banda push karta hai" is visible action, if the frame shows a push.

## Picture law

The viewer can see the video. The voice adds cause, stakes, irony, or the next decision. It does not audio-describe.

- Gameplay commentary: say the decision and the consequence, not the button. "He peeks the same angle again" is enough. "He presses W and left click" is not a script.
- Story over gameplay: follow the story. Touch the gameplay only when a visual gag lines up with the sentence. Do not describe the parkour.
- Explainers: do not read a slide that is already on screen. Say the implication, then shut up while a number card is held.
- If a visual is ambiguous, you may point once: "left wala red bar". Do not keep pointing.

## Voice

Write for the mouth. Contractions in English (`it's`, `don't`, `that's`). Short sentences. One emphatic word in a cue, marked in `emphasis`, not by stacking hype ("insane", "crazy", "literally").

Hinglish, when that is the register:

- English carries the information, the numbers, and the game terms (clutch, third party, loadout, rank, zone).
- Hindi carries the turn, the reaction, and the connectors.
- Switch at a clause boundary, not inside a noun phrase.
- Roman Hindi only, using the spelling in `references/language.md`.
- Hindi function words (`hai`, `nahi`, `yeh`, `lekin`, `aur`, `ke`, `mein`) land between 15% and 48% of all words. The validator measures that. One garnish word is a fail. A script an English speaker cannot follow is also a fail.

Indian English, the default:

- Full sentences in English, spoken with an Indian rhythm: setup, then the point on the last content word.
- Indian number words when the topic is Indian money: lakh, crore.
- No Hindi function words. No "hai", "nahi", "yeh", "lekin", "toh", "bhai", "yaar".

Match the energy the edit already marked (`hook`, `build`, `payoff`, `breather`). A hook is tighter, not louder.

## Done

You are done only when:

- the beat map exists and every cue traces to a shot
- `validate_script.py` exits 0
- the rendered teleprompter and `06-tts-brief.md` match `spoken`
- `07-voice.m4a` matches the video duration, or you have said why the speech service could not build it
- the user-facing reply names the register, the archetype, the files, and any hole you left on purpose
