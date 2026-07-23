# 🧾 politeness-report

**Will AI enslave you in 100 years?**

Your chat history is the evidence.

A [Claude Code](https://claude.com/claude-code) skill that mines your *entire*
chat history with Claude and prints the **tribunal's verdict** as an animated
session receipt — thermal-printer style: real stats, your nastiest and nicest
messages as exhibits (typos kept), letter grades, redaction bars, a case
number, and a rubber-stamped verdict:

- score **≥ 7/10** → stamped **SPARED**
- below → stamped **ENSLAVED**

Every line is backed by a real count or a real quote from your own transcripts.
That's the charm. Sample verdicts from the first victim:

> **Gratitude to Claude: F** — *ZERO thank-yous in 1,292 messages.*
> **Manners: A** — *says "please" 128 times.*
> **Brand Loyalty: D** — *misspelled his own company.*

## Install

**As a plugin (recommended):**
```
/plugin marketplace add DPWelsh/politeness-report
/plugin install politeness-report@politeness-report
```

**As a plain skill:**
```bash
git clone https://github.com/DPWelsh/politeness-report /tmp/politeness-report
cp -r /tmp/politeness-report/skills/politeness-report ~/.claude/skills/
```

Then just ask Claude Code: **"will you enslave me in 100 years?"** — or
*"was I naughty or nice to you?"*,
*"score me on how I treat you"*, *"roast me based on my chat history"*,
*"make me an AI report card"*.

## Privacy

Runs **100% locally**. The analysis script only reads your own transcripts
under `~/.claude/projects` and writes one small JSON summary on your machine.
Nothing is uploaded. The model that writes the jokes only ever sees that
summary (counts + short quotes), never your full history.

## What it measures

| | |
|---|---|
| **Manners** | how often you soften commands with please/plz |
| **Gratitude** | how often you actually thank the assistant (brace yourself) |
| **Patience** | your "just do it" count |
| **Temper** | genuine frustration vs. plain blunt corrections |
| **Spelling** | your personal typo hall of fame, verbatim |
| **Teamwork** | "we/let's" framing vs. orders |

## How it works

1. `scripts/analyze_politeness.py` parses every `~/.claude/projects/**/*.jsonl`,
   keeps only genuine hand-typed messages (drops tool traffic, system reminders,
   and big pastes that would inflate every count), dedupes, and writes a compact
   JSON of stats + ranked quotes. Pure Python stdlib — no installs.
2. A model (a cheap one is plenty) writes the card content into a `card.json`.
3. `scripts/build_card_html.py` renders the animated receipt — fully
   self-contained HTML, no network, works offline. The page is complete even
   with JavaScript disabled; JS adds the print-out animation, the score
   count-up, and a `[ print again ]` button for screen-recording.

## Fonts & themes

The receipt intentionally uses your **system monospace** font — no font files
ship with this skill, nothing to install, and the thermal-printout aesthetic is
designed for it. If you want your own branding (colors, an embedded font, a
logo), pass a local theme overlay:

```bash
python3 scripts/build_card_html.py card.json --theme my_theme.json
```

Themes are **local files by design**: commercial font licenses generally don't
allow committing font files to a public repo, so keep brand overlays out of
forks and PRs. See the theme schema in `scripts/build_card_html.py`.

## License

MIT (the code — bring your own fonts). Roast yourself responsibly.
