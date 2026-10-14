# Ear test

Run this after `validate_script.py` exits 0. The script can pass the numbers and still sound like a language model. Fix the script, re-render, re-validate.

Read `02-script.md` aloud, under your breath, at the cue times. Then check:

1. **Hook.** The first sentence is a claim, a mistake, or a stake. It is not a topic announcement. A stranger who hears only that line knows why they should stay.
2. **Picture.** Mute the script in your head and imagine the frames. Anything the viewer can already see, cut. Anything you claimed that no frame showed, cut or mark `confidence` low and make the line generic.
3. **Mouth.** No sentence needs a second breath. No line twists so a TTS voice would stress the wrong word. Hindi spelling matches `references/language.md`.
4. **Register.** Indian English contains zero Hindi function words. Hinglish still makes sense as information if you listen for the English nouns, and does not make sense if you delete the Hindi turns. One register for the whole file.
5. **Silence.** Every text hold has a real gap, and the line before it has already landed. You are not talking over the card.
6. **Facts.** Every number still has a `fact_source` you could point at on screen or in the brief. No source, no number.
7. **Begging.** Likes, subscribes, "follow for part 2", and "comment mein batao" appear only on a CTA shot.
8. **Gameplay.** You can tell the story without naming a button. In story-over-gameplay, the game is mentioned at most twice in a short.
9. **Host.** The host is not on camera and is not the player, unless the brief said the voice is the player. No "welcome back to my channel".
10. **Read-aloud.** The record notes in `05-record-notes.md` mention any `mein` / `main` trap and the pace of the hook. A human can record from that file alone without opening the JSON.

If you change a word, you render and validate again. The reply to the user happens after that, not before.
