"""uv run --with pillow --with numpy build.py [voice.wav]  -> final/short.silent.mp4
Picture follows the voice: edit TL start times (seconds in voice.wav, from voice.srt) and rebuild."""
import subprocess, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
J = (Path.home() / "Videos/pipeline/gta6-editions"); ART = J / "art"; OUT = J / "final"; OUT.mkdir(exist_ok=True)
VOICE = Path(sys.argv[1]) if len(sys.argv) > 1 else J / "vo2/out/voice.wav"
DUR = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(VOICE)]))
total = DUR + 0.9
W, H, FPS = 1080, 1920, 30; F = "C:/Windows/Fonts/"
WHITE = (238, 243, 246); INK = (22, 19, 15); CREAM = (243, 234, 215); RED = (224, 53, 43); GREY = (92, 98, 104)
ease = lambda x: 1 - (1 - min(max(x, 0), 1)) ** 3
SH = J / "shots"
FILES = {
 "key": ART / "poster_full.0az_iud2g3y4j.jpg", "ult": ART / "ultimate_mobile_en_us.03~7e7tlo4k4r.jpg", "t1": ART / "trailer-1.06b6paykx247w.jpg", "t2": ART / "trailer-2.0l.7aqib91fz6.jpg",
 "hotel": ART / "extended-look.0f0-3vo3w9u26.jpg", "leo": ART / "onlyInLeonidaMobile.0mupfnk-x6x~r.jpg", "launch": ART / "featured.0.fbrrtu5j-9_.jpg",
 "pack": SH / "vint/VINTAGE_VICE_CITY_PACK_01.jpg", "stanier": SH / "vint/VINTAGE_VICE_CITY_PACK_VAPID_STANIER_01.jpg", "looks": SH / "vint/VINTAGE_VICE_CITY_PACK_EXCLUSIVE_LOOKS_01.jpg", "wpat": SH / "vint/VINTAGE_VICE_CITY_WEAPON_PATTERN_01.jpg",
 "u1": SH / "ult/ULTIMATE_EDITION_01.jpg", "u2": SH / "ult/ULTIMATE_EDITION_02.jpg", "cheetah": SH / "ult/ULTIMATE_EDITION_GROTTI_CHEETAH_01.jpg", "rev": SH / "ult/ULTIMATE_EDITION_HAWK_AND_LITTLE_MORGAN_REVOLVERS_01.jpg",
 "wyman": SH / "ult/ULTIMATE_EDITION_WYMAN_CAR_COLLECTION_01.jpg", "ride": SH / "ult/ULTIMATE_EDITION_RIDEOUT_CUSTOMS_01.jpg", "sara": SH / "ult/ULTIMATE_EDITION_SARAS_SALON_01.jpg", "fang": SH / "ult/ULTIMATE_EDITION_ELECTRIC_FANG_01.jpg"}
def _ld(p):
    im = Image.open(p).convert("RGB")
    return im.resize((1920, int(1920 * im.height / im.width)), Image.LANCZOS) if im.width > 1920 else im
A = {k: _ld(p) for k, p in FILES.items()}
def fnt(n, s): return ImageFont.truetype(F + n, s)
def cover(im, w, h):
    s = max(w / im.width, h / im.height); im = im.resize((int(im.width * s) + 1, int(im.height * s) + 1), Image.LANCZOS)
    x, y = (im.width - w) // 2, (im.height - h) // 2; return im.crop((x, y, x + w, y + h))
def rounded(im, r=14):
    m = Image.new("L", im.size, 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, im.width - 1, im.height - 1), r, fill=255); o = im.convert("RGBA"); o.putalpha(m); return o
def shadow(w, h):
    im = Image.new("RGBA", (w + 160, h + 160), (0, 0, 0, 0)); ImageDraw.Draw(im).rounded_rectangle((80, 96, 80 + w, 96 + h), 16, fill=(0, 0, 0, 190)); return im.filter(ImageFilter.GaussianBlur(26))
def paste(base, ov, x, y):
    if x >= W or y >= H or x + ov.width <= 0 or y + ov.height <= 0: return
    base.alpha_composite(ov, (max(x, 0), max(y, 0)), (max(-x, 0), max(-y, 0)))
def spaced(d, xy, text, f, fill, track=3):
    x, y = xy
    for ch in text: d.text((x, y), ch, font=f, fill=fill); x += d.textlength(ch, font=f) + track
