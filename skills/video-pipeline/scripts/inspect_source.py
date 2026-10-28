"""Probe a source video and say what kind it is, so the pipeline picks the right branch.

Usage: python -I inspect_source.py "<video>" [--out job.json]
Prints a short report and writes job.json (next to the video unless --out is given).
Kinds:
  obs-ps5   3 audio tracks (OBS: mix / PS5 game / mic) -> full edit from raw gameplay
  raw       one audio track, long, not yet edited       -> full edit
  edited    short or already-finished looking upload    -> Shorts + packaging only (ask the user)
"""
import json, os, subprocess, sys


def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")


def probe(path):
    r = run(["ffprobe", "-v", "error", "-show_format", "-show_streams", "-of", "json", path])
    if r.returncode != 0:
        sys.exit(f"ffprobe failed: {r.stderr.strip()}")
    return json.loads(r.stdout)


def loudness(path, idx, seconds):
    """Integrated loudness and peak of one audio stream over the first `seconds`."""
    r = run(["ffmpeg", "-hide_banner", "-nostats", "-t", str(seconds), "-i", path, "-map", f"0:a:{idx}",
             "-af", "ebur128=peak=true:framelog=quiet", "-f", "null", "-"])
    txt = r.stderr[r.stderr.rfind("Summary"):]
    out = {}
    for line in txt.splitlines():
        line = line.strip()
        if line.startswith("I:"):
            out["lufs"] = float(line.split()[1])
        elif line.startswith("Peak:"):
            out["peak_db"] = float(line.split()[1])
    return out


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    path = os.path.abspath(sys.argv[1])
    if not os.path.isfile(path):
        sys.exit(f"not found: {path}")
    out_path = sys.argv[sys.argv.index("--out") + 1] if "--out" in sys.argv else os.path.join(os.path.dirname(path), "job.json")

    info = probe(path)
    fmt = info["format"]
    dur = float(fmt.get("duration", 0))
    v = next((s for s in info["streams"] if s["codec_type"] == "video"), None)
    auds = [s for s in info["streams"] if s["codec_type"] == "audio"]
    num, den = (v or {}).get("avg_frame_rate", "0/1").split("/")
    fps = round(float(num) / float(den), 2) if float(den) else 0
    tags = {k.lower(): str(val) for k, val in fmt.get("tags", {}).items()}

    sample = min(dur, 300) or 60
    tracks = []
    for i, a in enumerate(auds):
        t = {"index": i, "codec": a.get("codec_name"), "channels": a.get("channels"),
             "sample_rate": a.get("sample_rate"), "title": a.get("tags", {}).get("title", "")}
        t.update(loudness(path, i, sample))
        tracks.append(t)

    if len(auds) == 3:
        kind = "obs-ps5"
        roles = {"mix": 0, "game": 1, "mic": 2}
    elif dur < 75 or (v and int(v.get("height", 0)) > int(v.get("width", 1))):
        kind = "edited"
        roles = {"mix": 0} if auds else {}
    else:
        kind = "raw"
        roles = {"mix": 0} if auds else {}
    # a finished YouTube download is usually H.264/VP9/AV1 with one track and no OBS name
    looks_downloaded = len(auds) <= 1 and not os.path.basename(path).startswith("PS5 ")

    job = {
        "source": path,
        "kind": kind,
        "looks_downloaded": looks_downloaded,
        "duration_s": round(dur, 2),
        "video": {"width": (v or {}).get("width"), "height": (v or {}).get("height"), "fps": fps,
                  "codec": (v or {}).get("codec_name"), "pix_fmt": (v or {}).get("pix_fmt")},
        "audio_tracks": tracks,
        "audio_roles": roles,
        "size_mb": round(int(fmt.get("size", 0)) / 1e6, 1),
        "encoder_tag": tags.get("encoder", ""),
        "job_dir": os.path.join(os.path.dirname(path), os.path.splitext(os.path.basename(path))[0] + " - pipeline"),
    }
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(job, f, indent=2)

    print(f"source   {path}")
    print(f"kind     {kind}{'  (looks like a downloaded/finished video)' if looks_downloaded and kind != 'obs-ps5' else ''}")
    print(f"length   {dur/60:.1f} min   {job['video']['width']}x{job['video']['height']} {fps} fps {job['video']['codec']}   {job['size_mb']} MB")
    names = {0: "mix", 1: "game", 2: "mic"} if kind == "obs-ps5" else {}
    for t in tracks:
        print(f"audio {t['index']}  {names.get(t['index'], 'audio'):5s} {t.get('lufs', 'n/a')} LUFS  peak {t.get('peak_db', 'n/a')} dB  (first {sample/60:.0f} min)")
    print(f"job.json {out_path}")


if __name__ == "__main__":
    main()
