# TTS brief — The first minute

Generated from 03-script.json. Change the JSON and render again.

## Content analysis

- Format: faceless-gameplay
- Register: indian-english
- Platform: youtube-shorts
- Duration: 18.0s
- Archetype: Commentator
- Why this voice: A ranked-game observer. You name the decision, then you stop so the sound of the game can land. No shoutcast.

## Emotion map

| Cue | Time | Role | Emphasis | Delivery |
| --- | --- | --- | --- | --- |
| c01 | 00:00:00.180 | hook | before | [close, no shout] Most players lose the match before it starts. |
| c02 | 00:00:04.700 | turn | still | [drop the pace on the zone] They push one knock. The zone is still twenty seconds away. |
| c03 | 00:00:12.100 | payoff | zone | [deadpan] The fight can wait. The zone will not. |

Holds where the voice stays out:

- 00:00:16.200 → 00:00:18.000: Card reads ROTATE FIRST. Do not read it aloud.

## ElevenLabs

Model: `eleven_multilingual_v2`.
Settings: stability 0.48, similarity_boost 0.78, style 0.15, speed 0.98.

Paste this as the voice direction:

A ranked-game observer. You name the decision, then you stop so the sound of the game can land. No shoutcast.

Persona on this video: Pan-India observer, late 20s, close-mic, calm. Sounds like someone who has watched the VOD, not like a shoutcaster.

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

Most players lose the match before it starts.

[pause 0.5s]

They push one knock. The zone is still twenty seconds away.

[pause 0.5s]

The fight can wait. The zone will not.
