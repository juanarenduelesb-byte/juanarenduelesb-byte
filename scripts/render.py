#!/usr/bin/env python3
"""Render every SVG card in cards/ from config.json + data/contributions.json.

All cards share one terminal theme. Animations are pure CSS/SMIL, so they play
inside GitHub's <img> sandbox, and respect prefers-reduced-motion.
"""
import datetime as dt
import html
import json
import pathlib
import textwrap

import pyfiglet

ROOT = pathlib.Path(__file__).resolve().parent.parent
CFG = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))
DATA_PATH = ROOT / "data" / "contributions.json"
OUT = ROOT / "cards"

BG, PANEL, BORDER = "#0d1117", "#161b22", "#30363d"
TEXT, MUTED = "#e6edf3", "#7d8590"
TEAL, CYAN, VIOLET, GREEN = "#2dd4bf", "#22d3ee", "#a78bfa", "#3fb950"
SCALE = ["#161b22", "#0b4f4a", "#0f766e", "#14b8a6", "#5eead4"]
MONO = "ui-monospace,SFMono-Regular,'SF Mono',Menlo,Consolas,'Liberation Mono',monospace"
W = 880

BASE_CSS = """
.f{opacity:0;animation:f .5s ease-out forwards}
@keyframes f{from{opacity:0;transform:translateY(6px)}to{opacity:1;transform:none}}
.p{opacity:0;transform-box:fill-box;transform-origin:center;animation:p .45s ease-out forwards}
@keyframes p{0%{opacity:0;transform:scale(.2)}70%{opacity:1;transform:scale(1.15)}100%{opacity:1;transform:scale(1)}}
.g{transform-box:fill-box;transform-origin:bottom;transform:scaleY(0);animation:g .7s cubic-bezier(.2,.8,.2,1) forwards}
@keyframes g{to{transform:scaleY(1)}}
.cur{animation:b 1s steps(1) infinite}
@keyframes b{50%{opacity:0}}
@media (prefers-reduced-motion:reduce){.f,.p,.g{opacity:1!important;transform:none!important;animation:none!important}}
"""


def esc(s):
    return html.escape(str(s), quote=True)


def window(h, title, body, w=W):
    """A macOS-style terminal window."""
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" font-family="{MONO}">
<style>{BASE_CSS}</style>
<defs>
<linearGradient id="bg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#121821"/><stop offset="1" stop-color="{BG}"/></linearGradient>
<linearGradient id="acc" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{TEAL}"/><stop offset=".55" stop-color="{CYAN}"/><stop offset="1" stop-color="{VIOLET}"/></linearGradient>
<linearGradient id="accv" x1="0" y1="1" x2="0" y2="0"><stop offset="0" stop-color="{TEAL}"/><stop offset="1" stop-color="{VIOLET}"/></linearGradient>
<linearGradient id="ban" gradientUnits="userSpaceOnUse" x1="0" y1="0" x2="{w}" y2="0"><stop offset=".05" stop-color="{TEAL}"/><stop offset=".5" stop-color="{CYAN}"/><stop offset=".95" stop-color="{VIOLET}"/></linearGradient>
</defs>
<rect x=".5" y=".5" width="{w-1}" height="{h-1}" rx="12" fill="url(#bg)" stroke="{BORDER}"/>
<line x1="0" y1="34" x2="{w}" y2="34" stroke="{BORDER}"/>
<circle cx="22" cy="17" r="6" fill="#ff5f56"/><circle cx="42" cy="17" r="6" fill="#ffbd2e"/><circle cx="62" cy="17" r="6" fill="#27c93f"/>
<text x="{w/2}" y="22" fill="{MUTED}" font-size="12" text-anchor="middle">{esc(title)}</text>
{body}
</svg>
"""


def typed(x, y, cmd, start=0.0, speed=0.05, size=15):
    """Prompt + command revealed character by character (SMIL clip)."""
    prompt = f"{CFG['prompt']} ~ $ "
    cid = f"t{abs(hash((x, y, cmd))) % 10**8}"
    char_w = size * 0.6
    full = (len(prompt) + len(cmd)) * char_w + 4
    pw = len(prompt) * char_w
    dur = max(len(cmd) * speed, 0.01)
    steps = ";".join(f"{pw + i * char_w:.1f}" for i in range(len(cmd) + 1))
    return f"""<clipPath id="{cid}"><rect x="{x}" y="{y-size-2}" width="{pw:.1f}" height="{size+8}">
