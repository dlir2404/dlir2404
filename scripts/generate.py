"""Render the neofetch-style profile card (dark_mode.svg and light_mode.svg).

Static facts live in PROFILE below; GitHub numbers are fetched from the GraphQL API.
Run locally with:  GH_TOKEN=$(gh auth token) python3 scripts/generate.py
"""

import datetime as dt
import json
import os
import urllib.request
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
USER = os.environ.get("GH_USER", "dlir2404")
CAREER_START = dt.date(2023, 3, 1)
WIDTH = 56  # characters in the info column

PROFILE = [
    ("header", "dlir2404@github"),
    ("kv", "Experience", "{experience}"),
    ("kv", "Location", "Hanoi, Vietnam"),
    ("kv", "Role", "Full Stack Developer"),
    ("blank",),
    ("kv", "Languages.Code", "TypeScript, Python, JavaScript"),
    ("kv", "Languages.Real", "Vietnamese, English"),
    ("blank",),
    ("kv", "Stack.Backend", "NestJS, Django, FastAPI, gRPC"),
    ("kv", "Stack.Frontend", "React, Next.js, Vue.js"),
    ("kv", "Stack.Data", "PostgreSQL, MySQL, Redis, Kafka"),
    ("kv", "Stack.Infra", "Docker, Kubernetes, GitHub Actions"),
    ("kv", "Interests", "AI agents, LLM evals, backend systems"),
    ("section", "Contact"),
    ("kv", "Email", "dinhlinh.work24@gmail.com"),
    ("kv", "Portfolio", "larry.is-a.dev"),
    ("kv", "LinkedIn", "in/dlir2404"),
    ("section", "GitHub Stats"),
    ("pair", ("Repos", "{repos}"), ("Stars", "{stars}")),
    ("pair", ("Contributions", "{contributions}"), ("Followers", "{followers}")),
]

THEMES = {
    "dark": dict(bg="#161b22", text="#c9d1d9", key="#ffa657", value="#a5d6ff", dots="#616e7f"),
    "light": dict(bg="#f6f8fa", text="#24292f", key="#953800", value="#0a3069", dots="#c2cfde"),
}

FONT = "ui-monospace,SFMono-Regular,Menlo,Consolas,'Liberation Mono',monospace"
FONT_SIZE = 16
LINE_HEIGHT = 20
CHAR_WIDTH = FONT_SIZE * 0.6
ART_FONT_SIZE = 26
INFO_X = 420
TOP = 30


