# Writing Devanagari for this voice

The model was trained on Devanagari transcripts. Roman Hinglish fed straight in sounds like someone who does not speak Hindi. This was tested and was the original failure. So every Hindi or Hinglish cue is written in Devanagari before rendering.

The `draft` step converts the words in `assets/lexicon.json` and marks the rest `[[word]]`. The result is a draft. You must read it, finish it and save it with `set-deva`.

## Rules

1. **Hindi words** in Devanagari: `yeh bahut accha hai` -> `ये बहुत अच्छा है`.
2. **English-origin words** also in Devanagari, spelled the way a Hindi speaker says them: `video` -> `वीडियो`, `time` -> `टाइम`, `review` -> `रिव्यू`, `update` -> `अपडेट`, `performance` -> `परफ़ॉर्मेंस`. Do not leave them in Latin letters inside a Hindi cue. The linter fails on that.
3. **Spelling convention**: use the nukta where it is standard (ज़, फ़, ग़, ख़, ड़) the way the training transcripts do: `ज़रूर`, `फ़ोन`, `ख़ुशी`, `ज़्यादा`, `सिर्फ़`.
4. **Punctuation**: end every sentence with `।` (or `?` `!`). Commas mark the pauses the user's own recordings had. Do not stack punctuation, and do not use dashes or ellipses for rhythm: they are normalised away.
5. **Numbers are words**, never digits. Common ones: 1 एक, 2 दो, 3 तीन, 4 चार, 5 पाँच, 6 छह, 7 सात, 8 आठ, 9 नौ, 10 दस, 11 ग्यारह, 12 बारह, 15 पंद्रह, 20 बीस, 25 पच्चीस, 30 तीस, 40 चालीस, 50 पचास, 60 साठ, 70 सत्तर, 80 अस्सी, 90 नब्बे, 100 सौ, 1000 हज़ार, लाख, करोड़. For the other numbers between 21 and 99 spell them carefully from the Hindi forms and flag them for the user to listen to.
6. **Acronyms** (FPS, RTX, GPU, CPU, RAM, SSD, USB, AI, PC) may stay in Latin: the linter allows them. If they sound wrong, write them as letters: `एफ़पीएस`.
7. **Names and brands**: write them phonetically in Devanagari. Use the source's `pronounce` entry if there is one. Ask the user only if the name is central to the video.
8. **Ambiguous words**: `to` is `तो`, `ki` is `कि` or `की`, `main` is `मैं`, `is` is `इस`, `hi` is `ही`. Decide from the sentence. If the sentence is genuinely English, the whole cue is probably an English cue.
9. **Do not change the meaning.** Convert the spelling only. Gender, tense and word choice stay exactly as the script has them.
10. **English cues are transliterated too.** The user tested Latin text (other seeds, other English references) against English written in Devanagari with the Hindi reference, and chose the Devanagari version. It reads as Indian-accented English in their voice. Write what a Hindi speaker would say, one English word at a time, with `ज़` for z, `फ़` for f, and a final `्` where the English word ends in a consonant cluster:

    | English | Devanagari |
    | --- | --- |
    | Most players lose the match before it starts. | मोस्ट प्लेयर्स लूज़ द मैच बिफ़ोर इट स्टार्ट्स। |
    | They push one knock, while the zone is still twenty seconds away. | दे पुश वन नॉक, वाइल द ज़ोन इज़ स्टिल ट्वेंटी सेकंड्स अवे। |

    Numbers stay as words, here in English ("twenty" -> `ट्वेंटी`). Keep punctuation exactly as the English sentence has it: commas are the pauses. `--english-as latin` restores Latin text with the English reference; it was judged worse.

## Approved spellings

| Word | Spelling | Source |
| --- | --- | --- |
| waste | `वेस्ट` | approved by the user after A/B tests against `वैस्ट`, `वेईस्ट`, `वेस्टट` and the Latin word |

Saved in `assets/lexicon.json` under `approved_by_user`. Never replace an approved spelling. `lint --fix` rewrites known-bad spellings (`avoid`) to the approved one.

When the user approves a new spelling, record it:

```powershell
ovr.ps1 lexicon waste वेस्ट --kind loanword --approved
```

## When a word sounds off

The linter and QA cannot hear. Only the user can. Work through these in order and render only the affected cue (`render --only cXX`):

1. **Respell** one letter at a time and render each variant of a short test sentence, so the user can compare: shorter or longer vowel, a different consonant cluster. Send the variants labelled with their spelling.
2. **Seeds:** `candidates --seeds 1-6`. The same text gives a different take per seed.
3. **A different reference clip:** the model copies the reference's delivery. A clip where the user says the troublesome word correctly fixed `वेस्ट` after six seeds had failed. See `qa.md`.
4. **More data:** if the pattern never appeared in training (a word in a position the user never recorded), the fix is more recordings of it and a retrain. Say so. Do not promise a spelling trick will fix it.

Record what worked in the lexicon, so it never has to be solved twice.
