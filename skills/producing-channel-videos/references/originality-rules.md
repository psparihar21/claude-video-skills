# Originality rules

The craft brief may describe structure. The spoken script may not reuse the reference's sentences, jokes, anecdotes, metaphors, examples, statistics, or order of reveals.

## Same topic, new video

Covering the same topic is fine; topics belong to nobody. What must be new is the take: the angle, the examples, the proof, the order, and the words. Start from the topic map in the craft brief, re-research every fact it lists, and lead with what the reference missed or got outdated.

## Must be new

- **Promise.** A new promise, or a sharper version the user agrees with. Not the reference title reworded.
- **Examples and proof.** From the user's life, work, data, or fresh research the user can verify. A statistic the reference cited is not available even if true; find the primary source independently and only use it if the user's angle needs it.
- **Running order.** Different beat sequence. If the user's angle naturally lands on the same order, change where proof or the stake sits.
- **Reveal order.** If the reference withholds item X until the end, do not withhold the equivalent item in the same slot.
- **Jokes and metaphors.** Write from the style card's humor notes, not from the reference.

## Spoken language

Contractions, short lines, one idea per line. Read each line at the style card's pace; cut anything the user would not say aloud. Use words from the card's "always" list; never use the "never" list.

## Required structure

1. Hook in the first 5–10 s that delivers on the title.
2. One retention line right after: what the viewer gets by staying.
3. An interrupt every 60–90 s, written into the script as `[INTERRUPT: visual | question | stake | graphic]`.
4. One ending that pays off the click.
5. One clear CTA, in the user's style.

## Claims

Every factual claim gets a source the user can check, noted in the Source column or a footnote under the table. Shaky or unsourced claims get `[VERIFY: ...]` and go to the user before the script locks. Never claim the user did, owns, or believes something not in their material or answers.

## Guard

Run `scripts/similarity_guard.py <production-folder>` before showing the script. It fails on any shared 12-word window (after lowercasing and stripping punctuation) and on an identical beat sequence. Fix by rewriting the line in the user's own words, or moving a beat. Do not "fix" by swapping synonyms into the same sentence; that is still the reference's sentence.

If no reference transcript exists (the reference was watched only), the guard still checks beat order against the craft brief and reports that the text check was skipped. Say so when showing the script.
