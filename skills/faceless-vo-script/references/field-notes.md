# What the public skills do, and what this one keeps

Read this only when changing the skill. A script job does not need it.

Compared in public writeups, not by copying their prompts.

| Skill | What it actually ships | What we kept | What we left |
| --- | --- | --- | --- |
| Anthropic skill authoring | A short `SKILL.md`, references one level down, deterministic work in scripts, a description that says when to trigger | Same shape. Trigger evals in `evals/triggers.json` | No model-graded description optimizer. There is no eval harness in this repo |
| CreatorSkills, AI Voiceover for YouTube | Content analysis, a spoken rewrite, an emotion map, a paste-ready TTS prompt, archetypes, retention pacing. It does not render audio | Analysis, emotion map, and engine settings are `06-tts-brief.md`, rendered from the script so they cannot drift. Archetypes are Expert, Storyteller, Commentator. Longform must plant a new stake between 2:30 and 3:30 | Their Hype Man archetype. It fights a faceless Indian read. Their skill starts from a topic. This one starts from a locked edit |
| Agensi, Faceless Video Blueprint | Timestamps taken from real speech onsets, then a visual per beat | The direction is reversed on purpose. The edit already exists, so the voice moves to the picture. Holds stay silent | Image prompts and slideshow assembly. That is the editing skill's job |
| skills.rest `faceless-channel` and OpenClaw `youtube-factory` | End-to-end video, including an Edge TTS voice | `scripts/speak.py` uses the same class of engine: Indian Edge voices, no key, ffmpeg to place each line | B-roll, thumbnails, music, and a fresh cut. Those skills invent the video. This one will not |

The implementation bar those skills share: the model writes the words once, and a script does every mechanical step after that. Rendering, validation, and the voice file are those steps.
