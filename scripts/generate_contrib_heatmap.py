#!/usr/bin/env python3
"""
Generates an animated SVG of a GitHub contribution heatmap (cells "pop" in
one by one, like a terminal drawing itself) using REAL data scraped from the
user's public contribution calendar page:

    https://github.com/users/<username>/contributions

No GitHub token is required — that page is public HTML for any public
profile. This script is meant to be run by a scheduled GitHub Actions
workflow so the SVG stays fresh (see .github/workflows/update-profile-art.yml).

Usage:
    python scripts/generate_contrib_heatmap.py <github_username> [output.svg]
"""

import html
import re
import sys
import urllib.request

CELL = 13
GAP = 3
STEP = CELL + GAP
LEFT_PAD = 34
TOP_PAD = 24
LABEL_ROW_H = 16

# GitHub's own contribution-level colors (dark theme)
LEVEL_COLORS = {
    "0": "#161b22",
    "1": "#0d2b4e",
    "2": "#0a4a8f",
    "3": "#1f6feb",
    "4": "#58a6ff",
}

MONTHS = [
    "Jan", "Feb", "Mar", "Apr", "May", "Jun",
    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
]


def fetch_contribution_days(username: str):
    url = f"https://github.com/users/{username}/contributions"
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (compatible; profile-art-bot/1.0)"},
    )
    with urllib.request.urlopen(req, timeout=20) as resp:
        raw = resp.read().decode("utf-8", errors="replace")

    # GitHub renders each day as a <td>/<rect|tool-tip> with data-date and
    # data-level attributes. Match both possible tag shapes defensively.
    days = []
    pattern = re.compile(
        r'data-date="(\d{4}-\d{2}-\d{2})"[^>]*data-level="(\d)"'
        r'|data-level="(\d)"[^>]*data-date="(\d{4}-\d{2}-\d{2})"'
    )
    for m in pattern.finditer(raw):
        if m.group(1):
            date, level = m.group(1), m.group(2)
        else:
            date, level = m.group(4), m.group(3)
        days.append((date, int(level)))

    if not days:
        raise RuntimeError(
            "Could not find contribution cells — GitHub may have changed its "
            "markup, or the profile/username is private or invalid."
        )

    # dedupe, keep order
    seen = set()
    unique_days = []
    for d in days:
        if d[0] not in seen:
            seen.add(d[0])
            unique_days.append(d)
    unique_days.sort(key=lambda d: d[0])

    total_match = re.search(r'([\d,]+)\s+contributions? in the last year', raw)
    total = total_match.group(1) if total_match else str(sum(1 for _, lv in unique_days if lv > 0))

    return unique_days, total


def build_weeks(days):
    """Group (date, level) pairs into weeks starting on Sunday, like GitHub does."""
    from datetime import datetime

    weeks = []
    current_week = [None] * 7
    for date_str, level in days:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        weekday = (dt.weekday() + 1) % 7  # Mon=0..Sun=6 -> Sun=0..Sat=6
        if weekday == 0 and any(c is not None for c in current_week):
            weeks.append(current_week)
            current_week = [None] * 7
        current_week[weekday] = (dt, level)
    if any(c is not None for c in current_week):
        weeks.append(current_week)
    return weeks


def render_svg(weeks, total_label, username):
    n_weeks = len(weeks)
    width = LEFT_PAD + n_weeks * STEP + 10
    height = TOP_PAD + 7 * STEP + 30

    cells = []
    labels = []
    delay_unit = 0.036  # seconds between successive cells, tuned like the reference

    seen_months = set()
    for wi, week in enumerate(weeks):
        x = LEFT_PAD + wi * STEP
        for entry in week:
            if entry is None:
                continue
            dt, level = entry
            weekday = (dt.weekday() + 1) % 7
            y = TOP_PAD + weekday * STEP
            color = LEVEL_COLORS.get(str(min(level, 4)), LEVEL_COLORS["0"])
            delay = round((wi * 7 + weekday) * delay_unit / 2, 3)
            empty_cls = " e" if level == 0 else ""
            cells.append(
                f'<rect class="c g{empty_cls}" x="{x}" y="{y}" width="{CELL}" '
                f'height="{CELL}" rx="2.5" fill="{color}" '
                f'style="animation-delay:{delay}s"/>'
            )

            month_key = (dt.year, dt.month)
            if dt.day <= 7 and month_key not in seen_months:
                seen_months.add(month_key)
                labels.append(
                    f'<text class="lbl" x="{x}" y="16">{MONTHS[dt.month - 1]}</text>'
                )

    day_labels = (
        f'<text class="lbl" x="2" y="{TOP_PAD + 1 * STEP + 4}">Mon</text>'
        f'<text class="lbl" x="2" y="{TOP_PAD + 3 * STEP + 4}">Wed</text>'
        f'<text class="lbl" x="2" y="{TOP_PAD + 5 * STEP + 4}">Fri</text>'
    )

    total_escaped = html.escape(f"{total_label} contributions in the last year")

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" font-family="-apple-system,Segoe UI,Helvetica,Arial,sans-serif">
<style>
  text.lbl {{ fill:#7d8590; font-size:13px; font-weight:600; }}
  text.total {{ fill:#e6edf3; font-size:15px; font-weight:700; }}
  .c {{ transform-box:fill-box; transform-origin:center; opacity:0; animation:pop 0.55s ease-out both; }}
  .g {{ animation:pop 0.55s ease-out both, flash 0.7s ease-out both; }}
  @keyframes pop {{ 0%{{opacity:0;transform:scale(.2)}} 60%{{opacity:1;transform:scale(1.1)}} 100%{{opacity:1;transform:scale(1)}} }}
  @keyframes flash {{ 0%{{filter:brightness(2.4)}} 45%{{filter:brightness(2.4)}} 100%{{filter:brightness(1)}} }}
  @media (prefers-reduced-motion: reduce) {{ .c {{ opacity:1 !important; animation:none !important; }} }}
</style>
<rect width="{width}" height="{height}" fill="none"/>
{"".join(labels)}{day_labels}
{"".join(cells)}
<text class="total" x="{LEFT_PAD}" y="{height - 6}">{total_escaped}</text>
</svg>
'''
    return svg


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    username = sys.argv[1]
    out_path = sys.argv[2] if len(sys.argv) > 2 else "contrib-heatmap.svg"

    days, total = fetch_contribution_days(username)
    weeks = build_weeks(days)
    svg = render_svg(weeks, total, username)

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(svg)

    print(f"Wrote {out_path} ({len(days)} days parsed, {total} contributions)")


if __name__ == "__main__":
    main()