def card(label, title, detail="", size=60):
    fl, ft, fd = fnt("segoeuib.ttf", 24), fnt("seguibl.ttf", size), fnt("segoeui.ttf", 30)
    pr = ImageDraw.Draw(Image.new("RGB", (4, 4)))
    tw = max(pr.textlength(title, font=ft), sum(pr.textlength(c, font=fl) + 3 for c in label.upper()), pr.textlength(detail, font=fd) if detail else 0)
    w = int(tw + 100); h = 92 + size + (44 if detail else 0)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, w - 1, h - 1), 20, fill=WHITE + (255,)); d.rounded_rectangle((0, 0, 22, h - 1), 20, fill=INK + (255,)); d.rectangle((11, 0, 22, h - 1), fill=INK + (255,))
    spaced(d, (54, 24), label.upper(), fl, GREY); d.text((52, 56), title, font=ft, fill=INK + (255,))
    if detail: d.text((54, 56 + size + 14), detail, font=fd, fill=GREY + (255,))
    return im
def tape(text, size, fill, ink, rot, pad=(46, 22)):
    f = fnt("seguibl.ttf", size); d = ImageDraw.Draw(Image.new("RGB", (4, 4))); tw = d.textlength(text, font=f)
    w, h = int(tw + pad[0] * 2), int(size + pad[1] * 2); im = Image.new("RGBA", (w, h), fill + (255,))
    ImageDraw.Draw(im).text((w // 2, h // 2 + 2), text, font=f, fill=ink + (255,), anchor="mm"); return im.rotate(rot, expand=True, resample=Image.BICUBIC)
INKBG = Image.new("RGBA", (W, H), INK + (255,))
def backdrop(k):
    b = cover(A[k], 270, 480).filter(ImageFilter.GaussianBlur(14)).resize((W, H), Image.BICUBIC)
    return Image.fromarray((np.asarray(b, dtype=np.float32) * 0.42).astype(np.uint8)).convert("RGBA")
CARD_Y = 1150  # inside the safe band (above the bottom ~35 % the apps cover)
def art_scene(k, c, wide=False, bgk=None, fx=0.5):
    p = A[k]; full = p.height / p.width > 1.2
    def f(t, dur):
        s = 1.0 + 0.06 * (t / max(dur, 0.1)); base = Image.new("RGBA", (W, H), INK + (255,))
        if full:   # portrait art: full bleed, slow push-in
            w, h = int(W * s), int(H * s); im = cover(p, W, H) if s == 1.0 else cover(p, W, H).resize((w, h), Image.LANCZOS)
            paste(base, im.convert("RGBA"), (W - w) // 2, (H - h) // 2)
        else:      # landscape art: bg blur + a near-square crop (focal x = fx) filling the width
            base = backdrop(bgk or k).copy(); bw, bh = 1080, 1240
            sc = max(bw / p.width, bh / p.height) * s; w, h = int(p.width * sc), int(p.height * sc)
            im = p.resize((w, h), Image.LANCZOS); x0 = min(max(int((w - bw) * fx), 0), w - bw); y0 = (h - bh) // 2
            blk = im.crop((x0, y0, x0 + bw, y0 + bh)).convert("RGBA")
            sh = shadow(bw, bh); paste(base, sh, -80, 340 - 96); paste(base, blk, 0, 340)
        a = ease(t / 0.35); paste(base, c, int(60 - (c.width + 60) * (1 - a)), CARD_Y); return base
    return f
def hook_scene():
    t1 = tape("STANDARD OR ULTIMATE?", 66, RED, (255, 255, 255), -2.0); t2 = tape("WHAT THE EXTRA ₹1,500 GETS YOU", 44, CREAM, INK, 1.5)
    inner = art_scene("ult", Image.new("RGBA", (1, 1), (0, 0, 0, 0)))
    def f(t, dur):
        base = inner(t, dur)
        a = ease(t / 0.35); paste(base, t1, int((W - t1.width) / 2 - 500 * (1 - a)), 1080)
        b = ease((t - 0.2) / 0.35); paste(base, t2, int((W - t2.width) / 2 + 500 * (1 - b)), 1250); return base
    return f
def end_scene():
    keys = ["key", "cheetah", "t1", "looks", "hotel", "fang"]; tw, th = 330, 490
    tiles = [rounded(cover(A[k], tw, th), 10) for k in keys]
    ask = card("Tell me in the comments", "WHICH ONE ARE YOU GETTING?", "", 46)
    tp = Image.new("RGBA", (620, 150), CREAM + (255,)); ImageDraw.Draw(tp).text((310, 75), "PUSHPSTATION", font=fnt("seguibl.ttf", 78), fill=INK + (255,), anchor="mm"); tp = tp.rotate(2.5, expand=True, resample=Image.BICUBIC)
    pill = Image.new("RGBA", (520, 120), (0, 0, 0, 0)); d = ImageDraw.Draw(pill); d.rounded_rectangle((0, 0, 519, 119), 60, fill=RED + (255,)); d.text((260, 60), "SUBSCRIBE", font=fnt("seguibl.ttf", 58), fill=(255, 255, 255, 255), anchor="mm")
    def f(t, dur):
        base = INKBG.copy()
        for i, tl in enumerate(tiles):
            r, c = divmod(i, 3); x = 30 + c * (tw + 12) + (6 if c else 0); y = 140 + r * (th + 12)
            tt = Image.fromarray((np.asarray(tl, dtype=np.float32) * np.array([.35, .35, .35, 1])).astype(np.uint8)); paste(base, tt, x, y)
        a = ease(t / 0.35); paste(base, ask, (W - ask.width) // 2, int(300 - 80 * (1 - a)))
        b = ease((t - 0.15) / 0.4); paste(base, tp, (W - tp.width) // 2, int(760 - 200 * (1 - b)))
        d2 = ImageDraw.Draw(base); d2.text((W // 2, 1060), "LIKE  ·  SUBSCRIBE  ·  FOLLOW", font=fnt("segoeuib.ttf", 40), fill=CREAM + (255,), anchor="mm")
        c2 = ease((t - 0.5) / 0.4); paste(base, pill, (W - pill.width) // 2, int(1150 + 200 * (1 - c2))); return base
    return f
LEAD = 0.12  # picture lands just before the word (cue starts from voice.srt)
def wide(k, c, bgk=None, fx=0.5): return art_scene(k, c, wide=True, bgk=bgk or k, fx=fx)
TL = [  # (start s, scene); cue starts come from vo2/out/voice.srt, sub-shots are inside a cue
 (0.0, hook_scene()),
 (6.329 - LEAD, art_scene("t1", card("Standard · PS Store India", "₹5,999", "Full game + pre-order bonus pack"), bgk="t1")),
 (11.2, wide("pack", card("Pre-order bonus", "Vintage Vice City Pack", "Pre-order bonus on both editions", 50))),
 (15.752 - LEAD, wide("stanier", card("Pack includes", "1955 Vapid Stanier", "", 56))),
 (19.2, wide("looks", card("Pack includes", "Outfits for Jason & Lucia", "", 52))),
 (21.2, wide("wpat", card("Pack includes", "Exclusive weapon pattern", "", 52))),
 (22.821 - LEAD, wide("u1", card("Ultimate · PS Store India", "₹7,499", "Extra ₹1,500 over Standard", 64))),
 (25.3, wide("cheetah", card("Ultimate", "Grotti Cheetah", "", 60))),
 (27.1, wide("rev", card("Ultimate", "Hawk & Little Morgan Revolvers", "", 46))),
 (28.9, wide("wyman", card("Ultimate", "Classic car collection", "", 54))),
 (30.84 - LEAD, wide("ride", card("Ultimate shops", "Rideout Customs", "", 60))),
 (32.4, wide("sara", card("Ultimate shops", "Sara's Salon", "", 60))),
 (33.9, wide("fang", card("Ultimate shops", "Electric Fang Tattoo", "", 60), fx=0.35)),
 (35.927 - LEAD, wide("u2", card("The catch", "Only extras", "Same story in both editions", 58))),
 (39.224 - LEAD, wide("launch", card("Launch", "19 NOV 2026", "PS5 · Xbox Series X|S", 64), bgk="t2")),
 (44.047 - LEAD, end_scene()),
]
XF = 0.15
def frame(t):
    for i, (s, fn) in enumerate(TL):
        e = TL[i + 1][0] if i + 1 < len(TL) else total
        if s <= t < e or i == len(TL) - 1:
            a = fn(t - s, e - s)
            if i + 1 < len(TL) and t > e - XF:
                b = TL[i + 1][1](0.0, 99); a = Image.blend(a, b, (t - (e - XF)) / XF)
            return a
if __name__ == "__main__":
    vid = OUT / "short.silent.mp4"
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
      "-c:v", "h264_nvenc", "-preset", "p5", "-rc", "vbr", "-cq", "20", "-b:v", "12M", "-maxrate", "18M", "-bufsize", "30M", "-pix_fmt", "yuv420p", str(vid)], stdin=subprocess.PIPE)
    for k in range(int(total * FPS)): enc.stdin.write(frame(k / FPS).convert("RGB").tobytes())
    enc.stdin.close(); enc.wait(); print("picture", round(total, 2), "s")
