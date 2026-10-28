# Style card

The card describes how the user sounds and looks on screen. Build it from the user's material only.

## Valid sources

- The user's past scripts, notes, captions, or posts written in their voice.
- Transcripts of the user's own videos or voice memos.
- The user's channel, if connected, for pacing, openers, endings, on-screen text, color, and music energy.
- Corrections the user makes during a run.

Not valid: the reference creator, "typical YouTuber" defaults, or anything you imagine. If no valid source exists, stop and ask for one sample (one past script, one video link of theirs, or a two-minute voice memo transcript). Explain in one line that the script will otherwise sound like someone else.

## Measure, don't guess

- **Pace (wpm):** spoken words ÷ minutes from a transcript of the user talking. With no timed sample, use 140 and mark it `assumed — confirm`. Typical conversational range is 125–150.
- **Sentence length:** average words per sentence from their writing or transcript.
- **Humor, swearing, opinions:** quote short phrases from their own material as evidence (their words, not the reference's).
- **Never-say list:** words they never use or have rejected. Grows when they correct a draft.

## Fields

Fill every field in `assets/style-card-template.md`. Write `unknown — ask` rather than inventing. Fields: who the user is talking to (one specific person), what they will not claim, pace, sentence length, humor, swearing, repeated opinions, always-words, never-words, openers, endings and CTA style, on-camera / faceless / VO-on-footage, on-screen text style, caption style, color, music energy, evidence list (which samples each field came from).

## Saving and updating

- Save to the production folder and to `~/.claude/channel/style-card.md` (shared with yt-plan, yt-comment, yt-audit; fall back to environment memory or `channel/style-card.md` when there is no home folder).
- Before building a card, look there first, then read the "My style" block in `video-edit/RULES.md` for format and look if that skill is installed.
- On a new run, load the saved card and show it in five lines. Do not rebuild it.
- Change it only when the user corrects it. Log each correction with date at the bottom of the card.
