---
name: yt-audit
description: >-
  Audit a YouTube channel end to end - packaging, consistency, the first
  fifteen seconds, and what to fix first. Use for "audit my channel", "why
  isn't my channel growing", "review my videos", or a pasted channel URL.
---

# yt-audit

An audit that lists twenty problems is a way of avoiding the one that matters. This ends in ONE fix.

## Before you write

1. Read the user's style card at `~/.claude/channel/style-card.md` (the same card
   `producing-channel-videos` builds and saves): who they talk to, how they talk, words they never use,
   what they will not claim, how they open and close. Also read the "My style" block in
   `~/.claude/skills/video-edit/RULES.md` for format and look. The channel is the user's own
   (Pushpstation: tech and gameplay, Hindi, Hinglish or English). If neither file says how they talk,
   ask for **three of their own videos**, read or transcribe them, and write the card with the fields
   of `producing-channel-videos/assets/style-card-template.md`. Never invent a voice and call it theirs.
2. Never invent a number, a result or a source. If a figure would strengthen it and you do not have
   one, ask for it or write the line without it.

## What to look at, in this order

1. **The last ten titles, as a set.** Read them as a list, the way the channel page shows them. Do
   they promise different things? Run them through `scripts/title.py` (one per line: `python "${CLAUDE_SKILL_DIR}/scripts/title.py" titles.txt`). A channel where every
   title is the same shape has a format problem, not a title problem.
2. **The thumbnails, at feed size.** Shrink them. What survives? If three of them are unreadable at
   that size, that is the fix and nothing else matters yet.
3. **The first fifteen seconds of the three most recent.** Transcribe them and score with
   `scripts/hookscore.py` (English word patterns: for Hindi or Hinglish openings, score a plain-English rendering and treat it as a rough check). This is where most channels lose.
4. **Upload rhythm.** Not frequency - CONSISTENCY. Six videos in one week and then nothing for a
   month is worse than one a fortnight forever.
5. **The retention shape**, if they can export it: Studio → Analytics → Engagement → download, then `python "${CLAUDE_SKILL_DIR}/scripts/retention.py" retention.csv --transcript <srt>`. Hook leak, cliffs, slide.

## What to hand back

- The single biggest fix, named, with what to do this week.
- Three things that are already working, so they do not break them. Be specific; "your energy is
  good" is not an observation.
- What NOT to do yet, and why.

Never open an audit with praise you do not mean, and never end one with a list of twenty things.

## The gate

Nothing here publishes. This skill writes and you publish. Every output ends in a block the user
copies, and the last line of every run is the question: **ship it, or change it?**

---
Adapted from github.com/Jakeschincariol/youtube-agent-skill (MIT, (c) Jake Schincariol); see LICENSE-youtube-agent-skill.txt. Changed to read the user's style card instead of voice.md.
