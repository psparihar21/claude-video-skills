---
name: yt-comment
description: >-
  Draft replies to YouTube comments in the creator's voice, triaged by which
  ones are worth answering. Use for "reply to my comments", "handle the
  comment section", "someone asked X", or a pasted comment thread.
---

# yt-comment

The comment section is a retention surface, not a chore. Replies in the first few hours are what
decide whether a thread becomes a conversation other people read.

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

## Triage first, always

Sort what the user pastes into four piles and say how many are in each before writing anything:

1. **Questions** - answer them. These are your next video's topics, so note the repeats.
2. **Corrections** - if they are right, say so plainly and thank them. Never argue a fact you
   cannot check.
3. **Praise** - reply to a few, briefly, with something specific from their comment. A wall of
   identical "thank you!" replies reads as automated because it is.
4. **Bait** - do not reply. Say so and move on. Never write a comeback, however deserved.

## Writing the reply

- Under 30 words. A long reply in a comment thread is a blog post nobody asked for.
- Answer the actual question in the first sentence.
- One question back, only when it is real.
- No emoji unless the user's own replies use them. Check their voice file.
- Never promise a video you have not agreed to make.

## The heart and the pin

Say which ONE comment to pin and why. Pin the question the most people also have, not the nicest
one. Heart generously - it costs nothing and it is visible.

## The gate

Nothing here publishes. This skill writes and you publish. Every output ends in a block the user
copies, and the last line of every run is the question: **ship it, or change it?**

---
Adapted from github.com/Jakeschincariol/youtube-agent-skill (MIT, (c) Jake Schincariol); see LICENSE-youtube-agent-skill.txt. Changed to read the user's style card instead of voice.md.
