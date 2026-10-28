"""uv run mkscript2.py -> vo/hi-v3 and vo/en-v1 (edit.json + 03-script.json)"""
import json
from pathlib import Path
R = (Path.home() / "Videos/pipeline/ps-nov26/vo")
SRC = "PS Store removal list (PlayStation LifeStyle, Oct 2026); posters on screen"
ROLE = ["hook","line","line","line","line","line","line","cta"]
HI = [
 "PS Subscription walon ke liye bura news hai, seventeen November tak twelve game Extra, Premium aur Deluxe se hat jaayenge.",
 "GTA six aane se pehle Rockstar ke sabse bade game, Red Dead Redemption two aur GTA five, PS Subscription se hat rahe hain.",
 "Sports lovers ke liye bhi sad news hai, Football Manager twenty six aur Cricket twenty four bhi ja rahe hain.",
 "Saath mein The Talos Principle two, Rock of Ages three, Monster Boy, Hotshot Racing, aur Earth Defense Force four point one bhi jaa rahe hain.",
 "Phir hai Thank Goodness You're Here, ye khelne mein sach mein bahut maza wala game hai, agar aapne nahi khela toh zaroor try karein.",
 "Aur Rapala Fishing Pro Series, aur Yet Another Zombie Defense HD bhi isi list mein hain.",
 "Toh jo bhi aapki wishlist mein hai, seventeen November se pehle khel lijiye, phir mauka nahi milega.",
 "Video pasand aaye toh like karein, Pushpstation ko subscribe karein, aur gaming news aur interesting gameplay ke liye follow karein.",
]
EN = [
 "Bad news for PS Subscription members. Twelve games leave Extra, Premium and Deluxe by seventeen November.",
 "Just before GTA six arrives, Rockstar's biggest games, Red Dead Redemption two and GTA five, are leaving the PS Subscription.",
 "Sad news for sports lovers too. Football Manager twenty six and Cricket twenty four are going as well.",
 "Also leaving are The Talos Principle two, Rock of Ages three, Monster Boy, Hotshot Racing, and Earth Defense Force four point one.",
 "Thank Goodness You're Here was really fun to play. If you have not tried it yet, please do.",
 "And Rapala Fishing Pro Series and Yet Another Zombie Defense HD are leaving too.",
 "So whatever is on your wishlist, play it before seventeen November, because after that the chance is gone.",
 "If you liked the video, hit like, subscribe to Pushpstation, and follow for more gaming news and interesting gameplays.",
]
def mk(name, lines, reg, wps):
    t = 0.0; shots = []; cues = []
    for i, sp in enumerate(lines, 1):
        n = len(sp.replace("-", " ").split()); d = round(n / wps + 0.5, 2); s, e = round(t, 2), round(t + d, 2)
        shots.append({"id": f"s0{i}", "in_sec": s, "out_sec": e, "visual": "game poster(s) on blurred poster backdrop", "on_screen_text": "", "energy": "hook" if i == 1 else "build", "cut_type": "hard"})
        cues.append({"id": f"c0{i}", "shot_id": f"s0{i}", "role": ROLE[i - 1], "in_sec": round(s + .12, 2), "out_sec": round(e - .18, 2), "spoken": sp,
                     "performance": "[close-mic, brisk]", "emphasis": [], "fact_source": SRC if i < 8 else "", "mix_note": ""})
        t = e
    o = R / name; o.mkdir(parents=True, exist_ok=True)
    edit = {"title": "PS Plus Nov 2026 leaving - Short", "slug": name, "format": "faceless-explainer", "platform": "youtube-shorts", "video_path": "", "video_duration_sec": round(t, 2), "shots": shots}
    sc = {"title": edit["title"], "slug": name, "status": "final", "register": reg, "format": "faceless-explainer", "platform": "youtube-shorts", "video_duration_sec": round(t, 2),
          "persona": "Pushpstation observer, close-mic, brisk news read.", "mic_note": "Say it your way. Add your own reaction at the fun-game line.", "pronounce": [], "cues": cues, "intentional_silence": [], "recut_requests": []}
    (o / "edit.json").write_text(json.dumps(edit, indent=1), encoding="utf8"); (o / "03-script.json").write_text(json.dumps(sc, indent=1, ensure_ascii=False), encoding="utf8")
mk("hi-v3", HI, "hinglish", 2.4); mk("en-v1", EN, "indian-english", 2.5)