def graphql(query, variables=None):
    token = os.environ["GH_TOKEN"]
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": query, "variables": variables or {}}).encode(),
        headers={"Authorization": f"bearer {token}", "User-Agent": "profile-card"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        body = json.load(resp)
    if "errors" in body:
        raise RuntimeError(body["errors"])
    return body["data"]


def fetch_stats():
    data = graphql(
        """query($login: String!) {
          user(login: $login) {
            followers { totalCount }
            repositories(first: 100, ownerAffiliations: OWNER, privacy: PUBLIC, isFork: false) {
              totalCount
              nodes { stargazerCount }
            }
            contributionsCollection { contributionYears }
          }
        }""",
        {"login": USER},
    )["user"]
    total = 0
    for year in data["contributionsCollection"]["contributionYears"]:
        start = f"{year}-01-01T00:00:00Z"
        end = f"{year}-12-31T23:59:59Z"
        cal = graphql(
            """query($login: String!, $from: DateTime!, $to: DateTime!) {
              user(login: $login) {
                contributionsCollection(from: $from, to: $to) {
                  contributionCalendar { totalContributions }
                }
              }
            }""",
            {"login": USER, "from": start, "to": end},
        )
        total += cal["user"]["contributionsCollection"]["contributionCalendar"]["totalContributions"]
    repos = data["repositories"]
    return {
        "repos": f"{repos['totalCount']:,}",
        "stars": f"{sum(n['stargazerCount'] for n in repos['nodes']):,}",
        "contributions": f"{total:,}",
        "followers": f"{data['followers']['totalCount']:,}",
    }


def experience(today=None):
    today = today or dt.date.today()
    months = (today.year - CAREER_START.year) * 12 + today.month - CAREER_START.month
    years, months = divmod(months, 12)
    parts = [f"{years} year{'s' * (years != 1)}"]
    if months:
        parts.append(f"{months} month{'s' * (months != 1)}")
    return ", ".join(parts)


def tspan(text, cls):
    return f'<tspan class="{cls}">{escape(text)}</tspan>'


def kv_line(key, value, width):
    """'. Key: ...... value' padded with dots to exactly `width` characters."""
    head = f"{key}:"
    dots = width - len(". ") - len(head) - len(value) - 2
    dots = max(dots, 1)
    return tspan(". ", "dots") + tspan(head, "key") + tspan(" " + "." * dots + " ", "dots") + tspan(value, "value")


def rule(title, width):
    label = f"{title} "
    return tspan(label, "text") + tspan("—" * (width - len(label)), "dots")


def render_info(values):
    lines = []
    for item in PROFILE:
        kind = item[0]
        if kind == "header":
            lines.append(rule(item[1], WIDTH))
        elif kind == "section":
            lines.append(tspan("— ", "dots") + rule(item[1], WIDTH - 2))
        elif kind == "blank":
            lines.append(tspan(".", "dots"))
        elif kind == "kv":
            lines.append(kv_line(item[1], item[2].format(**values), WIDTH))
        elif kind == "pair":
            (k1, v1), (k2, v2) = item[1], item[2]
            left = kv_line(k1, v1.format(**values), 32)
            right_width = WIDTH - 32 - 3
            head = f"{k2}:"
            value = v2.format(**values)
            dots = max(right_width - len(head) - len(value) - 2, 1)
            right = tspan(head, "key") + tspan(" " + "." * dots + " ", "dots") + tspan(value, "value")
            lines.append(left + tspan(" | ", "dots") + right)
    return lines


def render_svg(theme, art_lines, info_lines):
    c = THEMES[theme]
    height = TOP + len(info_lines) * LINE_HEIGHT + 10
    art_cols = max(map(len, art_lines))
    art_width = art_cols * CHAR_WIDTH
    art_x = (INFO_X - 15 - art_width) / 2
    art_top = TOP + (len(info_lines) - len(art_lines)) * LINE_HEIGHT / 2
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="985" height="{height}" viewBox="0 0 985 {height}" '
        f'font-family="{FONT}" font-size="{FONT_SIZE}px">',
        "<style>",
        f".text{{fill:{c['text']}}} .key{{fill:{c['key']}}} .value{{fill:{c['value']}}} .dots{{fill:{c['dots']}}}",
        "text,tspan{white-space:pre}",
        "</style>",
        f'<rect width="985" height="{height}" rx="15" fill="{c["bg"]}"/>',
        f'<text class="text" font-size="{ART_FONT_SIZE}px" xml:space="preserve">',
    ]
    # Braille glyphs come from a fallback font whose width varies by platform,
    # so every line is stretched to the exact width of a monospace cell row.
    for i, line in enumerate(art_lines):
        out.append(
            f'<tspan x="{art_x:.1f}" y="{art_top + i * LINE_HEIGHT:.1f}" '
            f'textLength="{art_width:.1f}" lengthAdjust="spacingAndGlyphs">{escape(line)}</tspan>'
        )
    out.append("</text>")
    out.append(f'<text x="{INFO_X}" y="{TOP}" class="text" xml:space="preserve">')
    for i, line in enumerate(info_lines):
        out.append(f'<tspan x="{INFO_X}" y="{TOP + i * LINE_HEIGHT}">{line}</tspan>')
    out.append("</text>")
    out.append("</svg>")
    return "\n".join(out) + "\n"


def main():
    values = {"experience": experience(), **fetch_stats()}
    info_lines = render_info(values)
    for theme in THEMES:
        art_lines = (ROOT / "assets" / f"art-{theme}.txt").read_text().splitlines()
        (ROOT / f"{theme}_mode.svg").write_text(render_svg(theme, art_lines, info_lines))
    print(json.dumps(values))


if __name__ == "__main__":
    main()
