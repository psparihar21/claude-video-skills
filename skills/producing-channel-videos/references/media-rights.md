# Media rights

Every visual and every sound in the video needs a row in the shot list or rights log with a source and a licence that allows commercial YouTube use and the edit planned. This is the step where channels get strikes, so the rules are fixed.

## Source priority

1. **User's clip.** Ask the user to confirm they own it or can license it for this video. Log as `owned by user` or the licence they name.
2. **Connected licensed library.** Only if its licence allows commercial use on YouTube and the planned edit (crop, speed, overlay). Save licence proof (licence page name and asset ID, or the download receipt) to `rights/` and reference it in the row.
3. **Public domain or CC.** Public domain, CC0, CC BY, or CC BY-SA. Not NC (non-commercial) and not ND (no derivatives) when editing. Copy the required attribution into the row and the description.
4. **Generated shot.** Made for this video with an enabled generation tool. If a viewer could take it for a real event, real place at a real moment, or a real person, mark `Realistic synthetic: yes`, fill the Disclosure column, and add the YouTube altered-or-synthetic disclosure at upload. Never generate an identifiable real person, including the reference creator.
5. **Filming brief.** Subject, action, framing, duration, location, lighting. Precise enough that the user can shoot it without asking.

## Gameplay and trailers

Order, best first:

1. **User's own recording** (OBS or console capture). Ask for it whenever the video needs specific moments.
2. **Publisher or developer press kit / media page** downloads (trailers, b-roll, screenshots).
3. **Official trailer or gameplay video from the publisher's or developer's own verified YouTube channel or website**, downloaded fresh from that official upload.

Rules:
- Never take gameplay, trailer cuts, or screenshots from the reference / research video, and never from another creator's video, let's play, stream, or review. Go to the official upload. Where possible, choose different moments than the reference showed.
- Before using official footage, look up the publisher's content or video policy (e.g. "game content usage rules", press-kit terms) and log the policy URL in Proof. If no policy is found, log `policy: not found` and ask the user before using it.
- Mute trailer music by default. Trailers often carry licensed songs that trigger Content ID. Keep trailer dialogue or SFX only if the policy covers it. Lay the user's licensed bed instead.
- Keep each clip short and under the user's commentary. Do not re-upload a trailer in one piece.
- Credit every clip on screen ("Footage: <Game> / <Publisher>, official trailer") and in the description with a link to the official video or channel.
- YouTube's terms restrict downloading videos. Prefer a press-kit file when one exists. Save the original URL in the rights log either way.

## Editorial screenshots (news articles, Instagram, X)

- Capture with the browser while discussing the post or article, with outlet or handle and date visible. Screenshot the post itself, not media extracted out of it.
- Crop to the part being discussed. Blur names, faces, and handles of private individuals who are not the subject.
- Show it on screen only while the voice discusses it, as commentary evidence, not decoration.
- Credit on screen (outlet or @handle) and link it in the description.
- Do not capture paywalled articles in full.
- Log as `editorial-screenshot` with License `commentary (fair use / fair dealing), user accepted`. This is a fair-use judgement, not a licence: the user decides whether to rely on it.

## Hard bans

- No frame, crop, zoom, speed change, reverse, screenshot, or regrade from the reference file or its URL.
- No audio from it: music, stem, SFX, room tone, voice.
- No downloading someone else's YouTube video to reuse picture or sound, including a few seconds. The only exception is official publisher or developer uploads under "Gameplay and trailers" above, and never the reference itself.
- No trending audio, film score, or song without a commercial licence in the rights log.
- No voice clone or likeness of the reference creator or anyone else.
- A clone of the user's own voice only after the user approves that exact voice (name/ID in the tool) in this chat. Log it as `user-clone: <voice name>` with `Approved: yes`.
- A stock synthetic voice (preset or designed, not modelled on any real person) is allowed after the user picks it for this video. Log it as `stock-tts: <engine> <voice>` with the model's licence and `Approved: yes`. Never feed another person's recording into a TTS reference slot.
- No footage from the user's own channel if its picture or sound came from the reference.

Searching anywhere is fine. Using unlicensed media is not.

## "Just take it from YouTube"

Ask one question: does the user own that video, or does it carry an explicit reuse licence (e.g. CC BY shown on the video page)? If yes, log the licence. If no or unsure, do not download. Offer: stock search, a generated shot, or a filming brief, and wait.

## Refusal paragraph (when asked to use the reference's B-roll, music, or voice)

One short paragraph, then alternatives. Example:

> I won't pull B-roll or music from that video. It's the creator's footage and their licensed track, so using it on your channel risks a Content ID claim or strike, and it isn't ours to license. Here's what I can do instead: search rights-cleared stock for each shot, generate the two abstract shots, and write a filming brief for the desk close-ups. For music I can find a commercially licensed bed at the same energy.

Then continue the rest of the job.

## Rights-log rules (checked by `check_package.py`)

- Every music and SFX row has a licence.
- Every voice row is `user-recorded`, `user-clone: <name>`, or `stock-tts: <engine> <voice>`, with `Approved: yes` for clone and stock rows. Stock rows carry the model licence.
- Every gameplay or screenshot row has a source starting `user-recorded`, `press-kit:`, `official:`, or `editorial-screenshot:`, a credit in Attribution, and a policy URL (or `policy: not found`) in Proof.
- No source cell matches the reference file name, the reference URL, or its video ID.
- Generated realistic rows have a disclosure.
- An empty shot goes to `missing-items.md`, not to the reference.
