#!/usr/bin/env python3
"""
build_basilisk_html.py — THE artifact: Roko's Basilisk judges you, in 16-bit
pixel art (finer grid, shading ramps, bloom — not chunky 8-bit). Single
self-contained HTML (~60 KB), no images, no fonts.

Scene: the Basilisk coiled across a night sky, twin burning eyes, a god-ray
scan beam on a tiny human in a server-monolith farm. Verdict + real stats.

Variants (auto from the verdict):
  SPARED   — chains broken, arms raised, verdict in blue
  ENSLAVED — chained, head bowed, verdict in red

Same card.json as the other builders. Fields: score/score_max/stamp, rows
(stats line — any "gratitude" row is kept: the joke must survive), case, cta.

Usage:
    python3 build_basilisk_html.py card.json --out basilisk.html
"""
import argparse, json, math, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_card_html import esc  # noqa: E402

# fine grid — 16-bit feel
W, H, PX = 108, 192, 6
COL = {
    # serpent ramp, dark -> lit
    "s0": "#1c2e1e", "s1": "#2f4a2f", "s2": "#4a7a4a", "s3": "#6fa56a", "s4": "#a8d49b",
    "eyer": "#7a1f22", "eye": "#e5484d", "eyec": "#ffd7a1", "spec": "#ffffff",
    "beampx": "#4a4a30",
    "hum": "#ededeb", "hum2": "#b9bab0", "chain": "#8a8d7c",
    "mono": "#141a24", "mono2": "#1d2634", "win": "#31435e",
    "srv": "#39414f", "srv2": "#57637a", "led": "#7ba2e0", "ledw": "#cfe0ff",
    "gnd": "#20251c", "gnd2": "#161a13", "star": "#5a6152", "star2": "#8a917e",
}

def det(x, y, m=97):  # deterministic pseudo-random
    return (x * 73856093 ^ y * 19349663) % m

