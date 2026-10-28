#!/usr/bin/env python3
"""Check a production folder before a channel video package can be marked READY.

Usage:
    python3 check_package.py <production-folder>

Reads: intake.md, style-card.md, script.md, shot-list.md, rights-log.md,
missing-items.md, package.md (formats in references/run-workflow.md).

Exits 1 and prints one FAIL line per problem:
  - style card missing or still a template
  - script missing, not "Status: LOCKED", or not "Approved by user: yes"
  - a shot with no source
  - a shot or rights row whose source is the reference file, reference URL, or its video ID
  - a music or SFX row with no license
  - a voice row that is not the user's recording, an approved clone of the user's voice,
    or an approved stock TTS voice with its model license
  - a gameplay/screenshot row not from user-recorded, press-kit:, official: or
    editorial-screenshot:, or missing its credit or publisher policy proof
  - a realistic generated shot with no disclosure (or package with "Disclosure: none")
  - package marked READY while any (required...) question is unanswered
Exit 0 = pass. Exit 2 = folder not found.
"""
import os
import re
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

COMMENT_RE = re.compile(r"<!--.*?-->", re.S)
TEMPLATE_MARK = "<!-- TEMPLATE:"
YES = {"yes", "y", "true", "approved"}
EMPTY = {"", "-", "—", "n/a", "na", "none", "tbd", "todo", "?"}


def raw(path):
    return path.read_text(encoding="utf-8", errors="replace")


def strip(text):
    return COMMENT_RE.sub("", text)


def split_row(line):
    line = line.strip()
    if line.startswith("|"):
        line = line[1:]
    if line.endswith("|"):
        line = line[:-1]
    return [c.strip() for c in line.split("|")]


def parse_tables(text):
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


def col(row, *prefixes):
    for key, val in row.items():
        if any(key.startswith(p) for p in prefixes):
            return val.strip()
    return ""


def empty(val):
    return val.strip().strip("`*_").lower() in EMPTY


def field(text, name):
    m = re.search(rf"^\s*{name}\s*:\s*(.+?)\s*$", text, re.I | re.M)
    return m.group(1).strip() if m else ""


def table_rows(path, required_col):
    rows = []
    for headers, rs in parse_tables(strip(raw(path))):
        if any(h.startswith(required_col) for h in headers):
            rows.extend(rs)
    return rows


def reference_markers(intake_text):
    markers = []
    for line in re.findall(r"^\s*reference (?:file|url)s?\s*:\s*(.+)$", intake_text, re.I | re.M):
        for item in re.split(r"[,\s]+", line.strip()):
            item = item.strip("`<>\"'").lower()
            if empty(item):
                continue
            if item.startswith("http") or "youtu" in item or "/" in item:
                markers.append(re.sub(r"^https?://(www\.)?", "", item).rstrip("/"))
                m = re.search(r"(?:v=|youtu\.be/|shorts/|embed/|live/)([a-z0-9_-]{11})", item, re.I)
                if m:
                    markers.append(m.group(1).lower())
            else:
                markers.append(Path(item).name)
    return [m for m in markers if len(m) >= 5]


def reuses_reference(source, markers):
    s = source.lower()
    if re.search(r"(^|[\s/`(])reference/", s):
        return "reference/ folder"
    for m in markers:
        if m in s:
            return m
    return None


