"""Render punch / ratchet / ken-burns zooms onto a video from a map.json.
usage: python zoom.py in.mp4 map.json out.mp4 [--cpu]
map.json: {"focus_y":0.4, "punch":[{"t":1.2,"dur":0.6,"z":1.25}],
           "ratchet":[{"t":5,"steps":[1.1,1.2,1.3],"each":1.2}],
           "kenburns":[{"t":9,"dur":3,"z":1.12}]}
"""
import json, subprocess, sys

def probe(p):
    o = subprocess.check_output(["ffprobe", "-v", "error", "-select_streams", "v:0",
        "-show_entries", "stream=width,height", "-of", "csv=p=0", p], text=True).strip()
    return map(int, o.split(","))

def zexpr(m):
    terms = []
    for p in m.get("punch", []):
        terms.append(f"between(t,{p['t']},{p['t']+p['dur']})*{p.get('z',1.25)-1}")
    for r in m.get("ratchet", []):
        for i, z in enumerate(r["steps"]):
            a = r["t"] + i * r["each"]
            terms.append(f"between(t,{a},{a+r['each']})*{z-1}")
    for k in m.get("kenburns", []):
        a, b = k["t"], k["t"] + k["dur"]
        terms.append(f"between(t,{a},{b})*{k.get('z',1.12)-1}*(t-{a})/{b-a}")
    return "1+(" + ("+".join(terms) or "0") + ")"

def main():
    src, mp, out = sys.argv[1:4]
    m = json.load(open(mp))
    for p in m.get("punch", []) + m.get("kenburns", []):
        assert p.get("z", 1.25) <= 1.30, "peak zoom above 1.30 goes soft; lower it"
    w, h = probe(src)
    fy = m.get("focus_y", 0.4)
    z = zexpr(m)
    vf = (f"scale=w='trunc({w}*({z})/2)*2':h='trunc({h}*({z})/2)*2':eval=frame:flags=bicubic,"
          f"crop={w}:{h}:x='(iw-{w})/2':y='(ih-{h})*{fy}',setsar=1")
    enc = ["-c:v", "libx264", "-crf", "16", "-preset", "fast"] if "--cpu" in sys.argv else \
          ["-c:v", "h264_nvenc", "-cq", "18", "-preset", "p5"]
    subprocess.check_call(["ffmpeg", "-y", "-v", "error", "-i", src, "-vf", vf, *enc,
        "-pix_fmt", "yuv420p", "-c:a", "copy", out])

if __name__ == "__main__":
    main()
