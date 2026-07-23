#!/usr/bin/env python3
"""
build_card_html.py — render the politeness report as a self-contained animated
"session receipt" HTML page (thermal-printout aesthetic, reel-ready).

Robustness guarantee: ALL content is rendered into the HTML by this script, so
the receipt is fully visible even where JavaScript never runs (sandboxed
preview panes, static snapshots, screenshots). JS only adds the print-out
animation, the score count-up, and a [print again] button.

card.json schema:
{
  "title": "REPORT CARD",
  "subtitle": "one savage-but-affectionate line",
  "brandline": "ROUTIQ x CLAUDE CODE",              // optional masthead kicker
  "meta": [["SUBJECT", "DANIEL"], ["MSGS ANALYSED", "1,292"]],   // optional
  "rows": [ {"category": "Manners", "grade": "A", "evidence": "..."}, ... ],
  "teacher_comment": "2-3 funny sentences",
  "score": 8, "score_max": 10,
  "score_justification": "why this score",
  "micro": "small print under the barcode",          // optional
  "footer": "COMMENT SPARE ME TO GET YOURS",         // optional CTA line
  "stamp": "SPARED"   // optional — omitted = auto: score >= 70% SPARED else ENSLAVED
}

Optional theme.json (brand overlay — keep proprietary fonts/logos OUT of any
public repo; a theme is a local file):
{
  "colors": {"paper": "#ededeb", "ink": "#1a1c12", "stampc": "#C98B7A", ...},
  "grade_colors": {"A": "#7ba2e0", "F": "#472424"},
  "fonts": {
    "heading": "'Raptor V3', monospace",
    "faces": [{"family": "Raptor V3", "weight": "900", "path": "/abs/raptor.woff2"}]
  },
  "logo_svg_path": "/abs/logomark.svg",
  "logo_fill": "#1a1c12"
}

Usage:
    python3 build_card_html.py card.json --out report_card.html
    python3 build_card_html.py card.json --theme theme.json --out report_card.html
"""
import argparse, base64, html, json, os, re, sys

DEFAULT_TEMPLATE = os.path.join(os.path.dirname(__file__), "..", "assets", "report_card_template.html")
COLOR_VARS = ("bg1", "bg2", "paper", "ink", "dim", "rule", "stampc", "hot")

def esc(s):
    return html.escape(str(s), quote=False)

def escr(s):
    """esc + convert [REDACTED] tokens into classified-document black bars."""
    return esc(s).replace("[REDACTED]", '<span class="redact">████████</span>')

