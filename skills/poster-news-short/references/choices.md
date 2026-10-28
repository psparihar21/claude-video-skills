# Choices and corrections (poster news Short, Oct 2026), in order

These are the user's decisions in their own words. A later line beats an earlier one.

## Format and content
- "create a shorts video and use all the poster of the game ... faceless video and a script" - Short, 9:16, all listed games as posters, faceless, script first, scratch voice before the user records.
- "in the end just remove that full list is on the channel ... keep the outro and ask them to subscribe and like the video and follow for more gaming news, and interesting gameplays" - no "full list on the channel" (the video is the full list). Outro: like, subscribe to Pushpstation, follow for gaming news and interesting gameplays.
- Add interesting angle lines: games leaving just before GTA 6; sad news for sports lovers (Football Manager 26, Cricket 24); "Thank Goodness You're Here was really fun, try it if you have not". These are the user's opinions: keep them as his take, do not invent reasons or dates.
- "instead of saying premium add deluxe also so reel will target both Indian and other ps users" - name the tiers Extra, Premium and Deluxe in captions and on cards where a tier is shown. In speech the user says "PS Subscription".
- The user records his own voice after hearing the scratch voice; he improves the script while recording. Everything after (cards, captions, timing) follows what he said, not the draft.

## Voice edit
- "use take 4 from the start and take 6 for the last part ... remove blank spaces and filler" - pick the better take per part, splice at a pause, squeeze pauses, remove fillers, no dead air.
- "match the game name with the poster" - poster changes on the spoken name (switch 0.12 s early). Show a pair shot when two games are named together ("donon games").
- "my voice is not audible" / "increase the volume of my voice" - voice track from the studio can be very quiet (-28 LUFS): level it to about -15 LUFS alone with a light compressor, then mix.
- "improve the voice quality by using some free skill or tool" - `voice-enhance` skill (DeepFilterNet). Run it on every take before splicing; repair a clipped take with `--declip`.

## Music
- "the background music is not audible" -> bed about -25 LUFS under speech, not -34.
- "music editing can be better like while I'm taking names of the game dip the music very little bit" -> automated gain curve: small dip (about 2.5 dB) on each game name, ducked about 5 dB while talking, lifts in gaps and under the outro, intro swell, fade out 1.4 s.
- "I did not like Night Runner, it was very distorted and it disturbs my voice" -> never pick heavy or busy synth/darksynth for voiceover. Prefer clean, sparse, mid-energy instrumentals: the user kept **Energetic Jersey Club Beat (SnipSound 563, Brick City Club)**. A clean corporate-tech track (Launch Day, Brightwork, 132) was the alternative; short tracks (< 55 s) need a fade that lands before the last words.
- "yes let's keep it as final cut and remove other things" -> final = jersey club mix; delete test versions only when told.

## Packaging
- "create an Instagram caption and YouTube Shorts title and caption which will go viral" -> 3 ranked titles under 60 characters, subject and date in the first 40 characters, a comment question in every caption, tiers in the caption for reach, no unverifiable claims, "Not affiliated with ..." on YouTube.
- "create a proper viral thumbnail also" -> 1080x1920 cover: red tape "LEAVING 17 NOV", cream tape "12 PS PLUS GAMES", the two biggest posters overlapped and tilted, inside the Shorts/Reels safe zone.

## Checks before delivering
- Final -14 LUFS, true peak under -2 dB; frames at every poster switch; cover through `video-packaging check`.
- Say what was not verified: nobody can hear the audio here (ask the user to listen), Whisper cannot see fillers, source lists vary by region.

## GTA 6 editions Short (Oct 2026)
- "copy this reel ... create a reel / youtube shorts for my channel" + a second reference reel: take the structure only, "dont make it AI looking" -> no neon template cards; official art, white cards, cream/red tape, Pushpstation look.
- "first create with cloned voice then if i dont like it i will record my voice" -> scratch voice is the first deliverable (English, Devanagari path in own-voice-render), user re-records only if unhappy; the picture is rebuilt from `voice.srt` times.
- "make it according to india in rupees and ... get all the correct screen shots" -> PS Store India prices (₹5,999 / ₹7,499, extra ₹1,500), screenshots from the publisher's media page zips.
- "starting 5 sec framing is not good as 3/4 screen is empty ... keep all the contents same" -> full-bleed hook, bigger crops; text and facts unchanged.
- "use take 9 for starting 50% and take 6 for last 50% ... if something is missing use other takes ... improve the voice quality ... nice bg music" (GTA 6 India Short): takes were whole-script takes. Hook came from t6 (t9 had no hook), ending (extras, launch, subscribe) from t17 because t6/t9 never reached it. Run voice-enhance on each used take, cut inside pauses (quietest 30 ms in a window), skip restarts ("saara salon, saara salon" -> second try), pick the fluent repeat, squeeze pauses > 0.28 s, level takes to -21 dB speech RMS, then `scripts/assemble_editions_voice.py` writes `anchors.json` (word times in the final voice) and `build_editions_short.py` reads it so the pictures follow the spoken words.
- The user speaks Hinglish and rewrites the script while recording ("lagbag 5999 matlab 6000 ka"): never rebuild cards from the draft script, only from what was said. Whisper forced to `hi` dropped 20 s of this mixed speech; check the splice with `--language en` (full coverage).
