# Run workflow

Detail for each step in `SKILL.md`, the file formats the scripts parse, and one worked example.

## Contents
- Gates at a glance
- File formats the scripts parse
- Step notes
- Worked example

## Gates at a glance

| Gate | Blocks | Opens when |
|---|---|---|
| Style sample | Style card, script | At least one real sample of the user's voice or writing, or a saved card |
| Question batch (script) | Script | Every `(required: script)` question answered: angle, length, aspect, presence |
| Question batch (production) | Producing media, `READY` | Every `(required: production)` question answered: voice, clips, library permission, music, faces, refusals |
| Similarity guard | Showing the script | `similarity_guard.py` exits 0 |
| Script approval | Voice, footage, spending | User approves in chat (or said earlier to skip this gate) |
| Asset approval | Generating or downloading media | User approves shot list and rights log |
| Voice approval | Any cloned voice | User approves that exact clone of their own voice in this chat |
| Package check | `Status: READY` | `check_package.py` exits 0 and both approvals exist |

Approval means a clear yes in chat to the specific thing shown. Silence, "looks fine so far", or approval of an earlier version does not count.

## File formats the scripts parse

Keep these exact markers. Everything else in the files is free text.

**intake.md**
```
Reference file: budget-video.mp4
Reference URL: https://www.youtube.com/watch?v=XXXXXXXXXXX
```
Use `none` when there is no file or no URL.

**craft-brief.md** needs a `## Beat map` section, one numbered line per section of the reference:
```
## Beat map
1. beat: hook — names the cost in the first line
2. beat: list-item — habit one, fast
```
Beat labels come from the vocabulary in `craft-extraction.md`.

**script.md** (from `assets/av-script-template.md`): `Status: DRAFT` or `Status: LOCKED`, `Approved by user: yes|no`, and one heading per section, `## Section N — beat: <label>`, each followed by the AV table. The `Spoken line` column is what the guard checks.

**shot-list.md / rights-log.md**: the tables in the templates. Column names matter; row order does not. Leave a cell empty only when the template says it may be empty.

**missing-items.md**: one checkbox per question.
```
- [ ] (required: production) Will you record the voiceover yourself?
- [x] (required: script) Target length? — Answer: 6–7 min
- [ ] (default ok) Working title — default: "The Budget That Survives a Bad Month"
```

**package.md**: `Status: DRAFT` or `Status: READY`, and a `Disclosure:` line (`Disclosure: none` when no realistic synthetic media remains).

## Step notes

**0. Inventory.** Check the tool list, not memory. A skill counts only if it is listed as available; a connector counts only if its tools are callable. Write `inventory.md` as a table: step → tool (`ServerName:tool_name` or skill name) → status (`ok`, `gap → handoff`, `gap → user does it`). See `connectors.md`.

**1. Intake.** If the user pastes a link and no connector can read it, ask for a transcript or the file, and say the file is used only to study structure. If the user's own channel is connected, use it for the style card only, never as a footage source for this video unless the user confirms the clip is theirs and did not come from the reference.

**2. Craft brief.** Run `analyze_reference.py` first when there is a file (see `video-analysis.md`). About 200–300 words plus the beat map and topic map, with the measured numbers quoted from `metrics.json`. Describe mechanisms ("withholds item three until the end to hold the list"), not content ("talks about cold showers"). Once written, do not reopen the transcript for wording.

**3. Style card.** Follow `style-card.md`. When the user gives a sample mid-run, build the card, show it in five lines, and continue.

**4. Questions.** One batch. Production questions never hold up the script: if the script-blockers are known, write the script in the same turn and attach the open production questions. If the user answers only part of the batch, continue with what is unlocked and re-ask only the remaining required items in one short message.

**5. Script.** Word budget = target minutes × style-card wpm. Mark interrupts in the Visual or On-screen column with `[INTERRUPT: type]`. Mark unverified claims `[VERIFY: what and why]`. Run the guard before showing.

**6. Shot list.** One row per visual change, including graphics and text cards. Sounds go in the rights log. Searching any library is fine; only rows with a licence that fits go in.

**7. Produce.** Generate only rows marked `Approved: yes`. Name files `<slug>_<row>_<short-desc>.<ext>`. Handoff timeline notes list row, file name, in/out, track, and any effect.

