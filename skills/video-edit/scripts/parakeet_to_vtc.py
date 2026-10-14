"""Convert a HyperFrames Parakeet transcript ([{id,text,start,end}]) into the
video-timeline-copilot (vtc) transcript format, so `vtc pack-transcripts`,
`refine-audio-cuts`, `validate-edl` and `export-srt` use Parakeet word times.

Usage:
  python -I parakeet_to_vtc.py TRANSCRIPT_JSON SOURCE_VIDEO OUT_JSON
Segments split on sentence punctuation or a word gap > 0.6 s.
"""
import json
import sys
from pathlib import Path

GAP = 0.6


def main() -> None:
    src_json, source, out = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
    words = json.loads(src_json.read_text(encoding="utf-8"))
    segments, cur = [], []

    def flush() -> None:
        if cur:
            segments.append({
                "start": cur[0]["start"], "end": cur[-1]["end"],
                "text": " ".join(w["text"] for w in cur), "words": list(cur),
            })
            cur.clear()

    prev_end = None
    for w in words:
        item = {"start": w["start"], "end": w["end"], "text": w["text"], "probability": 1.0}
        if prev_end is not None and w["start"] - prev_end > GAP:
            flush()
        cur.append(item)
        prev_end = w["end"]
        if w["text"].rstrip().endswith((".", "?", "!")):
            flush()
    flush()

    payload = {
        "source": str(source.resolve()),
        "language": "en",
        "language_probability": 1.0,
        "duration": words[-1]["end"] if words else 0,
        "engine": "parakeet-tdt-0.6b-v3",
        "segments": segments,
        "words": [w for s in segments for w in s["words"]],
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"vtc transcript -> {out} ({len(payload['words'])} words, {len(segments)} segments)")


if __name__ == "__main__":
    main()
