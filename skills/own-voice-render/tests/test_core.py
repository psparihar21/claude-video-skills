"""GPU-free tests. Run: python -X utf8 -m unittest discover -s tests -v   (from the skill folder)"""
import json
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np

SKILL = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL / "scripts"))
import core  # noqa: E402

LEX = core.load_lexicon()
CFG = core.load_config()
VOCAB = core.load_vocab()
SR = 24000


def tone(sec, amp=0.3, sr=SR):
    t = np.arange(int(sec * sr)) / sr
    return (amp * np.sin(2 * np.pi * 220 * t)).astype("float32")


class TextTests(unittest.TestCase):
    def test_normalize(self):
        self.assertEqual(core.normalize_text("a​  b ,c"), "a b,c")
        self.assertEqual(core.normalize_text("“hi” — yes"), '"hi", yes')

    def test_chunks_get_terminal_punctuation(self):
        out = core.chunks_for("ये अच्छा है। और ये बात भी बिल्कुल सही है", 150)
        self.assertTrue(all(c[-1] in "।?!." for c in out))
        self.assertEqual(out[0], "ये अच्छा है।")
        self.assertEqual(len(out), 2)
        self.assertEqual(core.chunks_for("Hello there", 150), ["Hello there."])

    def test_long_sentence_splits_on_clauses_not_words(self):
        s = ", ".join(["यह एक बहुत लंबा वाक्य है"] * 12) + "।"
        parts = core.chunks_for(s, 100)
        self.assertGreater(len(parts), 1)
        self.assertEqual(" ".join(parts).replace("।", "").replace(" ,", ",").count("वाक्य"), 12)
        self.assertTrue(all(len(p) <= 140 for p in parts))

    def test_short_fragments_merge(self):
        self.assertEqual(len(core.split_sentences("ये ठीक है। हाँ।")), 1)

    def test_speech_chars_ignores_punct_and_space(self):
        self.assertEqual(core.speech_chars("a, b."), 2)

    def test_lock_key_is_stable_and_text_sensitive(self):
        self.assertEqual(core.lock_key("वेस्ट  है", "hi"), core.lock_key("वेस्ट है", "hi"))
        self.assertNotEqual(core.lock_key("वेस्ट है", "hi"), core.lock_key("वेस्ट हैं", "hi"))


class DraftTests(unittest.TestCase):
    def test_known_words_convert_and_waste_is_approved_spelling(self):
        t, unk = core.draft_devanagari("Time waste mat karo.", LEX)
        self.assertEqual(t, "टाइम वेस्ट मत करो।")
        self.assertEqual(unk, [])

    def test_unknown_and_ambiguous_are_marked(self):
        t, unk = core.draft_devanagari("main kal xyzzy karunga", LEX)
        self.assertIn("[[main]]", t)
        self.assertIn("[[xyzzy]]", t)
        self.assertIn("कल", t)
        self.assertEqual(set(unk), {"main", "xyzzy"})

    def test_keep_latin_acronyms(self):
        t, _ = core.draft_devanagari("FPS bahut accha hai", LEX)
        self.assertTrue(t.startswith("FPS "))

    def test_pronounce_override_wins(self):
        t, _ = core.draft_devanagari("zorbax hai", LEX, {"zorbax": "ज़ोरबैक्स"})
        self.assertTrue(t.startswith("ज़ोरबैक्स"))

    def test_lexicon_has_no_conflicting_spellings_for_waste(self):
        self.assertEqual(LEX["loanwords"]["waste"], "वेस्ट")
        for bad in ("वास्ट", "वैस्ट"):
            self.assertEqual(LEX["avoid"][bad], "वेस्ट")

    def test_every_lexicon_value_is_in_model_vocab(self):
        if not VOCAB:
            self.skipTest("vocab not cached")
        missing = {}
        for sec in ("hindi", "loanwords"):
            for w, d in LEX[sec].items():
                bad = {c for c in d if c not in VOCAB}
                if bad:
                    missing[w] = bad
        self.assertEqual(missing, {})

    def test_hindi_ratio(self):
        self.assertGreater(core.hindi_ratio("yeh bahut accha hai lekin nahi", LEX), 0.5)
        self.assertEqual(core.hindi_ratio("Most players lose the match", LEX), 0.0)


