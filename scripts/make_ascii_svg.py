#!/usr/bin/env python3
"""
Converts a photo into a monochrome ASCII-art portrait rendered as an
animated SVG (terminal window chrome + row-by-row "typing" reveal).

Usage:
    python scripts/make_ascii_svg.py <photo.jpg> <output.svg> [--cols 90] [--title "user@github ~ $ ./portrait.sh"]

To regenerate with a new photo later: replace images/profile-source.jpg and
re-run this script with the same arguments used originally (see the comment
in README.md above the portrait image).
"""
import argparse
import html

from PIL import Image, ImageOps

# Dark-to-light ramp (index 0 = darkest/background-ish, last = brightest)
RAMP = " .:-=+*#%@"

FONT_ASPECT = 0.52  # width/height ratio of a monospace glyph, used to keep proportions


def image_to_ascii_rows(path, cols):
    img = Image.open(path).convert("L")
    img = ImageOps.autocontrast(img, cutoff=1)

    w, h = img.size
    cell_w = w / cols
    cell_h = cell_w / FONT_ASPECT
    rows = max(1, int(h / cell_h))

    img_small = img.resize((cols, rows), Image.LANCZOS)
    pixels = img_small.load()

    ascii_rows = []
    for y in range(rows):
        line = []
        for x in range(cols):
            v = pixels[x, y] / 255.0
            idx = int(v * (len(RAMP) - 1))
            line.append(RAMP[idx])
        ascii_rows.append("".join(line))
    return ascii_rows


def render_svg(rows, title):
    n_rows = len(rows)
    cols = max(len(r) for r in rows) if rows else 0

    font_size = 8.6
    line_h = font_size * 1.14
    char_w = font_size * FONT_ASPECT

    pad_left = 16
    pad_top = 34
    width = int(pad_left * 2 + cols * char_w)
    height = int(pad_top + n_rows * line_h + 16)

    body = []
    row_delay_step = 0.045
    typed_dur = 0.5

    for i, row in enumerate(rows):
        y = pad_top + (i + 1) * line_h - 3
        text_len = len(row) * char_w
        delay = round(i * row_delay_step, 3)
        escaped = html.escape(row)
        body.append(
            f'<clipPath id="r{i}"><rect x="{pad_left}" y="{y - font_size}" height="{font_size + 4}" width="0">'
            f'<animate attributeName="width" from="0" to="{text_len:.1f}" begin="{delay}s" dur="{typed_dur}s" fill="freeze"/>'
            f"</rect></clipPath>"
            f'<g clip-path="url(#r{i})"><text xml:space="preserve" x="{pad_left}" y="{y:.1f}" '
            f'fill="#c9d1d9" font-size="{font_size}" textLength="{text_len:.1f}" lengthAdjust="spacing">{escaped}</text></g>'
        )

    title_escaped = html.escape(title)

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace">
<defs><linearGradient id="bg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#111722"/><stop offset="1" stop-color="#0d1117"/></linearGradient></defs>
<rect width="{width}" height="{height}" rx="12" fill="url(#bg)"/>
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
    ap = argparse.ArgumentParser()
    ap.add_argument("photo")
    ap.add_argument("output")
    ap.add_argument("--cols", type=int, default=90)
    ap.add_argument("--title", default="mateus@github ~ $ ./portrait.sh")
    args = ap.parse_args()

    rows = image_to_ascii_rows(args.photo, args.cols)
    svg = render_svg(rows, args.title)

    with open(args.output, "w", encoding="utf-8") as f:
        f.write(svg)

    print(f"Wrote {args.output} ({len(rows)} rows x {args.cols} cols)")


if __name__ == "__main__":
    main()
