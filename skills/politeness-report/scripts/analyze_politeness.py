#!/usr/bin/env python3
"""
analyze_politeness.py — mine your Claude Code history for how you *actually* talk
to your AI assistant, and emit a compact stats + quotes bundle a model can turn
into a funny "report card".

Everything runs locally. It reads your own transcripts under ~/.claude/projects
and writes a single JSON summary. No message text leaves your machine until you
(optionally) hand the summary to a model to write the card.

Usage:
    python3 analyze_politeness.py                 # scans ~/.claude/projects
    python3 analyze_politeness.py --root PATH      # custom transcript root
    python3 analyze_politeness.py --out report.json --tz-offset 8

Then point a (cheap) model at the JSON and ask it for a report card.
"""
import argparse, json, glob, os, re, random
from collections import Counter

# --- strings the harness injects that are NOT you talking ---------------------
SYS_PREFIXES = (
    "<system-reminder>", "Caveat:", "<command-name>", "<command-message>",
    "<local-command-stdout>", "<local-command-stderr>", "<user-prompt-submit-hook>",
    "[Request interrupted", "<bash-", "<user-memory-input>", "<session-start-hook>",
    "This session is being continued", "<persisted-output>", "<task-notification>",
    "<budget-", "<post-tool", "<pre-tool",
)

def is_system_string(s: str) -> bool:
    st = s.lstrip()
    return st.startswith(SYS_PREFIXES) or "SessionStart:" in st[:120] or "hook success" in st[:120]

def extract_messages(root: str):
    """Yield genuine human-typed user messages (dedup'd) from all transcripts."""
    seen = set()
    for path in glob.glob(os.path.join(root, "*", "*.jsonl")):
        proj = os.path.basename(os.path.dirname(path))
        # automated / background session dirs are not you talking
        if "observer" in proj or "runner" in proj:
            continue
        try:
            fh = open(path, "r", errors="replace")
        except OSError:
            continue
        with fh:
            for line in fh:
                if '"type":"user"' not in line and '"type": "user"' not in line:
                    continue
                try:
                    d = json.loads(line)
                except ValueError:
                    continue
                if d.get("type") != "user" or d.get("isSidechain"):
                    continue
                # sdk/system prompt sources are tool traffic, not typed messages
                if d.get("promptSource") in ("sdk", "system"):
                    continue
                content = d.get("message", {}).get("content")
                if isinstance(content, str):
                    text = content
                elif isinstance(content, list):  # image-caption messages arrive as a list
                    text = " ".join(
                        p.get("text", "") for p in content
                        if isinstance(p, dict) and p.get("type") == "text"
                    )
                else:
                    continue
                text = text.strip()
                if not text or is_system_string(text) or text in seen:
                    continue
                seen.add(text)
                yield {"ts": d.get("timestamp", ""), "proj": proj, "text": text}

# --- lexicons -----------------------------------------------------------------
WARMTH = {
    "thank you": 3, "thanks": 2, "legend": 3, "genius": 3, "amazing": 2, "awesome": 2,
    "brilliant": 3, "appreciate": 3, "great job": 3, "great work": 3, "well done": 3,
    "perfect": 2, "love it": 3, "love this": 3, "nice work": 2, "you're the best": 4,
    "wonderful": 3, "fantastic": 3, "excellent": 2, "good job": 2, "nailed it": 3,
    "you rock": 4, "🙏": 3, "❤": 4, "🥰": 4, "🔥": 1, "haha": 1, "hahah": 1, "lol": 1,
}
HEAT = {
    "wtf": 3, "ffs": 4, "useless": 4, "stupid": 4, "idiot": 4, "pathetic": 4, "garbage": 3,
    "rubbish": 3, "terrible": 3, "awful": 3, "for fuck": 4, "fucking": 3, "shitty": 3,
    "no you": 2, "you didn't": 2, "you broke": 3, "you keep": 2, "did you even": 4,
    "why would you": 3, "not what i asked": 4, "come on": 2, "seriously": 2,
    "disappoint": 3, "🙄": 3, "😡": 4, "🤦": 3, "a disaster": 2, "this is chaos": 2,
}
SOFTEN = re.compile(r"(?<![a-z])(please|plz|pls)(?![a-z])", re.I)
TEAM   = re.compile(r"(?<![a-z])(we|we're|lets|let's|our|us)(?![a-z])", re.I)

def score(text, table):
    low = text.lower()
    total, hits = 0, []
    for k, w in table.items():
        c = low.count(k)
        if c:
            total += w * c
            hits.append(k)
    return total, hits

def word_count(msgs, pat):
    return sum(len(pat.findall(m["text"])) for m in msgs)

