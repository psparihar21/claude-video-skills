"""PS Plus Nov 2026 'leaving' Short, faceless, built from official posters.
uv run --with pillow --with numpy build_short.py <voice.wav> <cues.json> <out.mp4>
cues.json = [{"id":"c01","start":0.25,"end":7.1}, ...] times inside voice.wav (scratch voice or the user's cut take).
The picture follows the voice: change the voice + cues.json, rebuild, done."""
import json, subprocess, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

VOICE, CUES, OUT = map(Path, sys.argv[1:4])   # CUES = timeline.json from assemble_nov26.py
J = (Path.home() / "Videos/pipeline/ps-nov26"); ART = J / "art"; MUS = (Path.home() / "Videos/pipeline/ps-oct26/music/563.mp3")
W, H, FPS = 1080, 1920, 30
F = "C:/Windows/Fonts/"
WHITE = (238, 243, 246); INK = (22, 19, 15); CREAM = (243, 234, 215); RED = (224, 53, 43); GREY = (92, 98, 104)
ease = lambda x: 1 - (1 - min(max(x, 0), 1)) ** 3

# (key, file, card title, note)
G = {
 "rdr2": ("rdr2.jpg", "Red Dead Redemption 2", ""), "gta5": ("gta5.jpg", "Grand Theft Auto V", ""),
 "fm26": ("fm26.jpg", "Football Manager 26", ""), "cricket24": ("cricket24.jpg", "Cricket 24", ""),
 "talos2": ("talos2.jpg", "The Talos Principle 2", ""), "rockofages3": ("rockofages3.jpg", "Rock of Ages 3", ""),
 "monsterboy": ("monsterboy.jpg", "Monster Boy", "select regions"), "hotshot": ("hotshot.jpg", "Hotshot Racing", "select regions"),
 "edf41": ("edf41.jpg", "Earth Defense Force 4.1", "select regions"), "thankgoodness": ("thankgoodness.jpg", "Thank Goodness You're Here", "select regions"),
 "rapala": ("rapala.jpg", "Rapala Fishing: Pro Series", "select regions"), "zombiedef": ("zombiedef.jpg", "Yet Another Zombie Defense HD", "select regions"),
}
ORDER = ["rdr2", "gta5", "fm26", "cricket24", "talos2", "rockofages3", "monsterboy", "hotshot", "edf41", "thankgoodness", "rapala", "zombiedef"]
# cue -> poster items, switch points as a fraction of the cue (lead 0.1 s is applied so the picture lands before the word)
# cue -> [(poster, marker in the spoken text where it appears; None = cue start)]; same plan for every language
SEQ = {
 "c02": [("rdr2", None), ("gta5", "GTA five")],
 "c03": [("fm26", None), ("cricket24", "Cricket")],
 "c04": [("talos2", None), ("rockofages3", "Rock of Ages"), ("monsterboy", "Monster Boy"), ("hotshot", "Hotshot"), ("edf41", "Earth Defense")],
 "c05": [("thankgoodness", None)],
 "c06": [("rapala", None), ("zombiedef", "Yet Another")],
}
LEAD = 0.1

def fnt(n, s): return ImageFont.truetype(F + n, s)
def load(k):
    im = Image.open(ART / G[k][0]).convert("RGB"); return im
POST = {k: load(k) for k in ORDER}

def cover(im, w, h):
    s = max(w / im.width, h / im.height); im = im.resize((int(im.width * s) + 1, int(im.height * s) + 1), Image.LANCZOS)
    x, y = (im.width - w) // 2, (im.height - h) // 2; return im.crop((x, y, x + w, y + h))
BG = {}
for k in ORDER:
    b = cover(POST[k], 270, 480).filter(ImageFilter.GaussianBlur(14)).resize((W, H), Image.BICUBIC)
    BG[k] = (np.asarray(b, dtype=np.float32) * 0.42).astype(np.uint8)
INKBG = np.full((H, W, 3), INK, np.uint8)

def spaced(d, xy, text, f, fill, track=3):
    x, y = xy
    for ch in text: d.text((x, y), ch, font=f, fill=fill); x += d.textlength(ch, font=f) + track
    return x
def card(label, title, detail="", size=58):
    fl, ft, fd = fnt("segoeuib.ttf", 24), fnt("seguibl.ttf", size), fnt("segoeui.ttf", 30)
    pr = ImageDraw.Draw(Image.new("RGB", (4, 4)))
    tw = max(pr.textlength(title, font=ft), sum(pr.textlength(c, font=fl) + 3 for c in label.upper()), pr.textlength(detail, font=fd) if detail else 0)
    w = int(tw + 100); h = 92 + size + (44 if detail else 0)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, w - 1, h - 1), 20, fill=WHITE + (255,)); d.rounded_rectangle((0, 0, 22, h - 1), 20, fill=INK + (255,)); d.rectangle((11, 0, 22, h - 1), fill=INK + (255,))
    spaced(d, (54, 24), label.upper(), fl, GREY); d.text((52, 56), title, font=ft, fill=INK + (255,))
    if detail: d.text((54, 56 + size + 14), detail, font=fd, fill=GREY + (255,))
    return im

