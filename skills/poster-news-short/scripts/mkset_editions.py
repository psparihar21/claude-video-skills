"""uv run mkset_gta.py -> ~/voice-studio/sets/gta6in (proxy video, my-script.txt, cues.json, video.json)"""
import json, subprocess
from pathlib import Path
J = (Path.home() / "Videos/pipeline/gta6-editions"); D = (Path.home() / "voice-studio/sets/gta6in"); D.mkdir(parents=True, exist_ok=True)
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(J / "final/short.silent.mp4"), "-vf", "scale=540:-2", "-an", "-c:v", "libx264", "-crf", "26", "-preset", "fast", str(D / "proxy.mp4")], check=True)
dur = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(D / "proxy.mp4")]))
STARTS = [0.0, 6.3, 15.8, 22.8, 30.8, 35.9, 39.2, 44.0]
TXT = [
 "Standard or Ultimate? / Here is what the extra ₹1,500 gets you in GTA 6.",
 "On the PlayStation Store India, Standard is ₹5,999. // You get the full game, / and the Vintage Vice City pack if you pre-order.",
 "That pack has a 1955 Vapid Stanier, / outfits and hairstyles for Jason and Lucia, / and a weapon pattern.",
 "Ultimate is ₹7,499. // It adds the Grotti Cheetah, / special revolvers, / and a classic car collection.",
 "Plus shops like Rideout Customs, / Sara's Salon / and Electric Fang tattoo parlor.",
 "It is all extras, / so the story is the same in both.",
 "Both launch on 19 November, / on PS5 and Xbox Series X and S.",
 "So which one are you getting? // Tell me in the comments, / and follow Pushpstation for more GTA 6 news.",
]
lines = [f"GTA 6 STANDARD VS ULTIMATE, INDIA ₹ - SHORT, ENGLISH (about {int(round(dur))} s)",
         "Read it like you're telling a friend. Small pause at every /. Say each block while its picture is on screen. The marker time is when the block starts. Change any words you like.", ""]
marks = []
for i, (t0, txt) in enumerate(zip(STARTS, TXT), 1):
    t1 = STARTS[i] if i < len(STARTS) else dur
    lines += [f"[{int(t0 // 60)}:{t0 % 60:04.1f}] PART {i}  ({int(round(t1 - t0))} s)", txt, ""]
    marks.append({"t": t0, "label": f"Part {i}", "kind": "section"})
(D / "my-script.txt").write_text("\n".join(lines), encoding="utf8")
(D / "cues.json").write_text(json.dumps({"proxy.mp4": marks}, indent=1), encoding="utf8")
(D / "video.json").write_text(json.dumps({"name": "proxy.mp4", "duration": dur}), encoding="utf8")
print("set ready", D, round(dur, 1), "s")
