# video-packaging v2: test results and comparison

Tested 2026-10-15 on two real videos:
- **`desk-gta6-short.mp4`:** 20 s, 1080×1920 HEVC with audio. An edited Short with burned-in titles
  ("EMPTY DESK", "LOADING SETUP", the GTA VI logo, "NIGHT MODE", "MISSION PASSED") and zoom bars.
- **`1000203307.mp4`:** 58 s, 4K rotated phone footage, no audio.

## What v1 got wrong on real footage, and the v2 fix

| v1 failure (seen on the real videos) | v2 fix |
|---|---|
| Ranked frames with burned-in titles and the GTA logo first (#1 was "GTA VI / READY?"). | OCR (Windows built-in, or tesseract) runs on 2× pool frames **and their neighbours**. Clean frames are ranked first. Look-alike suppression runs only after the text check, so the clean night shot at 17.17 s is no longer dropped. |
| Exposure scoring punished moody RGB night shots. | Penalise only truly underexposed or blown frames, and weight colourfulness more. |
| 1 fps sampling missed short clean moments. | 4 fps, or up to 12 fps inside `--window`. |
| Sample times were off by half a sample. | Timestamps follow the fps filter (`i/fps`), and keyframe mode reads `pts_time`. |
| 4K analyze took 28 s, slower with `-hwaccel` (copying frames back from the GPU). | Software decode; keyframes only for heavy input; audio and frame grabs run in parallel. **4K: 28 s → 8 s.** |
| Centre crop: the YouTube cover from a vertical video put the hook over the monitor (52% of the subject covered). | Fit type to 4 layouts first, then search crop × layout against a saliency map. **Subject under type: 52% → 25%, and 41% → 13%.** |
| Edit bars (black bands) would be baked into the cover. | Auto-trim (`trim_bars`). |
| Thin plain eyebrow; a highlight word that vanished on a pink scene. | Filled accent tag; the highlight colour is chosen by measured contrast (frame accent → yellow → cyan). |
| Dangling line breaks ("EMPTY DESK TO / NIGHT MODE"). | Tries all ≤22 splits, with a penalty for short function words at line ends. |
| Hindi rendered in the regular weight; complex Devanagari would mis-shape silently. | Nirmala UI **Bold** (ttc face 1). Text needing ि or ् is refused when Pillow lacks raqm. |
| Canva: a flat rectangle scrim leaves a hard edge. | `background_only` bakes a soft scrim into the uploaded frame. Canva holds only editable text. |
| No legibility or contrast gate. | Hard gates: cap height ≥ 7 px at the real phone tile width; white type ≥ 3:1 (scrim aims for 4.5:1); safe zones. Plus a preview sheet with light and dark UI tiles. |

Final regression: 5/5 production renders pass, all 6 refusal and negative cases behave correctly, `check` passes
a good export and fails a wrong-size one, and the Canva path ran end to end up to an uncommitted preview.
Render time is about 1.5 s per cover.

## Compared with other thumbnail skills (read 2026-10-15)

| | **video-packaging v2** | [Samin12 claude-thumbnails](https://github.com/Samin12/claude-thumbnails) | [higgsfield generate-youtube-thumbnail](https://github.com/Schwarzkopf/higgsfield-claude-code/blob/main/skills/generate-youtube-thumbnail/SKILL.md) | [charlie947 youtube-thumbnail](https://github.com/charlie947/social-media-skills/blob/main/skills/youtube-thumbnail/SKILL.md) | [sergebulaev yt-thumbnail-brief](https://github.com/sergebulaev/youtube-skills/blob/main/skills/yt-thumbnail-brief/SKILL.md) | [pottertech thumbnail-design](https://github.com/pottertech/claude-skills/blob/main/youtube/thumbnail-design/SKILL.md) | [Namtanmk youtube-thumbnail](https://github.com/Namtanmk/Claude-Skills-Ultimate-Bundle/blob/main/Content%20%26%20Copywriting/youtube-thumbnail/SKILL.md) |
|---|---|---|---|---|---|---|---|
| Output | finished JPG | finished image | finished image | Gemini prompt | brief | brief | Canva design |
| Picture source | **real frame of the video** | Gemini generation + headshot | paid image model | Gemini | none | none | Canva generation |
| Matches the actual video | **guaranteed** | no | no | no | "must not show a moment not in the video" (by rule) | no | no |
| Reads the video | **yes**: ffprobe, scoring, OCR, audio | no | no | no | no | no | no |
| Burned-in text / logo avoidance | **OCR + visual gate** | n/a | n/a | n/a | n/a | n/a | n/a |
| Subject-aware crop | **saliency × layout search** | n/a | n/a | n/a | rule of thirds (advice) | face on a third (advice) | no |
| Platforms | YouTube, Shorts, Reel, feed | YouTube | YouTube | YouTube | YouTube | YouTube | YouTube |
| Safe zones | **enforced per platform** | bottom-right (advice) | no | bottom-right (advice) | none | bottom 25% (advice) | centre 80% (advice) |
| Phone legibility | **measured: 7 px cap at 168/180/130 px** | 320×180 (judged) | judged | 320/360 px (judged) | 120 px test (judged) | 168×94 (judged) | 168×94 (judged) |
| Contrast | **measured, auto scrim** | judged | judged | squint test | advice | advice | no |
| Export verification | **exit-code checks: size, bytes, zones, contrast** | `file` type check | no | inspect | spec list | none | 1280×720 / 2 MB |
| Preview on light and dark UI | **yes, automatic** | 2×2 grid | no | no | no | "white and dark" (judged) | no |
| Concepts per run | 1 (A/B ≤ 3 on request) | 4 | batch | 1 | 2–3 | 2–3 | 3 |
| Cost / keys | **free, offline**; Canva optional | Gemini + Scrape Creators keys | paid credits | Gemini | none | none | Canva |
| Speed | ~10 s analyze + ~1.5 s per render | model latency | model latency + polling | manual | instant | instant | Canva latency |
| Deterministic | **yes** | no | no | no | n/a | n/a | no |

### Where others are stronger, honestly
- **Invented drama.** Generators can stage exaggerated faces, arrows and impossible composites. This skill never
  does that, by design: the cover must be a moment that is in the video. If the footage has no strong frame, it
  says so instead of faking one.
- **Concept exploration.** Samin12 and pottertech give 3–4 directions by default. Here, variants are on request
  only, one variable at a time, which suits a single honest cover and YouTube Test & Compare.
- **Competitor research.** Samin12 can pull top-performing thumbnails in the niche (paid API). Not included.
- **Subject cut-out "pop"** (outline glow) is not done. It would need background removal on the frame.

### Ideas adopted from them
The phone-size read test (pottertech, sergebulaev, charlie947), the title-complements-not-repeats rule (all), one
focal point (sergebulaev), light and dark UI checks (pottertech), changing one element per A/B variant
(sergebulaev), and checking the export before handing over (charlie947, Samin12).

### Kept from v1 sources
ffprobe and accurate frame grabs (oaustegard), the contact sheet (ElSalvatore), the hard post-render check
(HyperFrames idea), 9:16 pass/fail (nopefallacy), and the Canva order with export checks (Namtanmk).
