"""GPU rendering for own-voice-render: IndicF5 fine-tuned on the user's voice.

Loads the model once, renders chunk by chunk with a content-addressed cache and a
seeded QA retry loop. Run only through ovr.py (needs the indicf5 env).
"""
from __future__ import annotations

import os
import sys
import time
from pathlib import Path

import numpy as np
import soundfile as sf

sys.path.insert(0, str(Path(__file__).resolve().parent))
import core  # noqa: E402

LOCK = Path.home() / ".cache" / "own-voice-render" / "gpu.lock"


class GpuBusy(SystemExit):
    pass


def acquire_lock() -> None:
    """One render at a time: an 8 GB card cannot hold two copies of the model."""
    LOCK.parent.mkdir(parents=True, exist_ok=True)
    if LOCK.exists():
        try:
            pid = int(LOCK.read_text().strip() or 0)
        except ValueError:
            pid = 0
        import psutil  # os.kill(pid, 0) sends CTRL_C_EVENT on Windows, so never use it as a liveness probe

        alive = bool(pid) and psutil.pid_exists(pid)
        if alive and pid != os.getpid():
            raise GpuBusy(f"another own-voice-render process (pid {pid}) is using the GPU. Wait for it or stop it.")
    LOCK.write_text(str(os.getpid()))


def release_lock() -> None:
    try:
        if LOCK.exists() and LOCK.read_text().strip() == str(os.getpid()):
            LOCK.unlink()
    except OSError:
        pass


def _install_audio_loader() -> None:
    import torch
    import torchaudio

    def _load(path, *a, **k):
        d, sr = sf.read(path, dtype="float32", always_2d=True)
        return torch.from_numpy(d.T.copy()), sr

    torchaudio.load = _load


def _vram_free_gb() -> float | None:
    try:
        import torch

        free, _ = torch.cuda.mem_get_info()
        return free / 1e9
    except Exception:
        return None


class Engine:
    def __init__(self, cfg: dict):
        self.cfg = cfg
        self.cache = Path(cfg["cache_dir"])
        self.cache.mkdir(parents=True, exist_ok=True)
        self.model = None
        self.sr = cfg["sample_rate"]
        ck = Path(cfg["checkpoint"])
        if not ck.exists():
            raise SystemExit(f"fine-tuned checkpoint missing: {ck}. Re-run the fine-tune or fix config.json.")
        st = ck.stat()
        self.ck_sig = f"{ck.name}:{st.st_size}:{int(st.st_mtime)}"
        self.stats = {"cache_hits": 0, "renders": 0, "render_sec": 0.0}

    def load(self) -> None:
        import torch

        if not torch.cuda.is_available():
            raise SystemExit("CUDA is not available to PyTorch. Run `ovr.py doctor`.")
        free = _vram_free_gb()
        if free is not None and free < 2.5:
            raise SystemExit(f"only {free:.1f} GB of VRAM free; close other GPU apps (DaVinci, browsers, training) and retry.")
        _install_audio_loader()
        from transformers import AutoModel

        try:
            model = AutoModel.from_pretrained(self.cfg["model_id"], trust_remote_code=True)
        except OSError as e:
            msg = str(e)
            if "gated" in msg.lower() or "401" in msg or "403" in msg:
                raise SystemExit("IndicF5 is a gated Hugging Face model. Accept its terms on the model page and run "
                                 "`hf auth login` in YOUR terminal (never paste the token into chat), then retry.")
            raise
        model = model.to("cuda")
        cfm = getattr(model.ema_model, "_orig_mod", model.ema_model)
        state = torch.load(self.cfg["checkpoint"], map_location="cuda")
        cfm.load_state_dict(state)
        self.model = model

    # -- one chunk
    def _key(self, text: str, ref: dict, ref_name: str, seed: int) -> str:
        ref_sig = core.sha(Path(ref["audio"]).read_bytes(), core.ref_text(ref))
        return core.sha(core.ENGINE_VERSION, self.ck_sig, ref_name, ref_sig, text, str(seed))

    def chunk(self, text: str, ref_name: str, seed: int) -> tuple[np.ndarray, bool]:
        import torch

        ref = self.cfg["refs"][ref_name]
        path = self.cache / f"{self._key(text, ref, ref_name, seed)}.wav"
        if path.exists():
            self.stats["cache_hits"] += 1
            return sf.read(path, dtype="float32")[0], True
        if self.model is None:
            self.load()
        torch.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)
        t0 = time.time()
        a = self.model(text, ref_audio_path=ref["audio"], ref_text=core.ref_text(ref))
        a = np.asarray(a)
        if a.dtype == np.int16:
            a = a.astype("float32") / 32768.0
        a = core.trim_edges(a.astype("float32"), self.sr, self.cfg["silence_floor_db"], self.cfg["keep_edge_silence_sec"])
        self.stats["renders"] += 1
        self.stats["render_sec"] += time.time() - t0
        sf.write(path, a, self.sr, subtype="PCM_16")
        return a, False

    def chunk_qa(self, text: str, ref_name: str, lang: str, seed: int, retries: int, locked: bool):
        """Render one chunk. If not locked, try successive seeds until QA passes; keep the best otherwise."""
        tries = []
        n = 1 if locked else retries + 1
        for i in range(n):
            s = seed + i
            a, hit = self.chunk(text, ref_name, s)
            flags = core.qa_chunk(text, a, self.sr, lang, self.cfg)
            tries.append((flags, s, a, hit))
            if not flags:
                break
        best = next((t for t in tries if not t[0]), None)
        if best is None:
            st = self.cfg["rate_stats"].get(lang, {}).get("median") or 0

            def badness(t):
                m = core.audio_metrics(t[2], self.sr, self.cfg["silence_floor_db"])
                cps = core.speech_chars(text) / max(m["duration"] - m["lead_sil"] - m["tail_sil"], 0.05)
                return (len(t[0]), abs(cps - st))

            best = min(tries, key=badness)
        flags, s, a, hit = best
        return {"audio": a, "seed": s, "flags": flags, "attempts": len(tries), "cache_hit": hit}

    # -- one cue (several chunks)
    def cue(self, cue: dict, text: str, lang: str, ref_name: str, seed: int, locked: bool) -> dict:
        gap = np.zeros(int(self.cfg["gap_in_cue_sec"] * self.sr), dtype="float32")
        parts, seeds, flags, attempts, hits = [], [], [], 0, 0
        for ch in core.chunks_for(text, self.cfg["max_chunk_chars"]):
            r = self.chunk_qa(ch, ref_name, lang, seed, self.cfg["max_seed_retries"], locked)
            parts += [r["audio"], gap]
            seeds.append(r["seed"])
            flags += [f"{ch[:18]}…:{f}" for f in r["flags"]]
            attempts += r["attempts"]
            hits += int(r["cache_hit"])
        audio = np.concatenate(parts[:-1]) if parts else np.zeros(1, dtype="float32")
        return {"audio": audio, "seeds": seeds, "flags": flags, "attempts": attempts, "chunks": len(seeds), "cache_hits": hits}
