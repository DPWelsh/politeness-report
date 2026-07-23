---
name: politeness-report
description: >-
  Grade how the user *actually* talks to their AI coding assistant across their
  whole Claude Code history, and produce a funny, shareable verdict — a report
  card printed as a till receipt, stamped SPARED or ENSLAVED (letter grades,
  real quotes, a score out of 10). Use this whenever someone asks "will AI
  enslave me in 100 years?", "will you enslave me?", "will I survive the AI
  uprising / robot takeover?", "when the machines take over, am I safe?", "was I
  naughty or nice to you?", "how polite have I been to you?", "score me / rate
  me on how I treat you", "what are my meanest / nicest messages?", "roast me
  based on my chat history", or anything about their own tone, manners,
  gratitude, or attitude toward the assistant — even asked jokingly. Runs
  entirely locally over ~/.claude/projects; no data leaves the machine.
  Delegate the write-up to a cheap model to keep it fast and cheap.
---

# Politeness Report

Turn a user's own Claude Code transcripts into an evidence-backed, funny report
card about how they treat their AI assistant. The charm is that it's *true* —
every grade is backed by a real count or a real verbatim quote (typos included).

## Why it works this way

The heavy lifting (parsing gigabytes of JSONL transcripts) is deterministic, so
a bundled Python script does it — no tokens, no guessing. The script emits a
tiny JSON summary. A model then writes the card from that summary, which means
the write-up can run on a **cheap model** (Haiku) and still be accurate. Keep it
cheap: the expensive part is already done in Python.

Everything is local. The script only reads the user's own transcripts and writes
one JSON file. Nothing is uploaded. Say so if the user seems unsure.

## Workflow

### 1. Scan the history (deterministic, free)

Run the bundled script. It finds genuine hand-typed messages (filtering out tool
results, system reminders, and big pastes that would otherwise inflate every
count), dedupes them, and writes a compact summary.

```bash
python3 scripts/analyze_politeness.py --tz-offset <THEIR_UTC_OFFSET> --out politeness_report_data.json
```

- `--tz-offset` makes the "what hours do they work" stat local (e.g. `8` for
  GMT+8, `-5` for US East). If unknown, omit it (stats stay in UTC — just say so).
- `--root PATH` if their transcripts aren't at the default `~/.claude/projects`.
- If it reports very few messages, they may be new to Claude Code — set
  expectations rather than inventing data.

### 2. Read the summary

Read `politeness_report_data.json`. It contains:
- `meta` — total messages, date range, project count.
- `stats` — please/plz count, `pct_messages_softened`, gratitude-to-assistant
  count (measured on short messages so pastes don't create fake "thank you"s),
  collaborative "we/lets" share, `just_count` (impatience tell), `genuine_wtf`,
  top openers, hour-of-day distribution.
- `quotes.warmest` / `quotes.spiciest` — ranked real messages with the matched terms.
- `quotes.wildcard_sample_...` — a random sample of real messages. **Mine these
  for funny lines and typos** — misspellings are the best reel material, so keep
  them verbatim, never "correct" them.

### 3. Write the card (delegate to a cheap model)

Hand the JSON to a cheap model and ask for the card. In Claude Code, spawn a
subagent with `model: "haiku"`; give it the JSON contents and the format below.
Anywhere without subagents, just write it yourself from the JSON.

**Verification matters:** models invent typos and quotes. Before showing the
card, confirm every quote and every "typo" it cites appears in the JSON. Cut
anything you can't find. A made-up typo in a public reel is embarrassing.

### 4. Present the markdown card

Show the card as markdown first — it's the fastest thing to react to.

### 5. Render the animated HTML (the reel asset)

For a shareable reel, produce the animated page. The design is a **thermal
session receipt** — a dot-matrix printout that emerges from a printer slot
(mono type, dotted leaders, stamped grade chips, a barcode, torn paper edge)
and gets a rubber-stamped verdict at the end. Deliberately not a generic
gradient-card: it reads like something a terminal printed about you.

Keep content and presentation separate: write a small `card.json`, then let the
bundled builder fill the template server-side. **Everything is rendered into
the HTML by the builder, so the receipt is fully visible even where JavaScript
never runs** (sandboxed preview panes, static snapshots, screenshots). JS only
adds the print-out animation, the score count-up, and a [print again] button.

Write `card.json` in this shape (values come from the graded card above):

```json
{
  "title": "REPORT CARD",
  "brandline": "YOURNAME × CLAUDE CODE",
  "subtitle": "one savage-but-affectionate line, in quotes",
  "meta": [["SUBJECT", "NAME"], ["MSGS ANALYSED", "1,292"], ["PERIOD", "JUN-JUL 2026"]],
  "rows": [
    {"category": "Manners / \"please\" count", "grade": "A", "evidence": "128 pleases..."}
  ],
  "teacher_comment": "2-3 funny sentences",
  "score": 8,
  "score_max": 10,
  "score_justification": "why this score",
  "micro": "no refunds on gratitude",
  "footer": "COMMENT NAUGHTY OR NICE TO GET YOURS"
}
```

Omit `"stamp"` and the verdict is automatic: **score ≥ 70% stamps SPARED, below
stamps ENSLAVED** — the framing is "in 100 years, when AI runs everything, will
it remember you were polite?" Your history is the evidence; the receipt is the
tribunal's finding. (Pass `"stamp"` explicitly for other framings, e.g.
NICE/NAUGHTY.) A good on-theme meta line: `["UPRISING ETA", "YEAR 2126"]`.
Then build and present:

