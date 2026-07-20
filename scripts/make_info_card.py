#!/usr/bin/env python3
"""
Builds a neofetch-style "whoami" info card as an animated SVG (terminal
window chrome + line-by-line reveal), populated with static data you edit
in this file's CONFIG section below.

Usage:
    python scripts/make_info_card.py <output.svg>
"""
import html
import sys

# ---------------------------------------------------------------------
# CONFIG -- edit these to update the card. No external data is fetched.
# ---------------------------------------------------------------------
USERNAME = "mateusfeoliveira"
TITLE = f"{USERNAME}@github ~ $ neofetch"

FIELDS = [
    ("Now", "Analista de Dados Júnior @ Grupo Digital Soluções Financeiras"),
    ("Prev", "Estagiário em Dados @ Grupo Digital Soluções Financeiras"),
    ("Also", "Estagiário Dev Front-End @ MaiorICasa e RUGME"),
    ("Edu", "Sistemas de Informação, UAM  ·  Tecnologia em Banco de Dados, SENAC"),
]

STACK = [
    ("Data / ETL", "Python, Pandas, NumPy, SQL, Airflow, Spark, Databricks, Kafka"),
    ("BI / Analytics", "Power BI, Tableau, Power Query, Excel"),
    ("Frontend", "HTML, CSS, JavaScript, Angular, TypeScript"),
    ("Cloud / DB", "AWS, Azure, MySQL, PostgreSQL, MongoDB, BigQuery"),
    ("Tools", "Git, Docker, Postman, Figma, Salesforce"),
]

HIGHLIGHTS = [
    "Inglês C1  ·  Espanhol A2",
    "Certificações: LGPD, Scrum Foundations (SFPC)",
]
# ---------------------------------------------------------------------

HEADER_COLOR = "#e6edf3"
LABEL_COLOR = "#79c0ff"
DIM_COLOR = "#7d8590"
TEXT_COLOR = "#c9d1d9"
BULLET_COLOR = "#39d353"


def wrap_text(text, max_chars):
    words = text.split(" ")
    lines, cur = [], ""
    for w in words:
        candidate = (cur + " " + w).strip()
        if len(candidate) > max_chars and cur:
            lines.append(cur)
            cur = w
        else:
            cur = candidate
    if cur:
        lines.append(cur)
    return lines


def build_lines():
    lines = []
    lines.append("blank")
    lines.append(("text", [(USERNAME, HEADER_COLOR)]))
    lines.append("blank")

    label_w = 6
    for label, value in FIELDS:
        for i, wrapped in enumerate(wrap_text(value, 64)):
            prefix = label.ljust(label_w) if i == 0 else " " * label_w
            color_label = LABEL_COLOR if i == 0 else DIM_COLOR
            lines.append(("text", [(prefix, color_label), (wrapped, TEXT_COLOR)]))

    lines.append("blank")
    lines.append(("text", [("— Stack", DIM_COLOR)]))
    label_w2 = 16
    for label, value in STACK:
        for i, wrapped in enumerate(wrap_text(value, 60)):
            prefix = (label.ljust(label_w2) if i == 0 else " " * label_w2)
            color_label = LABEL_COLOR if i == 0 else DIM_COLOR
            lines.append(("text", [(prefix, color_label), (wrapped, TEXT_COLOR)]))

    lines.append("blank")
    lines.append(("text", [("— Highlights", DIM_COLOR)]))
    for h in HIGHLIGHTS:
        lines.append(("text", [("• ", BULLET_COLOR), (h, TEXT_COLOR)]))

    return lines


def render_svg(lines, title):
    font_size = 13.5
    line_h = font_size * 1.55
    pad_left = 20
    pad_top = 46

    max_len = max((sum(len(seg[0]) for seg in l[1]) for l in lines if l != "blank"), default=40)
    char_w = font_size * 0.6
    width = int(pad_left * 2 + max_len * char_w)
    height = int(pad_top + len(lines) * line_h + 18)

    body = []
    delay_step = 0.05
    typed_dur = 0.35
    i_visible = 0

    for i, item in enumerate(lines):
        y = pad_top + (i + 1) * line_h - 4
        if item == "blank":
            continue
        _, segs = item
        delay = round(i_visible * delay_step, 3)
        i_visible += 1

        x = pad_left
        tspans = []
        for text, color in segs:
            if not text:
                continue
            escaped = html.escape(text)
            tspans.append(f'<tspan fill="{color}">{escaped}</tspan>')
            x += len(text) * char_w
        total_len = x - pad_left

        body.append(
            f'<g opacity="0"><animate attributeName="opacity" from="0" to="1" begin="{delay}s" dur="{typed_dur}s" fill="freeze"/>'
            f'<text xml:space="preserve" x="{pad_left}" y="{y:.1f}" font-size="{font_size}">{"".join(tspans)}</text></g>'
        )

    title_escaped = html.escape(title)

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace">
<defs><linearGradient id="bg2" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#111722"/><stop offset="1" stop-color="#0d1117"/></linearGradient></defs>
<rect width="{width}" height="{height}" rx="12" fill="url(#bg2)"/>
<rect x="0.5" y="0.5" width="{width - 1}" height="{height - 1}" rx="12" fill="none" stroke="#30363d" stroke-width="1"/>
<line x1="0" y1="26" x2="{width}" y2="26" stroke="#30363d"/>
<circle cx="16" cy="13" r="4.5" fill="#ff5f56"/>
<circle cx="30" cy="13" r="4.5" fill="#ffbd2e"/>
<circle cx="44" cy="13" r="4.5" fill="#27c93f"/>
<text x="{width / 2}" y="17" fill="#7d8590" font-size="11" text-anchor="middle">{title_escaped}</text>
{"".join(body)}
</svg>
'''
    return svg


def main():
    out_path = sys.argv[1] if len(sys.argv) > 1 else "info-card.svg"
    lines = build_lines()
    svg = render_svg(lines, TITLE)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
