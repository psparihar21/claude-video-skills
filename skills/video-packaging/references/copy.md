# Copy rules

Write only the format the user asked for. Every claim must trace back to a frame you looked at,
a number in analysis.json, or something the user said and the frames do not contradict.

## Thumbnail type (on the image)
- **Hook:** 2–4 words is the target. Hard limits: 3 lines, 7 words, 18 characters per line.
  Over the limit means rewrite, never shrink. The script refuses with exit 2.
- **Eyebrow (optional):** up to 4 words or 28 characters. Use it for the format, such as "Silent timelapse"
  or "Before / after". Do not repeat the hook in it.
- No emoji. No play button, view count, watermark, logo bug, or second caption bar.
- Do not repeat the title word for word. The hook is the feeling. The title is the search phrase.
- Hindi or Hinglish hooks are fine. Devanagari uses Nirmala UI Bold on Windows. Count the characters the same way.

## Titles: 3 options, ranked
- Each under 60 characters. Count them.
- Subject first. Sentence case. No clickbait you cannot back up with the frames.
- Rank 1 is the best search phrase. Give one line per option with its character count.
- Lint each with its thumbnail hook: `scripts/title.py --title "..." --thumb "..."`. Drop any title the hook repeats a word of. Keep the subject inside the first 40 characters (the mobile feed cut). At most two all-caps words. A number, name or date beats an adjective. The tool's 3-word thumbnail check is advisory; this skill's hook limits above still rule.

## YouTube description
- Line 1 says what the video shows and stands alone in search. Under 100 characters is best.
- Then 2–4 short lines: what happens, what changes, what it was made with **only if the user said so**.
- No chapters if the video is under 60 seconds. For longer videos, add chapters only from timestamps
  you verified on the contact sheet. The first chapter is 0:00.
  When a transcript exists (for example from video-edit), draft them with `scripts/chapters.py <srt> --target N`, which enforces 0:00, three or more, each 10 s or longer. Retitle every line as the promise of that section in 3–5 words.
- At most 3 hashtags, on the last line.
- Query test: write the three searches this video should win. The title and line 1 must carry their key words.
- Tags (only if asked): spellings, names, game and tool names, abbreviations people type. 15 at most.
- Under 120 words in total.
- No "like and subscribe" unless the user asks.
- If the copy names a game, console, or brand, add `Not affiliated with [owner].` as the last line before
  the hashtags. YouTube description only. Never on the thumbnail.

## Shorts caption
- 1 or 2 lines. At most 2 hashtags (#Shorts counts as one).

## Instagram caption
- Line 1 works alone when Instagram cuts it near 125 characters. Put the hook there.
- Then at most 3 short lines.
- Leave a blank line, then 5–8 specific hashtags: the subject, the format, and the niche.
  No #fyp, #viral, #explore or #reels pile.

## Never invent
- GPU, CPU, RAM, price, monitor size, model numbers, the song or artist, location, or time taken,
  unless the user stated it. If the user's notes give a spec, you may repeat it as their claim.
- Music or sound: only if `audio.real_audio` is true, and even then say "with music" only when the user
  says it is music. The measurement proves sound exists, not what it is. With no audio stream, or with
  real_audio false, the video is silent. Do not imply a soundtrack.
- Speech: this skill does not transcribe. Never quote dialogue or claim what someone says.
- "Ready", "best" or "ultimate" claims about future products (for example "GTA 6-ready") are the user's
  claim. Keep the user's wording only if they asked for it, and never add specs to justify it.

## When notes and frames disagree
The frames win. Say it in one sentence, for example: "Your notes say RGB lighting; the frames show none,
so I left it out."

## Example: YouTube thumbnail + description (silent timelapse)
This is an example of shape only. Every line below must describe something visible in that video's frames.
Hook: `DESK BUILD` / `TIMELAPSE`. Eyebrow: `No talking`.
```
Timelapse of a gaming desk setup going from empty to finished.
Every step of the build, sped up, no voiceover.
Cable routing, monitor placement and final lighting.
Not affiliated with Rockstar Games.
#desksetup #timelapse #gamingsetup
```


## Delivery and research (user rules, 2026-10-23)
- Show titles, descriptions and captions **in chat in code blocks**, one block per item. Never save them as a file or doc (a saved copy was deleted when the user said so).
- Before writing, search the web for the game or product facts (developer, publisher, release date, subscription tier, what it is) and for hashtag norms. Web search gave no search-volume data, so say so and never promise virality.
- Gaming long description: line 1 = game + platform + subscription + language; one line of facts; one line of what is in the video; the next video; chapters; a `Not affiliated with` line naming developer, publisher and platform owner; 3 hashtags. Examples are in `gameplay-longform-shorts/references/choices.md`.
- Shorts: a Hinglish question title and an English title (#Shorts at the end), 2-3 hashtags. Instagram: hook in the first 125 characters, channel pointer, next video, 7 specific hashtags.
- Tooling: write brief.json without a BOM (`[IO.File]::WriteAllText` with `UTF8Encoding($false)`), and never use a frame that shows a capture glitch (the vertical OBS file has a green bottom strip at times).
