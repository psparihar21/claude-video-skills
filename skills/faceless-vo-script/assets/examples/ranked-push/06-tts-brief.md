# TTS brief — Don't push that door

Generated from 03-script.json. Change the JSON and render again.

## Content analysis

- Format: story-over-gameplay
- Register: hinglish
- Platform: youtube-shorts
- Duration: 32.0s
- Archetype: Storyteller
- Why this voice: A dry Indian storyteller over gameplay wallpaper. The story leads. You mention the game only when the picture makes the same point.

## Emotion map

| Cue | Time | Role | Emphasis | Delivery |
| --- | --- | --- | --- | --- |
| c01 | 00:00:00.100 | hook | nahi | [close, slight smile] Yeh push nahi bachega. |
| c02 | 00:00:02.600 | setup | still | [deadpan on the second clause] The team bol rahi hai wait, lekin yeh banda still takes the door. |
| c03 | 00:00:09.200 | turn | zone | [lean in, not louder] Loot girta hai aur the call is simple: airdrop, ya zone? |
| c04 | 00:00:17.750 | payoff | behind | [drop the pace after the full stop] A third party walks in from behind. Jo abhi hero ban raha tha, ab sirf bachna hai. |
| c05 | 00:00:26.200 | payoff | akela | [close, no smile] Akela mat push karna. |

Holds where the voice stays out:

- 00:00:29.000 → 00:00:32.000: End card reads DON'T PUSH ALONE. The viewer reads it. The voice does not.

## ElevenLabs

Model: `eleven_multilingual_v2`.
Settings: stability 0.42, similarity_boost 0.75, style 0.25, speed 0.96.

Paste this as the voice direction:

A dry Indian storyteller over gameplay wallpaper. The story leads. You mention the game only when the picture makes the same point.

Persona on this video: Pan-India observer, late 20s, close-mic, slight smile, no shout. Not the player.

## Edge TTS

No API key. This is the voice `scripts/speak.py` records.

- Voice: `en-IN-PrabhatNeural`
- Rate: `+4%`
- Hindi neural voices (`hi-IN-MadhurNeural`, `hi-IN-SwaraNeural`) want Devanagari. This script is Roman, so the Indian English voice reads both registers.

## Do not

- Do not sound like a news reader.
- Do not welcome the viewer or ask for a like.
- Do not shout the hook. Make it closer, not louder.
- Do not flatten Hindi connectors into the same pitch as the English nouns.
- Do not fill the marked pauses.
- Do not read text that is already held on screen.

## Paste track

Spoken lines only, with the gaps the edit already has. A TTS box that ignores bracket pauses will run the lines together. Use the timed voice file instead.

Yeh push nahi bachega.

[pause 0.4s]

The team bol rahi hai wait, lekin yeh banda still takes the door.

[pause 0.5s]

Loot girta hai aur the call is simple: airdrop, ya zone?

[pause 3.2s]

A third party walks in from behind. Jo abhi hero ban raha tha, ab sirf bachna hai.

[pause 0.6s]

Akela mat push karna.
