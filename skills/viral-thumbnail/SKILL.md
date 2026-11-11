---
name: viral-thumbnail
description: Make a high-click YouTube thumbnail (1280x720) for the user's Pushpstation gaming videos - official key art or a real video frame, huge extruded title, episode chip and a round face badge. Use when the user asks for a "good / viral / better thumbnail", for an episode thumbnail of a game they play, or says the video-packaging thumbnail is not good enough. Not for Shorts covers (use video-packaging) and never for generated scenes.
---

# viral-thumbnail

One composer script, one brief file. The look is the channel's: chunky white Impact title with a coral extruded shadow, one volt-yellow word, rounded chips, a round face badge with a volt ring. Built from the TLOU2 Ep 1 session (2026-11-11), see `references/choices.md` for every correction the user made. **Read it first; it overrides this file.**

## Steps
1. **Scope.** Ask nothing the message already says. Need: game, episode number, platform text (PS5), the video file.
2. **Art.** Prefer the game's official key art when the user allows ("use the official image"): PlayStation Store listing images are on `image.api.playstation.com` (`store.playstation.com/concept/<id>` lists them; drop the `?w=54&thumb=true` query for 3840x2160). Look at every image; pick a clean hero with no logo text and a calm side for the title. Say plainly it is the publisher's art (small claim risk). If the user does not allow official art, use a clean frame extracted from the **final** video (video-packaging `analyze`), never a glitch frame (vertical OBS file has a green bottom strip at times).
3. **Face.** From the vertical OBS file (facecam is the bottom half, about 1080x960 starting at y=960): sample frames with `crop=720:720:240:1130` tiled 10x6, then look. Pick a **front-facing frame with the mouth closed** and eyes toward the screen. The user rejected open-mouth frames twice. Crop a 700 px square around the face at full resolution to `face.png`. A frame where he looks at the camera does not exist during gameplay; say so and offer a fresh photo.
4. **Brief.** Copy `examples/tlou2-ep1.json`, change art, title lines, chips, out. Rules: title at most 3 short lines, one word in volt; top-left chip = platform only (`PS5`); bottom-left chip = `EP n` (episode, not "full gameplay"); **no language word on the image** (no "Hindi"); English only; no emoji, no logos, no view counts.
5. **Render.** `uv run --with pillow python "$HOME/.claude/skills/viral-thumbnail/scripts/compose.py" brief.json` (needs Windows Impact font). Exits with the path and size; the file must be under 2 MB.
6. **Look.** Open the JPG. Checks: title does not cover the character's face; face is clean and mouth closed; text readable at 168 px wide (downscale and look); nothing inside the bottom-right 15 percent that YouTube's duration stamp covers except the face ring is fine.
7. **Deliver.** Put it in the video's final folder, keep the previous version as `-v1`, and say what the image is made from. Do not promise virality: web search gives no CTR data.

## What the research said (2026-11-11, blog sources, unverified numbers)
High contrast, one clear focal point, 1-3 words, expressive face, text in the upper two thirds, A/B with YouTube Test & Compare (up to 3 variants, change one thing). Treat the percentages in those blogs as marketing claims.

## Do not
- Generate a scene, a person or a background with an image model.
- Put the language, "full gameplay", a play button, a logo bug or a second caption bar on the image.
- Use a frame with burned-in edit text.

## Channel reference
`references/dattrax-style.md` - study of the Dattrax Plays channel (titles, thumbnail layout, series pattern). Read it when the user says "like Dattrax". Reference only; keep our own brand and face rules.

Template: `~/.claude/skills/episode-template/SKILL.md` builds the full Dattrax-style episode package (titles, thumbnail brief, hook, description).