def main():
    ap = argparse.ArgumentParser(description="Analyze how you talk to Claude Code.")
    ap.add_argument("--root", default=os.path.expanduser("~/.claude/projects"),
                    help="Transcript root (default: ~/.claude/projects)")
    ap.add_argument("--out", default="politeness_report_data.json")
    ap.add_argument("--tz-offset", type=int, default=0,
                    help="Hours to add to UTC timestamps for your local hour-of-day stats.")
    ap.add_argument("--max-quote-len", type=int, default=350)
    ap.add_argument("--sample", type=int, default=60,
                    help="How many random short messages to include for typo/quote mining.")
    args = ap.parse_args()

    if not os.path.isdir(args.root):
        raise SystemExit(f"No transcript folder at {args.root}. "
                         f"Point --root at your Claude Code projects dir.")

    msgs = list(extract_messages(args.root))
    if not msgs:
        raise SystemExit("Found transcripts but no human-typed messages. Nothing to grade!")
    msgs.sort(key=lambda m: m["ts"])

    # short messages = things you actually said (exclude big pastes/logs/drafts)
    short = [m for m in msgs if len(m["text"]) <= 1200]

    for m in short:
        m["warm"], m["warm_hits"] = score(m["text"], WARMTH)
        m["heat"], m["heat_hits"] = score(m["text"], HEAT)

    # Gratitude aimed at the assistant is measured on SHORT messages only —
    # long pastes (emails, scripts) are full of "thank you" that isn't you.
    thanks_short = sum(m["text"].lower().count("thank you") for m in short)

    hours = Counter()
    for m in msgs:
        try:
            hours[(int(m["ts"][11:13]) + args.tz_offset) % 24] += 1
        except (ValueError, IndexError):
            pass

    openers = Counter()
    for m in short:
        w = re.findall(r"[a-z']+", m["text"].lower())
        if w:
            openers[w[0]] += 1

    def top(bucket_key, n=8):
        arr = [m for m in short if m[bucket_key] > 0]
        arr.sort(key=lambda m: (-m[bucket_key], len(m["text"])))
        return [{"ts": m["ts"][:10], "proj": m["proj"],
                 "hits": m[bucket_key + "_hits"],
                 "text": m["text"][:args.max_quote_len]} for m in arr[:n]]

    rnd = random.Random(1234)  # deterministic sample so re-runs are stable
    pool = [m for m in short if 12 <= len(m["text"]) <= 220]
    wildcard = rnd.sample(pool, min(args.sample, len(pool)))

    total = len(msgs)
    # Behavioral stats are measured on SHORT messages — the things you actually
    # typed. Big pastes (emails, docs, logs) are full of "please"/"just"/"thank
    # you" that isn't you talking, and would wildly inflate every count.
    denom = len(short)
    soften_msgs = sum(1 for m in short if SOFTEN.search(m["text"]))
    team_msgs = sum(1 for m in short if TEAM.search(m["text"]))

    out = {
        "meta": {
            "total_messages": total,
            "short_messages": len(short),
            "date_range": [msgs[0]["ts"][:10], msgs[-1]["ts"][:10]],
            "projects": len({m["proj"] for m in msgs}),
        },
        "stats": {
            "please_plz_pls": word_count(short, SOFTEN),
            "pct_messages_softened": round(100 * soften_msgs / denom, 1),
            "gratitude_to_assistant_(short_msgs)": thanks_short,
            "collaborative_we_lets_our": word_count(short, TEAM),
            "pct_messages_collaborative": round(100 * team_msgs / denom, 1),
            "just_count": word_count(short, re.compile(r"(?<![a-z])just(?![a-z])", re.I)),
            "genuine_wtf": word_count(short, re.compile(r"(?<![a-z])wtf(?![a-z])", re.I)),
            "top_openers": openers.most_common(12),
            "hour_of_day": dict(sorted(hours.items())),
        },
        "quotes": {
            "warmest": top("warm"),
            "spiciest": top("heat"),
            "wildcard_sample_for_typo_and_quote_mining": [
                {"ts": m["ts"][:10], "proj": m["proj"], "text": m["text"]} for m in wildcard
            ],
        },
    }
    with open(args.out, "w") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)

    print(f"✅ Scanned {total} genuine messages across {out['meta']['projects']} projects "
          f"({out['meta']['date_range'][0]} → {out['meta']['date_range'][1]}).")
    print(f"   please/plz/pls: {out['stats']['please_plz_pls']}  |  "
          f"'thank you' to Claude: {thanks_short}  |  wtf: {out['stats']['genuine_wtf']}  |  "
          f"'just': {out['stats']['just_count']}")
    print(f"📄 Wrote {args.out} — hand this to a (cheap) model and ask for a report card.")

if __name__ == "__main__":
    main()
