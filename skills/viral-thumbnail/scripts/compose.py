"""Compose a 1280x720 YouTube thumbnail: big art + extruded title + chips + round face badge.
usage: uv run --with pillow python compose.py brief.json
Paths in the brief are relative to the brief's folder. Output is JPEG under 2 MB.
Brief keys (all optional except art and out):
  art, out, size [1280,720], art_zoom 1.18, art_y 0.045 (fraction of scaled height trimmed from the top)
  dark_left {"alpha":170,"width":620}  left-side darkening so white type reads
  grade {"contrast":1.12,"color":1.15}
  vignette 0.35
  title [{"text","x","y","size","color"}]  (Impact; 2-3 short lines; hook <= 3 words per line)
  extrude {"color":"#ff6246","depth":7}  chunky offset shadow behind title (channel look)
  chips [{"text","x","y","size","bg","fg","pad_x","h"}]
  face {"path","size":290,"margin":[34,30],"ring":"#d6ff3a","ring_w":10,"crop":[x0,y0,x1,y1] or null}
"""
import json, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter

IMPACT = "C:/Windows/Fonts/impact.ttf"


def rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def main(path):
    p = Path(path)
    b = json.loads(p.read_text(encoding="utf-8"))
    rel = lambda s: str((p.parent / s).resolve())
    W, H = b.get("size", [1280, 720])
    art = Image.open(rel(b["art"])).convert("RGB")
    z = b.get("art_zoom", 1.18)
    sw = int(W * z)
    sh = int(sw * art.height / art.width)
    art = art.resize((sw, sh), Image.LANCZOS)
    y0 = int(sh * b.get("art_y", 0.045))
    x0 = int(b.get("art_x", 0))
    art = art.crop((x0, y0, x0 + W, y0 + H))
    dl = b.get("dark_left", {"alpha": 170, "width": 620})
    grad = Image.new("L", (W, H), 0)
    gd = ImageDraw.Draw(grad)
    for x in range(W):
        gd.line([(x, 0), (x, H)], fill=int(max(0, dl["alpha"] * (1 - x / dl["width"]))))
    art = Image.composite(Image.new("RGB", (W, H), (4, 6, 14)), art, grad)
    g = b.get("grade", {"contrast": 1.12, "color": 1.15})
    art = ImageEnhance.Contrast(art).enhance(g["contrast"])
    art = ImageEnhance.Color(art).enhance(g["color"])
    v = b.get("vignette", 0.0)
    if v:
        m = Image.new("L", (W, H), 0)
        ImageDraw.Draw(m).ellipse((-W * 0.25, -H * 0.25, W * 1.25, H * 1.25), fill=255)
        m = m.filter(ImageFilter.GaussianBlur(120))
        dark = Image.new("RGB", (W, H), (0, 0, 0))
        art = Image.composite(art, Image.blend(art, dark, v), m)
    d = ImageDraw.Draw(art)
    ex = b.get("extrude")
    for t in b.get("title", []):
        f = ImageFont.truetype(IMPACT, t["size"])
        if ex:  # offset layers first, so the shadow sits behind the white type
            for k in range(ex.get("depth", 7), 0, -1):
                d.text((t["x"] + k, t["y"] + k), t["text"], font=f, fill=rgb(ex["color"]),
                       stroke_width=10, stroke_fill=rgb(ex["color"]))
        d.text((t["x"], t["y"]), t["text"], font=f, fill=rgb(t.get("color", "#ffffff")),
               stroke_width=10, stroke_fill=(0, 0, 0))
    for c in b.get("chips", []):
        f = ImageFont.truetype(IMPACT, c.get("size", 54))
        px = c.get("pad_x", 22)
        w = int(d.textlength(c["text"], font=f)) + 2 * px
        h = c.get("h", int(c.get("size", 54) * 1.55))
        d.rounded_rectangle((c["x"], c["y"], c["x"] + w, c["y"] + h), 16, fill=rgb(c["bg"]))
        bb = d.textbbox((0, 0), c["text"], font=f)
        d.text((c["x"] + px - bb[0], c["y"] + (h - (bb[3] - bb[1])) // 2 - bb[1]), c["text"], font=f, fill=rgb(c["fg"]))
    fc = b.get("face")
    if fc:
        s = fc.get("size", 290)
        im = Image.open(rel(fc["path"])).convert("RGB")
        if fc.get("crop"):
            im = im.crop(tuple(fc["crop"]))
        side = min(im.size)
        im = im.crop(((im.width - side) // 2, (im.height - side) // 2, (im.width + side) // 2, (im.height + side) // 2)).resize((s, s), Image.LANCZOS)
        im = ImageEnhance.Contrast(im).enhance(1.06)
        m = Image.new("L", (s, s), 0)
        ImageDraw.Draw(m).ellipse((0, 0, s - 1, s - 1), fill=255)
        mx, my = fc.get("margin", [34, 30])
        cx, cy = W - s - mx, H - s - my
        rw = fc.get("ring_w", 10)
        glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(glow).ellipse((cx - rw - 8, cy - rw - 8, cx + s + rw + 8, cy + s + rw + 8), fill=rgb(fc.get("ring", "#d6ff3a")) + (150,))
        glow = glow.filter(ImageFilter.GaussianBlur(14))
        art = Image.alpha_composite(art.convert("RGBA"), glow).convert("RGB")
        d = ImageDraw.Draw(art)
        d.ellipse((cx - rw, cy - rw, cx + s + rw, cy + s + rw), fill=rgb(fc.get("ring", "#d6ff3a")))
        art.paste(im, (cx, cy), m)
    out = rel(b["out"])
    q = 92
    while True:
        art.save(out, quality=q, subsampling=0)
        if Path(out).stat().st_size < 2_000_000 or q <= 70:
            break
        q -= 4
    print(out, art.size, Path(out).stat().st_size, "bytes")


if __name__ == "__main__":
    main(sys.argv[1])
