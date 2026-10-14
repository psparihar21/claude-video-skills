#!/usr/bin/env python3
"""Gate for a faceless voiceover script.

Exit 0 only when the timed script can be recorded over the locked edit.
The lexicon is a gate, not a linguist: it catches the wrong register and
unreadable pace. Style lives in references/language.md.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "assets" / "examples"

HARD_MAX_WPS = 2.85
TARGET_MAX_WPS = 2.85
SHORT_PLATFORMS = {"youtube-shorts", "reels", "tiktok"}
SHORT_HOOK_DEADLINE = 0.35

# Function words and auxiliaries only. The ratio gate uses this set.
# Left out on purpose because they collide with English: main, hi, log,
# scene, na, the, to, par, ban.
HINDI_FUNCTION = {
    "hai", "hain", "hoon", "nahi", "nahin", "mat", "kya", "kyun", "kyunki",
    "kaise", "kab", "kahan", "kaun", "yeh", "woh", "yahi", "wahi", "yehi",
    "mein", "mujhe", "mera", "meri", "mere", "lekin", "magar", "toh", "bas",
    "ab", "abhi", "phir", "agar", "jab", "tab", "isliye", "sirf", "bhi",
    "aur", "ke", "ki", "ka", "ko", "se", "pe", "jo", "ya", "wala", "wali",
    "wale", "raha", "rahi", "rahe", "gaya", "gayi", "gaye", "hota", "hoti",
    "hote", "tha", "thi", "usse", "unhe", "unko", "uska", "uski",
}

# Content words that do not belong in an Indian English script.
HINDI_CONTENT = {
    "yaar", "bhai", "dekho", "suno", "matlab", "waise", "jaise", "seedha",
    "akela", "banda", "andar", "bahar", "peeche", "aage", "galat", "sahi",
    "bol", "bolti", "bolta", "bolte", "jaata", "jaati", "jaate", "aata",
    "aati", "aate", "lena", "dena", "karo", "kar", "karna", "karta",
    "karti", "karte", "kiya", "kiye", "liya", "ghus", "tod", "todna",
    "agla", "agli", "baar", "bachega", "bachna", "girta", "khatam", "pehle",
}

ENGLISH_FUNCTION = {
    "the", "a", "an", "is", "are", "was", "were", "to", "of", "and", "or",
    "in", "on", "for", "with", "this", "that", "it", "you", "they", "we",
    "he", "she", "before", "after", "still", "most", "not", "be", "if",
    "from", "at", "as", "by", "his", "her", "their", "them", "can", "will",
}

CLAIM_NUM = re.compile(
    r"\d|₹|\$|£|€|\b(?:lakh|crore|thousand|million|billion|hundred|"
    r"twenty|thirty|forty|fifty|sixty|seventy|eighty|ninety)\b",
    re.IGNORECASE,
)
WORD_RE = re.compile(r"[A-Za-z0-9₹]+(?:'[A-Za-z]+)?", re.UNICODE)
BANNED = (
    "in this video",
    "without further ado",
    "buckle up",
    "let's dive in",
    "lets dive in",
    "smash that like",
    "smash the like",
    "like share and subscribe",
    "to dosto",
    "toh dosto",
    "bhai log",
    "aapko pata hai",
    "kya aap jante",
    "stay tuned",
    "hey guys",
    "what's up guys",
    "whats up guys",
    "welcome back",
    "do the needful",
    "kindly",
    "it is to be noted",
)
CTA_WORDS = ("subscribe", "like kar", "follow for", "comment mein")
FACT_MARK = "[FACT:"
DIRECTION_MARK = re.compile(r"\[(?!FACT:)")


class Finding:
    def __init__(self, level: str, code: str, message: str) -> None:
        self.level = level
        self.code = code
        self.message = message

    def format(self) -> str:
        return f"{self.level.upper():7} {self.code}: {self.message}"


def tokens(text: str) -> list[str]:
    return [t.lower() for t in WORD_RE.findall(text)]


def load(path: Path) -> dict:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def hold_window(shot: dict) -> tuple[float, float] | None:
    if not shot.get("hold_for_read"):
        return None
    start = float(shot.get("hold_in_sec", shot["in_sec"]))
    return start, float(shot["out_sec"])


def covered(window: tuple[float, float], silences: list[dict], slack: float = 0.15) -> bool:
    start, end = window
    cursor = start
    spans = sorted(
        (float(item["in_sec"]), float(item["out_sec"])) for item in silences
    )
    for left, right in spans:
        if right < cursor - slack:
            continue
        if left <= cursor + slack:
            cursor = max(cursor, right)
        if cursor >= end - slack:
            return True
    return cursor >= end - slack


def overlaps(a_in: float, a_out: float, b_in: float, b_out: float, eps: float = 0.02) -> bool:
    return a_in < b_out - eps and b_in < a_out - eps


def validate(edit: dict, script: dict) -> list[Finding]:
    findings: list[Finding] = []
    shots = {shot["id"]: shot for shot in edit.get("shots", [])}
    cues = script.get("cues", [])
    register = script.get("register", "")
    platform = script.get("platform", edit.get("platform", ""))
    duration = float(script.get("video_duration_sec", edit.get("video_duration_sec", 0)))
    silences = script.get("intentional_silence", [])

    if abs(float(script.get("video_duration_sec", 0)) - float(edit.get("video_duration_sec", 0))) > 0.2:
        findings.append(Finding(
            "error", "DURATION",
            "script video_duration_sec does not match the edit",
        ))

    spoken_bits: list[str] = []
    previous_out = -1.0

    for cue in cues:
        cid = cue.get("id", "?")
        spoken = cue.get("spoken", "")
        spoken_bits.append(spoken)
        words = tokens(spoken)
        start = float(cue.get("in_sec", 0))
        end = float(cue.get("out_sec", 0))
        span = end - start

        if span <= 0:
            findings.append(Finding("error", "TIMING", f"{cid} ends before it starts"))
            continue
        if start < -0.001 or end > duration + 0.05:
            findings.append(Finding(
                "error", "UNBOUNDED",
                f"{cid} sits outside the video ({start:.2f}–{end:.2f}s, video {duration:.2f}s)",
            ))
        if start < previous_out - 0.02:
            findings.append(Finding(
                "error", "OVERLAP",
                f"{cid} starts at {start:.2f}s before the previous cue ends at {previous_out:.2f}s",
            ))
        previous_out = end

        shot = shots.get(cue.get("shot_id"))
        if shot is None:
            findings.append(Finding(
                "error", "SHOT",
                f"{cid} points at unknown shot {cue.get('shot_id')}",
            ))
        else:
            if start < float(shot["in_sec"]) - 0.05 or end > float(shot["out_sec"]) + 0.05:
                findings.append(Finding(
                    "error", "CROSS_CUT",
                    f"{cid} ({start:.2f}–{end:.2f}s) leaves shot {shot['id']} "
                    f"({shot['in_sec']:.2f}–{shot['out_sec']:.2f}s). Split the line or move it inside the shot.",
                ))
            window = hold_window(shot)
            if window and overlaps(start, end, window[0], window[1]):
                findings.append(Finding(
                    "error", "HOLD_COLLISION",
                    f"{cid} talks over the read-hold on {shot['id']} ({window[0]:.2f}–{window[1]:.2f}s)",
                ))

        wps = len(words) / span
        if wps > HARD_MAX_WPS:
            findings.append(Finding(
                "error", "WPS_HIGH",
                f"{cid} is {wps:.2f} words/sec over {span:.2f}s ({len(words)} words). "
                f"Ceiling is {TARGET_MAX_WPS:.2f}. Cut words or lengthen the cue inside the shot.",
            ))
        elif span >= 4.5 and wps < 1.5:
            findings.append(Finding(
                "warn", "WPS_LOW",
                f"{cid} is {wps:.2f} words/sec. The pause will feel empty unless the picture is doing the work. "
                "Shorten the cue so the silence is intentional.",
            ))

        if DIRECTION_MARK.search(spoken):
            findings.append(Finding(
                "error", "DIRECTION_IN_SPEECH",
                f"{cid} has a bracket in spoken. Move it to performance.",
            ))
        if any(phrase in spoken.lower() for phrase in BANNED):
            findings.append(Finding(
                "error", "BANNED",
                f"{cid} uses a banned opener or office phrase. Say the point instead.",
            ))
        if FACT_MARK in spoken and script.get("status") == "final":
            findings.append(Finding(
                "error", "FACT_OPEN",
                f"{cid} still has {FACT_MARK}. Keep status at draft until the source exists.",
            ))
        if CLAIM_NUM.search(spoken) and not cue.get("fact_source"):
            findings.append(Finding(
                "error", "FACT_SOURCE",
                f"{cid} states a quantity with no fact_source. Point at the on-screen text or the brief, "
                "or replace the number with [FACT: ...].",
            ))

        late_cta = start < duration * 0.8 and cue.get("role") != "cta"
        if late_cta and any(word in spoken.lower() for word in CTA_WORDS):
            findings.append(Finding(
                "error", "CTA",
                f"{cid} asks for a follow before a CTA shot. Delete it or move it onto the end card.",
            ))

        for word in cue.get("emphasis", []):
            if word.lower() not in words and word.strip("[]").lower() not in words:
                findings.append(Finding(
                    "warn", "EMPHASIS",
                    f"{cid} emphasizes '{word}', which is not in the spoken line.",
                ))

    all_words = tokens(" ".join(spoken_bits))
    hindi_hits = [word for word in all_words if word in HINDI_FUNCTION]
    content_hits = [word for word in all_words if word in HINDI_CONTENT]
    english_hits = [word for word in all_words if word in ENGLISH_FUNCTION]
    hindi_ratio = len(hindi_hits) / len(all_words) if all_words else 0

    if register == "hinglish":
        if hindi_ratio < 0.15:
            findings.append(Finding(
                "error", "HINDI_RATIO",
                f"Hinglish ratio is {hindi_ratio:.0%} Hindi function words "
                f"({len(hindi_hits)} of {len(all_words)}). Need at least 15%. "
                "Put the turns and connectors in Hindi, not one garnish word.",
            ))
        elif hindi_ratio > 0.48:
            findings.append(Finding(
                "error", "HINDI_RATIO",
                f"Hinglish ratio is {hindi_ratio:.0%} Hindi function words. This reads as Hindi. "
                "Move the information and the game terms back to English.",
            ))
        if len(english_hits) < 3:
            findings.append(Finding(
                "warn", "ENGLISH_THIN",
                "Almost no English function words. Hinglish still needs English to carry the facts.",
            ))
    elif register == "indian-english":
        leaked = sorted(set(hindi_hits + content_hits))
        if leaked:
            sample = ", ".join(leaked[:8])
            findings.append(Finding(
                "error", "REGISTER",
                f"Indian English script contains Hindi words: {sample}. "
                "Switch the register to hinglish or rewrite the line in English.",
            ))
    else:
        findings.append(Finding(
            "error", "REGISTER",
            f"Unknown register '{register}'. Use indian-english or hinglish.",
        ))

    if platform in SHORT_PLATFORMS and cues:
        first = min(cues, key=lambda cue: float(cue["in_sec"]))
        if float(first["in_sec"]) > SHORT_HOOK_DEADLINE or first.get("role") != "hook":
            findings.append(Finding(
                "error", "HOOK_LATE",
                f"Short-form open is {first.get('id')} at {float(first['in_sec']):.2f}s "
                f"with role {first.get('role')}. First speech starts by {SHORT_HOOK_DEADLINE:.2f}s and the role is hook.",
            ))

    for shot in edit.get("shots", []):
        window = hold_window(shot)
        if window and not covered(window, silences):
            findings.append(Finding(
                "error", "HOLD_UNMARKED",
                f"{shot['id']} is hold_for_read ({window[0]:.2f}–{window[1]:.2f}s) "
                "but intentional_silence does not cover it.",
            ))

    hook_shots = [shot["id"] for shot in edit.get("shots", []) if shot.get("energy") == "hook"]
    referenced = {cue.get("shot_id") for cue in cues}
    silenced_shots = set()
    for shot in edit.get("shots", []):
        window = hold_window(shot)
        if window and covered(window, silences) and window[0] <= float(shot["in_sec"]) + 0.05:
            silenced_shots.add(shot["id"])
    for shot_id in hook_shots:
        if shot_id not in referenced and shot_id not in silenced_shots:
            findings.append(Finding(
                "error", "HOOK_SHOT",
                f"Hook shot {shot_id} has no spoken cue. Write the open, or mark the whole shot as intentional silence.",
            ))

    if platform == "youtube-long" and duration >= 240 and cues:
        held = any(150 <= float(cue["in_sec"]) <= 210 for cue in cues)
        if not held:
            findings.append(Finding(
                "warn", "RETENTION",
                "No spoken cue between 2:30 and 3:30. Long faceless videos drop there. "
                "Land a new stake on a shot in that window.",
            ))

    return findings


def report(findings: list[Finding]) -> int:
    errors = [item for item in findings if item.level == "error"]
    for item in findings:
        print(item.format())
    if errors:
        print(f"\n{len(errors)} error(s). The script is not recordable yet.")
        return 1
    print("\nPass. The script clears the timing and register gates.")
    return 0


def run_pair(edit_path: Path, script_path: Path) -> int:
    return report(validate(load(edit_path), load(script_path)))


def self_test() -> int:
    cases = [
        ("ranked-push", 0),
        ("first-minute", 0),
        ("bad-overlap", 1),
    ]
    failed = 0
    for name, expect in cases:
        folder = EXAMPLES / name
        findings = validate(load(folder / "edit.json"), load(folder / "03-script.json"))
        errors = [item for item in findings if item.level == "error"]
        codes = sorted({item.code for item in errors})
        ok = (1 if errors else 0) == expect
        if name == "bad-overlap":
            needed = {"OVERLAP", "WPS_HIGH", "BANNED", "HOLD_COLLISION", "REGISTER"}
            ok = ok and needed <= set(codes)
        state = "ok" if ok else "FAIL"
        print(f"{state:4} {name}: {len(errors)} error(s) {codes}")
        if not ok:
            for item in errors:
                print("    ", item.format())
            failed += 1
    return 1 if failed else 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a faceless voiceover script against its edit.")
    parser.add_argument("--edit", type=Path, help="Path to edit.json")
    parser.add_argument("--script", type=Path, help="Path to 03-script.json")
    parser.add_argument("--self-test", action="store_true", help="Run the shipped fixtures")
    args = parser.parse_args()
    if args.self_test:
        return self_test()
    if not args.edit or not args.script:
        parser.error("provide --edit and --script, or --self-test")
    return run_pair(args.edit, args.script)


if __name__ == "__main__":
    sys.exit(main())