def shadow(w, h):
    im = Image.new("RGBA", (w + 160, h + 160), (0, 0, 0, 0)); ImageDraw.Draw(im).rounded_rectangle((80, 96, 80 + w, 96 + h), 16, fill=(0, 0, 0, 190))
    return im.filter(ImageFilter.GaussianBlur(26))
def rounded(im, r=14):
    m = Image.new("L", im.size, 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, im.width - 1, im.height - 1), r, fill=255)
    o = im.convert("RGBA"); o.putalpha(m); return o

def paste_rgba(base, ov, x, y):
    if x >= W or y >= H or x + ov.width <= 0 or y + ov.height <= 0: return
    base.alpha_composite(ov, (max(x, 0), max(y, 0)), (max(-x, 0), max(-y, 0)))

# ---- scenes: each is f(t, dur) -> RGBA PIL image (W x H) ----
CARD = {k: card("Leaving PS Plus · 17 Nov", G[k][1], G[k][2], 52 if len(G[k][1]) > 22 else 60) for k in ORDER}
def poster_scene(k):
    p = POST[k]; w0 = 760; h0 = int(w0 * p.height / p.width)
    sh = shadow(w0, h0)
    def f(t, dur):
        s = 1.0 + 0.06 * (t / max(dur, 0.1))
        w, h = int(w0 * s), int(h0 * s)
        base = Image.fromarray(BG[k]).convert("RGBA")
        paste_rgba(base, sh.resize((int(sh.width * s), int(sh.height * s))), W // 2 - int(sh.width * s) // 2, 800 - int(sh.height * s) // 2 + 30)
        paste_rgba(base, rounded(p.resize((w, h), Image.LANCZOS)), W // 2 - w // 2, 800 - h // 2)
        c = CARD[k]; a = ease(t / 0.35); xo = int(60 - (c.width + 60) * (1 - a)); paste_rgba(base, c, xo, 1430)
        return base
    return f

def grid_scene(mode):
    cols, rows, tw, th = 4, 3, 255, 383
    gx, gy = (W - cols * tw - (cols - 1) * 12) // 2, 560
    tiles = [rounded(cover(POST[k], tw, th), 10) for k in ORDER]
    top = card("12 games · PS Subscription", "LEAVING 17 NOV", "", 64) if mode == "hook" else None
    big = card("Last day to play", "17 NOV 2026", "", 96) if mode == "date" else None
    ask = card("Tell me in the comments", "WHICH WILL YOU PLAY?", "", 52)
    tape = Image.new("RGBA", (620, 150), (0, 0, 0, 0)); d = ImageDraw.Draw(tape); d.rectangle((0, 0, 619, 149), fill=CREAM + (255,))
    d.text((310, 75), "PUSHPSTATION", font=fnt("seguibl.ttf", 78), fill=INK + (255,), anchor="mm"); tape = tape.rotate(2.5, expand=True, resample=Image.BICUBIC)
    pill = Image.new("RGBA", (520, 120), (0, 0, 0, 0)); d = ImageDraw.Draw(pill); d.rounded_rectangle((0, 0, 519, 119), 60, fill=RED + (255,))
    d.text((260, 60), "SUBSCRIBE", font=fnt("seguibl.ttf", 58), fill=(255, 255, 255, 255), anchor="mm")
    def f(t, dur):
        base = Image.fromarray(INKBG).convert("RGBA")
        z = 1.0 + 0.04 * (t / max(dur, 0.1))
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        for i, tl in enumerate(tiles):
            r, c = divmod(i, cols); pop = ease((t - 0.05 * i) / 0.25) if mode == "hook" else 1
            if pop <= 0: continue
            w, h = max(2, int(tw * (0.85 + 0.15 * pop))), max(2, int(th * (0.85 + 0.15 * pop)))
            x = gx + c * (tw + 12) + (tw - w) // 2; y = gy + r * (th + 12) + (th - h) // 2
            tt = tl.resize((w, h), Image.LANCZOS)
            if mode != "hook":
                dim = 0.35 if mode == "date" else 0.3
                tt = Image.fromarray((np.asarray(tt, dtype=np.float32) * np.array([dim, dim, dim, 1])).astype(np.uint8))
            if pop < 1: tt.putalpha(tt.getchannel("A").point(lambda v: int(v * pop)))
            lay.alpha_composite(tt, (x, y))
        cx, cy = W // 2, gy + (rows * th + (rows - 1) * 12) // 2
        lay = lay.resize((int(W * z), int(H * z)), Image.LANCZOS); base.alpha_composite(lay, (cx - int(cx * z) , cy - int(cy * z)) if False else (int(-(W * z - W) / 2), int(-(H * z - H) / 2)))
        if mode == "hook" and t > 0.15:
            a = ease((t - 0.15) / 0.35); paste_rgba(base, top, int(60 - (top.width + 60) * (1 - a)), 300)
        if mode == "date":
            a = ease(t / 0.3); paste_rgba(base, big, (W - big.width) // 2, int(900 + 80 * (1 - a)))
            b2 = ease((t - 0.25) / 0.3); paste_rgba(base, ask, (W - ask.width) // 2, int(680 - 60 * (1 - b2)))
        if mode == "end":
            pa = ease(t / 0.3); pn = Image.new("RGBA", (W, 760), INK + (int(238 * pa),)); base.alpha_composite(pn, (0, 620))
            a = ease(t / 0.4); paste_rgba(base, tape, (W - tape.width) // 2, int(700 - 200 * (1 - a)))
            b = ease((t - 0.5) / 0.4); paste_rgba(base, pill, (W - pill.width) // 2, int(1150 + 200 * (1 - b)))
            c2 = fnt("segoeuib.ttf", 40); d2 = ImageDraw.Draw(base); d2.text((W // 2, 1060), "LIKE  ·  SUBSCRIBE  ·  FOLLOW", font=c2, fill=CREAM + (255,), anchor="mm")
        return base
    return f


def pair_scene(keys):
    w0 = 470; ims = [POST[k] for k in keys]; hs = [int(w0 * im.height / im.width) for im in ims]; sh = [shadow(w0, h) for h in hs]
    cd = card("Leaving PS Plus · 17 Nov", "Red Dead Redemption 2  +  GTA V", "", 44)
    def f(t, dur):
        s = 1.0 + 0.04 * (t / max(dur, 0.1)); base = Image.fromarray(BG[keys[0]]).convert("RGBA")
        for i, (k, im) in enumerate(zip(keys, ims)):
            w, h = int(w0 * s), int(hs[i] * s); x = W // 2 + (-w - 20 if i == 0 else 20); y = 790 - h // 2
            slide = int(120 * (1 - ease((t - 0.08 * i) / 0.35))) * (-1 if i == 0 else 1)
            paste_rgba(base, rounded(im.resize((w, h), Image.LANCZOS)), x + slide, y)
        a = ease(t / 0.35); paste_rgba(base, cd, int(60 - (cd.width + 60) * (1 - a)), 1430)
        return base
    return f
SC = {"hook": grid_scene("hook"), "date": grid_scene("date"), "end": grid_scene("end")}
TLJ = json.load(open(CUES, encoding="utf8")); ev = TLJ["events"]; total = TLJ["duration"] + 1.0
tl = []
for i, e in enumerate(ev):
    s0 = 0.0 if i == 0 else e["t"]; e0 = total if i + 1 == len(ev) else ev[i + 1]["t"]
    tl.append((s0, e0, poster_scene(e["key"]) if e["scene"] == "poster" else (pair_scene(["rdr2", "gta5"]) if e["scene"] == "pair" else SC[e["scene"]])))
XF = 0.15
print("picture", round(total, 2), "s,", len(tl), "shots")

def frame(t):
    for i, (s, e, fn) in enumerate(tl):
        if s <= t < e or i == len(tl) - 1:
            a = fn(t - s, e - s)
            if i + 1 < len(tl) and t > e - XF:
                nx = tl[i + 1]; b = nx[2](max(0.0, t - nx[0]), nx[1] - nx[0])
                a = Image.blend(a, b, (t - (e - XF)) / XF)
            return a
vid = OUT.with_suffix(".silent.mp4")
enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                        "-c:v", "h264_nvenc", "-preset", "p5", "-rc", "vbr", "-cq", "20", "-b:v", "12M", "-maxrate", "18M", "-bufsize", "30M", "-pix_fmt", "yuv420p", str(vid)], stdin=subprocess.PIPE)
n = int(total * FPS)
for k in range(n):
    enc.stdin.write(frame(k / FPS).convert("RGB").tobytes())
enc.stdin.close(); enc.wait()

# ---- audio: voice over one low music bed (ducked), -14 LUFS ----
af = (f"[0:a]aformat=sample_rates=48000:channel_layouts=stereo,loudnorm=I=-24:TP=-3:LRA=7,afade=t=in:d=0.8,afade=t=out:st={total-1.6:.2f}:d=1.6,atrim=0:{total:.2f}[m];"
      f"[1:a]aformat=sample_rates=48000:channel_layouts=stereo,apad=whole_dur={total:.2f},asplit=2[v1][v2];"
      f"[m][v1]sidechaincompress=threshold=0.05:ratio=4:attack=20:release=400[md];[md][v2]amix=inputs=2:normalize=0:duration=longest,loudnorm=I=-14:TP=-2.5:LRA=9[a]")
mix = OUT.with_suffix(".m4a")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", "21", "-i", str(MUS), "-i", str(VOICE), "-filter_complex", af, "-map", "[a]", "-t", f"{total:.2f}", "-ar", "48000", "-c:a", "aac", "-b:a", "256k", str(mix)], check=True)
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(vid), "-i", str(mix), "-map", "0:v", "-map", "1:a", "-c", "copy", "-t", f"{total:.2f}", "-movflags", "+faststart", str(OUT)], check=True)
print("done", OUT)