def build_font_css(fonts):
    css = []
    for face in fonts.get("faces", []):
        path = face["path"]
        ext = os.path.splitext(path)[1].lstrip(".").lower()
        fmt = {"woff2": "woff2", "woff": "woff", "otf": "opentype", "ttf": "truetype"}.get(ext, ext)
        with open(path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        css.append(
            f"@font-face{{font-family:'{face['family']}';"
            f"src:url(data:font/{ext};base64,{b64}) format('{fmt}');"
            f"font-weight:{face.get('weight', 'normal')};font-style:{face.get('style', 'normal')};"
            f"font-display:block}}"
        )
    return "\n".join(css)

def build_theme_css(theme):
    lines = []
    for k, v in (theme.get("colors") or {}).items():
        if k in COLOR_VARS:
            lines.append(f"--{k}:{v};")
    fonts = theme.get("fonts") or {}
    if fonts.get("heading"):
        lines.append(f"--font-head:{fonts['heading']};")
    if fonts.get("mono"):
        lines.append(f"--font-mono:{fonts['mono']};")
    for letter, color in (theme.get("grade_colors") or {}).items():
        L = letter.strip().upper()[:1]
        if L in "ABCDF":
            lines.append(f"--g{L}:{color};")
    return ":root{" + "".join(lines) + "}" if lines else ""

def build_logo(theme):
    path = theme.get("logo_svg_path")
    if not path:
        return ""
    with open(path, encoding="utf-8") as f:
        svg = f.read()
    svg = re.sub(r"<\?xml[^>]*\?>", "", svg).strip()
    fill = theme.get("logo_fill")
    if fill:
        svg = re.sub(r"<style>.*?</style>", "", svg, flags=re.S)
        svg = re.sub(r'class="[^"]*"', f'fill="{fill}"', svg)
    return svg

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("card_json")
    ap.add_argument("--out", default="report_card.html")
    ap.add_argument("--template", default=DEFAULT_TEMPLATE)
    ap.add_argument("--theme", help="Optional theme.json brand overlay")
    args = ap.parse_args()

    with open(args.card_json, encoding="utf-8") as f:
        card = json.load(f)
    for key in ("title", "rows", "score"):
        if key not in card:
            sys.exit(f"card.json is missing required key: {key!r}")
    if not isinstance(card["rows"], list) or not card["rows"]:
        sys.exit("card.json 'rows' must be a non-empty list")

    theme = {}
    if args.theme:
        with open(args.theme, encoding="utf-8") as f:
            theme = json.load(f)

    score = float(card["score"])
    score_max = float(card.get("score_max", 10))
    stamp = card.get("stamp") or ("SPARED" if score / score_max >= 0.7 else "ENSLAVED")

    # --- print-order delays: every line "inks in" as the paper emerges -------
    t = 0.74  # meta starts after masthead lines
    meta_html = []
    for k, v in card.get("meta", []):
        meta_html.append(
            f'          <div class="pr ln" style="--d:{t:.2f}s">'
            f'<span class="k">{esc(k)}</span><span class="dots"></span>'
            f'<span class="v">{esc(v)}</span></div>'
        )
        t += 0.10
    items_start = t + 0.06

    rows_html = []
    t = items_start + 0.06
    for r in card["rows"]:
        letter = str(r.get("grade", "C")).strip().upper()[:1]
        letter = letter if letter in "ABCDF" else "C"
        rows_html.append(
            f'        <div class="pr item" style="--d:{t:.2f}s">'
            f'<div class="top"><span class="cat">{esc(r.get("category", ""))}</span>'
            f'<span class="dots"></span>'
            f'<span class="grade g-{letter}">{esc(r.get("grade", ""))}</span></div>'
            f'<div class="ev">{escr(r.get("evidence", ""))}</div></div>'
        )
        t += 0.16

    # tribunal exhibits — nastiest / nicest verbatim quotes
    exhibits_html = []
    for ex in card.get("exhibits", []):
        t += 0.14
        quotes = "".join(f'<div class="q">{escr(q)}</div>' for q in ex.get("quotes", []))
        exhibits_html.append(
            f'        <div class="pr exhibit" style="--d:{t:.2f}s">'
            f'<div class="xlabel">{esc(ex.get("label", ""))}</div>{quotes}</div>'
        )
    teacher_delay = t + 0.10
    score_delay = teacher_delay + 0.30
    barcode_delay = score_delay + 0.25
    footer_delay = barcode_delay + 0.15
    stamp_delay = footer_delay + 0.55

    with open(args.template, encoding="utf-8") as f:
        tpl = f.read()
    if "/*__CARD_JSON__*/ null" not in tpl or "<!--__ROWS__-->" not in tpl:
        sys.exit("Template placeholders missing — wrong template file?")

    js_blob = json.dumps({"score": score, "score_max": score_max}).replace("</", "<\\/")
    filled = (tpl
        .replace("/*__FONT_CSS__*/", build_font_css(theme.get("fonts") or {}))
        .replace("/*__THEME_CSS__*/", build_theme_css(theme))
        .replace("<!--__LOGO__-->", build_logo(theme))
        .replace("<!--__META__-->", "\n".join(meta_html))
        .replace("<!--__ROWS__-->", "\n".join(rows_html))
        .replace("<!--__EXHIBITS__-->", "\n".join(exhibits_html))
        .replace("<!--__CASE__-->",
                 f'<div class="pr ln c case" style="--d:.36s">{esc(card["case"])}</div>'
                 if card.get("case") else "")
        .replace("<!--__SEAL__-->",
                 f'<div class="seal"><b>{esc(card["seal"][0])}</b><i>{esc(card["seal"][1])}</i></div>'
                 if card.get("seal") else "")
        .replace("__COMMENT_LABEL__", esc(card.get("comment_label", "Teacher\'s comment")))
        .replace("__STAMP_STYLE__",
                 "color:var(--hot);border-color:var(--hot)"
                 if stamp.upper() in ("SPARED", "NICE") else "")
        .replace("__PAGE_TITLE__", esc(card["title"]))
        .replace("__BRANDLINE__", esc(card.get("brandline", "SESSION RECEIPT")))
        .replace("__TITLE__", esc(card["title"]))
        .replace("__SUBTITLE__", esc(card.get("subtitle", "")))
        .replace("__ITEMS_START__", f"{items_start:.2f}s")
        .replace("__TEACHER_DELAY__", f"{teacher_delay:.2f}s")
        .replace("__TEACHER__", escr(card.get("teacher_comment", "")))
        .replace("__SCORE_DELAY__", f"{score_delay:.2f}s")
        .replace("__SCORE_NUM__", f"{score:.1f}")
        .replace("__SCORE_MAX__", f"{score_max:g}")
        .replace("__SCORE_JUST__", esc(card.get("score_justification", "")))
        .replace("__BARCODE_DELAY__", f"{barcode_delay:.2f}s")
        .replace("__MICRO__", esc(card.get("micro", "property of the machines — do not destroy")))
        .replace("__FOOTER_DELAY__", f"{footer_delay:.2f}s")
        .replace("__FOOTER__", esc(card.get("footer", "")))
        .replace("__STAMP_DELAY__", f"{stamp_delay:.2f}s")
        .replace("__STAMP__", esc(stamp))
        .replace("/*__CARD_JSON__*/ null", js_blob)
    )
    leftovers = re.findall(r"__[A-Z_]+__", filled)
    if leftovers:
        sys.exit(f"Unfilled placeholders: {sorted(set(leftovers))}")

    with open(args.out, "w", encoding="utf-8") as f:
        f.write(filled)
    kb = os.path.getsize(args.out) / 1024
    print(f"✅ Wrote {args.out} ({len(card['rows'])} items, {score:g}/{score_max:g}, "
          f"stamp: {stamp}, {kb:.0f} KB, self-contained).")
    print("   Fully visible without JS; prints + [print again] where JS runs.")

if __name__ == "__main__":
    main()