class LintTests(unittest.TestCase):
    def codes(self, text, lang="hi"):
        return {f["code"] for f in core.lint_text(text, lang, VOCAB, LEX)}

    def test_clean_hindi_passes(self):
        self.assertEqual(self.codes("अपना टाइम वेस्ट मत करो।"), set())

    def test_digits_blocked(self):
        self.assertIn("digits", self.codes("मेरे पास 20 वीडियो हैं।"))

    def test_latin_in_hindi_blocked(self):
        self.assertIn("latin-in-hindi", self.codes("ये video अच्छा है।"))

    def test_unresolved_marker_and_fact_hole(self):
        self.assertIn("unresolved", self.codes("ये [[xyz]] है।"))
        self.assertIn("fact-hole", self.codes("कीमत [FACT: price] है।"))

    def test_avoid_spelling_warns(self):
        self.assertIn("avoid-spelling", self.codes("ये वैस्ट है।"))

    def test_english_ok_in_en(self):
        self.assertEqual(self.codes("Most players lose.", "en"), set())

    def test_vocab_gap_detected(self):
        if not VOCAB:
            self.skipTest("vocab not cached")
        self.assertIn("not-in-vocab", self.codes("ये 😀 है।"))


class IngestTests(unittest.TestCase):
    def write(self, name, body):
        d = Path(tempfile.mkdtemp())
        p = d / name
        p.write_text(body, encoding="utf-8")
        return p

    def test_faceless_vo_script_package(self):
        src = {"title": "T", "slug": "t", "status": "final", "register": "indian-english", "format": "faceless-gameplay",
               "platform": "youtube-shorts", "video_duration_sec": 18.0, "persona": "p", "mic_note": "m",
               "pronounce": [{"word": "Zorbax", "say": "zor-backs"}],
               "cues": [{"id": "c01", "shot_id": "s01", "role": "hook", "in_sec": 0.18, "out_sec": 4.25,
                         "spoken": "Most players lose.", "performance": "[calm] x", "emphasis": ["lose"]}]}
        plan = core.ingest_file(self.write("03-script.json", json.dumps(src)), english_mode="latin")
        self.assertEqual(plan["mode"], "timed")
        self.assertEqual(plan["cues"][0]["lang"], "en")
        self.assertEqual(plan["cues"][0]["in_sec"], 0.18)
        self.assertEqual(plan["video_duration_sec"], 18.0)
        self.assertEqual(plan["pronounce"], {"Zorbax": "zor-backs"})
        self.assertEqual(plan["ignored"], ["c01"])

    def test_english_goes_through_hindi_path_by_default(self):
        src = {"title": "T", "slug": "t", "status": "final", "register": "indian-english", "format": "faceless-gameplay",
               "platform": "youtube-shorts", "video_duration_sec": 18.0, "persona": "p", "mic_note": "m",
               "cues": [{"id": "c01", "shot_id": "s01", "role": "hook", "in_sec": 0.18, "out_sec": 4.25,
                         "spoken": "Most players lose.", "performance": "x", "emphasis": []}]}
        plan = core.ingest_file(self.write("s.json", json.dumps(src)))
        c = plan["cues"][0]
        self.assertEqual((c["lang"], c["from_english"], c["deva"]), ("hi", True, ""))
        self.assertEqual(plan["english_mode"], "devanagari")

    def test_already_devanagari_english_is_not_flagged_from_english(self):
        plan = core.ingest_file(self.write("a.txt", "मोस्ट प्लेयर्स लूज़ द मैच।"))
        self.assertFalse(plan["cues"][0]["from_english"])
        self.assertTrue(plan["cues"][0]["deva"])

    def test_latin_mode_keeps_english_cues_latin(self):
        plan = core.ingest_file(self.write("b.txt", "The quick brown fox jumps over the dog."), english_mode="latin")
        self.assertEqual(plan["cues"][0]["lang"], "en")
        self.assertEqual(plan["cues"][0]["deva"], "The quick brown fox jumps over the dog.")

    def test_hinglish_register_makes_hi_cues_needing_deva(self):
        src = {"title": "T", "slug": "t", "status": "final", "register": "hinglish", "format": "faceless-story",
               "platform": "reels", "video_duration_sec": 5, "persona": "p", "mic_note": "m",
               "cues": [{"id": "c01", "shot_id": "s", "role": "hook", "in_sec": 0, "out_sec": 3, "spoken": "Yeh time waste hai.",
                         "performance": "x", "emphasis": []}]}
        plan = core.ingest_file(self.write("s.json", json.dumps(src)))
        self.assertEqual(plan["cues"][0]["lang"], "hi")
        self.assertEqual(plan["cues"][0]["deva"], "")

    def test_draft_status_warns(self):
        src = {"title": "T", "slug": "t", "status": "draft", "register": "indian-english", "format": "faceless-story",
               "platform": "reels", "video_duration_sec": 5, "persona": "p", "mic_note": "m",
               "cues": [{"id": "c01", "shot_id": "s", "role": "hook", "in_sec": 0, "out_sec": 3, "spoken": "Hi there.",
                         "performance": "x", "emphasis": []}]}
        plan = core.ingest_file(self.write("s.json", json.dumps(src)))
        self.assertTrue(any("draft" in w for w in plan["warnings"]))

    def test_srt(self):
        srt = "1\n00:00:01,000 --> 00:00:03,500\nHello <i>world</i>\n\n2\n00:00:04,000 --> 00:00:05,000\nBye\n"
        plan = core.ingest_file(self.write("a.srt", srt))
        self.assertEqual(plan["mode"], "timed")
        self.assertEqual((plan["cues"][0]["in_sec"], plan["cues"][0]["out_sec"]), (1.0, 3.5))
        self.assertEqual(plan["cues"][0]["roman"], "Hello world")

    def test_markdown_strips_structure(self):
        md = "# Title\n\nFirst para line one.\nline two.\n\n- bullet one\n\n```\ncode\n```\n\n| a | b |\n\nLast para."
        plan = core.ingest_file(self.write("a.md", md), "en")
        texts = [c["roman"] for c in plan["cues"]]
        self.assertNotIn("Title", " ".join(texts))
        self.assertNotIn("code", " ".join(texts))
        self.assertIn("bullet one", " ".join(texts))
        self.assertTrue(any(c["paragraph_break"] for c in plan["cues"]))

    def test_plain_text_language_detection(self):
        plan = core.ingest_file(self.write("a.txt", "Yeh bahut accha video hai lekin time waste nahi karna.\n"))
        self.assertEqual(plan["cues"][0]["lang"], "hi")
        plan = core.ingest_file(self.write("b.txt", "The quick brown fox jumps over the dog.\n"), english_mode="latin")
        self.assertEqual(plan["cues"][0]["lang"], "en")

    def test_bad_windows_rejected(self):
        src = {"cues": [{"id": "a", "text": "Hi.", "start": 3, "end": 2}]}
        with self.assertRaises(SystemExit):
            core.ingest_file(self.write("x.json", json.dumps(src)))

    def test_empty_script_rejected(self):
        with self.assertRaises(SystemExit):
            core.ingest_file(self.write("e.txt", "# only a heading\n"))


