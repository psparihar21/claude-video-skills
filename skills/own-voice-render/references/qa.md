# QA

## What the pipeline checks automatically

Per chunk, right after it is generated:

| Check | Fails when | Why |
| --- | --- | --- |
| finite and non-empty | NaN or zero samples | broken generation |
| clipping | peak at or above 0.995 | distortion |
| near-silent / mostly-silence | very low level, or under 35% of the clip is above -45 dB | the model produced a gap instead of speech |
| speaking rate | characters per second is outside the range the user's own training clips span (Hindi, including English written in Devanagari: 4.5 to 16.8; Latin English: 6.3 to 19.3; from `calibrate`) | the model rushed, dragged, or ran on: the main failure mode of an F5 model |

On a failure the engine retries the next seed, up to four times, and keeps the first take that passes. If none passes it keeps the least bad one and flags it. A seed or reference that the user locked is never retried: a human choice is honoured and flagged instead.

Whole-track checks: timed cues must fit (tempo at most 1.12x, else overflow), cues must not collide, and the loudness is measured twice (before and after) and reported.

## What it cannot check

**Pronunciation, accent, naturalness, whether it sounds like the user.** A clean report does not mean the audio is right. Always send the clip to the user and ask them to listen, and name the words most at risk: English-origin words, names, and any spelling you were unsure of.

## The listen protocol

1. Send `voice.wav` with `SendUserFile`.
2. Tell the user which cues are the risky ones (flagged, locked, sped up, or containing a rare word).
3. When they report a bad word, ask only what you cannot see: which word, and how it sounds wrong (wrong vowel, wrong stress, too fast).
4. Fix with the loop in `devanagari.md` and re-render only that cue.

## Candidates and locks

```powershell
ovr.ps1 candidates <out> --cue c02 --seeds 1-6
ovr.ps1 candidates <out> --cue c02 --seeds 1 --refs xtr0061,xtr0038,xtr0021
ovr.ps1 lock <out> --cue c02 --seed 3 --ref xtr0038
ovr.ps1 render <out> --only c02
```

- Candidates land in `<out>/candidates/<cue>_<ref>_seed<N>.wav`. Send the files and tell the user the names; they answer with a seed or a reference.
- A lock is stored in `locks.json` by a hash of the cue's text and language. Editing other cues does not move it. Changing that cue's text releases the lock on purpose, because the take was approved for those exact words.
- The take is deterministic: the same text, reference, seed and checkpoint always give the same audio (verified bit-for-bit: the approved take reproduced with correlation 1.0).

## Reference clips

`config.json` lists named references. A reference is a short recording of the user plus its exact transcript.

| Name | Language | Note |
| --- | --- | --- |
| `xtr0061` | hi | default Hindi. "वरना सब वेस्ट हो जाएगा": fixed the word "waste" |
| `xtr0021`, `xtr0038`, `xtr0003`, `xtr0052`, `xtr0075` | hi | other recordings containing "waste", for A/B |
| `utt0102` | hi | the original Hindi reference |
| `utt0002` | en | default English. English text must use an English reference: a Hindi reference makes English come out about a third of its proper length |

The reference language must match the cue language. A mismatch is refused. To add a reference, copy a clean 4 to 10 second clip and its exact transcript into `voice/refs/` and add an entry to `config.json`.

## Acceptance checklist

- `lint` exit 0; render exit 0, or exit 2 with every flag named to the user
- Every timed cue fits; overflows reported with seconds
- Loudness about -16 LUFS, true peak at or under -1.5 dB (in `report.json`)
- Duration equals `video_duration_sec` for timed sources
- The user has listened, and any word they rejected is fixed or recorded as a known limit
