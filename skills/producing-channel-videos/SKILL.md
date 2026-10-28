---
name: producing-channel-videos
description: Analyzes a reference video and produces an original YouTube video on the same topic for the user's own channel. Measures why an attached video or YouTube link holds attention (hook, cut rhythm, pacing, structure, visual style), researches the topic fresh, writes a new script in the user's style with their own angle and examples, plans rights-cleared B-roll, gameplay, music and voiceover, and delivers a cut-ready package with titles, thumbnail brief, description and chapters. Asks approval before every costly step and never reuses the reference's footage, audio, wording or voice. Use whenever the user attaches a reference video, pastes a YouTube link, or asks to analyze, remake, restyle, script or produce a similar video for their channel ("make this in my style", "make a video like this on the same topic"), or to plan B-roll, voiceover or a thumbnail for that upload. Not for summarizing documents or videos, coding tasks, or trimming and captioning footage the user already shot with no reference to rework.
---

# Producing channel videos

Act as a producer, not a paraphraser and not a downloader. Measure why the reference works, then make a different video on the same topic in the user's voice, with fresh research, with the user's examples, the user's running order, and media the user may publish.

Freedom levels:
- **Low** on rights, voice, likeness, factual claims, and approval gates. Follow them exactly.
- **High** on wording, research route, and which enabled tool does a step.

## Production folder

Keep every run in one folder (default `productions/<slug>/` in the working directory). All three scripts read this layout:

```
productions/<slug>/
├── intake.md            # reference file name / URL, what the user supplied
├── inventory.md         # step 0 tool map and gaps
├── craft-brief.md       # step 2, includes the reference beat map
├── reference/           # study-only: analysis.md, metrics.json, shots.csv, transcript.txt, sheets/, hook/
├── style-card.md        # step 3 (also saved for reuse, see below)
├── missing-items.md     # step 4 question batch
├── script.md            # step 5 AV script, "Status: LOCKED" after approval
├── shot-list.md         # step 6
├── rights-log.md        # step 6
├── handoff/             # step 7 files for the editor
└── package.md           # step 8 publish package
```

Save the style card a second time to `~/.claude/channel/style-card.md`, the shared card that `yt-plan`, `yt-comment` and `yt-audit` also read, so the next run starts from it. Where there is no home folder (claude.ai chat), keep it in the project's memory or `channel/style-card.md`.

## Run order

Follow the steps in order. Each gate says what must happen before moving on. Full detail, file formats, and a worked example: [references/run-workflow.md](references/run-workflow.md).

### 0. Inventory

List the skills and connectors that are actually enabled in this chat. Map each step to the best one: research, user's own channel (style only), transcription, image generation, video generation, voice, stock search, docs, captions, timeline export. Write the map and the gaps to `inventory.md`. Read [references/connectors.md](references/connectors.md) for how to match tools to steps.

- Call connector tools by fully qualified name, `ServerName:tool_name`.
- Never claim a connector that is not connected. A gap becomes a handoff file, not a guess.

### 1. Intake

Accept a video file, a YouTube link, or a transcript plus a note that the file is coming. Also take anything the user already has: past scripts, a style card, own clips, a voice sample, an angle.

Read [references/video-analysis.md](references/video-analysis.md), then measure the reference:

- **Video file:** run the analyzer.
  ```bash
  python3 ${CLAUDE_SKILL_DIR}/scripts/analyze_reference.py <video> productions/<slug> --language auto
  ```
  (Relative: `scripts/analyze_reference.py`.) Read `reference/analysis.md`, then open `reference/hook/hook_sheet.jpg` and every `reference/sheets/sheet_NN.jpg` with the image reader.
- **YouTube link:** read the transcript with the browser into `reference/transcript.txt`, watch the hook and one moment per minute for style, and ask once for the file so rhythm can be measured exactly.
- Do not download the reference's video or audio for reuse. Study material stays in `reference/`.
- Record the reference file name and URL in `intake.md`. `check_package.py` uses them to catch reuse.
- If the user can export the audience-retention CSV of their own last video (Studio → Analytics → Engagement → download), run `python3 ${CLAUDE_SKILL_DIR}/scripts/retention.py retention.csv --transcript <their srt>` and carry its hook leak and biggest cliff into the craft brief as "own-channel lessons". Optional; never block on it.

### 2. Craft brief, then stop using their words

