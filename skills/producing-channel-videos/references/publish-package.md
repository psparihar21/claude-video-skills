# Publish package

Write `package.md` in the production folder. It is the last file and depends on the locked script and approved asset plan.

## Layout

```
# Publish package: <working title>
Status: DRAFT
Disclosure: none

## Titles
| # | Title | Promise match (1–5) | Why |

## Thumbnail brief
Direction A / B / C: subject, text (≤4 words), expression or object, color from style card, image source (row in rights log).

## Description
<first two lines: the payoff, in the user's voice>
<chapters>
<sources: every claim source, every CC attribution>
<disclosure line if any realistic synthetic media remains>

## Chapters
0:00 ...

## Pinned comment

## End screen and card
End screen: ... (last 5–20 s)
Card: at <TC>, links to ...

## Rights log
See rights-log.md (N rows, all licensed).
```

## Rules

- **Titles:** five, each scored 1–5 on how exactly the script's first 10 s and ending deliver it, and each run through `scripts/title.py` with the thumbnail text: under 60 characters (desktop cut) with the subject inside the first 40 (mobile feed), at most two all-caps words, a number, name or date where the script has one. Drop any title the script does not pay off. Do not reuse the reference's title or its structure word-for-word.
- **Thumbnail:** three directions. The title and the thumbnail are one unit: thumbnail text says what the title does not (no shared words), three words or fewer as the target. Faces only of people who have given rights (usually the user); images only from rights-logged rows or new generation. Do not copy the reference thumbnail layout.
- **Description:** lead with the payoff, then chapters, then sources and attributions. The first two lines are the search snippet: write them in the words a viewer would type.
- **Query test:** write the three searches this video should win; the title and first two description lines must contain their key words. If not, fix the title, not the description.
- **Tags:** only spellings, names, tool names and abbreviations people type; 15 at most. Tags are a weak signal; never stuff.
- **Chapters:** start at 0:00, at least three, each ≥10 s, matching the locked script's section timecodes. Draft with `scripts/chapters.py` from the voice track's SRT, then retitle each as the promise of that section in 3–5 of the user's words. A section that cannot be named in five words is two sections or filler.
- **Pinned comment:** one question or prompt that fits the CTA.
- **Disclosure:** `Disclosure: none` or the exact line, plus a reminder to tick altered-or-synthetic content in YouTube Studio.
- **Status:** set `READY` only after `check_package.py` passes and the user approved script and asset plan. Ready means ready to upload. The user publishes; never post or schedule on their behalf.