def main():
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    folder = os.path.abspath(sys.argv[1])
    if os.name == "nt" and len(folder) >= 200 and not folder.startswith("\\\\?\\"):
        folder = "\\\\?\\" + folder  # Windows long-path prefix
    folder = Path(folder)
    if not folder.is_dir():
        print(f"FAIL: production folder not found: {folder}")
        return 2

    fails, notes = [], []
    p = lambda name: folder / name

    # Reference markers
    markers = []
    if p("intake.md").is_file():
        markers = reference_markers(strip(raw(p("intake.md"))))
        if not markers:
            notes.append("intake.md lists no reference file or URL; only reference/ paths are checked")
    else:
        fails.append("intake.md missing: record 'Reference file:' and 'Reference URL:' so reuse can be checked.")

    # Style card
    sc = p("style-card.md")
    if not sc.is_file():
        fails.append("style card missing: style-card.md not found. Build it from the user's own samples (step 3).")
    elif TEMPLATE_MARK in raw(sc):
        fails.append("style card is still the template (TEMPLATE marker present). Fill it from the user's samples.")

    # Script
    sp = p("script.md")
    if not sp.is_file():
        fails.append("script missing: script.md not found.")
    else:
        st = raw(sp)
        status = field(strip(st), "status").upper()
        approved = field(strip(st), "approved by user").lower()
        if TEMPLATE_MARK in st:
            fails.append("script is still the template (TEMPLATE marker present).")
        if status != "LOCKED":
            fails.append(f"script not locked: script.md Status is '{status or 'missing'}', needs 'LOCKED' after the user approves it.")
        if approved not in YES:
            fails.append(f"script not approved: 'Approved by user' is '{approved or 'missing'}'. Show the script and wait for a yes.")

    # Shot list
    realistic_rows = []
    sl = p("shot-list.md")
    if not sl.is_file():
        fails.append("shot list missing: shot-list.md not found.")
    else:
        rows = table_rows(sl, "source")
        if not rows:
            fails.append("shot list has no rows (needs a table with a 'Source' column).")
        for r in rows:
            sid = col(r, "#", "id", "shot") or "?"
            stype = col(r, "source type", "type").lower()
            source = col(r, "source")
            # 'source' prefix also matches 'source type'; prefer the exact column
            source = r.get("source", source).strip()
            if empty(source):
                fails.append(f"shot {sid} has no source. Find a licensed/owned/generated source or move it to missing-items.md.")
            hit = reuses_reference(source, markers)
            if hit:
                fails.append(f"shot {sid} uses the reference as its source ({hit}): '{source}'. Replace it; never cut from the reference.")
            realistic = col(r, "realistic").lower()
            if "generat" in stype or "generat" in source.lower():
                if realistic in YES:
                    realistic_rows.append(sid)
                    if empty(col(r, "disclosure")):
                        fails.append(f"shot {sid} is realistic AI-generated with no disclosure line. Fill Disclosure.")

    # Rights log
    rl = p("rights-log.md")
    if not rl.is_file():
        fails.append("rights log missing: rights-log.md not found.")
    else:
        rows = table_rows(rl, "license")
        if not rows:
            fails.append("rights log has no rows (needs a table with a 'License' column).")
        for r in rows:
            rid = col(r, "#", "id") or "?"
            atype = col(r, "type").lower()
            source = r.get("source", "").strip()
            lic = col(r, "license", "licence")
            appr = col(r, "approved").lower()
            hit = reuses_reference(source, markers)
            if hit:
                fails.append(f"rights row {rid} ({atype or 'asset'}) comes from the reference ({hit}): '{source}'.")
            if atype in ("music", "sfx", "sound", "sound effect", "audio") and empty(lic):
                fails.append(f"rights row {rid}: {atype} has no license. Log a commercial license or replace the track.")
            if atype == "voice":
                s = source.lower()
                if s.startswith("user-recorded") or s in ("user", "me", "self", "user recorded"):
                    pass
                elif s.startswith("user-clone:") and not empty(s.split(":", 1)[1]):
                    if appr.split(" ")[0].strip("(,.") not in YES:
                        fails.append(f"rights row {rid}: voice clone '{source}' is not explicitly approved. Get the user's yes for that exact voice in chat.")
                elif s.startswith("stock-tts:") and not empty(s.split(":", 1)[1]):
                    if appr.split(" ")[0].strip("(,.") not in YES:
                        fails.append(f"rights row {rid}: stock voice '{source}' is not approved. Get the user's pick for this video.")
                    if empty(lic):
                        fails.append(f"rights row {rid}: stock voice '{source}' has no model license.")
                else:
                    fails.append(f"rights row {rid}: voice source '{source or 'empty'}' is not allowed. Use 'user-recorded', an approved 'user-clone: <name>', or an approved 'stock-tts: <engine> <voice>'.")
            if atype in ("gameplay", "trailer", "screenshot"):
                s = source.lower()
                if not s.startswith(("user-recorded", "press-kit:", "official:", "editorial-screenshot:")):
                    fails.append(f"rights row {rid}: {atype} source '{source or 'empty'}' must start with user-recorded, press-kit:, official: or editorial-screenshot:. Never another creator's video.")
                if empty(col(r, "attribution")) and not s.startswith("user-recorded"):
                    fails.append(f"rights row {rid}: {atype} has no credit in Attribution (on-screen and description credit).")
                if empty(col(r, "proof")) and s.startswith(("press-kit:", "official:")):
                    fails.append(f"rights row {rid}: {atype} has no publisher policy URL (or 'policy: not found') in Proof.")

    # Package and questions
    pk = p("package.md")
    unanswered = []
    mi = p("missing-items.md")
    if mi.is_file():
        unanswered = [l.strip() for l in strip(raw(mi)).splitlines()
                      if re.match(r"^\s*[-*]\s*\[\s\]\s*\(required[^)]*\)", l, re.I)]
    if not pk.is_file():
        fails.append("package missing: package.md not found (step 8).")
    else:
        pt = strip(raw(pk))
        pstatus = field(pt, "status").upper()
        disclosure = field(pt, "disclosure")
        if realistic_rows and empty(disclosure):
            fails.append(f"package has no disclosure line but realistic synthetic shots remain ({', '.join(realistic_rows)}). Set 'Disclosure:'.")
        if pstatus == "READY":
            for q in unanswered:
                fails.append(f"package marked READY while a required question is unanswered: {q}")
        else:
            notes.append(f"package Status is '{pstatus or 'missing'}'; set READY only after this passes and both approvals exist")
            for q in unanswered:
                notes.append(f"still unanswered: {q}")

    for n in notes:
        print(f"note: {n}")
    if fails:
        for f in fails:
            print(f"FAIL: {f}")
        print(f"check_package: {len(fails)} failure(s).")
        return 1
    print("check_package: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
