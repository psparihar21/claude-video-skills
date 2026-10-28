"""Join per-cue wavs with short gaps -> voice_tight.wav + cues.json. uv run tight.py <cues_dir> <out_dir>"""
import json, subprocess, sys
from pathlib import Path
src, out = Path(sys.argv[1]), Path(sys.argv[2]); GAP, LEAD = 0.38, 0.3
ids = sorted(p.stem for p in src.glob("c*.wav")); t = LEAD; cues = []; args = ["ffmpeg","-v","error","-y"]; fc = []
for i, c in enumerate(ids):
    d = float(subprocess.check_output(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",str(src/f"{c}.wav")]))
    cues.append({"id": c, "start": round(t,3), "end": round(t+d,3)}); t += d + GAP; args += ["-i", str(src/f"{c}.wav")]
    fc.append(f"[{i}:a]aformat=sample_rates=48000:channel_layouts=mono,adelay={int(cues[-1]['start']*1000)}|{int(cues[-1]['start']*1000)}[a{i}]")
fc.append("".join(f"[a{i}]" for i in range(len(ids))) + f"amix=inputs={len(ids)}:normalize=0:duration=longest,apad=whole_dur={t:.2f}[o]")
subprocess.run(args + ["-filter_complex", ";".join(fc), "-map", "[o]", "-ar", "48000", str(out/"voice_tight.wav")], check=True)
(out/"cues.json").write_text(json.dumps(cues, indent=1)); print(cues[-1]["end"])