<animate attributeName="width" values="{steps}" begin="{start}s" dur="{dur:.2f}s" calcMode="discrete" fill="freeze"/></rect></clipPath>
<text x="{x}" y="{y}" font-size="{size}" clip-path="url(#{cid})" textLength="{full-4:.1f}" lengthAdjust="spacingAndGlyphs"><tspan fill="{GREEN}">{esc(CFG['prompt'])}</tspan><tspan fill="{MUTED}"> ~ $ </tspan><tspan fill="{TEXT}">{esc(cmd)}</tspan></text>"""


def load_data():
    if DATA_PATH.exists():
        return json.loads(DATA_PATH.read_text(encoding="utf-8"))
    # Placeholder until the first workflow run fills real data in.
    today = dt.date.today()
    start = today - dt.timedelta(days=364 + (today.weekday() + 1) % 7)
    days = [{"date": (start + dt.timedelta(i)).isoformat(), "count": 0, "level": 0}
            for i in range((today - start).days + 1)]
    months = {}
    for d in days:
        months[d["date"][:7]] = 0
    return {"updated": today.isoformat(), "total": 0, "active_days": 0, "current_streak": 0,
            "longest_streak": 0, "best_day": {"date": today.isoformat(), "count": 0},
            "months": months, "weekday": [0] * 7, "days": days}


# --------------------------------------------------------------------- hero
def hero():
    art = pyfiglet.figlet_format(CFG["banner_text"], font="ansi_regular", width=400).rstrip("\n").split("\n")
    art = [r for r in art if r.strip()]
    cols = max(len(r) for r in art)
    cw = min(8.4, (W - 80) / cols)
    ch = cw * 1.35
    x0 = (W - cols * cw) / 2
    y0 = 92
    cells, shadow = [], []
    for r, row in enumerate(art):
        for c, char in enumerate(row):
            if char.strip():
                x, y = x0 + c * cw, y0 + r * ch
                d = 0.9 + c * 0.012 + r * 0.03
                shadow.append(f'<rect x="{x+2.5:.1f}" y="{y+2.5:.1f}" width="{cw:.2f}" height="{ch:.2f}"/>')
                cells.append(f'<rect class="p" style="animation-delay:{d:.2f}s" x="{x:.1f}" y="{y:.1f}" width="{cw+.3:.2f}" height="{ch+.3:.2f}"/>')
    banner_h = len(art) * ch
    body = [typed(32, 70, "whoami", start=0.2),
            f'<g fill="{TEAL}" opacity=".12">{"".join(shadow)}</g>',
            f'<g fill="url(#ban)">{"".join(cells)}</g>']

    y = y0 + banner_h + 42
    body.append(f'<line class="f" style="animation-delay:1.9s" x1="32" y1="{y-22}" x2="{W-32}" y2="{y-22}" stroke="{BORDER}" stroke-dasharray="4 4"/>')
    pairs = CFG["whoami"]
    half = (len(pairs) + 1) // 2
    for i, (k, v) in enumerate(pairs):
        col, row = divmod(i, half)
        x = 32 + col * (W - 64) / 2
        yy = y + row * 28
        d = 2.0 + i * 0.12
        body.append(f'<text class="f" style="animation-delay:{d:.2f}s" x="{x}" y="{yy}" font-size="14">'
                    f'<tspan fill="{CYAN}">{esc(k)}</tspan><tspan fill="{MUTED}">{"." * (10 - len(k))} </tspan>'
                    f'<tspan fill="{TEXT}">{esc(v)}</tspan></text>')
    yc = y + half * 28 + 12
    end = 2.0 + len(pairs) * 0.12 + 0.3
    body.append(typed(32, yc, "", start=end))
    pw = len(f"{CFG['prompt']} ~ $ ") * 9 + 32
    body.append(f'<rect class="f" style="animation-delay:{end:.2f}s" x="{pw:.0f}" y="{yc-14}" width="9" height="18" fill="{TEAL}">'
                f'<animate attributeName="opacity" values="1;0;1" dur="1s" begin="{end+0.5:.2f}s" repeatCount="indefinite" calcMode="discrete"/></rect>')
    h = int(yc + 26)
    return window(h, f"{CFG['prompt']}: ~ — zsh", "\n".join(body))


# ------------------------------------------------------------------ heatmap
def heatmap(data):
    days = data["days"]
    first = dt.date.fromisoformat(days[0]["date"])
    offset = (first.weekday() + 1) % 7  # Sunday-first rows, like GitHub
    cell, gap = 12, 3
    x0, y0 = 62, 92
    rects, labels, seen = [], [], set()
    for i, d in enumerate(days):
        idx = i + offset
        col, row = divmod(idx, 7)
        x, y = x0 + col * (cell + gap), y0 + row * (cell + gap)
        lvl = d.get("level", 0)
        delay = 0.6 + col * 0.022 + row * 0.03
        rects.append(f'<rect class="p" style="animation-delay:{delay:.2f}s" x="{x}" y="{y}" width="{cell}" height="{cell}" rx="2.5" fill="{SCALE[lvl]}">'
                     f'<title>{d["count"]} contributions on {d["date"]}</title></rect>')
        date = dt.date.fromisoformat(d["date"])
        if date.day <= 7 and row == 0 and date.month not in seen and col < 52:
            seen.add(date.month)
            labels.append(f'<text x="{x}" y="{y0-10}" fill="{MUTED}" font-size="11">{date.strftime("%b")}</text>')
    for r, name in ((1, "Mon"), (3, "Wed"), (5, "Fri")):
        labels.append(f'<text x="{x0-10}" y="{y0 + r*(cell+gap) + 10}" fill="{MUTED}" font-size="11" text-anchor="end">{name}</text>')
    yb = y0 + 7 * (cell + gap) + 26
    legend_x = W - 32 - 5 * 15 - 70
    legend = [f'<text x="{legend_x}" y="{yb}" fill="{MUTED}" font-size="11">less</text>']
    for i, c in enumerate(SCALE):
        legend.append(f'<rect x="{legend_x + 34 + i*15}" y="{yb-10}" width="11" height="11" rx="2.5" fill="{c}"/>')
    legend.append(f'<text x="{legend_x + 34 + 5*15 + 4}" y="{yb}" fill="{MUTED}" font-size="11">more</text>')
    summary = (f'<text class="f" style="animation-delay:1.6s" x="32" y="{yb}" font-size="12" fill="{MUTED}">'
               f'<tspan fill="{TEAL}" font-weight="700">{data["total"]:,}</tspan> contributions in the last year'
               f'<tspan> · updated {esc(data["updated"])}</tspan></text>')
    body = typed(32, 62, "./contributions.sh --last-year", start=0.1) + "\n" + "".join(labels) + "".join(rects) + "".join(legend) + summary
    return window(yb + 22, "contributions — live", body)


# -------------------------------------------------------------------- stats
def stats(data):
    tiles = [
        ("total", f'{data["total"]:,}', "contributions / 12 mo"),
        ("streak", f'{data["current_streak"]}', "days current streak"),
        ("longest", f'{data["longest_streak"]}', "days longest streak"),
        ("best day", f'{data["best_day"]["count"]}', dt.date.fromisoformat(data["best_day"]["date"]).strftime("%d %b %Y")),
    ]
    gap = 14
    tw = (W - 64 - gap * 3) / 4
    body = [typed(32, 62, "./stats.sh", start=0.1)]
    for i, (k, v, sub) in enumerate(tiles):
        x = 32 + i * (tw + gap)
        d = 0.5 + i * 0.12
        body.append(f'<g class="f" style="animation-delay:{d:.2f}s">'
                    f'<rect x="{x:.1f}" y="84" width="{tw:.1f}" height="96" rx="10" fill="{PANEL}" stroke="{BORDER}"/>'
                    f'<text x="{x+16:.1f}" y="108" fill="{MUTED}" font-size="12">$ {esc(k)}</text>'
                    f'<text x="{x+16:.1f}" y="146" fill="url(#acc)" font-size="32" font-weight="700">{esc(v)}</text>'
                    f'<text x="{x+16:.1f}" y="168" fill="{MUTED}" font-size="11">{esc(sub)}</text></g>')
    # monthly bars (last 12 months)
    months = sorted(data["months"].items())[-12:]
    top = max([v for _, v in months] + [1])
    cx0, cy0, chh = 32, 214, 110
    bw_total = (W - 64) / len(months)
    bw = bw_total * 0.56
    body.append(f'<text class="f" style="animation-delay:1s" x="32" y="{cy0-6}" fill="{MUTED}" font-size="12">$ monthly --bars</text>')
    for i, (m, v) in enumerate(months):
        x = cx0 + i * bw_total + (bw_total - bw) / 2
        h = max(3, v / top * chh)
        y = cy0 + 18 + chh - h
        d = 1.1 + i * 0.06
        label = dt.date.fromisoformat(m + "-01").strftime("%b")
        body.append(f'<rect x="{x:.1f}" y="{cy0+18}" width="{bw:.1f}" height="{chh}" rx="4" fill="{PANEL}"/>'
                    f'<rect class="g" style="animation-delay:{d:.2f}s" x="{x:.1f}" y="{y:.1f}" width="{bw:.1f}" height="{h:.1f}" rx="4" fill="url(#accv)"><title>{v} in {m}</title></rect>'
                    f'<text x="{x + bw/2:.1f}" y="{cy0+18+chh+18}" fill="{MUTED}" font-size="11" text-anchor="middle">{label}</text>'
                    f'<text class="f" style="animation-delay:{d+.5:.2f}s" x="{x + bw/2:.1f}" y="{y-6:.1f}" fill="{TEXT}" font-size="10" text-anchor="middle">{v if v else ""}</text>')
    h = cy0 + 18 + chh + 36
    return window(h, "stats — refreshed daily", "\n".join(body))


# ---------------------------------------------------------------- projects
def project(p, i):
    w, h = 292, 210
    lines = textwrap.wrap(p["desc"], 36)[:3]
    body = [f'<text x="20" y="62" fill="{MUTED}" font-size="12"><tspan fill="{GREEN}">~/</tspan>{esc(p["name"])}</text>',
            f'<rect x="{w-20-len(p["tag"])*7.2-16:.1f}" y="49" width="{len(p["tag"])*7.2+16:.1f}" height="20" rx="10" fill="none" stroke="{TEAL}" stroke-opacity=".6"/>',
            f'<text x="{w-20-(len(p["tag"])*7.2+16)/2:.1f}" y="63" fill="{TEAL}" font-size="11" text-anchor="middle" font-weight="700">{esc(p["tag"])}</text>',
            f'<text class="f" style="animation-delay:{0.2+i*0.15:.2f}s" x="20" y="98" fill="url(#acc)" font-size="24" font-weight="700">{esc(p["name"])}</text>']
    for j, ln in enumerate(lines):
        body.append(f'<text class="f" style="animation-delay:{0.35+i*0.15:.2f}s" x="20" y="{124 + j*18}" fill="{TEXT}" font-size="12">{esc(ln)}</text>')
    body.append(f'<line x1="20" y1="{h-38}" x2="{w-20}" y2="{h-38}" stroke="{BORDER}"/>')
    body.append(f'<text x="20" y="{h-16}" fill="{MUTED}" font-size="11">{esc(p["stack"])}</text>')
    return window(h, f'{p["name"]}', "\n".join(body), w=w)


def main():
    OUT.mkdir(exist_ok=True)
    data = load_data()
    (OUT / "hero.svg").write_text(hero(), encoding="utf-8")
    (OUT / "heatmap.svg").write_text(heatmap(data), encoding="utf-8")
    (OUT / "stats.svg").write_text(stats(data), encoding="utf-8")
    for i, p in enumerate(CFG["building"]):
        (OUT / f"project-{p['name']}.svg").write_text(project(p, i), encoding="utf-8")
    print("cards rendered:", ", ".join(sorted(f.name for f in OUT.glob("*.svg"))))


if __name__ == "__main__":
    main()
