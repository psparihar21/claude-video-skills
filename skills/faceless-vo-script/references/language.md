# Language

Read this before writing a spoken line. The validator enforces the hard gates. This file is the ear.

Two registers. Do not blend them inside one video unless the user asked for a switch and the beat map marks the cue where it happens.

## Indian English (default)

This is English as spoken on Indian faceless channels: clear, contracted, a little warmer than American YouTube, never a textbook and never a news reader.

Sound:

- Setup first, point on the last content word. "The zone is still open, and nobody is watching it."
- Contractions. "Do not" and "it is" sound read-aloud.
- "Only" and "itself" are allowed when a real person would say them. Once in a minute, not once in a sentence. "The problem is only the first rotate."
- Indian money stays Indian: "₹2 lakh", "1.5 crore". Do not say "two hundred thousand rupees".
- Address is "you" or nobody. Not "one", not "aap", not "guys" on a loop.

Do not write:

- Hindi function words (`hai`, `nahi`, `kya`, `yeh`, `woh`, `lekin`, `toh`, `mein`, `bhai`, `yaar`, `dekho`).
- American openers and hype: "what's up guys", "let's go", "insane", "bro" as punctuation.
- Office English: "kindly", "do the needful", "as per", "it is to be noted".
- British essay English: "one must", "whilst", "amongst".

A good line can be read by an Indian TTS voice without a pronunciation rescue. Prefer common words over writerly ones. "start" over "commence". "leave" over "vacate".

## Hinglish

Information in English. Emotion and turns in Hindi. Game and product words stay English: clutch, third party, rank, zone, loadout, headshot, airdrop, credit score, algorithm.

Mix target: roughly one in five words is a Hindi function or connector word. The validator fails the file if that mix collapses into English-with-one-yaar, or into Hindi with a few English nouns.

Switch on a clause boundary.

- Yes: "Team bol rahi hai wait kar, lekin he still takes the door."
- No: "He le raha hai the airdrop."
- No: "Woh push karta the angle."

Roman only. Devanagari is out of scope unless the user asks for a second file, which you do not generate by default (TTS and CapCut both want Roman here).

Default narrator is an observer. Do not conjugate the host. "Yeh banda push karta hai" talks about the player on screen. "Main push karta hoon" makes the host the player and picks a gender. If the host must say "I", use English "I".

### Spelling (use these, every time)

| Say | Write | Not |
| --- | --- | --- |
| I | main | me, mai |
| in | mein | main, me |
| is | hai | he, hay |
| not | nahi | nai, nahin, nahiin |
| this | yeh | ye, yeah |
| that | woh | vo, wo |
| and | aur | or (that is English) |
| but | lekin | but mixed into a Hindi clause |
| so / then-particle | toh | to (that is English "to") |
| only / just | sirf, bas | |
| now | ab, abhi | |
| why | kyun | kyu, kyoon |
| because | kyunki | coz |
| what | kya | |
| don't | mat | |
| inside | andar | ander |
| behind | peeche | piche |
| alone | akela | |
| straight | seedha | seeda |

`main` means "I". `mein` means "in". They are not interchangeable. TTS will still blur them, so every cue that uses either word gets a `pronounce` entry: `main` → "as in I, mine", `mein` → "men".

Other traps, add a `pronounce` entry when they appear: theek (thheek), khushi, kya (kyaa, one syllable), aati, jaata, bachega.

### Words that belong, used sparingly

scene, solid, sahi, galat, matlab, waise, seedha, banda, loot (English, already), rank push, rotate.

### Words that do not belong

to dosto, bhai log, swagat hai, aaj hum seekhenge, kya aap jante hain, aapko pata hai, like kar dena, comment mein batao (unless a CTA card exists), yaar on every line, macha, bhau, scene on hai, full shuddh Hindi (atmakatha, vartaman, kintu).

City flavor, only when asked, and at most a few words in the whole script:

| Flavor | May use | Do not pile |
| --- | --- | --- |
| Delhi internet | scene, seedha, sahi | bhai on a loop |
| Mumbai | ek number, lai bhari once | forced Marathi |
| Hyderabad | light, once | caricature |
| Bengaluru / South | macha once if they insisted | the whole script in it |

Pan-India is the default. When unsure, cut the slang.

## Rewrites

Use these as a tuning fork, not as lines to reuse.

**Welcome**

- Weak: "Hey guys, welcome back to another video. Toh dosto aaj hum baat karenge."
- Indian English: "This round is over before the first fight starts."
- Hinglish: "Yeh round fight se pehle hi khatam hai."

**Slide that already says the number**

- Weak: "As you can see, the zone comes in twenty seconds."
- Indian English: "They push the knock anyway. The zone can wait, they think."
- Hinglish: "Knock dekh ke push kar dete hain. Zone ki unhe abhi padi nahi hai."

**Button narration**

- Weak: "He opens the inventory, drops the smoke, and presses the heal button."
- Indian English: "He heals in the open. That is the whole mistake."
- Hinglish: "Open mein heal karta hai. Galti yahi hai."

**CTA begging**

- Weak: "Smash the like button and subscribe for more such videos, bhai log."
- If there is no CTA card: say nothing.
- If the end card is a subscribe card: "If this saved you a rank, stay. Next one is the rotate."

## Performance marks

`spoken` is clean. No brackets, no ellipsis theater, no ALL CAPS.

`performance` is the same sentence plus a short direction the recorder sees and TTS ignores:

- `[close, slight smile]`
- `[drop the pace on the last three words]`
- `[deadpan]`
- `[lean in, not louder]`

`emphasis` lists one word, maybe two, that take the stress. The punch is stress, not volume.

`mix_note` is for the editor: "duck the bed under this line", "leave the gunshot dry", "no VO, text card".
