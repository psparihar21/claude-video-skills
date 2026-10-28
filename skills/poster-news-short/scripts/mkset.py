"""Create Voice Studio sets nov26 (Hinglish) and nov26en (English). uv run mkset.py"""
import json, re, subprocess
from pathlib import Path
P = (Path.home() / "Videos/pipeline/ps-nov26"); S = (Path.home() / "voice-studio/sets")
NUM = [("seventeen","17"),("twelve","12"),("twenty six","26"),("twenty four","24"),("four point one","4.1"),(" five"," 5"),("GTA six","GTA 6"),("Rock of Ages three","Rock of Ages 3"),("Redemption two","Redemption 2"),("Principle two","Principle 2")]
def disp(t):
    for a, b in NUM: t = t.replace(a, b)
    return t
def mk(setname, vid, title):
    d = S / setname; d.mkdir(parents=True, exist_ok=True)
    subprocess.run(["ffmpeg","-v","error","-y","-i",str(P/f"ps-leaving-short-{vid}.silent.mp4"),"-vf","scale=540:-2","-an","-c:v","libx264","-crf","26","-preset","fast",str(d/"proxy.mp4")],check=True)
    dur = float(subprocess.check_output(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",str(d/"proxy.mp4")]))
    cues = json.load(open(P/"voice"/vid/"cues.json")); sc = json.load(open(P/"vo"/vid/"03-script.json",encoding="utf8"))["cues"]
    lines = [f"{title} (about {int(round(dur))} s)", "Read it like you're telling a friend. Small pause at every /. Say each block while its picture is on screen. The marker time is when the block starts. Change any words you like.", ""]
    marks = []
    for i, (c, s) in enumerate(zip(cues, sc), 1):
        t0 = 0.0 if i == 1 else round(c["start"] - 0.2, 1); t1 = cues[i]["start"] - 0.2 if i < len(cues) else dur
        txt = disp(s["spoken"]).replace(", ", ", / ").replace(". ", ". // ")
        lines += [f"[{int(t0//60)}:{t0%60:04.1f}] PART {i}  ({int(round(t1-t0))} s)", txt, ""]
        marks.append({"t": t0, "label": f"Part {i}", "kind": "section"})
    (d/"my-script.txt").write_text("\n".join(lines), encoding="utf8")
    (d/"cues.json").write_text(json.dumps({"proxy.mp4": marks}, indent=1), encoding="utf8")
    (d/"video.json").write_text(json.dumps({"name": "proxy.mp4", "duration": dur}), encoding="utf8")
mk("nov26", "hi-v3", "PS PLUS NOV 2026 LEAVING - SHORT, HINGLISH"); mk("nov26en", "en-v1", "PS PLUS NOV 2026 LEAVING - SHORT, ENGLISH")
