"""Shorts/Reel cover 1080x1920 from the official posters used in the video. uv run --with pillow --with numpy cover.py OUT.jpg"""
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageFont
import numpy as np
OUT = sys.argv[1]; ART = (Path.home() / "Videos/pipeline/ps-nov26/art"); F = "C:/Windows/Fonts/"
W, H = 1080, 1920; RED = (224, 53, 43); CREAM = (243, 234, 215); INK = (22, 19, 15)
def cover(im, w, h):
    s = max(w / im.width, h / im.height); im = im.resize((int(im.width * s) + 1, int(im.height * s) + 1), Image.LANCZOS)
    x, y = (im.width - w) // 2, (im.height - h) // 2; return im.crop((x, y, x + w, y + h))
rdr = Image.open(ART / "rdr2.jpg").convert("RGB"); gta = Image.open(ART / "gta5.jpg").convert("RGB")
bg = cover(rdr, 270, 480).filter(ImageFilter.GaussianBlur(40)).resize((W, H), Image.BICUBIC)
bg = Image.fromarray((np.asarray(bg, dtype=np.float32) * 0.45).astype(np.uint8)).convert("RGBA")
def shadow(w, h, r=0):
    s = Image.new("RGBA", (w + 200, h + 200), (0, 0, 0, 0)); ImageDraw.Draw(s).rectangle((100, 120, 100 + w, 120 + h), fill=(0, 0, 0, 210)); return s.filter(ImageFilter.GaussianBlur(28))
def poster(im, w, rot):
    h = int(w * im.height / im.width); p = im.resize((w, h), Image.LANCZOS).convert("RGBA")
    # thin cream paper border like a printed poster
    bd = Image.new("RGBA", (w + 16, h + 16), CREAM + (255,)); bd.paste(p, (8, 8)); sh = shadow(w + 16, h + 16)
    canvas = Image.new("RGBA", sh.size, (0, 0, 0, 0)); canvas.alpha_composite(sh); canvas.alpha_composite(bd, (100, 100))
    return canvas.rotate(rot, expand=True, resample=Image.BICUBIC)
def tape(text, size, fill, ink, rot, pad=(46, 22)):
    f = ImageFont.truetype(F + "seguibl.ttf", size); d = ImageDraw.Draw(Image.new("RGB", (4, 4))); tw = d.textlength(text, font=f)
    w, h = int(tw + pad[0] * 2), int(size * 1.0 + pad[1] * 2); im = Image.new("RGBA", (w, h), fill + (255,)); dd = ImageDraw.Draw(im)
    dd.text((w // 2, h // 2 + 2), text, font=f, fill=ink + (255,), anchor="mm"); return im.rotate(rot, expand=True, resample=Image.BICUBIC)
def put(base, ov, cx, cy): base.alpha_composite(ov, (int(cx - ov.width / 2), int(cy - ov.height / 2)))
# posters sit in the safe band (y 0.16-0.70, x 0.06-0.80): two overlapping, GTA on top
put(bg, poster(rdr, 440, 3.5), 305, 960)
put(bg, poster(gta, 440, -3), 590, 1010)
# hook: red tape (big) + cream tape (count)
put(bg, tape("LEAVING 17 NOV", 104, RED, (255, 255, 255), -2.0), 462, 420)
put(bg, tape("12 PS PLUS GAMES", 64, CREAM, INK, 1.5), 450, 570)
bg.convert("RGB").save(OUT, "JPEG", quality=92, subsampling=0, progressive=True, optimize=True)
