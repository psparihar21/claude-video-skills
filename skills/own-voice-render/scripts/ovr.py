#!/usr/bin/env python
"""own-voice-render CLI: turn any skill's script into audio in the user's own cloned voice.

Run with the indicf5 env's python in UTF-8 mode (see SKILL.md):
  <your-indicf5-env>/python.exe -X utf8 ovr.py <command> ...

Commands: doctor | ingest | draft | set-deva | review | lint | render | candidates | lock | calibrate | lexicon | selftest
Exit codes: 0 clean, 1 error/blocked, 2 rendered but cues need a human listen (QA flags), 3 timing overflow/collision.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import core  # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass


# --------------------------------------------------------------------------- io helpers
def jload(p: Path) -> dict:
    return json.loads(Path(p).read_text(encoding="utf-8"))


def jsave(p: Path, data) -> None:
    Path(p).write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def plan_path(arg: str) -> Path:
    p = Path(arg)
    if p.is_dir():
        p = p / "plan.json"
    if not p.exists():
        raise SystemExit(f"plan not found: {p}. Run `ovr.py ingest <script>` first.")
    return p


def cue_by_id(plan: dict, cid: str) -> dict:
    for c in plan["cues"]:
        if c["id"] == cid:
            return c
    raise SystemExit(f"no cue {cid}. Cues: {', '.join(c['id'] for c in plan['cues'])}")


def parse_seeds(s: str) -> list[int]:
    out: list[int] = []
    for part in s.split(","):
        if "-" in part:
            a, b = part.split("-")
            out += list(range(int(a), int(b) + 1))
        else:
            out.append(int(part))
    return out


# --------------------------------------------------------------------------- commands
def cmd_doctor(a) -> int:
    cfg = core.load_config()
    rows: list[tuple[str, str, str]] = []

    def row(name, ok, detail, warn=False):
        rows.append(("PASS" if ok else ("WARN" if warn else "FAIL"), name, detail))

    row("python", Path(cfg["python"]).exists(), cfg["python"])
    row("running python is the indicf5 env", Path(sys.executable).resolve() == Path(cfg["python"]).resolve(),
        sys.executable, warn=True)
    try:
        import torch

        ok = torch.cuda.is_available()
        detail = f"torch {torch.__version__}"
        if ok:
            free, total = torch.cuda.mem_get_info()
            detail += f", {torch.cuda.get_device_name(0)}, {free / 1e9:.1f}/{total / 1e9:.1f} GB free"
        row("CUDA", ok, detail)
        if ok:
            row("VRAM free >= 2.5 GB", free / 1e9 >= 2.5, f"{free / 1e9:.1f} GB (close DaVinci/browsers/training if low)")
    except Exception as e:
        row("torch", False, str(e))
    try:
        import transformers

        row("transformers 4.49.x (IndicF5 breaks on 5.x)", transformers.__version__.startswith("4.49"), transformers.__version__)
    except Exception as e:
        row("transformers", False, str(e))
    try:
        ff = core.find_ffmpeg(cfg)
        row("ffmpeg", True, ff)
    except SystemExit as e:
        row("ffmpeg", False, str(e))
    ck = Path(cfg["checkpoint"])
    row("fine-tuned checkpoint", ck.exists(), f"{ck} ({ck.stat().st_size / 1e9:.2f} GB)" if ck.exists() else str(ck))
    for lang, name in cfg["default_ref"].items():
        r = cfg["refs"][name]
        row(f"default {lang} reference '{name}'", Path(r["audio"]).exists() and Path(r["text_file"]).exists(), r["audio"])
    base = Path.home() / ".cache" / "huggingface" / "hub" / "models--ai4bharat--IndicF5" / "snapshots"
    cached = bool(list(base.glob("*/model.safetensors"))) if base.exists() else False
    row("IndicF5 weights cached", cached, "yes, works offline" if cached else "no: needs HF access (gated) to download")
    try:
        from huggingface_hub import get_token

        row("Hugging Face login present", bool(get_token()), "yes (token value is never printed)" if get_token() else "no", warn=cached)
    except Exception as e:
        row("Hugging Face login", False, str(e), warn=True)
    vocab = core.load_vocab()
    row("model vocab readable", bool(vocab), f"{len(vocab)} symbols" if vocab else "missing: run the model once to cache it")
    rs = cfg["rate_stats"]
    row("rate calibration", bool(rs["hi"]["median"] and rs["en"]["median"]),
        f"hi {rs['hi']['median']} cps, en {rs['en']['median']} cps" if rs["hi"]["median"] else "run `ovr.py calibrate`", warn=True)
    try:
        Path(cfg["cache_dir"]).mkdir(parents=True, exist_ok=True)
        probe = Path(cfg["cache_dir"]) / ".w"
        probe.write_text("x"); probe.unlink()
        row("cache dir writable", True, cfg["cache_dir"])
    except OSError as e:
        row("cache dir writable", False, str(e))
    try:
        core.load_lexicon()
        row("lexicon valid", True, str(core.SKILL / "assets" / "lexicon.json"))
    except Exception as e:
        row("lexicon valid", False, str(e))
    w = max(len(r[1]) for r in rows)
    for status, name, detail in rows:
        print(f"{status:<4}  {name:<{w}}  {detail}")
    bad = [r for r in rows if r[0] == "FAIL"]
    print("\nready" if not bad else f"\n{len(bad)} blocking problem(s). See troubleshooting.md")
    return 0 if not bad else 1


def cmd_ingest(a) -> int:
    src = Path(a.script).resolve()
    if not src.exists():
        raise SystemExit(f"script not found: {src}")
    lex = core.load_lexicon()
    plan = core.ingest_file(src, a.lang, lex, a.english_as or core.load_config().get("english_mode", "devanagari"))
    slug = plan.get("slug") or re.sub(r"[^a-z0-9]+", "-", src.stem.lower()).strip("-") or "script"
    plan["slug"] = slug
    out = Path(a.out).resolve() if a.out else src.parent / ("own-voice" if plan["source"].get("format") == "faceless-vo-script" else f"voice-out-{slug}")
    out.mkdir(parents=True, exist_ok=True)
    plan["out_dir"] = str(out)
    plan["compat"] = "faceless-vo-script" if plan["source"].get("format") == "faceless-vo-script" else None
    plan["compat_dir"] = str(src.parent) if plan["compat"] else None
    jsave(out / "plan.json", plan)
    hi = [c for c in plan["cues"] if c["lang"] == "hi" and not c["deva"]]
    n_en = len([c for c in plan["cues"] if c.get("from_english")])
    if n_en:
        print(f"{n_en} English cue(s) will be written in Devanagari (Indian-accented English in the user's voice). Use --english-as latin to keep Latin text.")
    en = [c for c in plan["cues"] if c["lang"] == "en"]
    print(f"plan: {out / 'plan.json'}")
    print(f"mode={plan['mode']}  cues={len(plan['cues'])}  hindi/hinglish={len([c for c in plan['cues'] if c['lang'] == 'hi'])}  english={len(en)}")
    for w in plan["warnings"]:
        print("warn:", w)
    if plan["ignored"]:
        print(f"note: performance/emphasis notes on {len(plan['ignored'])} cue(s) are ignored: this engine has no emotion control")
    if hi:
        print(f"next: {len(hi)} cue(s) need Devanagari. Run `draft`, then fix [[unknown]] words and `set-deva`.")
    else:
        print("next: `lint`, then `render`.")
    return 0


def cmd_draft(a) -> int:
    p = plan_path(a.plan)
    plan = jload(p)
    lex = core.load_lexicon()
    notes = ["# Devanagari to finish\n",
             "Read each Roman line, fix every `[[word]]`, and resolve ambiguous words from context.",
             "Write English-origin words in Devanagari phonetically (वेस्ट, टाइम). Spell out numbers in Hindi words.",
             "Then: `set-deva` with a JSON file of {cue id: final Devanagari}.\n"]
    n = 0
    for c in plan["cues"]:
        if c["lang"] != "hi" or c.get("deva_status") == "reviewed" or (c["deva"] and not c.get("deva_status")):
            continue
        text, unknown = core.draft_devanagari(c["roman"], lex, plan.get("pronounce"))
        c["deva"], c["deva_status"] = text, "draft"
        n += 1
        notes += [f"## {c['id']}" + ("  (ENGLISH: transliterate the whole sentence phonetically)" if c.get("from_english") else ""),
                  f"roman: {c['roman']}", f"draft: {text}",
                  f"unknown: {', '.join(unknown) if unknown else '(none)'}\n"]
    jsave(p, plan)
    (p.parent / "needs-deva.md").write_text("\n".join(notes), encoding="utf-8")
    print(f"drafted {n} cue(s) -> {p.parent / 'needs-deva.md'}")
    return 0


def cmd_set_deva(a) -> int:
    p = plan_path(a.plan)
    plan = jload(p)
    data = jload(Path(a.file))
    for cid, text in data.items():
        c = cue_by_id(plan, cid)
        c["deva"], c["deva_status"] = core.normalize_text(text), "reviewed"
    jsave(p, plan)
    print(f"set Devanagari on {len(data)} cue(s); marked reviewed")
    return 0


def cmd_review(a) -> int:
    p = plan_path(a.plan)
    plan = jload(p)
    n = 0
    for c in plan["cues"]:
        if c.get("deva_status") == "draft" and (a.all or c["id"] in (a.cues or "").split(",")):
            c["deva_status"] = "reviewed"; n += 1
    jsave(p, plan)
    print(f"marked {n} cue(s) reviewed")
    return 0


def lint_plan(plan: dict, fix: bool = False) -> tuple[list[tuple[str, dict]], bool]:
    lex, cfg, vocab = core.load_lexicon(), core.load_config(), core.load_vocab()
    changed, findings = False, []
    for c in plan["cues"]:
        if fix and c["deva"]:
            t = core.normalize_text(c["deva"])
            for bad, good in lex["avoid"].items():
                t = t.replace(bad, good)
            if t != c["deva"]:
                c["deva"], changed = t, True
        text = c["deva"]
        if c["lang"] == "hi" and not text:
            findings.append((c["id"], {"level": "error", "code": "no-deva", "msg": "no Devanagari yet (run draft, then set-deva)"}))
            continue
        if c["lang"] == "hi" and c.get("deva_status") == "draft":
            findings.append((c["id"], {"level": "error", "code": "unreviewed", "msg": "machine draft not reviewed: fix it with set-deva or confirm with `review`"}))
        for f in core.lint_text(text, c["lang"], vocab, lex, cfg["max_chunk_chars"]):
            findings.append((c["id"], f))
    if plan.get("status") == "draft":
        findings.append(("*", {"level": "error", "code": "draft-source", "msg": "source script status is 'draft'; wait for a final script"}))
    return findings, changed


def cmd_lint(a) -> int:
    p = plan_path(a.plan)
    plan = jload(p)
    findings, changed = lint_plan(plan, a.fix)
    if changed:
        jsave(p, plan)
        print("applied safe fixes (whitespace, punctuation, approved spellings)")
    for cid, f in findings:
        print(f"{f['level'].upper():5} {cid:6} {f['code']}: {f['msg']}")
    errs = [f for _, f in findings if f["level"] == "error"]
    print(f"\n{len(errs)} error(s), {len(findings) - len(errs)} warning(s)")
    return 1 if errs else 0


def cmd_render(a) -> int:
    from assemble import build_timeline, normalise_and_encode, write_srt
    import engine as eng
    import numpy as np
    import soundfile as sf

    p = plan_path(a.plan)
    plan = jload(p)
    out = p.parent
    cfg = core.load_config()
    ffmpeg = core.find_ffmpeg(cfg)
    findings, _ = lint_plan(plan)
    errs = [(cid, f) for cid, f in findings if f["level"] == "error"]
    if errs:
        for cid, f in errs:
            print(f"ERROR {cid} {f['code']}: {f['msg']}")
        print("\nblocked by lint errors. Fix them (see `lint`).")
        return 1
    locks = core.load_locks(out / "locks.json")
    only = set(a.only.split(",")) if a.only else None
    (out / "cues").mkdir(exist_ok=True)
    engine = eng.Engine(cfg)
    eng.acquire_lock()
    t0 = time.time()
    rendered, rows, qa_flags = {}, [], []
    try:
        for c in plan["cues"]:
            text = c["deva"] or c["roman"]
            lk = locks.get(core.lock_key(text, c["lang"]), {})
            ref = c.get("ref") or lk.get("ref") or cfg["default_ref"][c["lang"]]
            if ref not in cfg["refs"]:
                raise SystemExit(f"cue {c['id']}: unknown reference '{ref}'. Known: {', '.join(cfg['refs'])}")
            if cfg["refs"][ref]["lang"] != c["lang"]:
                raise SystemExit(f"cue {c['id']}: reference '{ref}' is {cfg['refs'][ref]['lang']} but the cue is {c['lang']}")
            seed = c.get("seed") or lk.get("seed") or cfg["default_seed"]
            locked = bool(c.get("seed") or lk.get("seed"))
            wav = out / "cues" / f"{c['id']}.wav"
            if only is not None and c["id"] not in only:
                if not wav.exists():
                    raise SystemExit(f"--only skipped {c['id']} but it has no earlier render")
                rendered[c["id"]] = sf.read(wav, dtype="float32")[0]
                rows.append({"id": c["id"], "status": "reused"})
                continue
            r = engine.cue(c, text, c["lang"], ref, seed, locked)
            sf.write(wav, r["audio"], cfg["sample_rate"], subtype="PCM_16")
            rendered[c["id"]] = r["audio"]
            row = {"id": c["id"], "lang": c["lang"], "ref": ref, "seeds": r["seeds"], "locked": locked,
                   "chunks": r["chunks"], "attempts": r["attempts"], "cache_hits": r["cache_hits"],
                   "sec": round(len(r["audio"]) / cfg["sample_rate"], 3), "qa_flags": r["flags"]}
            rows.append(row)
            if r["flags"]:
                qa_flags.append(row)
            print(f"{c['id']:6} {row['sec']:6.2f}s  seeds={r['seeds']} ref={ref}{'  (locked)' if locked else ''}"
                  f"{'  QA: ' + '; '.join(r['flags']) if r['flags'] else ''}", flush=True)
    finally:
        eng.release_lock()
    master, placements, issues = build_timeline(plan, rendered, cfg, ffmpeg, a.allow_overflow)
    meta = normalise_and_encode(master, out, cfg, ffmpeg)
    write_srt(plan, placements, out / "voice.srt")
    blocking = [i for i in issues if i["level"] in ("overflow", "collision")]
    soft = [i for i in issues if i["level"] == "truncated"]
    status = "overflow" if blocking else ("needs-listen" if (qa_flags or soft) else "ok")
    report = {"status": status, "slug": plan.get("slug"), "mode": plan["mode"], "audio": meta,
              "engine": {"model": cfg["model_id"], "checkpoint": cfg["checkpoint"], **engine.stats, "wall_sec": round(time.time() - t0, 1)},
              "cues": rows, "placements": placements, "issues": issues, "warnings": plan.get("warnings", []),
              "ignored_performance_notes": plan.get("ignored", [])}
    jsave(out / "report.json", report)
    if plan.get("compat") == "faceless-vo-script" and plan.get("compat_dir"):
        cdir = Path(plan["compat_dir"])
        shutil.copy(out / "voice.m4a", cdir / "07-voice.m4a")
        jsave(cdir / "07-voice-report.json", {
            "voice": "own-voice (IndicF5 fine-tune)", "rate": "n/a", "file": "07-voice.m4a", "duration_sec": meta["duration_sec"],
            "cues": [{"id": pl["id"], "in_sec": pl["start"], "window_sec": pl["window"], "spoken_sec": round(pl["end"] - pl["start"], 3),
                      "tempo": pl["tempo"], "trimmed": pl["status"] == "overflow"} for pl in placements]})
        print(f"compat: wrote {cdir / '07-voice.m4a'} and 07-voice-report.json")
    print(f"\n{out / meta['wav']}  {meta['duration_sec']}s  {meta['output_lufs']:.1f} LUFS  tp {meta['output_tp']:.1f} dB")
    print(f"cache: {engine.stats['cache_hits']} hit(s), {engine.stats['renders']} render(s) in {engine.stats['render_sec']:.0f}s")
    for i in issues:
        print(f"{i['level'].upper()} {i['cue']}: {i['msg']}")
    if qa_flags:
        print(f"{len(qa_flags)} cue(s) have QA flags: listen to them, or run `candidates` then `lock`.")
    print(f"status: {status}")
    return 3 if blocking else (2 if (qa_flags or soft) else 0)


def cmd_candidates(a) -> int:
    import engine as eng
    import soundfile as sf

    p = plan_path(a.plan)
    plan = jload(p)
    cfg = core.load_config()
    c = cue_by_id(plan, a.cue)
    text = c["deva"] or c["roman"]
    refs = a.refs.split(",") if a.refs else [cfg["default_ref"][c["lang"]]]
    for r in refs:
        if r not in cfg["refs"] or cfg["refs"][r]["lang"] != c["lang"]:
            raise SystemExit(f"reference '{r}' is unknown or the wrong language for cue {c['id']} ({c['lang']})")
    d = p.parent / "candidates"
    d.mkdir(exist_ok=True)
    engine = eng.Engine(cfg)
    eng.acquire_lock()
    made = []
    try:
        for r in refs:
            for s in parse_seeds(a.seeds):
                res = engine.cue(c, text, c["lang"], r, s, True)
                f = d / f"{c['id']}_{r}_seed{s}.wav"
                sf.write(f, res["audio"], cfg["sample_rate"], subtype="PCM_16")
                made.append(f)
                print(f"{f.name}  {len(res['audio']) / cfg['sample_rate']:.2f}s  {'QA: ' + '; '.join(res['flags']) if res['flags'] else ''}", flush=True)
    finally:
        eng.release_lock()
    print(f"\n{len(made)} candidate(s) in {d}. Send them to the user; they pick one; then:\n"
          f"  ovr.py lock {p.parent} --cue {c['id']} --seed <N> [--ref <name>]")
    return 0


def cmd_lock(a) -> int:
    p = plan_path(a.plan)
    plan = jload(p)
    cfg = core.load_config()
    c = cue_by_id(plan, a.cue)
    if a.ref and (a.ref not in cfg["refs"] or cfg["refs"][a.ref]["lang"] != c["lang"]):
        raise SystemExit(f"reference '{a.ref}' is unknown or the wrong language")
    locks_p = p.parent / "locks.json"
    locks = core.load_locks(locks_p)
    key = core.lock_key(c["deva"] or c["roman"], c["lang"])
    locks[key] = {"cue": c["id"], "seed": a.seed, **({"ref": a.ref} if a.ref else {}), "text": (c["deva"] or c["roman"])[:60]}
    jsave(locks_p, locks)
    print(f"locked {c['id']}: seed {a.seed}" + (f", ref {a.ref}" if a.ref else "") + f"  ({locks_p}). Re-render with --only {c['id']}.")
    return 0


def cmd_calibrate(a) -> int:
    import numpy as np
    import soundfile as sf

    cfgp = core.SKILL / "config.json"
    cfg = jload(cfgp)
    td = cfg["training_data"]
    deva = [l.strip() for l in open(td["deva_txt"], encoding="utf-8") if l.strip()]
    items = []
    for l in open(td["raw_jsonl"], encoding="utf-8"):
        r = json.loads(l)
        n = int(Path(r["audio"]).stem[3:7])
        items.append((td["data_root"] + r["audio"][2:], deva[n - 102] if n >= 102 else r["text"], "hi" if n >= 102 else "en"))
    if Path(td["extra_jsonl"]).exists():
        for l in open(td["extra_jsonl"], encoding="utf-8"):
            r = json.loads(l)
            items.append((td["data_root"] + r["audio"][2:], r["text"], "hi"))
    # English written in Devanagari is read through the Hindi path, so it belongs to the "hi" range
    if td.get("en_deva_txt") and Path(td["en_deva_txt"]).exists():
        for i, t in enumerate([l.strip() for l in open(td["en_deva_txt"], encoding="utf-8") if l.strip()], 1):
            items.append((td["data_root"] + f"data/utt{i:04d}.wav", t, "hi"))
    if td.get("en_new_jsonl") and Path(td["en_new_jsonl"]).exists():
        for l in open(td["en_new_jsonl"], encoding="utf-8"):
            r = json.loads(l)
            items.append((td["data_root"] + r["audio"][2:], r["text"], "hi"))
    by: dict[str, list[float]] = {"hi": [], "en": []}
    for path, text, lang in items:
        x, sr = sf.read(path, dtype="float32")
        m = core.audio_metrics(x, sr, cfg["silence_floor_db"])
        live = max(m["duration"] - m["lead_sil"] - m["tail_sil"], 0.05)
        by[lang].append(core.speech_chars(text) / live)
    for lang, v in by.items():
        v = np.array(v)
        cfg["rate_stats"][lang] = {"median": round(float(np.median(v)), 2), "lo": round(float(np.percentile(v, 2)) * 0.8, 2),
                                   "hi": round(float(np.percentile(v, 98)) * 1.2, 2), "n": int(v.size)}
        print(lang, cfg["rate_stats"][lang])
    jsave(cfgp, cfg)
    return 0


def cmd_lexicon(a) -> int:
    lp = core.SKILL / "assets" / "lexicon.json"
    lex = jload(lp)
    section = "loanwords" if a.kind == "loanword" else "hindi"
    lex[section][a.roman.lower()] = a.deva
    if a.approved:
        lex["approved_by_user"][a.roman.lower()] = a.deva
    jsave(lp, lex)
    print(f"added {a.roman.lower()} -> {a.deva} ({section})")
    return 0


def cmd_selftest(a) -> int:
    tmp = Path(tempfile.mkdtemp(prefix="ovr-selftest-"))
    script = tmp / "selftest.json"
    jsave(script, {"cues": [
        {"id": "h1", "text": "दोस्तों, अपना टाइम वेस्ट मत करो, सीधा काम की बात पर आते हैं।"},
        {"id": "e1", "text": "मोस्ट प्लेयर्स लूज़ द मैच बिफ़ोर इट स्टार्ट्स।"}]})
    ns = argparse.Namespace(script=str(script), out=str(tmp / "out"), lang="auto", english_as=None)
    cmd_ingest(ns)
    ns = argparse.Namespace(plan=str(tmp / "out"), allow_overflow=False, only=None)
    rc = cmd_render(ns)
    rep = jload(tmp / "out" / "report.json")
    lufs = rep["audio"]["output_lufs"]
    ok = rc in (0, 2) and abs(lufs - core.load_config()["target_lufs"]) < 1.5
    print(f"\nselftest {'PASS' if ok else 'FAIL'}  rc={rc}  loudness {lufs:.1f} LUFS  files in {tmp / 'out'}")
    return 0 if ok else 1


# --------------------------------------------------------------------------- main
def main() -> int:
    ap = argparse.ArgumentParser(prog="ovr", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("doctor").set_defaults(fn=cmd_doctor)
    s = sub.add_parser("ingest"); s.add_argument("script"); s.add_argument("--out"); s.add_argument("--lang", default="auto", choices=["auto", "hi", "en"]); s.add_argument("--english-as", choices=["devanagari", "latin"]); s.set_defaults(fn=cmd_ingest)
    s = sub.add_parser("draft"); s.add_argument("plan"); s.set_defaults(fn=cmd_draft)
    s = sub.add_parser("set-deva"); s.add_argument("plan"); s.add_argument("file"); s.set_defaults(fn=cmd_set_deva)
    s = sub.add_parser("review"); s.add_argument("plan"); s.add_argument("--all", action="store_true"); s.add_argument("--cues"); s.set_defaults(fn=cmd_review)
    s = sub.add_parser("lint"); s.add_argument("plan"); s.add_argument("--fix", action="store_true"); s.set_defaults(fn=cmd_lint)
    s = sub.add_parser("render"); s.add_argument("plan"); s.add_argument("--allow-overflow", action="store_true"); s.add_argument("--only"); s.set_defaults(fn=cmd_render)
    s = sub.add_parser("candidates"); s.add_argument("plan"); s.add_argument("--cue", required=True); s.add_argument("--seeds", default="1-6"); s.add_argument("--refs"); s.set_defaults(fn=cmd_candidates)
    s = sub.add_parser("lock"); s.add_argument("plan"); s.add_argument("--cue", required=True); s.add_argument("--seed", type=int, required=True); s.add_argument("--ref"); s.set_defaults(fn=cmd_lock)
    sub.add_parser("calibrate").set_defaults(fn=cmd_calibrate)
    s = sub.add_parser("lexicon"); s.add_argument("roman"); s.add_argument("deva"); s.add_argument("--kind", default="loanword", choices=["loanword", "hindi"]); s.add_argument("--approved", action="store_true"); s.set_defaults(fn=cmd_lexicon)
    sub.add_parser("selftest").set_defaults(fn=cmd_selftest)
    a = ap.parse_args()
    return a.fn(a)


if __name__ == "__main__":
    sys.exit(main())
