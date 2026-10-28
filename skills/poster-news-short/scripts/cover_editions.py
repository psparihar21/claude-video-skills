"""uv run --with pillow --with numpy cover_gta.py OUT.jpg -> 1080x1920 Shorts/Reel cover from the official Rockstar art used in the video."""
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageFont
import numpy as np
OUT = sys.argv[1]; ART = (Path.home() / "Videos/pipeline/gta6-editions/art"); F = "C:/Windows/Fonts/"
W, H = 1080, 1920; RED = (224, 53, 43); CREAM = (243, 234, 215); INK = (22, 19, 15)
def cover(im, w, h):
    s = max(w / im.width, h / im.height); im = im.resize((int(im.width * s) + 1, int(im.height * s) + 1), Image.LANCZOS)
    x, y = (im.width - w) // 2, (im.height - h) // 2; return im.crop((x, y, x + w, y + h))
std = Image.open(ART / "trailer-1.06b6paykx247w.jpg").convert("RGB"); ult = Image.open(ART / "ultimate_mobile_en_us.03~7e7tlo4k4r.jpg").convert("RGB")
bg = cover(std, W // 6, H // 6).filter(ImageFilter.GaussianBlur(5)).resize((W, H), Image.BICUBIC)
bg = Image.fromarray((np.asarray(bg, dtype=np.float32) * 0.5).astype(np.uint8)).convert("RGBA")
def shadow(w, h):
    s = Image.new("RGBA", (w + 200, h + 200), (0, 0, 0, 0)); ImageDraw.Draw(s).rectangle((100, 120, 100 + w, 120 + h), fill=(0, 0, 0, 210)); return s.filter(ImageFilter.GaussianBlur(28))
def poster(im, w, rot):
    h = int(w * im.height / im.width); p = im.resize((w, h), Image.LANCZOS).convert("RGBA")
    bd = Image.new("RGBA", (w + 16, h + 16), CREAM + (255,)); bd.paste(p, (8, 8)); sh = shadow(w + 16, h + 16)
    c = Image.new("RGBA", sh.size, (0, 0, 0, 0)); c.alpha_composite(sh); c.alpha_composite(bd, (100, 100)); return c.rotate(rot, expand=True, resample=Image.BICUBIC)
def tape(text, size, fill, ink, rot, pad=(40, 20)):
    f = ImageFont.truetype(F + "seguibl.ttf", size); d = ImageDraw.Draw(Image.new("RGB", (4, 4))); tw = d.textlength(text, font=f)
    w, h = int(tw + pad[0] * 2), int(size + pad[1] * 2); im = Image.new("RGBA", (w, h), fill + (255,))
    ImageDraw.Draw(im).text((w // 2, h // 2 + 2), text, font=f, fill=ink + (255,), anchor="mm"); return im.rotate(rot, expand=True, resample=Image.BICUBIC)
def put(base, ov, cx, cy): base.alpha_composite(ov, (int(cx - ov.width / 2), int(cy - ov.height / 2)))
# safe band: x 0.06-0.80, y 0.16-0.70
put(bg, poster(std, 440, 3.0), 300, 930)
put(bg, poster(ult, 440, -3.0), 590, 990)
put(bg, tape("WORTH ₹1,500 MORE?", 76, RED, (255, 255, 255), -2.0), 450, 470)
put(bg, tape("GTA 6 STANDARD VS ULTIMATE", 44, CREAM, INK, 1.5), 450, 600)
put(bg, tape("₹5,999", 54, CREAM, INK, -3), 280, 1290)
put(bg, tape("₹7,499", 54, RED, (255, 255, 255), 3), 620, 1330)
bg.convert("RGB").save(OUT, "JPEG", quality=92, subsampling=0, progressive=True, optimize=True)