**8. Package.** Follow `publish-package.md`, then run `check_package.py`.

## Worked example

### Reference (20 s, attached as `habits.mp4`)

The reference is a fast vertical clip: a creator lists five morning habits, says one is "the one nobody does", and reveals it last. Stock-style shots, a trending song, text on screen.

### Craft brief (what was kept)

> **Hook type:** contrarian list. Opens by saying most habit lists are wrong, then promises five that work.
> **First 5 s:** names the promise and the twist ("one nobody does") so the viewer stays for it.
> **Section jobs:** fast list, items 1, 2, 4, 5 at ~3 s each; item 3 withheld as the payoff.
> **Interrupts:** a cut every ~1.5 s; on-screen counter changes each item.
> **Open loop / payoff:** "habit three" is named as special early, paid at 17 s.
> **Weak spot:** no proof for any habit; payoff is a claim, not a demonstration.
>
> ## Beat map
> 1. beat: hook — contrarian claim plus promise
> 2. beat: list-item — items 1, 2
> 3. beat: list-item — items 4, 5
> 4. beat: reveal — withheld item 3
> 5. beat: cta — follow for more

Not kept: their habits, their wording, the song, their shots, the counter design.

### Style card (excerpt, from the user's two past scripts)

> Voice: dry, direct, short sentences (avg 7 words). No hype words ("insane", "game-changer"). One deadpan joke per minute. 145 wpm. Faceless, hands and desk. Ends with a one-line verdict, never "smash that like button".

### Original script (excerpt)

The user's angle: they tested morning routines for a month and kept one thing. New promise, new order (proof first), no list.

```
Status: LOCKED
Approved by user: yes

## Section 1 — beat: hook
| TC | Spoken line | On-screen text | Visual | Music/SFX | Source |
|---|---|---|---|---|---|
| 0:00 | I tried a morning routine for thirty days. I kept one thing. | 30 days → 1 thing | Alarm clock, 6:00, hand slaps it | low pulse in | S1 |

## Section 2 — beat: proof
| TC | Spoken line | On-screen text | Visual | Music/SFX | Source |
|---|---|---|---|---|---|
| 0:04 | Here's the log. Twenty-nine days of crossed-out boxes. | Day 1–29 | Notebook page, boxes crossed | — | S2 |

## Section 3 — beat: stake
| TC | Spoken line | On-screen text | Visual | Music/SFX | Source |
|---|---|---|---|---|---|
| 0:09 | Most of it cost me sleep and gave me nothing. | [INTERRUPT: graphic] sleep −40 min | Wide: empty street at dawn | pulse drops | S3 |

## Section 4 — beat: payoff
| TC | Spoken line | On-screen text | Visual | Music/SFX | Source |
|---|---|---|---|---|---|
| 0:14 | The one that stayed: water before phone. That's it. Boring works. | water > phone | Glass filled, phone face down | button hit | S4 |
| 0:19 | Try it for a week and tell me I'm wrong. | | Hold on glass | out | S4 |
```

Beat sequence hook → proof → stake → payoff differs from the reference's hook → list-item → reveal → cta. No sentence, example, or reveal order is shared. Guard passes.

### Shot list (four rows)

| # | TC | Visual | Source type | Source | License / proof | Realistic synthetic | Disclosure | Approved |
|---|---|---|---|---|---|---|---|---|
| S1 | 0:00 | Alarm clock slap | user-clip | user: `desk_alarm_0412.mov` (user confirmed own footage) | owned by user | no | | yes |
| S2 | 0:04 | Notebook with crossed boxes | stock | Pexels, video 3,1xx,xxx "notebook checklist" | Pexels License, saved `rights/pexels_31xxxxx.txt` | no | | yes |
| S3 | 0:09 | Empty street at dawn, wide | generated | image-gen tool from inventory, prompt saved `handoff/S3_prompt.txt` | generated for this video | yes | "Altered or synthetic content" label set in YouTube Studio; description line added | yes |
| S4 | 0:14 | Glass filled, phone face down | filming-brief | filming brief: overhead, glass center frame, pour 3 s, then phone placed face down left, 6 s total, kitchen counter, daylight | to be shot by user | no | | yes |

None of the rows cite `habits.mp4` or its URL. Music is a licensed bed from the user's own library, logged in the rights log with its licence; the reference's trending song is not used.
