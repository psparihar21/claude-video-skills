---
name: episode-template
description: Fill-in package for any YouTube video (gameplay series, news, tech, review, tutorial, vlog, explainer, collab, challenge): titles, thumbnail brief, first-90-seconds hook outline, description and tags from a topic. Built from a study of the Dattrax Plays channel; gaming is the observed genre, other genres use the same skeleton. Use for "make it like Dattrax", "video package", "title and thumbnail for this video", "template for a new video/series".
---

# episode-template

Skeleton from `~/.claude/skills/viral-thumbnail/references/dattrax-style.md` (14 top videos' titles/thumbnails/descriptions, 3 transcripts). **Only gameplay was observed.** For other genres the skeleton is the same but the genre packs in `templates/genres.md` are general practice, not studied data; say so to the user. The user's brand, face, voice and rules win (read `viral-thumbnail/references/choices.md`).

## Inputs (ask only what is missing)
topic or game, genre, series/episode number if any, one real fact for the hook (date, number, result, what changes), platform text, long or Short.

## Output (show in chat code blocks, English only)
1. **3 titles**: `templates/titles.md` (universal formulas + genre lines), 55-80 chars.
2. **Thumbnail brief**: one focal subject (real frame or official art, never generated), 0-3 words, face slot, chip (EP n / number / PS5). Copy `templates/thumb-brief.json`, run viral-thumbnail compose.py.
3. **Hook outline**: `templates/hook.md`, with the promise paid inside 5 min (Shorts: inside 3 s).
4. **Description + tags**: `templates/description.md`.
5. Build with the other skills: script/VO (faceless-vo-script, own-voice-render), cut (video-edit, gameplay-longform-shorts, clipify), packaging (video-packaging), Shorts (poster-news-short).

## Universal rules (all genres)
- One promise per video; title, thumbnail and first 30 s say the same thing.
- Never claim a "first", "today", price or number that is not verified.
- No other creators' names in tags or titles unless in the video and agreed.
- No generated scenes or people in thumbnails. Do not promise virality; A/B with Test & Compare.