class AudioQaTests(unittest.TestCase):
    def test_metrics_find_edge_silence(self):
        x = np.concatenate([np.zeros(int(0.5 * SR), "float32"), tone(1.0), np.zeros(int(0.3 * SR), "float32")])
        m = core.audio_metrics(x, SR, -45)
        self.assertAlmostEqual(m["lead_sil"], 0.5, delta=0.03)
        self.assertAlmostEqual(m["tail_sil"], 0.3, delta=0.03)

    def test_trim_keeps_margin(self):
        x = np.concatenate([np.zeros(SR, "float32"), tone(1.0), np.zeros(SR, "float32")])
        y = core.trim_edges(x, SR, -45, 0.08)
        self.assertAlmostEqual(len(y) / SR, 1.16, delta=0.05)

    def test_qa_flags(self):
        text = "यह एक सामान्य वाक्य है।"
        n = core.speech_chars(text)
        good = tone(n / CFG["rate_stats"]["hi"]["median"])
        self.assertEqual(core.qa_chunk(text, good, SR, "hi", CFG), [])
        fast = tone(n / (CFG["rate_stats"]["hi"]["hi"] * 2))
        self.assertTrue(any(f.startswith("too-fast") for f in core.qa_chunk(text, fast, SR, "hi", CFG)))
        slow = tone(n / (CFG["rate_stats"]["hi"]["lo"] / 3))
        self.assertTrue(any(f.startswith("too-slow") for f in core.qa_chunk(text, slow, SR, "hi", CFG)))
        self.assertIn("clipping", core.qa_chunk(text, np.clip(good * 10, -1, 1), SR, "hi", CFG))
        self.assertTrue(core.qa_chunk(text, np.zeros(SR, "float32"), SR, "hi", CFG))
        self.assertEqual(core.qa_chunk(text, np.array([np.nan] * 100, "float32"), SR, "hi", CFG), ["non-finite-or-empty"])


class TimingTests(unittest.TestCase):
    def test_fits(self):
        self.assertEqual(core.plan_fit(3.0, 4.0, 1.12)["status"], "fits")

    def test_sped_within_cap(self):
        r = core.plan_fit(4.2, 4.0, 1.12)
        self.assertEqual(r["status"], "sped")
        self.assertLessEqual(r["tempo"], 1.12)

    def test_overflow_never_exceeds_cap_and_reports_amount(self):
        r = core.plan_fit(6.0, 4.0, 1.12)
        self.assertEqual(r["status"], "overflow")
        self.assertEqual(r["tempo"], 1.12)
        self.assertGreater(r["over_by"], 0)

    def test_srt_time(self):
        self.assertEqual(core.fmt_srt_time(3661.5), "01:01:01,500")


if __name__ == "__main__":
    unittest.main()
