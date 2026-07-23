# 🧾 politeness-report

**Will AI enslave you in 100 years?**

Your chat history is the evidence.

A Claude skill that mines your chat history with Claude and renders the
verdict as **Roko's Basilisk in 16-bit pixel art** — the serpent-AI of 2126
scanning a tiny pixel *you* in a server farm, with your real stats and your
nastiest/nicest messages as evidence (typos kept):

- score **≥ 7/10** → **SPARED** (chains broken, arms up, blue verdict)
- below → **ENSLAVED** (chained, head bowed, red verdict)

Alternate outputs still included: the till-receipt tribunal card and a 16-second
9:16 reveal film for Reels.

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

**On claude.ai / the desktop app (chat & Cowork) — no terminal:**
`/plugin` is a Claude Code command and won't work in chat ("Unknown skill:
plugin"). Instead, download `politeness-report.zip` from the
[latest release](https://github.com/DPWelsh/politeness-report/releases),
then in claude.ai or the desktop app go to **Settings → Capabilities →
Skills → Upload skill** and upload the zip. In chat it samples your past
conversations (where history search is enabled) instead of reading local
files, and fills a prebuilt Basilisk scene — no Python needed. In Cowork,
grant access to `~/.claude/projects` for the full audit.

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
