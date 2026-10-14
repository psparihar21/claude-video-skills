# Output contract

Write files under `vo/<slug>/`. The slug is short, lowercase, from the video title.

## edit.json

Normalized from the upstream skill. Match `assets/edit-package.schema.json`.

Required on every shot: `id`, `in_sec`, `out_sec`, `visual`, `energy`, `cut_type`.

`energy`: `hook`, `build`, `payoff`, `breather`.

`cut_type`: `hard`, `j-cut`, `text-card`, `zoom`.

`hold_for_read: true` means the viewer must be allowed to read. Optional `hold_in_sec` when the hold starts mid-shot. If omitted, the whole shot is the hold.

`video_path` may be absolute or relative to the edit file. Empty string if they only gave a paper cut.

Do not drop editor notes. Park them on `editor_notes` or on the shot's `note`.

## 01-beat-map.md

Written by you, in this shape, one section per shot:

```markdown
# Beat map — <title>

Format: story-over-gameplay
Register: hinglish
Platform: youtube-shorts
Video: 32.0s
Seen: frames for s01–s05

## s01 · 0.00–2.40 · hook · confidence high
Sees: a solo player breaking a door while the squad marker stays behind.
Already understands: he is going in alone.
Voice may add: that this choice will not survive.
Voice must not: name a rank, a gun, or a teammate who is not visible.
Spoken room: 1.9s
```

`Seen` says whether you looked at frames or only at notes. A shot you did not see cannot be `confidence high` unless the editor note is specific enough to storyboard.

## 03-script.json

Match `assets/script-package.schema.json`. You write this by hand (it is the creative artifact). The renderer and the validator consume it.

```json
{
  "title": "Don't push that door",
  "slug": "dont-push-that-door",
  "status": "final",
  "register": "hinglish",
  "format": "story-over-gameplay",
  "platform": "youtube-shorts",
  "video_duration_sec": 32.0,
  "persona": "Pan-India observer, late 20s, close-mic, slight smile, no shout.",
  "mic_note": "One hand from the mic. Leave the pauses in. Do not punch the Hindi harder than the English.",
  "pronounce": [
    {"word": "mein", "say": "men"}
  ],
  "cues": [
    {
      "id": "c01",
      "shot_id": "s01",
      "role": "hook",
      "in_sec": 0.12,
      "out_sec": 2.2,
      "spoken": "Yeh push akela nahi bachega.",
      "performance": "[close, slight smile] Yeh push akela nahi bachega.",
      "emphasis": ["akela"],
      "fact_source": "",
      "mix_note": ""
    }
  ],
  "intentional_silence": [
    {
      "in_sec": 29.0,
      "out_sec": 32.0,
      "reason": "End card is on screen."
    }
  ],
  "recut_requests": []
}
```

Rules the validator also checks:

- `status` is `draft` if any `spoken` contains `[FACT:`. Otherwise `final`.
- `spoken` has no brackets, no stage direction, no emoji.
- `shot_id` exists on the edit.
- Times are seconds, floats, inside the shot, inside the video.
- `fact_source` is non-empty when the line contains a quantity.
- Every `hold_for_read` window is covered by `intentional_silence`.
- `recut_requests` entries are `{shot_id, reason, need}`. A request does not change the cue times.

`pronounce` is global plus any cue-level list of the same shape. Cue-level wins on the same word.

## Rendered files

Generate only with:

```bash
python .cursor/skills/faceless-vo-script/scripts/render_script.py \
  --script vo/<slug>/03-script.json \
  --out vo/<slug>
```

That writes `02-script.md`, `04-captions.srt`, `05-record-notes.md`, and `06-tts-brief.md`. After a script change, render again. Do not patch the renders by hand.

`06-tts-brief.md` is the production handoff the public voiceover skills stop at: content analysis, an emotion map, ElevenLabs settings, the Edge voice id, an anti-instruction list, and a paste track with the edit's pauses. The archetype follows the format (Expert, Storyteller, Commentator) unless `archetype` is set on the JSON.

When status is `final`:

```bash
python .cursor/skills/faceless-vo-script/scripts/speak.py \
  --script vo/<slug>/03-script.json \
  --out vo/<slug>
```

That writes `07-voice.m4a`, lined up to the cue times across the full video duration, and `07-voice-report.json`. A cue that still contains `[FACT:` refuses to speak.

## Upstream skills that used a different shape

Take what they gave you and map it.

| Theirs | Yours |
| --- | --- |
| `start`, `end`, `in`, `out`, `tc_in` | `in_sec`, `out_sec` (convert `HH:MM:SS` or frames at the fps they named; if fps is missing, do not guess, ask by listing the field) |
| `description`, `caption`, `shot`, `label` | `visual` |
| `text`, `title`, `overlay` | `on_screen_text` |
| `type: text`, `card`, `lower-third` | `cut_type: text-card` and usually `hold_for_read` |
| SRT of burned captions | a shot or a `on_screen_text` span, not a voice line |
| A video and nothing else | one shot per scene you can see after sampling one frame every 2 seconds, with `confidence` capped at medium until you look |

Preserve their ids when they had ids. Otherwise `s01`, `s02`, in order.
