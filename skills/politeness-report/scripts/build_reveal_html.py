#!/usr/bin/env python3
"""
build_reveal_html.py — render the 9:16 VERDICT REVEAL: a 16-second looping,
self-playing sequence designed to be screen-recorded for Reels/Stories.

Beats (tuned to short-video research — hook by 1s, one focal element per beat,
safe zones respected): HOOK → STAKES → DELIBERATION (their quotes flicker past)
→ REVEAL (stamp slam + score) → PROOF (worst vs best exhibit) → END CARD
(the screenshot frame, with the comment-keyword CTA).

Driven by the SAME card.json as build_card_html.py — no extra authoring.
Extra optional fields it reads:
  "hook":        "Will AI enslave you in 100 years?"   // beat-1 line
  "hook_accent": "enslave you"                          // substring tinted
  "evidence_n":  "1,292"                                // beat-2 big number
  "evidence_label": "messages analysed",
  "cta":         "",                                   // optional end-card CTA
  "site":        "labs.routiq.ai/naughty-or-nice"       // end-card footer

Pure CSS loop — records fine even with JavaScript disabled; tap restarts.
Usage:
    python3 build_reveal_html.py card.json --out reveal.html [--theme theme.json]
"""
import argparse, json, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_card_html import build_font_css, build_theme_css, esc, escr  # noqa: E402

DEFAULT_TEMPLATE = os.path.join(os.path.dirname(__file__), "..", "assets", "reveal_template.html")

def hook_html(card):
    hook = card.get("hook", "Will AI enslave you in 100 years?")
    accent = card.get("hook_accent")
    out = esc(hook)
    if accent and accent in hook:
        out = out.replace(esc(accent), f'<span class="accent">{esc(accent)}</span>', 1)
    return out

def evidence_bits(card):
    n, lbl = card.get("evidence_n"), card.get("evidence_label", "messages analysed")
    if not n:
        for k, v in card.get("meta", []):
            if any(w in str(k).upper() for w in ("EVIDENCE", "MSGS", "MESSAGES")):
                m = re.search(r"[\d,\.]+", str(v))
                if m:
                    n = m.group(0)
                    break
    return n or "ALL OF IT", lbl

def flashes(card):
    """Three lines that flicker during deliberation — their own words."""
    pool = []
    for ex in card.get("exhibits", []):
        pool.extend(ex.get("quotes", []))
    if not pool:
        pool = [card.get("subtitle", ""), card.get("teacher_comment", ""), ""]
    pool = [q for q in pool if q][:3]
    while len(pool) < 3:
        pool.append("…")
    return pool

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("card_json")
    ap.add_argument("--out", default="reveal.html")
    ap.add_argument("--template", default=DEFAULT_TEMPLATE)
    ap.add_argument("--theme", help="Optional theme.json brand overlay")
    args = ap.parse_args()

    with open(args.card_json, encoding="utf-8") as f:
        card = json.load(f)
    for key in ("rows", "score"):
        if key not in card:
            sys.exit(f"card.json is missing required key: {key!r}")

    theme = {}
    if args.theme:
        with open(args.theme, encoding="utf-8") as f:
            theme = json.load(f)

    score = float(card["score"])
    score_max = float(card.get("score_max", 10))
    stamp = card.get("stamp") or ("SPARED" if score / score_max >= 0.7 else "ENSLAVED")
    verdict_color = "var(--hot)" if stamp.upper() in ("SPARED", "NICE") else "var(--stampc)"

    ev_n, ev_lbl = evidence_bits(card)
    f1, f2, f3 = flashes(card)

    exhibits = card.get("exhibits", [])
    xa = exhibits[0] if exhibits else {"label": "On record", "quotes": [card.get("subtitle", "")]}
    xb = exhibits[1] if len(exhibits) > 1 else {"label": "Also on record", "quotes": [""]}

    chips = "".join(
        f'<span class="g">{esc(r.get("category","").split("/")[0].strip())} '
        f'<b>{esc(r.get("grade",""))}</b></span>'
        for r in card.get("rows", [])[:4]
    )

    with open(args.template, encoding="utf-8") as f:
        tpl = f.read()
    if "__STAMP__" not in tpl:
        sys.exit("Template placeholders missing — wrong template file?")

    filled = (tpl
        .replace("/*__FONT_CSS__*/", build_font_css(theme.get("fonts") or {}))
        .replace("/*__THEME_CSS__*/", build_theme_css(theme))
        .replace("__PAGE_TITLE__", esc(card.get("title", "Verdict")) + " — reveal")
        .replace("__BRANDLINE__", esc(card.get("brandline", "SESSION VERDICT")))
        .replace("__HOOK__", hook_html(card))
        .replace("__EVIDENCE_N__", esc(ev_n))
        .replace("__EVIDENCE_LBL__", esc(ev_lbl))
        .replace("__CASE__", esc(card.get("case", "")))
        .replace("__FLASH1__", escr(f1))
        .replace("__FLASH2__", escr(f2))
        .replace("__FLASH3__", escr(f3))
        .replace("__VERDICT_COLOR__", verdict_color)
        .replace("__STAMP__", esc(stamp))
        .replace("__SCORE_NUM__", f"{score:.1f}")
        .replace("__SCORE_MAX__", f"{score_max:g}")
        .replace("__XA_LABEL__", esc(xa.get("label", "")))
        .replace("__XA_QUOTE__", escr((xa.get("quotes") or [""])[0]))
        .replace("__XB_LABEL__", esc(xb.get("label", "")))
        .replace("__XB_QUOTE__", escr((xb.get("quotes") or [""])[0]))
        .replace("<!--__GRADE_CHIPS__-->", chips)
        .replace("__CTA__", esc(card.get("cta", "")))
        .replace("__SITE__", esc(card.get("site", "")))
    )
    leftovers = re.findall(r"__[A-Z_]+__", filled)
    if leftovers:
        sys.exit(f"Unfilled placeholders: {sorted(set(leftovers))}")

    with open(args.out, "w", encoding="utf-8") as f:
        f.write(filled)
    kb = os.path.getsize(args.out) / 1024
    print(f"✅ Wrote {args.out} — 16s looping 9:16 reveal, verdict {stamp} {score:g}/{score_max:g} ({kb:.0f} KB).")
    print("   Open fullscreen, screen-record one loop; tap restarts the cycle.")

if __name__ == "__main__":
    main()
