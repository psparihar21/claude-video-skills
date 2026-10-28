#!/usr/bin/env python3
"""Check that a new spoken script does not reuse a reference video's words or beat order.

Usage:
    python3 similarity_guard.py <production-folder> [--window 12]
    python3 similarity_guard.py --script script.md --reference transcript.txt --brief craft-brief.md

Default file locations inside the production folder:
    script.md                       AV script; "Spoken line" column is checked
    reference/*.txt|*.srt|*.vtt|*.md  reference transcript(s), study-only
    reference-transcript*.txt       also accepted at the folder root
    craft-brief.md                  "## Beat map" section with "beat: <label>" lines
    reference/beats.txt             optional alternative beat map

Fails (exit 1) if any N-word window (default 12) of the spoken script appears in the
reference transcript, or if the script's beat sequence equals the reference's.
Prints every offending window. Exit 0 = pass. Exit 2 = usage or missing script.
"""
import argparse
import os
import re
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

COMMENT_RE = re.compile(r"<!--.*?-->", re.S)
BEAT_RE = re.compile(r"beat:\s*([a-z][a-z0-9-]*)", re.I)
SRT_TIME_RE = re.compile(r"^\s*\d{1,2}:\d{2}(:\d{2})?[.,]\d{1,3}\s*-->.*$", re.M)


def long_path(path):
    """Windows refuses paths over 260 characters unless they carry the \\\\?\\ prefix."""
    p = os.path.abspath(str(path))
    if os.name == "nt" and len(p) >= 240 and not p.startswith("\\\\?\\"):
        p = "\\\\?\\" + p
    return p


def read(path):
    return COMMENT_RE.sub("", Path(long_path(path)).read_text(encoding="utf-8", errors="replace"))


def split_row(line):
    line = line.strip()
    if line.startswith("|"):
        line = line[1:]
    if line.endswith("|"):
        line = line[:-1]
    return [c.strip() for c in line.split("|")]


def parse_tables(text):
    """Yield (headers, rows) for each markdown table; rows are dicts keyed by lowercased header."""
    lines = text.splitlines()
    i = 0
    while i < len(lines) - 1:
        if lines[i].strip().startswith("|") and re.match(r"^\s*\|?\s*:?-{3,}", lines[i + 1]):
            headers = [h.lower() for h in split_row(lines[i])]
            rows = []
            j = i + 2
            while j < len(lines) and lines[j].strip().startswith("|"):
                cells = split_row(lines[j])
                cells += [""] * (len(headers) - len(cells))
                rows.append(dict(zip(headers, cells)))
                j += 1
            yield headers, rows
            i = j
        else:
            i += 1


def spoken_text(script_md):
    parts = []
    for headers, rows in parse_tables(script_md):
        col = next((h for h in headers if h.startswith("spoken")), None)
        if col:
            parts.extend(r.get(col, "") for r in rows)
    return " ".join(parts)


def tokens(text):
    text = text.lower().replace("’", "'").replace("‘", "'")
    text = re.sub(r"[^a-z0-9'\s]+", " ", text)
    text = text.replace("'", "")
    return text.split()


def clean_transcript(text):
    text = SRT_TIME_RE.sub(" ", text)
    text = re.sub(r"^\s*WEBVTT.*$", " ", text, flags=re.M)
    text = re.sub(r"^\s*\d+\s*$", " ", text, flags=re.M)
    text = re.sub(r"\[\d{1,2}:\d{2}(:\d{2})?\]", " ", text)
    return text


def collapse(seq):
    out = []
    for b in seq:
        if not out or out[-1] != b:
            out.append(b)
    return out


def script_beats(script_md):
    beats = []
    for line in script_md.splitlines():
        if line.lstrip().startswith("#"):
            m = BEAT_RE.search(line)
            if m:
                beats.append(m.group(1).lower())
    return collapse(beats)


def reference_beats(brief_md):
    section = re.search(r"^#+\s*beat map\s*$(.*?)(?=^#+\s|\Z)", brief_md, re.I | re.M | re.S)
    body = section.group(1) if section else ""
    return collapse([m.group(1).lower() for m in BEAT_RE.finditer(body)])


def find_transcripts(folder):
    found = []
    ref = folder / "reference"
    if ref.is_dir():
        for ext in ("*.txt", "*.srt", "*.vtt", "*.md"):
            found.extend(p for p in sorted(ref.glob(ext)) if p.name != "beats.txt")
    found.extend(sorted(folder.glob("reference-transcript*.txt")))
    return found


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("folder", nargs="?", help="production folder")
    ap.add_argument("--script")
    ap.add_argument("--reference", action="append", default=[])
    ap.add_argument("--brief")
    ap.add_argument("--window", type=int, default=12)
    a = ap.parse_args()

    folder = Path(a.folder) if a.folder else None
    script_path = Path(a.script) if a.script else (folder / "script.md" if folder else None)
    if not script_path or not script_path.is_file():
        print(f"FAIL: script not found ({script_path}). Pass a production folder or --script.")
        return 2

    refs = [Path(r) for r in a.reference] or (find_transcripts(folder) if folder else [])
    brief = Path(a.brief) if a.brief else (folder / "craft-brief.md" if folder else None)
    beats_alt = folder / "reference" / "beats.txt" if folder else None

    script_md = read(script_path)
    failures = []
    notes = []

    # 1. Word-window overlap
    new_tokens = tokens(spoken_text(script_md))
    if not new_tokens:
        failures.append("script.md has no text in a 'Spoken line' column; nothing to check.")
    n = a.window
    if refs:
        ref_grams = set()
        for r in refs:
            t = tokens(clean_transcript(read(r)))
            ref_grams.update(tuple(t[i:i + n]) for i in range(len(t) - n + 1))
        hits = []
        i = 0
        while i <= len(new_tokens) - n:
            gram = tuple(new_tokens[i:i + n])
            if gram in ref_grams:
                # extend to the longest matching run so each reused passage prints once
                j = i + n
                while j < len(new_tokens) and tuple(new_tokens[j - n + 1:j + 1]) in ref_grams:
                    j += 1
                hits.append(" ".join(new_tokens[i:j]))
                i = j
            else:
                i += 1
        for h in hits:
            failures.append(f"{n}-word match with reference transcript: \"{h}\"")
        notes.append(f"text check: {len(new_tokens)} script words vs {len(refs)} transcript file(s)")
    else:
        notes.append("text check SKIPPED: no reference transcript found (tell the user)")

    # 2. Beat order
    s_beats = script_beats(script_md)
    r_beats = []
    if brief and brief.is_file():
        r_beats = reference_beats(read(brief))
    if not r_beats and beats_alt and beats_alt.is_file():
        r_beats = collapse([m.group(1).lower() for m in BEAT_RE.finditer(read(beats_alt))])
    if not s_beats:
        failures.append("script.md has no '## Section N - beat: <label>' headings; beat order cannot be checked.")
    elif not r_beats:
        notes.append("beat check SKIPPED: no '## Beat map' in craft-brief.md")
    elif s_beats == r_beats:
        failures.append("beat order is identical to the reference: " + " -> ".join(s_beats)
                        + ". Move proof, stake, or the reveal to a different slot.")
    else:
        notes.append("beats: script " + " -> ".join(s_beats) + " | reference " + " -> ".join(r_beats))

    for note in notes:
        print(f"note: {note}")
    if failures:
        for f in failures:
            print(f"FAIL: {f}")
        print(f"similarity_guard: {len(failures)} failure(s). Rewrite and run again.")
        return 1
    print("similarity_guard: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
