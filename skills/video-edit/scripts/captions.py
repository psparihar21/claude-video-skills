"""Remap word timestamps through the cut list and write caption files.

Inputs: the word transcript (Parakeet or GPU Whisper, [{id,text,start,end}] in
SOURCE seconds) and a vtc EDL (ranges with source_start/source_end/record_start
[/speed]). Only words fully inside a kept range survive; times move to the
OUTPUT timeline.

Outputs in OUT_DIR:
  words.out.json   word list on the output timeline (feed to HyperFrames captions)
  captions.srt     sidecar for YouTube
  captions.ass     "clean minimal" style for libass burn-in (Nirmala UI covers
                   Devanagari + Latin, so Hindi/Hinglish renders correctly)

Usage:
  python -I captions.py WORDS_JSON EDL_JSON OUT_DIR [--timeline 0] [--vertical]
         [--max-chars 42] [--margin-v N] [--top]
"""
import argparse
import json
from pathlib import Path

PUNCT_END = (".", "?", "!", "।", ",")


def remap(words, ranges):
    out = []
    for r in ranges:
        a, b = r["source_start"], r["source_end"]
        rec = r.get("record_start", 0.0)
        speed = r.get("speed", 1.0) or 1.0
        for w in words:
            if w["start"] >= a - 0.02 and w["end"] <= b + 0.02:
                out.append({
                    "text": w["text"].strip(),
                    "start": round(rec + (max(w["start"], a) - a) / speed, 3),
                    "end": round(rec + (min(w["end"], b) - a) / speed, 3),
                })
    out.sort(key=lambda w: w["start"])
    sentence_start = True
    for i, w in enumerate(out):
        w["id"] = f"w{i}"
        t = w["text"]
        if sentence_start and t[:1].isascii() and t[:1].isalpha():
            w["text"] = t[0].upper() + t[1:]
        sentence_start = t.endswith((".", "?", "!", "।"))
    return out


def cues(words, max_chars, max_dur=3.2, gap=0.5):
    """Group words into readable cues: <= 2 lines of max_chars, <= max_dur s,
    break on sentence punctuation or a pause."""
    cue, out = [], []

    def flush():
        if cue:
            out.append({"start": cue[0]["start"], "end": cue[-1]["end"], "words": list(cue)})
            cue.clear()

    for w in words:
        if cue:
            text_len = len(" ".join(x["text"] for x in cue + [w]))
            if (text_len > max_chars * 2 or w["end"] - cue[0]["start"] > max_dur
                    or w["start"] - cue[-1]["end"] > gap):
                flush()
        cue.append(w)
        if w["text"].endswith(PUNCT_END[:4]):
            flush()
    flush()
    # never overlap; hold short cues a touch longer for readability
    for i, c in enumerate(out):
        nxt = out[i + 1]["start"] if i + 1 < len(out) else c["end"] + 0.6
        c["end"] = min(max(c["end"], c["start"] + 0.8), nxt - 0.01)
    return out


def wrap(text, max_chars):
    if len(text) <= max_chars:
        return [text]
    words, best = text.split(), None
    for i in range(1, len(words)):
        l1, l2 = " ".join(words[:i]), " ".join(words[i:])
        score = max(len(l1), len(l2))
        if best is None or score < best[0]:
            best = (score, [l1, l2])
    return best[1]


def ts(t, sep):
    h, rem = divmod(max(t, 0), 3600)
    m, s = divmod(rem, 60)
    if sep == ",":
        return f"{int(h):02}:{int(m):02}:{int(s):02},{int(round((s % 1) * 1000)):03}"
    return f"{int(h)}:{int(m):02}:{int(s):02}.{int(round((s % 1) * 100)):02}"


def main():
    p = argparse.ArgumentParser()
    p.add_argument("words", type=Path)
    p.add_argument("edl", type=Path)
    p.add_argument("out_dir", type=Path)
    p.add_argument("--timeline", type=int, default=0)
    p.add_argument("--vertical", action="store_true")
    p.add_argument("--max-chars", type=int, default=None)
    p.add_argument("--margin-v", type=int, default=None)
    p.add_argument("--top", action="store_true", help="put captions at the top (e.g. facecam bottom)")
    a = p.parse_args()

    words = json.loads(a.words.read_text(encoding="utf-8"))
    tl = json.loads(a.edl.read_text(encoding="utf-8"))["timelines"][a.timeline]
    out_words = remap(words, tl["ranges"])
    max_chars = a.max_chars or (26 if a.vertical else 42)
    cs = cues(out_words, max_chars)

    a.out_dir.mkdir(parents=True, exist_ok=True)
    (a.out_dir / "words.out.json").write_text(json.dumps(out_words, ensure_ascii=False, indent=2), encoding="utf-8")

    srt = []
    for i, c in enumerate(cs, 1):
        lines = wrap(" ".join(w["text"] for w in c["words"]), max_chars)
        srt.append(f"{i}\n{ts(c['start'], ',')} --> {ts(c['end'], ',')}\n" + "\n".join(lines) + "\n")
    (a.out_dir / "captions.srt").write_text("\n".join(srt), encoding="utf-8")

    w, h = (1080, 1920) if a.vertical else (1920, 1080)
    size = 64 if a.vertical else 46
    margin = a.margin_v if a.margin_v is not None else (420 if a.vertical else 70)
    align = 8 if a.top else 2
    ass = [
        "[Script Info]", "ScriptType: v4.00+", f"PlayResX: {w}", f"PlayResY: {h}",
        "WrapStyle: 2", "ScaledBorderAndShadow: yes", "",
        "[V4+ Styles]",
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
        f"Style: Clean,Nirmala UI,{size},&H00FFFFFF,&H00FFFFFF,&H00000000,&H64000000,1,0,0,0,100,100,0,0,1,2.5,1.2,{align},90,90,{margin},1",
        "", "[Events]",
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
    ]
    for c in cs:
        lines = wrap(" ".join(x["text"] for x in c["words"]), max_chars)
        ass.append(f"Dialogue: 0,{ts(c['start'], '.')},{ts(c['end'], '.')},Clean,,0,0,0,,{{\\fad(80,80)}}" + "\\N".join(lines))
    (a.out_dir / "captions.ass").write_text("\n".join(ass) + "\n", encoding="utf-8-sig")
    print(f"{len(out_words)} words, {len(cs)} cues -> {a.out_dir}")


if __name__ == "__main__":
    main()