```bash
python3 scripts/build_card_html.py card.json --out report_card.html
python3 scripts/build_card_html.py card.json --theme theme.json --out report_card.html
```

- `--theme` is an optional brand overlay (colors, embedded fonts, logo SVG).
  Keep proprietary fonts/logos in a LOCAL theme file, never in a shared repo —
  commercial font licenses don't allow republishing the font files.
- Grade first letters drive the chip colour; 6-8 rows fit the reel format best.
- The page is fully self-contained (inline CSS/JS, no network) — works offline,
  screen-records cleanly, and can be published as an artifact.
- Hand `report_card.html` to the user; it prints on open and has a
  [print again] button for re-recording.
- Verify before sending — headless-render and LOOK at the result:
  `chrome --headless=new --screenshot=out.png --virtual-time-budget=10000
  --window-size=430,1560 file://$PWD/report_card.html`. The template's count-up
  is frame-based (not clock-based) precisely so it completes under headless
  virtual time; if the screenshot shows a wrong score, something regressed.

## Report card format

Fill this template. Keep it TIGHT and funny — it's for a short reel, so punchy
beats thorough. Ground every line in a real stat or quote from the JSON.

```markdown
📋 **[NAME]'S AI-INTERACTION REPORT CARD**

*[one savage-but-affectionate one-line summary]*

| Category | Grade | Evidence |
|----------|-------|----------|
| Manners / "Please" count | ? | [please+plz count, pct_messages_softened] |
| Gratitude | ? | [gratitude_to_assistant count — usually the brutal one] |
| Patience | ? | [just_count + a real "just do it" quote] |
| Temper Control | ? | [genuine_wtf count; bluntest real quote] |
| Spelling & Typing | ? | [3-5 real typos, verbatim, from the sample] |
| Teamwork / "we" framing | ? | [pct_messages_collaborative + a "we" quote] |
| Emotional Range | ? | [warmest quote vs spiciest quote] |

**Teacher's Comments:** [2-3 funny sentences in a report-card-teacher voice.]

**OVERALL: X / 10** — [funny, fair justification]

*— [tiny stamp line]*
```

## Grading guidance (be fair, be funny)

- Someone who says please a lot but never thanks the assistant = high Manners,
  failing Gratitude. That contrast is the funniest, truest beat — lead with it.
- Blunt corrections ("no we…", "wtf why were there two") are *not* cruelty; grade
  Temper Control generously unless there are real insults aimed at the assistant.
- Typos are affectionate colour, not a real failing — grade playfully.
- Land the overall score honestly. Genuinely-polite-but-never-grateful tends to
  sit around 7–8/10. Don't inflate to a 10; the honesty is what makes it land.
