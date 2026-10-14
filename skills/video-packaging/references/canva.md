# Canva Pro path

Use this when Canva tools are present. The background is always the user's own frame. The sequence below was
run end to end on 2026-10-15: upload, create, background replace, type restyle, and preview all worked.

## Tools (match on the suffix after the last `__`; prefixes differ by install)
| Step | Tool | Verified behaviour |
|---|---|---|
| Brand | `list-brand-kits` | Returns `{items:[{id}]}`. Canva requires asking the user before using a kit. |
| Upload | `create-upload-url`, then a raw-bytes POST | Responds `{"mediaId": "M…"}`. One URL per upload. It expires in about 30 minutes. |
| Create | `create-design` (`format`), then poll `get-create-design-async-job` | Wait 15 s, then about 10 s. "YouTube Thumbnail" comes back **1920×1080** (16:9). It holds a replaceable page background and the hook as text boxes. |
| Read / preview | `read-design` with `open_transaction: true`, fields `page_metadata`, `design_content`, `thumbnails` | Gives the transaction id, page locator, element locators and a preview. |
| Edit | `edit-design` (`keep_open`, then `commit` or `cancel`) | Each call returns an after-thumbnail. Compare it before any further edit. |
| Second size | `resize-design` `{type: custom, width, height}` | Pro. Creates a new design. |
| Fallback copy | `copy-design` | When resize is refused. |
| Export | `get-export-formats`, then `export-design` `{type: jpg, width, height, quality}` | Exports at the exact pixel size even though the canvas is 1920×1080. |

**Never call:** `generate-image`, `remove-background` (on the frame), autofill or brand-template dataset tools
(Enterprise), or `import-design-from-url` for the frame.

## Exact order
1. **Background, locally, with the scrim baked in.** Canva shapes cannot do gradients, and a flat rectangle
   leaves a hard edge. Run `package.py render` on a brief with `"background_only": true` (same frame, platform,
   side or `auto`). It writes the cropped, graded frame with a soft scrim on the type side, and reports `side` and
   `type_box_frac`. With no shell, upload the raw frame and use a 0.45-opacity black rectangle as the scrim.
2. **Brand kit.** Call `list-brand-kits`. If one exists, ask the user once: "Use your brand kit fonts and colours?"
   - If yes: use `generate-design` with `brand_kit_id` and `asset_ids: [mediaId]`, pick **one** candidate
     whose preview shows the frame, then `create-design-from-candidate`.
   - If no, or there is no kit: use `create-design` (step 4).
3. **Upload.** Call `create-upload-url`, then:
   `curl -sS -X POST -H "Content-Type: application/octet-stream" --data-binary "@bg.jpg" "<uploadUrl>"`
   and keep the `mediaId`. If the POST cannot run (no network from the sandbox), stop the Canva path. Ask the user
   to drag the frame into Canva Uploads.
4. **Create.** Call `create-design` with `format` "YouTube Thumbnail", "Instagram Reel" (also for Shorts), or
   "Instagram Post (Portrait)". Use this brief: "Plain <format> canvas. The background photo will be replaced with
   my uploaded video frame. One headline text box reading '<HOOK>'. No illustrations, people, icons or extra
   graphics." Poll until it completes.
5. **Rebuild on the frame.** Call `read-design` with `open_transaction`. Then one `edit-design` (`keep_open`):
   - `update_fill` with **locator = the page's locator_id** (the page background), `asset_id = mediaId`, and alt text
     "Frame from <video> at <t>s". Canva cover-fits it.
   - `delete_element` every generated image, sticker or illustration. Keep the generated hook text boxes.
   - `find_and_replace_text` to fix the wording. Use `format_text` for white (`#FFFFFF`), bold, and a size of at
     least the platform minimum × (canvas width / export width).
   - Use `position_element` to put the type inside `type_box_frac` × canvas size.
   - Eyebrow tag, if used: `insert_shape` a rounded rectangle in the accent, then `add_text` on top in black or white.
   - `layer_element` the text to `front`.
6. **Verify the after-thumbnail.** The background must be your frame, not a generated scene. Otherwise `cancel` and
   redo step 5. Type must sit inside the safe area and the YouTube bottom-right must be clear.
   **Show the preview and commit only after the user approves.**
7. **Second platform**, only if asked: `resize-design`, then reposition the type. If resize is refused, repeat steps
   1 and 3–6 for that size. Never use autofill.
8. **Export.** Call `get-export-formats`, then `export-design` with `{type: jpg, width: W, height: H, quality: 90}`.
   Download it, then:
   `uv run "${CLAUDE_SKILL_DIR}/scripts/package.py" check cover.jpg --platform <p>`
   If it is over 2 MB, export again at quality 80. Look at `cover.preview.jpg`.
9. **Hand-off.** Give the Canva link, the JPG path, size, byte count, and any upscale.

## Failure rules
- If a tool is missing, refused, or errors, name it and take the next fallback. Never claim a design exists
  without a design id and a preview you looked at.
- If Canva is not connected, say so ("Connect it under Settings → Connectors → Canva") and use the local renderer
  in Claude Code. Do not invent a thumbnail with an image model.
