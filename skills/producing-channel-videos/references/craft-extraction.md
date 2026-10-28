# Craft extraction

Goal: learn why the reference holds attention, in terms that transfer to a different video. Output is `craft-brief.md`, about half a page plus a beat map.

## Keep (mechanisms)

| Field | Write down | Example of a good note |
|---|---|---|
| Hook type | Which device opens it | "Contrarian claim, then a number" |
| Click promise | What the title/thumbnail promises, in one line | "One fix that stops budgets failing" |
| First 5–15 s | What job those seconds do | "States cost, shows proof object, names the twist" |
| Section jobs | Job of each section, not its title | "Lowers stakes before the reveal" |
| Attention dips | Timecode and why | "~3:40, second example repeats the first" |
| Interrupt types | What they use to recover | "Cold-open callback, zoom punch, on-screen question" |
| Open loops | What is set up and when it is paid | "Item 3 named at 0:05, paid at 0:17" |
| Stakes | What the viewer loses by leaving | "You'll keep making mistake #2" |
| Payoff | Does the ending pay the click? | "Partly; claim without demo" |
| Length and rhythm | Runtime, avg shot length, picture-change frequency | "8:50, ~2.5 s shots, text every ~10 s" |
| Gaps | What they left out or did weakly | "No real numbers, no counter-case" |
| Measured rhythm | From `reference/metrics.json` | "23 cuts/min, median shot 2.1 s, 168 wpm, sparse 3:20–4:30" |
| Visual grammar | From the contact sheets | "~60% B-roll, text card at every number, punch-in on each claim" |

## Do not keep

Sentences, jokes, anecdotes, examples, metaphors, statistics they cite, section titles, the order of reveals, thumbnail layout, footage, music, sound effects, voice, on-screen graphic designs. If a note only makes sense with their content in it, it is content, not craft: rewrite it as a mechanism or drop it.

## Beat vocabulary

Use these labels in the `## Beat map`. One line per section, in the reference's order.

`hook`, `promise`, `context`, `myth`, `problem`, `stake`, `proof`, `story`, `list-item`, `method`, `demo`, `test`, `counter`, `twist`, `reveal`, `recap`, `payoff`, `cta`

Add a new lowercase label only if none fits; keep it one word or hyphenated. The script uses the same vocabulary, and `similarity_guard.py` fails when the script's beat sequence equals the reference's (consecutive repeats collapsed).

## Brief layout

```
# Craft brief: <reference short name>
Hook type: ...
Click promise: ...
First 5–15 s: ...
Section jobs: ...
Attention dips and interrupts: ...
Open loops, stakes, payoff: ...
Length and rhythm (measured): ...
Visual grammar: ...
Gaps we can beat: ...

## Topic map
Viewer questions it answers: ...
Facts it relies on (re-check, do not reuse): ...
Missing or weak: ...
Angle options: 1. ... 2. ... 3. ...

## Beat map
1. beat: hook — ...
2. beat: ...
```

After writing the brief, stop reading the transcript. If something in the brief is unclear later, re-watch for structure, never for lines.
