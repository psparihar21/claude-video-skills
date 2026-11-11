# Decisions and corrections (TLOU2 Ep 1, 2026-11-11), newest overrides older

1. First thumbnail (video-packaging, a motion-blurred gameplay frame, hook "EPISODE 1" + "FULL GAMEPLAY"): "thumbnail is not good, create a good thumbnail which can get viral; if you can get a good image use the official image".
2. Official PlayStation Store key art (Ellie in flooded Seattle, 3840x2160, no title text) + big title + volt "2" + round face badge: accepted as the direction.
3. "its ep1 not full gameplay and my face is not looking good" - the tag must say `EP 1`, never "full gameplay"; the first face crop (side-looking, from the horizontal facecam) was rejected.
4. "my mouth is open" - the second face (front-facing but mid-word) was rejected. Chosen: vertical OBS file, recording 1 at 190 s, mouth closed, frontal, serious look.
5. "this one is better but it can be more better, remove hindi from the image" - no language word on the image. Language lives in the title and description only.
6. "add the skill in our skill set which can create viral thumbnails" - this skill.

## Design that was approved
- 1280x720, key art scaled 1.18 and shifted so the character sits right of centre, left side darkened (alpha 175, 640 px).
- Title `THE LAST / OF US` white Impact 150 px with black stroke and a 7 px coral (#ff6246) extruded shadow, `2` in volt (#d6ff3a) 230 px.
- Chips: `PS5` volt on navy (#080a18) top-left; `EP 1` coral with white Impact 120 px bottom-left.
- Face: 300 px circle bottom-right, volt ring 10 px with a soft glow.
- Colours match `video-edit/brand/hf/brand.css` (volt, coral, ink); the packaging copy rules (English only, hook 2-4 words) still apply.

## Facts to remember
- The facecam in the vertical file is 1080x960 at y=960; the face sits at about x 260-960, y 1130-1830 of the full frame.
- During gameplay he looks sideways at the screen nearly always; the first recording's opening commentary (0-300 s) has the best front-facing frames.
- Official art source: `store.playstation.com/concept/230079` (TLOU Part II Remastered). The images are Sony/Naughty Dog property.
- Title lint (video-packaging `title.py`) flags the game name repeated on thumbnail and title; accepted on purpose for official-art thumbnails.
