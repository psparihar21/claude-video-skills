# Input contract

`ovr.py ingest` accepts these. It never invents timing and never edits meaning.

| Source | Detected by | Mode | Notes |
| --- | --- | --- | --- |
| `faceless-vo-script` `03-script.json` | `cues[].spoken` present | timed | Uses `in_sec`, `out_sec`, `register`, `video_duration_sec`, `pronounce`. |
| Cue list JSON | `{"cues":[{"text","start","end"}]}` or a bare list | timed if every cue has start and end, else sequential | Also accepts `in_sec`/`out_sec`, `spoken`, `line`, and plain strings. |
| SRT | `.srt` | timed | HTML tags stripped. One cue per subtitle block. |
| Markdown, text | anything else | sequential | Headings, tables, code fences, comments, bullets markers and `[00:12]` stamps are dropped. Blank lines become paragraph pauses. |

## Field mapping for `faceless-vo-script`

| Their field | Becomes |
| --- | --- |
| `register: indian-english` | by default the cue is read through the Hindi path (`from_english`): you write the English phonetically in Devanagari. With `--english-as latin` it stays Latin text with the English reference clip. |
| `register: hinglish` | cue language `hi`: needs Devanagari (draft, then `set-deva`) |
| `spoken` | the only words that are rendered |
| `in_sec`, `out_sec` | the cue window (timed mode) |
| `video_duration_sec` | the exact length of the output audio |
| `pronounce[]` | a per-project spelling override used by `draft` |
| `performance`, `emphasis`, `mix_note` | ignored, listed under `ignored_performance_notes` in the report |
| `status: draft` or a `[FACT:` hole | refused: lint error, do not render as final |

`intentional_silence` windows are kept as silence by construction: nothing is placed there.

The compat files (`07-voice.m4a`, `07-voice-report.json`) land beside `03-script.json` and use that skill's report shape: `voice`, `rate`, `file`, `duration_sec`, and per cue `id`, `in_sec`, `window_sec`, `spoken_sec`, `tempo`, `trimmed`.

## Language detection (text and cue lists)

`--lang auto` decides per cue:

1. Devanagari present: `hi`.
2. Roman text where at least 15% of words are unambiguous Hindi function or common words: `hi` (needs Devanagari).
3. Otherwise `en`.

When detection is wrong, rerun `ingest --lang hi` or `--lang en`.

## What an upstream skill should write for best results

- One cue per spoken breath with `in_sec` and `out_sec`, or plain paragraphs if timing does not matter.
- No digits in `spoken`: write "twenty", "bees" or "बीस". Digits are a lint error.
- No stage directions inside `spoken`. Put them in `performance`.
- Keep a sentence under about 150 characters. Longer ones are split at commas and read as separate chunks, which can change the rhythm.
- For Hinglish, Roman Hindi in the spelling of `faceless-vo-script/references/language.md` converts well. Anything the lexicon does not know is marked for you to resolve.
