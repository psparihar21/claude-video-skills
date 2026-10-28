# Decisions and corrections (MycoPunk session, 22-23 Oct 2026)

Newest decisions override older ones. Dates are 2026.

## What the user asked, in order
1. "one horizontal and other vertical: long format video from horizontal, shorts from vertical; research how gameplay should look in these formats; use all skills and tools"; Shorts end with "watch full gameplay on the channel"; the long video ends with "thanks for watching, like and subscribe if you liked it, join back for the next gameplay of Mafia: The Old Country".
2. After the first cut: "like the 2nd Short, the long video is perfect". Changes to the Short: remove captions, double the length with more clips and fast cuts, start by showing which game it is with the poster, like the long format; render both in 4K.
3. "keep these two files, remove the other clips".
4. "create a thumbnail for YouTube long and Short, and the description for the long video, captions for Shorts and Instagram".
5. "don't save title/description/captions in a doc, show them in chat so I can copy and paste; research the net for what can go viral and keep it related to our video". (Shown in chat in code blocks; saved doc deleted.)
6. "save the scripts and all the changes in the skills".

## What was built and accepted
- Long: 15:21, 36 segments, 4 s action cold open, mic and game rebuilt from tracks 3 and 2 (voice -16, game -23 ducked, final -14.6 LUFS, peak -2.4), outro card over the last 9 s (his own sign-off), 3840x2160 60 fps HEVC, 3.45 GB.
- Short: 89 s, 12 fast cuts (blast, cowboy joke, cockroach, welding + jetpack, punch, space, "full tabahi"), zoom-punch 1.10 to 1.0 over 0.2 s on every live cut, no captions, 2.85 s "NOW PLAYING / MYCOPUNK / PS5 GAMEPLAY · PS PLUS" poster card over the opening blast, 3.5 s "WATCH THE FULL GAMEPLAY on the channel" card, -14.3 LUFS, 2160x3840 HEVC.
- First-round Shorts (1080p, captions, hook title) are superseded; the user liked the jetpack one best, so a jetpack/welding block stays in every Short version.

## Lessons (do not repeat)
- 4K in one filter graph: "Cannot allocate memory", 0-byte or 4-second output. Render per segment, concat with `-c copy`.
- A 4K render that ends mid-way (the machine slept, the date rolled over): the progress file shows the last finished segment; resume from the next one.
- Loudnorm `linear=true` alone let AAC peaks reach +0.2 dBFS on the long file; target TP -2.5 and add `alimiter=limit=0.7:level=disabled`, then measure the m4a.
- Hindi captions timed from Whisper on sparse speech were unreliable (clumped times, a hallucinated "subscribe kar do"). For captions re-transcribe the clip alone with VAD off and still treat times as approximate. Captions are not wanted in the finished Short anyway.
- The vertical file has an intermittent bright green strip at the bottom of the game area. Do not pick a thumbnail or cover frame that shows it (it appeared at 3.5 s of the Short; a calm arena frame at 14 s was clean).
- The vertical frame is about 1080x956 game on top and the facecam below with black side bars; a text block over the facecam's top band is clear of the face.
- Facecam in the horizontal file is bottom-left (about 230x360 px at 1080p). It stays in the long video as is (HUD fully visible).
- Whisper `--prompt` with game names leaked into silence as fake speech: leave the prompt out on gameplay commentary.
- PS5 hub frames show an avatar and the icon row; crop the poster to the art only.

## Copy that was approved (shape to reuse)
Research first: search the game's facts (developer, publisher, release date, PS Plus tier, what the game is) and treat them as claims with sources. Only describe what is in the footage. For the MycoPunk run: co-op looter shooter by Pigeons at Play, published by Devolver Digital, 1.0 on 20 Oct 2026, PS Plus Game Catalog (Extra/Premium) from day one; grid-based weapon upgrades; Borderlands-like look. No search-volume data came from the web search; say so.

Long titles (<60 chars, game + PS5 first), rank 1 = search phrase:
- `MycoPunk PS5 Gameplay: First Look (PS Plus, Hinglish)`
- `MycoPunk Is on PS Plus: Is It Worth Playing? (PS5)` (a question the video answers)
- `I Tried MycoPunk on PS5 (Jetpack, Bosses, Upgrades)`

Long description shape (under 120 words): line 1 stands alone with game + PS5 + PS Plus + language; one line of who/what/release; one line of what is in the video; "Next gameplay on this channel: <game>."; chapters (first at 0:00, each verified on frames, checked to a few seconds); `Not affiliated with <developer>, <publisher> or Sony Interactive Entertainment.`; 3 hashtags last. No "like and subscribe" in the description unless asked.

Short title: one Hinglish question (`PS Plus ka naya game MycoPunk kaisa hai? #Shorts`) and one English (`MycoPunk on PS5: jetpack, bosses and chaos #Shorts`). Short description: 1-2 lines, full gameplay is on the channel, `#Shorts #<Game> #PS5`. Instagram: hook in the first 125 characters, channel pointer, next game, blank line, 7 specific hashtags (`#<Game> #PS5 #PSPlus #PS5Gameplay #Gaming #IndianGamers #FPSGames`), no #fyp/#viral. Hashtag counts from the research: 2-4 for Shorts, 5-10 for Reels (vendor blogs, loosely).

Thumbnail (video-packaging, Path B local renderer): hook `FIRST LOOK`, eyebrow `PS Plus game`, frame from the final video with the boss and gun visible (2.0 s; the type covered 15% of the subject; the right-side variant covered 40% and was dropped). Shorts cover: hook `MYCOPUNK`, eyebrow `PS5 gameplay`, clean frame.
