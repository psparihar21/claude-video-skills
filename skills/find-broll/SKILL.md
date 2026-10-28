---
name: find-broll
description: Plan and place b-roll cutaways on a talking-head or voiceover video, landing on the spoken keyword. Use when the user says "add b-roll", "cutaways", "show what I'm talking about", or a Short feels like a static face. Free sources only. Method adapted from Tella's b-roll-finder (louisedesadeleer/b-roll-finder); no code copied.
---

# find-broll

Read `~/.claude/skills/video-edit/RULES.md` first. Free only, no stock subscriptions.

1. Word-level transcript (video-edit `whisper_gpu.py`).
2. Classify each candidate beat, then show the plan and **wait for approval** before downloading:
   - **Receipt**: time-sensitive claim -> screenshot of the official post/headline.
   - **Entity**: person, product, game, moment -> official trailer/channel footage (yt-dlp via agent-reach), or the user's own recording.
   - **Concept**: abstract idea -> simple motion graphic (HyperFrames) or authoritative footage.
   - **Meme/cultural**: never sourced by you; ask the user to supply.
3. One best candidate per approved beat. Accuracy beats volume: drop a beat rather than pad with a weak match. Prefer real footage over generated cards, motion over stills. Never cut to the speaker's own face as b-roll.
4. Place the clip on the spoken keyword, landing ~0.1 s late. Stills get a subtle slow push (see add-zooms kenburns), not a jump.
5. Keep a `broll-manifest.json` of approved beats (time, source, file) so re-renders never silently drop one.
6. Verify every cut in a frame grid at 100%: no watermarks, no wrong subject, no black frames, audio unbroken.
7. If a sourcing method fails, switch once, then drop the beat. User bans apply for the session; offer to save them to RULES.md.
