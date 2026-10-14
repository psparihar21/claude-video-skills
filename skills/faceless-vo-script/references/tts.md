# Voices

Read this only when the default voice is wrong for the job.

`scripts/speak.py` records `07-voice.m4a` with Edge TTS. No key. The line is placed at `in_sec` on a silent bed the length of the edit, so it drops onto the faceless picture in an editor.

| Persona | Voice | When |
| --- | --- | --- |
| Default, or any male observer | `en-IN-PrabhatNeural` | Indian English and Roman Hinglish |
| Persona says female or woman | `en-IN-NeerjaNeural` | Same registers, brighter |
| They ask for expressive | `en-IN-NeerjaExpressiveNeural` | Shorts hooks only. Set `edge_voice` on the JSON |

The neural voice speaks slower than the cue budget, so synthesis runs at `+4%` and may speed a single cue by up to 18% to land before the next cut. A human recording ignores that and uses the teleprompter. If a line is still too long, the tail is trimmed and the report marks `trimmed`. Shorten that line. Do not raise the tempo cap to hide a crowded script.

Do not point a Hindi voice (`hi-IN-MadhurNeural`, `hi-IN-SwaraNeural`) at this Roman script. Those voices want Devanagari and will misread "yeh", "mein", and "hai". If the user hands you Devanagari, set `edge_voice` and keep the spoken line in that script.

ElevenLabs is not called from here. The brief names `eleven_multilingual_v2` because that model family reads mixed Roman better than an English-only model. The user pastes the brief into their own account.

Override on one run:

```bash
python $HOME/.claude/skills/faceless-vo-script/scripts/speak.py \
  --script vo/<slug>/03-script.json \
  --out vo/<slug> \
  --voice en-IN-NeerjaNeural
```