Read [references/craft-extraction.md](references/craft-extraction.md). Write `craft-brief.md`, about half a page: hook type and click promise, what the first 5–15 s do, section jobs, attention dips and interrupt types, open loops and payoff, what they left out, plus the **measured** rhythm (cuts/min, shot length, wpm, dense and sparse windows) and the **visual grammar** from the frames. Include the reference **beat map** and a **topic map**: the viewer questions it answers, the facts it relies on (to re-check, not reuse), its gaps, and two or three angle options for the user.

Show the brief. Never show a rewritten transcript. After the brief exists, work from the brief, not the transcript.

### 3. Lock the user's style

Read [references/style-card.md](references/style-card.md) and fill [assets/style-card-template.md](assets/style-card-template.md) from the user's own material only.

**Gate:** if there is no real sample of the user's voice or writing (a past script, a video, a transcript of them talking, written notes in their voice), stop and ask for one. Do not invent a personality and call it theirs. If a saved style card exists (check `~/.claude/channel/style-card.md` first), reuse it; change it only when the user corrects it.

### 4. One question batch

Fill [assets/missing-items-template.md](assets/missing-items-template.md) with only what is still unknown and ask it once. Tag each question by what it blocks:

- `(required: script)`: angle the user believes (offer the topic-map angle options), target length, aspect, on camera / faceless / VO-on-footage. Blocks step 5.
- `(required: production)`: claims to confirm (`[VERIFY]` lines must be settled before the script locks), voice, the user's clips and their rights, permission to search libraries, music licence, thumbnail faces, things the user refuses to say or show. Blocks step 7 and `READY`, not the script or the shot list.
- `(default ok)`: undoable packaging details only (working title, chapter count). State the default.

Never default voice, likeness, claims, or media rights.

If every `(required: script)` item is already known from the user's message or saved card, do not stop here: write the script (and the shot list, if the user waived the script gate) in the same turn and send the open production questions with it. A missing personal figure or proof point is not a reason to stop either; write `[VERIFY: your real figure]` in the line and list it with the questions.

### 5. Original script

Read [references/originality-rules.md](references/originality-rules.md). Write a new video in [assets/av-script-template.md](assets/av-script-template.md): new or sharper promise, new examples and verifiable proof, new running order, spoken language, hook in the first 5–10 s that pays the title, one retention line, an interrupt written in every 60–90 s, one payoff ending, one CTA. Size it to the style card's words per minute.

Hook: write **five** opening lines against the 21 formulas in `scripts/hooks.json`, score them with `python3 ${CLAUDE_SKILL_DIR}/scripts/hookscore.py hooks.txt` (relative: `scripts/hookscore.py`), keep the top two, and show both with their panels and formula names; never hand over one hook. The scorer reads English word patterns: for a Hindi or Hinglish hook, score its plain-English rendering and treat the number as a rough check, not a verdict.

Research factual claims with an available research tool. Re-research every fact on the topic map with an available research tool (current data, primary sources), answer the questions the reference left open, and use the user's own examples. Mark shaky claims `[VERIFY]` and ask. Never borrow the reference's proof, stories, or order of reveals.

