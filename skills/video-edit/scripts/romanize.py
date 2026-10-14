"""Hindi (Devanagari) -> casual Hinglish Roman letters, word by word.

"यह वीडियो देखो" -> "yeh video dekho". Timestamps are never touched: word i in
the output is word i in the input.

Two steps:
  draft:  python -I romanize.py draft TRANSCRIPT_JSON OUT_DIR
          writes OUT_DIR/transcript.roman.json (rule-based draft) and
          OUT_DIR/romanize-review.json = {devanagari_word: draft_roman} for every
          UNIQUE Devanagari word, so Claude reviews each word once.
  apply:  python -I romanize.py apply TRANSCRIPT_JSON OUT_DIR
          re-reads the (edited) romanize-review.json and rewrites
          transcript.roman.json with the corrected spellings.

Claude's review: fix each draft to how a Hinglish YouTuber would type it; put
English loanwords back in English ("वीडियो" -> "video", "सेटिंग्स" -> "settings",
"क्लिक" -> "click"); keep punctuation. Corrections persist in
~/.claude/skills/video-edit/hinglish-dictionary.json for future videos.
"""
import json
import re
import sys
from pathlib import Path

DICT_PATH = Path(__file__).resolve().parent.parent / "hinglish-dictionary.json"

COMMON = {
    "यह": "yeh", "ये": "ye", "वह": "woh", "वो": "wo", "है": "hai", "हैं": "hain", "में": "mein",
    "मैं": "main", "नहीं": "nahi", "नही": "nahi", "और": "aur", "भी": "bhi", "तो": "toh", "कि": "ki",
    "की": "ki", "का": "ka", "के": "ke", "को": "ko", "से": "se", "पर": "par", "क्या": "kya",
    "हाँ": "haan", "हां": "haan", "आप": "aap", "हम": "hum", "तुम": "tum", "एक": "ek", "इस": "is",
    "उस": "us", "था": "tha", "थी": "thi", "थे": "the", "गया": "gaya", "गई": "gayi", "करना": "karna",
    "करो": "karo", "करें": "karein", "करते": "karte", "करता": "karta", "कर": "kar", "अब": "ab",
    "जब": "jab", "तब": "tab", "सब": "sab", "कुछ": "kuch", "बहुत": "bahut", "अच्छा": "achha",
    "ठीक": "theek", "लेकिन": "lekin", "क्योंकि": "kyunki", "मतलब": "matlab", "यानी": "yaani",
    "यहाँ": "yahan", "यहां": "yahan", "वहाँ": "wahan", "वहां": "wahan", "अपना": "apna",
    "अपने": "apne", "अपनी": "apni", "होता": "hota", "होती": "hoti", "होते": "hote", "हो": "ho",
    "सकते": "sakte", "सकता": "sakta", "चलो": "chalo", "देखो": "dekho", "देखते": "dekhte",
    "बताओ": "batao", "ज़्यादा": "zyada", "ज्यादा": "zyada", "पहले": "pehle", "फिर": "phir",
    "साथ": "saath", "बात": "baat", "दोस्तों": "doston", "दोस्तो": "dosto", "आज": "aaj",
    "कैसे": "kaise", "क्यों": "kyun", "कहाँ": "kahan", "कहां": "kahan", "कौन": "kaun",
    "मेरा": "mera", "मेरे": "mere", "मेरी": "meri", "तेरा": "tera", "उसका": "uska", "इसका": "iska",
    "वाला": "wala", "वाले": "wale", "वाली": "wali", "लिए": "liye", "रहा": "raha", "रहे": "rahe",
    "रही": "rahi", "दिया": "diya", "लिया": "liya", "किया": "kiya", "हुआ": "hua", "हुए": "hue",
}

VOWELS = {"अ": "a", "आ": "aa", "इ": "i", "ई": "ee", "उ": "u", "ऊ": "oo", "ऋ": "ri", "ए": "e",
          "ऐ": "ai", "ओ": "o", "औ": "au", "ऑ": "o", "ऍ": "e"}
MATRAS = {"ा": "aa", "ि": "i", "ी": "ee", "ु": "u", "ू": "oo", "ृ": "ri", "े": "e", "ै": "ai",
          "ो": "o", "ौ": "au", "ॉ": "o", "ॅ": "e"}
CONS = {"क": "k", "ख": "kh", "ग": "g", "घ": "gh", "ङ": "n", "च": "ch", "छ": "chh", "ज": "j",
        "झ": "jh", "ञ": "n", "ट": "t", "ठ": "th", "ड": "d", "ढ": "dh", "ण": "n", "त": "t",
        "थ": "th", "द": "d", "ध": "dh", "न": "n", "प": "p", "फ": "ph", "ब": "b", "भ": "bh",
        "म": "m", "य": "y", "र": "r", "ल": "l", "व": "v", "श": "sh", "ष": "sh", "स": "s", "ह": "h"}
