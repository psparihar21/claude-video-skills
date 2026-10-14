# Platforms: sizes, layouts, checks

This file and the `PLATFORMS` table in `scripts/package.py` must agree. If one changes, change both.

| Request words | Key | Export | Ratio | Phone read-test width |
|---|---|---|---|---|
| YouTube thumbnail, thumbnail for a long video | `youtube` | 1280×720 JPG | 16:9 | 168 px (search / up next) |
| Shorts thumbnail, Shorts cover | `shorts` | 1080×1920 JPG | 9:16 | 180 px (Shorts shelf) |
| Instagram Reel cover | `reel` | 1080×1920 JPG | 9:16 | 130 px (profile grid, centre 3:4) |
| Instagram feed, Instagram post | `feed` | 1080×1350 JPG | 4:5 | 130 px (profile grid) |

All exports: JPG (progressive, 4:4:4 chroma when quality ≥ 85), sRGB, under 2 MB (2,097,152 bytes), exact pixel
size. No PNG unless the user asks for it.

## Layouts (fractions of width W and height H)
The renderer fits the hook to every allowed layout, then searches crop × layout together and keeps the
pair with the most subject in frame and the least subject under the actual text block.

### YouTube 1280×720
- Forbidden: x > 0.76W and y > 0.78H. That is the duration badge (plus the progress bar on hover).
- `left`   x 0.05–0.60, y 0.07–0.93 (left-aligned, vertically centred)
- `right`  x 0.40–0.95, y 0.07–0.76 (right-aligned, stops above the badge)
- `top`    x 0.05–0.95, y 0.06–0.44
- `bottom` x 0.05–0.74, y 0.54–0.94 (stops left of the badge)
- The text block may cover at most 30% of the canvas.

### Shorts and Reels 1080×1920
- Forbidden: the top 16%, the right 20%, and the bottom 30%. These hold the status bar and search, the like /
  comment / share rail, and the caption, handle and audio stack.
- `top` x 0.06–0.80, y 0.16–0.43. `bottom` x 0.06–0.80, y 0.43–0.70.
- The Reel profile grid shows the centre 3:4 (y 0.125–0.875). Both boxes sit inside it.
- The text block may cover at most 16% of the canvas. A vertical cover sells the frame, not a poster.

### Instagram feed 1080×1350
- A 6% margin on every side. No platform overlay.
- `top` x 0.06–0.94, y 0.06–0.46. `bottom` x 0.06–0.94, y 0.54–0.94. Text budget: 22%.

## Legibility rules (enforced)
- **Phone read test:** the hook's cap height must be at least 7 px at the read-test width above. That sets the
  smallest allowed size per platform and font. The fitter never goes below it. It refuses instead.
- **Contrast:** the scrim darkens the text band until white type reaches 4.5:1 against the 85th-percentile
  background luminance, up to 90% scrim. Below 3:1 is a hard fail. Type also carries a dark stroke (4.5% of size)
  and a soft shadow, so it holds on light and dark UI.
- **Highlight word:** drawn in the frame accent only if that accent reaches 3:1 on the scrim. Otherwise it uses
  yellow `#FFD84A`, then cyan. Never one that disappears.
- **Wrapping:** every split of the hook into 1–3 lines is tried. Bigger type wins, an extra line must buy more than
  12% size, and a line ending in a short function word ("to", "the", "my", "ka"…) is penalised.

## Fitting the frame
- Edit bars (black or flat bands from a zoomed-out clip) are trimmed before cropping (`trim_bars`, default on).
- Cover-crop only: never stretch, never letterbox. `focus: [x, y]` (0–1) overrides the automatic,
  subject-aware crop.
- Scale above 1.0 means **upscaled**. Say so with the factor. Lanczos plus a light unsharp mask, never an AI
  upscaler. Above 2.2× the report warns that it will look soft.
- Grade (`grade: "auto"`, or `"none"`): levels at 0.4/99.6%, never more than about 1.2× stretch, a gentle S-curve,
  vibrance that lifts muted colours most, and mild sharpening. It is still the real frame.

## Hard checks on every export
1. JPEG, RGB, exact W×H, under 2,097,152 bytes.
2. The type bounding box sits inside its layout box and touches no forbidden zone.
3. The hook contrast is at least 3:1, and it passes the phone read test.
4. The background is the real frame. No generated imagery.

`render` checks all four and writes `<out>.preview.jpg`: the cover with zones drawn, plus phone-size tiles on light
and dark UI. `check <jpg> --platform P` runs check 1 and the preview on any export, such as one from Canva. Look
at the preview for 2–4.