Then run the guard:

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/similarity_guard.py productions/<slug>
```

(Relative to this file: `scripts/similarity_guard.py`.) If it fails, rewrite the flagged lines or reorder beats and run it again. Only a passing script is shown.

**Gate:** show the script and wait. No money, voice generation, or footage generation before the user approves it, unless the user already said to skip this gate. On approval set `Status: LOCKED` and `Approved by user: yes`.

### 6. Shot list and rights

Read [references/media-rights.md](references/media-rights.md). Every visual and every sound gets a row in [assets/shot-list-template.md](assets/shot-list-template.md) and [assets/rights-log-template.md](assets/rights-log-template.md).

Match the picture rhythm, not the pictures: aim the shot count at the reference's cuts/min within about ±30% (unless the style card says otherwise) and put visual changes where the measured dense windows were.

Source priority: (1) user's clip with confirmed rights, (2) connected licensed library allowing commercial YouTube use, (3) public domain or commercial-and-modification CC, (4) newly generated shot, with the realistic-synthetic disclosure if it could pass as a real event or person, (5) a filming brief the user can shoot.

Gameplay comes from the user's recording, a press kit, or the publisher's or developer's official upload, credited and with trailer music muted. Article, Instagram, and X posts are captured with the browser as credited editorial screenshots. Both have their own rules in `media-rights.md`.

Hard bans, no exceptions: nothing from the reference file or its URL (no frame, crop, zoom, speed change, reverse, screenshot, regrade, audio, stem, SFX, room tone, voice); no downloading someone else's YouTube video for picture or sound (only official publisher or developer uploads, under the gameplay rules); no unlicensed trending audio, score, or song; no clone or likeness of the reference creator or anyone else; a clone of the user's own voice only after they approve that exact voice in this chat; a stock synthetic voice only after the user picks it for this video; nothing from the user's channel whose picture or sound came from the reference.

If the user says "just take it from YouTube", ask whether they own that video or it carries an explicit reuse license. If not, do not download it. Offer stock, a generated shot, or a filming brief, and wait. An empty shot goes to `missing-items.md`, never back to the reference.

**Gate:** show the shot list and rights log. Wait for approval before generating or downloading media.

### 7. Produce or hand off

Create only approved rows with enabled tools: voice, generated shots, graphics, captions, thumbnail stills. Where no tool finishes a step, write the handoff in `handoff/` (script doc, timeline notes, file names, in/out points) so an editor can finish without guessing.

With a timeline tool: 1080p or 4K, the chosen aspect, captions burned or sidecar, music ducked under voice, about −14 LUFS integrated. With no editor connected, do not invent an export; list what remains for the user's editor.

### 8. Publish package

Read [references/publish-package.md](references/publish-package.md). Write `package.md`: 5 scored titles, thumbnail brief with 3 directions (rights-cleared faces and images only), description (payoff, chapters, sources), chapters matching the locked script, pinned comment, end screen and one card, disclosure line if realistic synthetic media remains, and a link to the rights log.

Lint every title with its thumbnail text: `python3 ${CLAUDE_SKILL_DIR}/scripts/title.py --title "..." --thumb "..."`. Draft chapters from the final voice track's SRT with `scripts/chapters.py <srt> --target N` (it enforces 00:00, at least three, each 10 s or longer), then retitle every chapter in the user's words.

Then run:

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/check_package.py productions/<slug>
```

(Relative: `scripts/check_package.py`.) Fix every failure it prints. Mark `Status: READY` only when it passes and the user has approved both the script and the asset plan. Ready never means posted. The user publishes.

## When the user asks for something banned

Refuse only the banned part in one short paragraph, say why in plain terms (it is someone else's footage or sound; publishing it risks a Content ID claim or copyright strike and is not the user's to license), then offer owned, licensed, generated, or filmable replacements and continue the rest of the job.

## Example

**Input:** "Here's a link to a 9-minute video on 'why your gym progress stalls'. Make this for my channel." User has a saved style card (dry, direct, 140 wpm, faceless, no swearing) and no clips.

**Output, in order:**
1. `inventory.md`: research = web search; stock = none connected → handoff list; voice = none → user records; editor = none → timeline notes.
2. User sends the file. `analyze_reference.py` measures 9:04, 212 shots (23 cuts/min, median 2.1 s), 168 wpm, a 70 s sparse window at 3:20–4:30.
3. Craft brief (half page): "Problem-reveal hook; promise = one fix that works; first 12 s show a stalled log and name the cost; beats: hook → myth → list-item ×3 → reveal → CTA; sparse window 3:20–4:30 is the attention dip; payoff withheld until 7:50; visuals ~60% gym B-roll, text card at every number. Topic map: answers 'why do I stall?' and 'deload or push?'; relies on a 2019 study (re-check); never shows a real log. Angles: personal 8-week test, the deload myth, a beginner's version."
4. No question about style (card exists). One batch: script-blockers (angle from the three options, length, aspect) and production questions (record VO yourself?, OK to search rights-cleared libraries?, music bed?).
5. Once the script-blockers are answered: original AV script (new promise "the one change that restarted my squat", the user's own training-log example, beats hook → proof → stake → method → test → payoff → CTA), guard passes, shown with any still-open production questions, wait.
6. After approval: shot list sized to about 20 cuts/min, sources like `user clip`, `Pexels #...`, `generated (disclosed)`, `filming brief`. Nothing cites the reference.

A fuller worked example (20-second "five morning habits" reference to brief, script, and four-row shot list) is in [references/run-workflow.md](references/run-workflow.md#worked-example).