NUKTA = {"क": "q", "ख": "kh", "ग": "gh", "ज": "z", "ड": "r", "ढ": "rh", "फ": "f", "य": "y"}
DIGITS = str.maketrans("०१२३४५६७८९", "0123456789")
DEV = re.compile(r"[ऀ-ॿ]")


def translit(word: str) -> str:
    # tokens: list of [consonant_roman_or_None, vowel_roman_or_None, explicit]
    syl, i, n = [], 0, len(word)
    while i < n:
        ch = word[i]
        if ch in CONS:
            c = CONS[ch]
            if i + 1 < n and word[i + 1] == "़":
                c = NUKTA.get(ch, c)
                i += 1
            syl.append([c, "a", False])  # inherent schwa, may be deleted
        elif ch in VOWELS:
            syl.append([None, VOWELS[ch], True])
        elif ch in MATRAS and syl:
            syl[-1][1], syl[-1][2] = MATRAS[ch], True
        elif ch == "्" and syl:
            syl[-1][1], syl[-1][2] = "", True
        elif ch in "ंँ":
            syl.append(["NASAL", "", True])
        elif ch == "ः":
            syl.append(["h", "", True])
        elif ch in "।॥":
            syl.append([None, ".", True])
        else:
            syl.append([None, ch.translate(DIGITS), True])
        i += 1
    # schwa deletion: word-final, and V C(a) C V  ->  drop the middle schwa
    cons_idx = [k for k, s in enumerate(syl) if s[0] not in (None, "NASAL")]
    if cons_idx and not syl[cons_idx[-1]][2] and cons_idx[-1] == len(syl) - 1 and len(cons_idx) > 1:
        syl[cons_idx[-1]][1] = ""
    for k in range(len(syl) - 2, 0, -1):
        s = syl[k]
        if s[0] in (None, "NASAL") or s[2]:
            continue
        prev_has_vowel = bool(syl[k - 1][1])
        nxt = syl[k + 1]
        if prev_has_vowel and nxt[0] not in (None, "NASAL") and nxt[1]:
            s[1] = ""
    out = []
    for k, (c, v, _) in enumerate(syl):
        if c == "NASAL":
            nxt = syl[k + 1][0] if k + 1 < len(syl) else None
            out.append("m" if nxt in ("p", "ph", "b", "bh", "m") else "n")
        else:
            out.append((c or "") + v)
    r = "".join(out)
    if len(r) > 2 and r.endswith("aa"):
        r = r[:-1]           # dekhaa -> dekha
    if len(r) > 2 and r.endswith("ee"):
        r = r[:-2] + "i"     # nahee -> nahi
    return r


PUNCT = "।॥.,!?;:\"'()[]…-–—"


def split_punct(t: str):
    t = t.strip()
    i, j = 0, len(t)
    while i < j and t[i] in PUNCT:
        i += 1
    while j > i and t[j - 1] in PUNCT:
        j -= 1
    return t[:i], t[i:j], t[j:].replace("।", ".").replace("॥", ".")


def load_dict():
    d = dict(COMMON)
    if DICT_PATH.exists():
        d.update(json.loads(DICT_PATH.read_text(encoding="utf-8")))
    return d


def main():
    mode, src, out_dir = sys.argv[1], Path(sys.argv[2]), Path(sys.argv[3])
    words = json.loads(src.read_text(encoding="utf-8"))
    out_dir.mkdir(parents=True, exist_ok=True)
    review_path = out_dir / "romanize-review.json"
    known = load_dict()

    if mode == "draft":
        review = {}
        for w in words:
            _, core, _ = split_punct(w["text"])
            if DEV.search(core) and core not in review:
                review[core] = known.get(core) or translit(core)
        review_path.write_text(json.dumps(review, ensure_ascii=False, indent=1), encoding="utf-8")
        mapping = review
    elif mode == "apply":
        mapping = json.loads(review_path.read_text(encoding="utf-8"))
        learned = json.loads(DICT_PATH.read_text(encoding="utf-8")) if DICT_PATH.exists() else {}
        for k, v in mapping.items():
            if COMMON.get(k) != v:
                learned[k] = v
        DICT_PATH.write_text(json.dumps(learned, ensure_ascii=False, indent=1, sort_keys=True), encoding="utf-8")
    else:
        sys.exit("mode must be draft or apply")

    out = []
    for w in words:
        lead, core, trail = split_punct(w["text"])
        roman = mapping.get(core, core) if DEV.search(core) else core
        out.append({**w, "text": f"{lead}{roman}{trail}", "orig": w["text"]})
    (out_dir / "transcript.roman.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    left = sum(1 for w in out if DEV.search(w["text"]))
    print(f"{mode}: {len(out)} words, {len(mapping)} unique Hindi words, {left} still in Devanagari -> {out_dir}")


if __name__ == "__main__":
    main()
