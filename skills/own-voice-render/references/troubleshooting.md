# Troubleshooting

Run `ovr.ps1 doctor` first. Most problems show up there.

| Symptom | Cause | Fix |
| --- | --- | --- |
| `403` / "gated repo" / "not in the authorized list" | The user has not been granted IndicF5 access, or is not logged in. | The user opens the model page on huggingface.co and accepts the conditions, then runs `hf auth login` in their own terminal. Never take or paste a token. If the weights are already cached, rendering works offline. |
| `Tensor on device cpu is not on the expected device meta` | `transformers` 5.x. | `pip install "transformers==4.49.0" "huggingface_hub<1.0" "datasets<4"` in the indicf5 env. |
| `TorchCodec is required` | torchaudio's loader. | Always run through `ovr.ps1`/`ovr.py`: it patches the loader. Do not call the model from a bare script. |
| `only X GB of VRAM free` / CUDA out of memory | Another app holds the GPU. | Close DaVinci Resolve, browsers with video, any training run. Retry. |
| `another own-voice-render process (pid N) is using the GPU` | A render is running, or crashed holding the lock. | Wait for it. If the process is gone, delete `~/.cache/own-voice-render/gpu.lock`. |
| `blocked by lint errors` | Digits, Latin in a Hindi cue, `[[unresolved]]`, unreviewed draft, a character the model never saw. | Fix the text. `lint` prints each cue and reason. |
| `characters the model has never seen` | A symbol outside the 2545-symbol vocab (emoji, rare scripts). | Remove it or respell it in plain Devanagari/Latin. |
| `OVERFLOW cNN ... shorten the line by ~X s` (exit 3) | The line reads longer than its window even at 1.12x. | Report it. The script skill shortens the line. Or widen the window. `--allow-overflow` only to preview. |
| `COLLISION` | A cue runs into the next cue's start. | Same as overflow: shorten, or move the next cue. |
| QA `too-fast` / `too-slow` | The take rushed or dragged. | The engine already tried four seeds. Run `candidates`, or respell, or split the sentence. |
| QA `mostly-silence` | The model emitted a gap. | Usually fixed by another seed. Check the text for odd characters. |
| English cue sounds bad | Latin English text goes through a model with little English data. | Use the default (`--english-as devanagari`) and transliterate. If you used `--english-as latin`, the English reference must be an English one: a Hindi reference makes English a third of its proper length. |
| A Hindi word sounds like an English speaker said it | The word was left in Latin letters or spelled unlike training. | Devanagari, phonetic: see `devanagari.md`. |
| One word is wrong, everything else is fine | A word the model learned imperfectly. | The fix loop in `devanagari.md`: respell, seeds, other reference, more data. |
| `ffmpeg not found` | Not on PATH in this shell. | `winget install Gyan.FFmpeg`, or set `ffmpeg` in `config.json`. |
| Output louder or quieter than -16 LUFS | Very short or very sparse tracks can't reach the target within the true-peak limit. | Check `report.json` `audio`. A deviation under about 1.5 LU is expected on short clips. |
| Render is slow | Model load, or a cold cache. | About a minute to load. Reruns of the same text are instant. |
| Cache seems stale after retraining | It is keyed by the checkpoint's name, size and time, so it cannot go stale. | If in doubt, delete `C:/voice/hindi/cache/`. |

If something fails that is not listed: capture the full error, run `doctor`, and report both. Do not retry in a loop, and do not delete the cache, the checkpoint or the user's recordings to "fix" it.
