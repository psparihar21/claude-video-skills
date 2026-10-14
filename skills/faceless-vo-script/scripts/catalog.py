"""Voice defaults shared by the renderer and the local speech step.

Derived from public faceless-voiceover practice: one archetype per format,
a paste-ready engine brief, and an Indian neural voice that needs no API key.
Numbers are this skill's defaults, not a copied preset from a paid skill.
"""

from __future__ import annotations

ARCHETYPES = {
    "faceless-explainer": {
        "id": "expert",
        "label": "Expert",
        "direction": (
            "A calm Indian explainer on a close mic. You are telling one person "
            "what the picture means. You do not sell, and you do not announce the topic."
        ),
        "elevenlabs": {"stability": 0.55, "similarity_boost": 0.80, "style": 0.10, "speed": 0.94},
    },
    "faceless-story": {
        "id": "storyteller",
        "label": "Storyteller",
        "direction": (
            "A dry Indian storyteller. Present tense, slight smile. You already know "
            "the ending, and you do not rush the turn."
        ),
        "elevenlabs": {"stability": 0.42, "similarity_boost": 0.75, "style": 0.25, "speed": 0.96},
    },
    "story-over-gameplay": {
        "id": "storyteller",
        "label": "Storyteller",
        "direction": (
            "A dry Indian storyteller over gameplay wallpaper. The story leads. "
            "You mention the game only when the picture makes the same point."
        ),
        "elevenlabs": {"stability": 0.42, "similarity_boost": 0.75, "style": 0.25, "speed": 0.96},
    },
    "faceless-gameplay": {
        "id": "commentator",
        "label": "Commentator",
        "direction": (
            "A ranked-game observer. You name the decision, then you stop so the "
            "sound of the game can land. No shoutcast."
        ),
        "elevenlabs": {"stability": 0.48, "similarity_boost": 0.78, "style": 0.15, "speed": 0.98},
    },
}

ANTI = [
    "Do not sound like a news reader.",
    "Do not welcome the viewer or ask for a like.",
    "Do not shout the hook. Make it closer, not louder.",
    "Do not flatten Hindi connectors into the same pitch as the English nouns.",
    "Do not fill the marked pauses.",
    "Do not read text that is already held on screen.",
]

# Faster than a human read. The neural voice undershoots the cue budget at
# 0% and still has to land before the next cut. Humans ignore this and use
# the teleprompter pace. speak.py owns this rate.
EDGE_RATE = {
    "indian-english": "+4%",
    "hinglish": "+4%",
}


def archetype(script: dict) -> dict:
    chosen = script.get("archetype")
    if chosen:
        for item in ARCHETYPES.values():
            if item["id"] == chosen or item["label"].lower() == str(chosen).lower():
                return item
    return ARCHETYPES.get(script.get("format"), ARCHETYPES["faceless-explainer"])


def edge_voice(script: dict, override: str | None = None) -> str:
    if override:
        return override
    if script.get("edge_voice"):
        return str(script["edge_voice"])
    persona = (script.get("persona") or "").lower()
    if "female" in persona or "woman" in persona:
        return "en-IN-NeerjaNeural"
    return "en-IN-PrabhatNeural"


def edge_rate(script: dict) -> str:
    return EDGE_RATE.get(script.get("register"), "-8%")


def model_for(script: dict) -> str:
    if script.get("register") == "hinglish":
        return "eleven_multilingual_v2"
    return "eleven_multilingual_v2"
