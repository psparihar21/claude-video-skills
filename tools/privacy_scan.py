#!/usr/bin/env python3
"""Fail if a tracked file (or the staged diff) leaks personal data or secrets.

Usage:
  python tools/privacy_scan.py            scan every tracked + untracked-not-ignored file
  python tools/privacy_scan.py --staged   scan only staged files (pre-commit hook)
  python tools/privacy_scan.py --self-test

Checks: home-folder paths with a real user name, personal e-mail addresses,
API keys / tokens, private camera-stream ids, voice recordings and personal
config files. Placeholders such as %USERPROFILE%, <you>, ~ are allowed.
Keep this file free of real personal values: it is published too.
"""
from __future__ import annotations

import re
import subprocess
import sys

PLACEHOLDER_USERS = {"%username%", "<you>", "<user>", "you", "user", "username", "public", "default", "runneradmin"}

RULES: list[tuple[str, re.Pattern[str]]] = [
    ("home path with a real user name", re.compile(r"(?i)\b[a-z]:[\\/]{1,2}users[\\/]{1,2}([^\\/\s\"'`<>%]+)")),
    ("home path with a real user name", re.compile(r"(?<![\w.])/(?:c/)?(?:Users|home)/([A-Za-z0-9._-]+)/")),
    ("personal e-mail address", re.compile(r"[A-Za-z0-9._%+-]+@(?!users\.noreply\.github\.com)(?!example\.(?:com|org))[A-Za-z0-9-]+\.[A-Za-z.]{2,}")),
    ("Hugging Face token", re.compile(r"\bhf_[A-Za-z0-9]{30,}")),
    ("OpenAI/Anthropic-style key", re.compile(r"\bsk-(?:ant-)?[A-Za-z0-9_-]{20,}")),
    ("GitHub token", re.compile(r"\b(?:ghp|gho|ghs|ghu)_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,}")),
    ("Google API key", re.compile(r"\bAIza[0-9A-Za-z_-]{35}")),
    ("AWS access key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("Slack token", re.compile(r"\bxox[abprs]-[A-Za-z0-9-]{10,}")),
    ("private key", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    ("hardcoded secret", re.compile(r"(?i)\b(?:api[_-]?key|secret|password|access[_-]?token)\b\s*[:=]\s*[\"'][^\"'\s<>{}$]{8,}[\"']")),
    ("VDO.Ninja stream id (anyone with it can watch the camera)", re.compile(r"vdo\.ninja/\?(?:view|push)=(?!<)([A-Za-z0-9_-]{4,})")),
]
# Files that must never be published, whatever they contain.
BLOCKED_PATHS = re.compile(
    r"(?i)(^|/)(\.env(\.|$)|config\.json$|config\.backup\.json$|RULES\.local\.md$|channel/style-card\.md$)"
    r"|own-voice-render/voice/refs/.+\.(wav|txt)$|ps5-obs-setup/assets/known-good/|\.(pem|key|pfx|p12)$"
)
ALLOWED_BLOCKED = {"skills/own-voice-render/voice/refs/README.md"}
# Third-party licence texts must ship verbatim (they carry the font foundry's public contact address).
THIRD_PARTY_TEXT = re.compile(r"(^|/)fonts/OFL[^/]*\.txt$")
TEXT_LIMIT = 2_000_000


def files(staged: bool) -> list[str]:
    cmd = ["git", "diff", "--cached", "--name-only", "--diff-filter=ACMR"] if staged else \
          ["git", "ls-files", "--cached", "--others", "--exclude-standard"]
    return [f for f in subprocess.run(cmd, capture_output=True, text=True, check=True).stdout.splitlines() if f]


def scan_text(path: str, text: str) -> list[str]:
    hits = []
    for n, line in enumerate(text.splitlines(), 1):
        for name, rx in RULES:
            for m in rx.finditer(line):
                if name.startswith("home path") and m.group(1).lower() in PLACEHOLDER_USERS:
                    continue
                hits.append(f"{path}:{n}: {name}: {m.group(0)[:60]}")
    return hits


def scan(paths: list[str]) -> list[str]:
    hits = []
    for p in paths:
        if p == "tools/privacy_scan.py":
            continue  # holds the patterns themselves
        if THIRD_PARTY_TEXT.search(p):
            continue
        if BLOCKED_PATHS.search(p) and p not in ALLOWED_BLOCKED:
            hits.append(f"{p}: personal file must not be committed")
            continue
        try:
            data = open(p, "rb").read(TEXT_LIMIT)
        except (FileNotFoundError, IsADirectoryError):
            continue
        if b"\0" in data[:8000]:
            continue  # binary: covered by BLOCKED_PATHS and .gitignore
        hits += scan_text(p, data.decode("utf-8", errors="replace"))
    return hits


def self_test() -> None:
    bad = ["C:\\Users\\jane\\Videos", "/c/Users/jane/x/", "mail jane.doe@gmail.com",
           "hf_" + "a" * 34, "sk-ant-" + "b" * 30, "https://vdo.ninja/?view=abc123x", "api_key = " + repr("abcd" + "1234efgh")]
    good = ["%USERPROFILE%\\Videos", "C:\\Users\\<you>\\x", "1+me@users.noreply.github.com",
            "https://vdo.ninja/?view=<private id>", "api_key = '<your key>'", "~/.claude/skills"]
    for s in bad:
        assert scan_text("t", s), f"missed: {s}"
    for s in good:
        assert not scan_text("t", s), f"false alarm: {s}"
    assert BLOCKED_PATHS.search("skills/own-voice-render/config.json")
    assert BLOCKED_PATHS.search("skills/own-voice-render/voice/refs/a.wav")
    assert not BLOCKED_PATHS.search("skills/own-voice-render/config.example.json")
    assert THIRD_PARTY_TEXT.search("skills/video-edit/brand/hf/fonts/OFL-Anton.txt")
    assert not THIRD_PARTY_TEXT.search("skills/video-edit/notes.txt")
    print("self-test ok")


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        self_test(); sys.exit(0)
    found = scan(files("--staged" in sys.argv))
    print("\n".join(found) if found else "privacy scan: clean")
    sys.exit(1 if found else 0)
