# Engine

Read this when something is broken or the user wants to retrain. Not needed to render.

## What it is

- **Model:** `ai4bharat/IndicF5` (F5-TTS DiT, 0.4B, MIT licence, gated on Hugging Face: the user accepted the terms on their own account).
- **Fine-tune (v3, live):** trained on the user's own recordings: 426 clips, about 40 minutes. That is 144 Hinglish clips with Devanagari transcripts, the 101 original English clips (once with Latin text and once with a Devanagari transcript) and 80 newer English clips recorded with Devanagari transcripts. 2500 steps, 8-bit AdamW, learning rate 1e-5, micro-batch 1 with 4-step accumulation (fits in about 6 GB). Checkpoint: `C:/voice/hindi/ft3/step_2500.pt` (a `CFM` state dict loaded over the stock weights). The user compared it with v2 by ear and chose it. `ft2/step_2000.pt` (Hinglish plus Latin English only) is kept as a backup: set `checkpoint` in `config.json` to go back.
- **Why not Qwen3-TTS:** it has no Hindi. Hinglish through it sounded like someone who could not speak Hindi. It is still installed in the `qwen3-tts` env but is not used here.
- **Env:** `<your-indicf5-env>` (Python 3.10, torch 2.11 cu128, `transformers==4.49.0`).

## Why the pins exist

| Pin | Reason |
| --- | --- |
| `transformers 4.49.0` | 5.x creates the model on a meta device and IndicF5's remote code crashes. |
| `huggingface_hub < 1.0`, `datasets < 4` | match that transformers. |
| `torchaudio.load` replaced by soundfile | torchaudio 2.11 needs the TorchCodec package. `engine.py` installs the patch. |
| `bitsandbytes` | 8-bit AdamW, so a fine-tune fits in 8 GB. |

## Files

| Path | What |
| --- | --- |
| `C:/voice/hindi/ft3/step_*.pt` | Fine-tune checkpoints. `step_2500.pt` is live. `ft2/step_2000.pt` is the previous voice (backup). |
| `C:/voice/hindi/english_deva.txt`, `train_en_new.jsonl`, `record_english.py` | Devanagari transcripts of the first 101 English clips, the newer English clips, and their recorder. |
| `C:/voice/hindi/cache/` | Render cache keyed by checkpoint, reference, text and seed. Safe to delete. |
| `C:/voice/hindi/finetune_indicf5.py` | The fine-tune script. |
| `C:/voice/hindi/record_extra.py`, `train_hi_extra.jsonl`, `hinglish_deva.txt` | Recorder and the Devanagari transcripts. |
| `C:/voice/Qwen3-TTS/finetuning/data/` | The user's recordings. Never upload them. |
| `skill/voice/refs/` | Reference clips and transcripts used at render time. |

## Performance on the 8 GB RTX 5070 laptop

- Model load: about one minute the first time per run.
- Generation: roughly real time or a little faster once loaded (7 s of speech rendered in about 7 s). Cached chunks cost nothing.
- Needs about 2.5 GB of VRAM free. A fine-tune peaks near 6 GB (micro-batch 1) and needs the GPU to itself: another GPU process (an ffmpeg encode, DaVinci) made one run ten times slower, from 0.5 to about 4 s per step. Check `nvidia-smi` for other GPU users first.
- Only one render process at a time (a lock file enforces it).

## Retraining

Only when the user asks, or after a limit that more data would fix. About 30 minutes of GPU.

1. Record more clips: `record_extra.py` pattern. Each clip needs its exact transcript, in Devanagari for Hindi. Do not invent transcripts. Use the user's mic, and check the printed `Mic:` line is the Fifine and not the laptop mic.
2. Add them to the training jsonl and run `finetune_indicf5.py <steps>` in the indicf5 env with `PYTHONUTF8=1`. It reads all the datasets listed above and writes `ft3/step_N.pt` (change `OUT` in the script for a new run so earlier checkpoints are kept).
3. Compare checkpoints by ear on the same lines, including the words that were wrong.
4. Point `config.json` `checkpoint` at the winner, run `calibrate`, then `selftest`.

Never overwrite the live checkpoint until the new one has been heard and approved.

## Limits to state honestly

- No emotion, pace or emphasis control. Notes from the script skill are ignored.
- Mispronunciation of words never seen in training is possible, especially English-origin words and names.
- English is the weakest part. The model is tuned for Indian languages, and the user judged Latin English bad. English cues therefore go through Devanagari with the Hindi reference. After training on 181 English-in-Devanagari clips (v3) the user judged English better. It still reads as Indian-accented English, and rare or unusual English words can come out wrong: respell, try seeds, or record more.
- Output varies by seed. Locks make a chosen take reproducible.
- The model is gated: a fresh machine needs the user to accept the terms and log in.