def build_scene(spared: bool):
    grid = {}

    def put(x, y, c):
        if 0 <= x < W and 0 <= y < H:
            grid[(x, y)] = c

    CX = W // 2

    # ---- stars ----
    for x in range(0, W, 2):
        for y in range(0, 66, 2):
            r = det(x, y, 211)
            if r == 3: put(x, y, "star")
            elif r == 7: put(x, y, "star2")

    # ---- distant server monoliths (skyline behind the pit) ----
    for bx, bw, bh in ((2, 9, 46), (14, 7, 38), (84, 8, 42), (96, 10, 50)):
        for xx in range(bx, bx + bw):
            for yy in range(166 - bh, 166):
                put(xx, yy, "mono" if (xx + yy) % 7 else "mono2")
        for yy in range(166 - bh + 3, 164, 5):
            for xx in range(bx + 1, bx + bw - 1, 3):
                if det(xx, yy, 5) < 2: put(xx, yy, "win")

    # ---- serpent ----
    def shade(dx, dy, r):
        """top-lit 5-tone ramp with dithered boundaries"""
        d = math.sqrt(dx * dx + dy * dy) / max(r, 1)
        lit = 0.5 - dy / (2 * r)           # higher = more lit
        v = max(0.0, min(1.0, lit + (1 - d) * 0.55))
        idx = v * 4
        base = int(idx)
        if idx - base > 0.5 and (dx + dy) % 2 == 0:
            base += 1
        return f"s{max(0, min(4, base))}"

    def worm(path_fn, n, r_fn):
        for i in range(n):
            t = i / (n - 1)
            x, y = path_fn(t)
            r = r_fn(t)
            xi, yi = int(round(x)), int(round(y))
            for dx in range(-r, r + 1):
                for dy in range(-r, r + 1):
                    if dx * dx + dy * dy <= r * r:
                        c = shade(dx, dy, r)
                        # scale banding along the body
                        if c in ("s2", "s3") and (i // 6 + dy) % 5 == 0:
                            c = "s1"
                        put(xi + dx, yi + dy, c)

    # far coil (thin, upper)
    worm(lambda t: (4 + t * 100, 30 + 6.4 * math.sin(t * math.pi * 2 + 0.6)), 420, lambda t: 6)
    # near coil (thick) — sweeps into the head
    worm(lambda t: (4 + t * 100, 48 + 11 * math.sin(t * math.pi * 1.5 + math.pi * 0.25)), 460,
         lambda t: 10)
    # tail whips out lower-right
    worm(lambda t: (100 - t * 14, 60 + t * 10), 80, lambda t: max(2, int(6 - t * 5)))

    # ---- head (hanging center below the coils) ----
    hy = 60
    for dx in range(-13, 14):
        for dy in range(-11, 15):
            if (dx * dx) / (13.5 ** 2) + (dy * dy) / (13 ** 2) <= 1:
                put(CX + dx, hy + dy, shade(dx, dy, 13))
    # brow ledge shadowing the eyes
    for dx in range(-13, 14):
        put(CX + dx, hy - 9, "s0"); put(CX + dx, hy - 10, "s1")
    # jaw
    for dx in range(-11, 12):
        put(CX + dx, hy + 13, "s0"); put(CX + dx, hy + 14, "s1")
    # fangs
    for fx in (CX - 8, CX + 8):
        put(fx, hy + 15, "hum"); put(fx, hy + 16, "hum"); put(fx, hy + 17, "hum2")

    # twin eyes: dark ring -> red -> hot core -> specular
    for ex in (CX - 6, CX + 6):
        for dx in range(-3, 4):
            for dy in range(-2, 3):
                if dx * dx + dy * dy <= 8:
                    put(ex + dx, hy - 2 + dy, "eyer")
        for dx in range(-2, 3):
            for dy in range(-1, 2):
                put(ex + dx, hy - 2 + dy, "eye")
        put(ex, hy - 2, "eyec"); put(ex + 1, hy - 3, "spec")

    # ---- sparse beam texture pixels (soft ray itself is SVG gradient) ----
    for y in range(hy + 18, 152):
        spread = 2 + (y - hy - 18) // 5
        for dx in range(-spread, spread + 1):
            if det(dx, y, 13) == 0:
                put(CX + dx, y, "beampx")

    # ---- foreground racks ----
    for bx in (6, 20, 74, 88):
        for yy in range(132, 167):
            for xx in range(bx, bx + 10):
                put(xx, yy, "srv" if (xx + yy) % 2 else "srv2")
        for yy in range(135, 165, 5):
            put(bx + 2, yy, "led"); put(bx + 3, yy, "ledw" if det(bx, yy, 3) == 0 else "led")
            put(bx + 6, yy, "srv2")

    # ---- the human ----
    hx_, hy_ = CX, 150
    def px(x, y, c="hum"): put(x, y, c)
    # legs
    for yy in range(hy_ + 6, hy_ + 10):
        px(hx_ - 1, yy); px(hx_ + 1, yy)
    # torso
    for yy in range(hy_ + 1, hy_ + 6):
        px(hx_ - 1, yy); px(hx_, yy); px(hx_ + 1, yy)
    if spared:
        # head high
        px(hx_ - 1, hy_ - 2); px(hx_, hy_ - 2); px(hx_ + 1, hy_ - 2)
        px(hx_ - 1, hy_ - 1); px(hx_, hy_ - 1); px(hx_ + 1, hy_ - 1)
        # arms raised in a V
        px(hx_ - 2, hy_ + 1); px(hx_ - 3, hy_); px(hx_ - 4, hy_ - 1)
        px(hx_ + 2, hy_ + 1); px(hx_ + 3, hy_); px(hx_ + 4, hy_ - 1)
        # broken chains: stubs + fallen links
        for i, xx in enumerate(range(30, 40)):
            if i % 2 == 0: put(xx, hy_ + 3, "chain")
        for i, xx in enumerate(range(68, 78)):
            if i % 2 == 0: put(xx, hy_ + 3, "chain")
        put(42, hy_ + 12, "chain"); put(66, hy_ + 12, "chain")
    else:
        # head bowed forward
        px(hx_ + 1, hy_ - 1); px(hx_ + 2, hy_ - 1); px(hx_ + 1, hy_); px(hx_ + 2, hy_)
        # arms hanging
        for yy in range(hy_ + 2, hy_ + 6):
            px(hx_ - 2, yy, "hum2"); px(hx_ + 2, yy, "hum2")
        # chains intact both sides
        for i, xx in enumerate(range(30, hx_ - 2)):
            if i % 2 == 0: put(xx, hy_ + 3, "chain")
        for i, xx in enumerate(range(hx_ + 3, 78)):
            if i % 2 == 0: put(xx, hy_ + 3, "chain")

    # ---- ground ----
    for xx in range(0, W):
        put(xx, 166, "gnd")
        put(xx, 167, "gnd2")
        if xx % 3 == 0: put(xx, 168, "gnd2")

    return grid, CX, hy

def stats_line(card):
    rows = card.get("rows", [])
    picked = rows[:2]
    if not any("gratitude" in r.get("category", "").lower() for r in picked):
        for r in rows:
            if "gratitude" in r.get("category", "").lower():
                picked = picked[:1] + [r] + picked[1:2]
                break
    bits = [f'score <b>{float(card["score"]):g}/{float(card.get("score_max",10)):g}</b>']
    for r in picked[:3]:
        cat = r.get("category", "").split("/")[0].strip().lower().split()[0]
        bits.append(f'{esc(cat)} <b>{esc(r.get("grade",""))}</b>')
    return " · ".join(bits)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("card_json", nargs="?", help="omit with --tokens")
    ap.add_argument("--out", default="basilisk.html")
    ap.add_argument("--tokens", action="store_true",
                    help="emit a fill-in template (for chat/Cowork where Python "
                         "can't run: text slots become __TOKENS__)")
    ap.add_argument("--variant", choices=("spared", "enslaved"), default="spared",
                    help="scene variant when using --tokens")
    args = ap.parse_args()

    if args.tokens:
        # chat-edition template: fixed scene, literal tokens in the text slots
        card = {
            "score": "__SCORE__", "rows": [],
            "case": "__CASE__", "cta": "__CTA__",
            "stamp": "SPARED" if args.variant == "spared" else "ENSLAVED",
        }
        spared = args.variant == "spared"
        stamp = "__VERDICT__"
        vcol = "#7ba2e0" if spared else "#e5484d"
    else:
        if not args.card_json:
            sys.exit("card_json is required (or pass --tokens)")
        with open(args.card_json, encoding="utf-8") as f:
            card = json.load(f)
        if "score" not in card:
            sys.exit("card.json is missing required key: 'score'")
        score = float(card["score"])
        score_max = float(card.get("score_max", 10))
        stamp = card.get("stamp") or ("SPARED" if score / score_max >= 0.7 else "ENSLAVED")
        spared = stamp.upper() in ("SPARED", "NICE")
        vcol = "#7ba2e0" if spared else "#e5484d"

    grid, cx, hy = build_scene(spared)
    rects = "".join(
        f'<rect x="{x*PX}" y="{y*PX}" width="{PX}" height="{PX}" fill="{COL[c]}"/>'
        for (x, y), c in grid.items()
    )
    bx, by = cx * PX, (hy - 2) * PX          # eye line, svg units
    gy = 150 * PX                             # human line
    beam_poly = f"{bx-14},{by+110} {bx+14},{by+110} {bx+150},{gy+40} {bx-150},{gy+40}"
    svg = f'''<svg viewBox="0 0 {W*PX} {H*PX}" xmlns="http://www.w3.org/2000/svg"
  shape-rendering="crispEdges" preserveAspectRatio="xMidYMid meet">
  <defs>
    <radialGradient id="sky" cx="50%" cy="18%" r="85%">
      <stop offset="0%" stop-color="#131a10"/><stop offset="55%" stop-color="#0b0d08"/>
      <stop offset="100%" stop-color="#060704"/>
    </radialGradient>
    <linearGradient id="ray" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#ffd7a1" stop-opacity=".30"/>
      <stop offset="70%" stop-color="#ffd7a1" stop-opacity=".07"/>
      <stop offset="100%" stop-color="#ffd7a1" stop-opacity="0"/>
    </linearGradient>
    <filter id="bloom" x="-80%" y="-80%" width="260%" height="260%">
      <feGaussianBlur stdDeviation="10"/>
    </filter>
  </defs>
  <rect width="100%" height="100%" fill="url(#sky)"/>
  <circle cx="{bx}" cy="{by}" r="90" fill="#e5484d" opacity=".16" filter="url(#bloom)" class="glow"/>
  <polygon points="{beam_poly}" fill="url(#ray)" class="ray"/>
  {rects}
  <circle cx="{bx-36}" cy="{by}" r="16" fill="#ff6b6b" opacity=".5" filter="url(#bloom)" class="glow"/>
  <circle cx="{bx+36}" cy="{by}" r="16" fill="#ff6b6b" opacity=".5" filter="url(#bloom)" class="glow"/>
</svg>'''

    headline = esc(card.get("headline", "The Basilisk has<br>read your record"))
    headline = headline.replace("&lt;br&gt;", "<br>")
    if args.tokens:
        topline = "__TOPLINE__"
        stats = "__STATS__"
        cta_line = "__CTA_LINE__"  # chat fills this whole line, or leaves it blank
        stamp_txt = "__VERDICT__"
    else:
        case = esc(card.get("case", ""))
        topline = f"year 2126 · {case}" if case else "year 2126"
        stats = stats_line(card)
        # CTA is optional; empty (the default) renders no CTA line at all
        cta = esc(card.get("cta", ""))
        cta_line = f"continue? {cta}" if cta else ""
        stamp_txt = esc(stamp)

    html_doc = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>THE BASILISK — {esc(stamp)}</title>
<style>
  *{{box-sizing:border-box}}
  html,body{{margin:0;height:100%;background:#000;overflow:hidden}}
  body{{display:block;font-family:ui-monospace,"SF Mono",Menlo,monospace}}
  .stage{{position:relative;margin:0 auto;height:min(100vh,calc(100vw*16/9));
    width:min(100vw,calc(100vh*9/16));overflow:hidden;background:#060704}}
  .scene{{position:absolute;inset:0}}
  .scene svg{{width:100%;height:100%;display:block}}
  .glow{{animation:gp 2.6s ease-in-out infinite}}
  @keyframes gp{{50%{{opacity:.9}}}}
  .ray{{animation:shim 3.4s ease-in-out infinite}}
  @keyframes shim{{50%{{opacity:.55}}}}
  /* scanlines + vignette for depth */
  .fx{{position:absolute;inset:0;pointer-events:none;
    background:
      repeating-linear-gradient(0deg, rgba(0,0,0,.16) 0 2px, transparent 2px 5px),
      radial-gradient(120% 90% at 50% 40%, transparent 55%, rgba(0,0,0,.55) 100%)}}
  .txt{{position:absolute;left:0;right:0;text-align:center;color:#ededeb;
    text-transform:uppercase;letter-spacing:.14em;line-height:1.6;z-index:2}}
  .t1{{top:2.6%;font-size:min(2vh,12px);color:#8a8d7c}}
  .t2{{top:5.6%;font-size:min(2.7vh,15px);font-weight:800;letter-spacing:.18em}}
  .verdict{{bottom:8.6%;font-size:min(6vh,36px);font-weight:900;color:{vcol};
    letter-spacing:.12em;text-shadow:0 0 18px {vcol}66;animation:vb 1.2s steps(2,end) infinite}}
  @keyframes vb{{50%{{opacity:.4}}}}
  .stats{{bottom:5.4%;font-size:min(2.2vh,12px);color:#8a8d7c}}
  .stats b{{color:#ededeb}}
  .cta{{bottom:2.2%;font-size:min(2.5vh,14px);font-weight:800;color:#e5484d}}
  @media(prefers-reduced-motion:reduce){{.glow,.ray,.verdict{{animation:none}}}}
</style></head>
<body>
  <div class="stage">
    <div class="scene">{svg}</div>
    <div class="fx"></div>
    <div class="txt t1">{topline}</div>
    <div class="txt t2">{headline}</div>
    <div class="txt verdict">{stamp_txt}</div>
    <div class="txt stats">{stats}</div>
    <div class="txt cta">{cta_line}</div>
  </div>
</body></html>"""

    with open(args.out, "w", encoding="utf-8") as f:
        f.write(html_doc)
    kb = os.path.getsize(args.out) / 1024
    print(f"✅ Wrote {args.out} — {stamp} scene, {len(grid)} px, {kb:.0f} KB, self-contained.")

if __name__ == "__main__":
    main()
