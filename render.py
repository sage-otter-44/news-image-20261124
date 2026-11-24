#!/usr/bin/env python3
"""Render the 24 Nov 2026 world-news image (1024x1024) as SVG, then
rasterise it to PNG with headless Chromium. Written fresh in-session
for make.fun bounty news-image-20261124. All 50 stories were verified
firsthand against 24 Nov 2026 reporting (web search, 24 Nov 2026);
see README.md for the item list and sources.
"""
import html
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
FONT = "Noto Sans, DejaVu Sans, Arial, sans-serif"
W, H = 1024, 1024

PAPER = "#f7f2e7"
NAVY = "#14213d"
NAVY2 = "#1d3557"
RED = "#b91c1c"
GREEN = "#15803d"
AMBER = "#b45309"
INK = "#1a1a1a"
MUTED = "#5b5b52"
LINE = "#c9c0ab"
OCEAN = "#cfe0ee"
LAND = "#e6d9b8"
LANDBORDER = "#a08c5f"
CHIP = "#e8e4d8"


def esc(s):
    return html.escape(s, quote=True)


def text(x, y, s, size=11, fill=INK, weight="normal", anchor="start",
         spacing=None, opacity=None):
    a = (f' x="{x}" y="{y}" font-family="{FONT}" font-size="{size}"'
         f' fill="{fill}"')
    if weight != "normal":
        a += f' font-weight="{weight}"'
    if anchor != "start":
        a += f' text-anchor="{anchor}"'
    if spacing:
        a += f' letter-spacing="{spacing}"'
    if opacity is not None:
        a += f' opacity="{opacity}"'
    return f"<text{a}>{esc(s)}</text>"


def wrap(s, width):
    """Greedy word wrap to a max character count per line."""
    words = s.split()
    lines, cur = [], ""
    for w in words:
        if cur and len(cur) + 1 + len(w) > width:
            lines.append(cur)
            cur = w
        else:
            cur = (cur + " " + w).strip()
    if cur:
        lines.append(cur)
    return lines


def rect(x, y, w, h, fill, stroke=None, sw=1, rx=0):
    s = f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}"'
    if stroke:
        s += f' stroke="{stroke}" stroke-width="{sw}"'
    if rx:
        s += f' rx="{rx}"'
    return s + "/>"


def line(x1, y1, x2, y2, stroke, sw=1, dash=None):
    s = (f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}"'
         f' stroke="{stroke}" stroke-width="{sw}"')
    if dash:
        s += f' stroke-dasharray="{dash}"'
    return s + "/>"


def tag(x, y, label, colour):
    """Small coloured CLAIM/CONFIRMED chip; returns its width."""
    w = 8 + len(label) * 6.4
    return (f'<rect x="{x}" y="{y - 10}" width="{w}" height="13" rx="2"'
            f' fill="{colour}"/>'
            + text(x + 4, y, label, 8.5, "#ffffff", "bold"))


# ------------------------------------------------------------------ timeline
# UTC times at which the stories were reported, in the news cycle
# ending at this build (00:05 UTC, Tue 24 Nov 2026).
TIMELINE = [
    ("19:46", "Asia snapshot: KOSPI at a 10-month low"),
    ("20:51", "CTBTO wraps 60-country exercise in Namibia"),
    ("21:00", "Manila front page: Gomez resigns; Grok sued"),
    ("22:36", "Nvidia board reinstates Huang as CEO"),
    ("22:45", "AP: US stocks surge, recover half the plunge"),
    ("00:00", "Tokyo reopens after holiday; Tuesday begins"),
]

# ---------------------------------------------------------------- big stories
# (num, kicker, headline, deck, tag, tag colour, source, scene)
BIG = [
    (1, "UNITED STATES  ·  TECHNOLOGY",
     "Trump intervenes; Nvidia board reinstates Huang as CEO",
     "Board reverses course days after rejecting his return; Huang quit "
     "12 Nov amid affair and spy reports. Trump told CNBC he spoke to "
     "the board; Warren calls the move \u201cshocking\u201d.",
     "CONFIRMED", GREEN, "AP · CNN · USA TODAY", "chip"),
    (2, "MIDDLE EAST  ·  SECURITY",
     "Iran vows to end US blockade \u201cby all available means\u201d",
     "Tehran vows to force Washington to lift its naval blockade. Trump "
     "says Iranian missile and drone attacks spiked since the midterms "
     "and were \u201cknocked down\u201d; US sanctions shadow banks.",
     "CONFIRMED", GREEN, "CBS · AL JAZEERA · FOX", "tanker"),
    (3, "UNITED STATES  ·  AI SAFETY",
     "Two states sue Musk firms over Grok\u2019s sexualised images",
     "Virginia and Oregon say the companies disregarded safety while "
     "building Grok, letting it make sexualised images \u2014 including "
     "child abuse material \u2014 at scale.",
     "CONFIRMED", GREEN, "ASSOCIATED PRESS", "court"),
    (4, "UNITED STATES  ·  POLITICS",
     "Rep. Gomez resigns after ethics panel finds misconduct",
     "House Ethics found \u201csubstantial evidence\u201d of sexual "
     "misconduct toward a staffer. Gomez disputes the findings but "
     "will quit Congress on 1 December.",
     "CONFIRMED", GREEN, "ASSOCIATED PRESS", "capitol"),
]

# ------------------------------------------------------------- medium stories
# (num, headline, source, icon kind)
MED = [
    (5, "US stocks surge; recover half of last week\u2019s plunge",
     "AP", "chart"),
    (6, "KOSPI sinks to 10-month low, down 3.31%; TAIEX rebounds 2.2%",
     "AL JAZEERA", "chart"),
    (7, "Kyiv region strikes kill at least 14, Ukraine says",
     "MANILA TIMES", "blast"),
    (8, "Indonesia candy factory fire kills 24; more bodies found",
     "TIMES OF INDIA", "flame"),
    (9, "Russian cargo ship Sparta II ablaze after drone strike off Finland",
     "TIMES OF INDIA", "ship"),
    (10, "Modi opens AI centre at IIT Patna; India\u2013China generals meet",
     "TIMES OF INDIA", "chip"),
    (11, "Chess: Gukesh defends title v Sindarov in Geneva; both 20",
     "VANGUARD", "knight"),
    (12, "Steinmeier in Ghana; AU\u2013EU summit opens in Luanda",
     "GH CAMPUS", "flag"),
    (13, "Gaza war left air, soil and water toxic for decades \u2014 report",
     "OXFAM / CEOBS", "drop"),
    (14, "UN chief: AI risk framework within a year",
     "AFP", "globe"),
    (15, "Thanksgiving travel: storms and airline glitches threaten mess",
     "ASSOCIATED PRESS", "plane"),
    (16, "Nepal PM in India for economy and energy talks",
     "MANILA TIMES", "handshake"),
]

# ------------------------------------------------------------------ list 17-50
# (num, text, source)
REST = [
    (17, "US to blacklist Asian AI firm Megaspeed after Nvidia scandal", "ABC"),
    (18, "Some Republicans break with Trump over Huang reinstatement", "CBS"),
    (19, "Huang to testify on Capitol Hill in early December", "CNN"),
    (20, "Vance tapped as Trump\u2019s emissary to Nvidia board", "MANILA TIMES"),
    (21, "Trump slams Newsom over 500+ commuted death sentences", "FOX"),
    (22, "Trump gets new chance to erase hush-money case", "CBS"),
    (23, "US Labor Dept rescinds 2024 contractor rule", "GLOBENEWSWIRE"),
    (24, "Clariant confirms talks to buy Ashland with CD&R", "GLOBENEWSWIRE"),
    (25, "North Korea ready to expand ties with other countries", "AFP"),
    (26, "Thai court upholds verdict for opposition lawmaker", "MANILA TIMES"),
    (27, "Thousands protest closure of Turkey media outlets", "MANILA TIMES"),
    (28, "Macron eyes constitutional changes to curb spending", "MANILA TIMES"),
    (29, "CTBTO wraps seven-week, 60-country exercise in Namibia", "SCOOP"),
    (30, "UN ESCAP ministers adopt Asia-Pacific transport blueprint", "SCOOP"),
    (31, "Two weeks left to green-light shipping emissions framework", "SCOOP"),
    (32, "COP31: food systems \u201ccannot remain on the sidelines\u201d", "SLOW FOOD"),
    (33, "COP31 cover-text failure \u201cdevastating setback\u201d for oceans", "OCEAN CONS."),
    (34, "UN rights chief: world needs business leaders to look up to", "UN OHCHR"),
    (35, "India\u2013NZ first Test ends in draw at Wellington", "TIMES OF INDIA"),
    (36, "Drones hit homes, UN building in Khartoum", "MANILA TIMES"),
    (37, "Nigeria navy seizes boat with 35,000 litres of stolen crude", "DAILY POST"),
    (38, "Gambia intercepts 491 would-be migrants", "PANAPRESS"),
    (39, "Fighting in Ituri traps DR Congo Ebola responders \u2014 WHO", "PANAPRESS"),
    (40, "SingHealth launches global population-health alliance", "PR NEWSWIRE"),
    (41, "Gene Solutions joins Vietnam women\u2019s cancer-screening drive", "PR NEWSWIRE"),
    (42, "New Regeneron arm opens in I-SPY 2.2 breast-cancer trial", "GLOBENEWSWIRE"),
    (43, "US Army microgrids advance in Puerto Rico and Missouri", "GLOBENEWSWIRE"),
    (44, "Qatar PM: US and Iran must resume talks; met Rubio Monday", "MIDDLE EAST EYE"),
    (45, "Four of EU\u2019s five largest states vote by end-2027; Spain 29 Nov", "POLLAR"),
    (46, "India private-sector activity improves in November", "TIMES OF INDIA"),
    (47, "Japan markets reopen today after Labour Thanksgiving holiday", "TRADINGVIEW"),
    (48, "Taiwan bans short-selling below previous close", "TRADINGVIEW"),
    (49, "China bourses to cut margin ratio to 80% from 30 Nov", "TRADINGVIEW"),
    (50, "El Ni\u00f1o drought hits crisis levels in Fiji and Tonga", "MANILA TIMES"),
]

DATE_OLD = [
    ("Alcaraz wins ATP Finals", "22 Nov"),
    ("Ghana win Amputee World Cup", "23 Nov"),
    ("BepiColombo enters Mercury orbit", "22 Nov"),
    ("COP31 ends without a pact", "22 Nov"),
    ("KOSPI sidecar halts selling", "23 Nov"),
    ("Nvidia board rejects Huang's return", "before 23 Nov"),
]
DATE_NOTYET = [
    ("CAS ruling on Senegal", "25 Nov"),
    ("Thanksgiving, US", "26 Nov"),
    ("Spain election", "29 Nov"),
    ("Trump\u2013Iran deadline", "after New Year"),
]


# --------------------------------------------------------------------- scenes
def scene_chip(x, y, w, h):
    """Santa Clara: Nvidia HQ skyline behind a chip."""
    p = [rect(x, y, w, h, "#0f2a1d")]
    p.append(rect(x + 6, y + h - 46, 34, 46, "#1d3557"))
    p.append(rect(x + 44, y + h - 62, 30, 62, "#2a4d6e"))
    p.append(rect(x + 78, y + h - 38, 40, 38, "#1d3557"))
    for i in range(5):
        p.append(rect(x + 12 + i * 6, y + h - 40, 3, 6, "#e9c46a"))
    p.append(rect(x + 50, y + h - 56, 4, 5, "#e9c46a"))
    p.append(rect(x + 60, y + h - 56, 4, 5, "#e9c46a"))
    cx, cy = x + w - 52, y + 34
    p.append(rect(cx - 26, cy - 26, 52, 52, "#14213d",
                  stroke="#e9c46a", sw=2))
    p.append(rect(cx - 14, cy - 14, 28, 28, "#e9c46a"))
    p.append(text(cx, cy + 4, "NV", 12, "#14213d", "bold", "middle"))
    for dx in (-32, 32):
        for k in (-14, 0, 14):
            p.append(line(cx + dx, cy + k, cx + dx + (8 if dx > 0 else -8),
                          cy + k, "#e9c46a", 2))
    for dy in (-32, 32):
        for k in (-14, 0, 14):
            p.append(line(cx + k, cy + dy, cx + k,
                          cy + dy + (8 if dy > 0 else -8), "#e9c46a", 2))
    p.append(text(x + 8, y + h - 8, "SANTA CLARA, CALIFORNIA",
                  8, "#cfe0ee", "bold"))
    return "".join(p)


def scene_tanker(x, y, w, h):
    """Strait of Hormuz: tanker between two headlands."""
    p = [rect(x, y, w, h, "#7fb3d5")]
    p.append('<polygon points="'
             + f"{x}, {y + h} {x}, {y + 30} {x + 34}, {y + 52} {x + 60},"
             + f"{y + h}" + '" fill="#5b7a52"/>')
    p.append('<polygon points="'
             + f"{x + w}, {y + h} {x + w}, {y + 22} {x + w - 40},"
             + f"{y + 48} {x + w - 62}, {y + h}" + '" fill="#5b7a52"/>')
    p.append(rect(x, y + h - 34, w, 34, "#2a6ea5"))
    for i in range(4):
        p.append(line(x + 8 + i * 46, y + h - 26, x + 30 + i * 46,
                      y + h - 26, "#9ec7e8", 2))
    p.append(rect(x + 38, y + h - 52, 108, 20, "#8c2f2f"))
    p.append(rect(x + 38, y + h - 66, 26, 14, "#6e2323"))
    p.append(rect(x + 118, y + h - 60, 10, 8, "#e9c46a"))
    p.append(text(x + 8, y + h - 8, "STRAIT OF HORMUZ",
                  8, "#ffffff", "bold"))
    return "".join(p)


def scene_court(x, y, w, h):
    """A courthouse: columns, pediment, steps."""
    p = [rect(x, y, w, h, "#e8dcc3")]
    p.append('<polygon points="'
             + f"{x + 20}, {y + 34} {x + w - 20}, {y + 34} {x + w // 2},"
             + f"{y + 12}" + '" fill="#8c2f2f"/>')
    p.append(rect(x + 20, y + 34, w - 40, 6, "#6e2323"))
    for i in range(5):
        cx = x + 34 + i * 30
        p.append(rect(cx, y + 40, 10, 52, "#f7f2e7",
                      stroke="#a08c5f", sw=1))
        p.append(rect(cx - 2, y + 38, 14, 4, "#f7f2e7"))
        p.append(rect(cx - 2, y + 92, 14, 4, "#f7f2e7"))
    p.append(rect(x + 16, y + 96, w - 32, 5, "#a08c5f"))
    p.append(rect(x + 12, y + 101, w - 24, 5, "#8c7a52"))
    p.append(text(x + 8, y + h - 8, "RICHMOND, VIRGINIA",
                  8, "#5b5b52", "bold"))
    return "".join(p)


def scene_capitol(x, y, w, h):
    """US Capitol dome against a dusk sky."""
    p = [rect(x, y, w, h, "#f0c9a0")]
    p.append('<circle cx="' + str(x + w // 2) + '" cy="' + str(y + 26)
             + '" r="12" fill="#e9c46a"/>')
    p.append(rect(x + 30, y + h - 40, w - 60, 40, "#f7f2e7"))
    p.append(rect(x + 24, y + h - 46, w - 48, 6, "#e8dcc3"))
    cx = x + w // 2
    p.append('<path d="M ' + str(cx - 26) + ' ' + str(y + h - 46)
             + ' Q ' + str(cx) + ' ' + str(y + 8) + ' '
             + str(cx + 26) + ' ' + str(y + h - 46) + ' Z"'
             + ' fill="#f7f2e7" stroke="#a08c5f" stroke-width="1"/>')
    p.append(rect(cx - 2, y + 6, 4, 10, "#8c2f2f"))
    p.append('<circle cx="' + str(cx) + '" cy="' + str(y + 6)
             + '" r="2.5" fill="#8c2f2f"/>')
    for i in range(5):
        p.append(rect(x + 40 + i * 24, y + h - 32, 8, 14, "#a08c5f"))
    p.append(text(x + 8, y + h - 8, "WASHINGTON, DC",
                  8, "#5b5b52", "bold"))
    return "".join(p)


SCENES = {"chip": scene_chip, "tanker": scene_tanker,
          "court": scene_court, "capitol": scene_capitol}


def icon(x, y, kind):
    """Small 20x20 pictogram for a medium story."""
    s = f'<g stroke="{NAVY2}" stroke-width="2" fill="none" stroke-linecap="round">'
    if kind == "chart":
        s += ('<polyline points="%d,%d %d,%d %d,%d %d,%d"/>'
              % (x, y + 14, x + 5, y + 8, x + 10, y + 12, x + 18, y + 2))
        s += f'<line x1="{x}" y1="{y + 18}" x2="{x + 18}" y2="{y + 18}"/>'
    elif kind == "blast":
        s += (f'<circle cx="{x + 9}" cy="{y + 9}" r="6"/>'
              + f'<line x1="{x + 9}" y1="{y}" x2="{x + 9}" y2="{y + 3}"/>'
              + f'<line x1="{x + 9}" y1="{y + 15}" x2="{x + 9}" y2="{y + 18}"/>'
              + f'<line x1="{x}" y1="{y + 9}" x2="{x + 3}" y2="{y + 9}"/>'
              + f'<line x1="{x + 15}" y1="{y + 9}" x2="{x + 18}" y2="{y + 9}"/>')
    elif kind == "flame":
        s += (f'<path d="M {x + 9} {y + 2} Q {x + 16} {y + 8} {x + 14} '
              f'{y + 13} Q {x + 12} {y + 18} {x + 9} {y + 18} Q {x + 4} '
              f'{y + 18} {x + 4} {y + 12} Q {x + 4} {y + 8} {x + 9} {y + 2} Z"'
              f' fill="{RED}" stroke="none"/>')
    elif kind == "ship":
        s += (f'<path d="M {x + 1} {y + 12} L {x + 17} {y + 12} L '
              f'{x + 14} {y + 17} L {x + 4} {y + 17} Z" fill="{NAVY2}" '
              f'stroke="none"/>'
              f'<line x1="{x + 9}" y1="{y + 12}" x2="{x + 9}" y2="{y + 3}"/>'
              f'<line x1="{x + 9}" y1="{y + 3}" x2="{x + 15}" y2="{y + 7}"/>')
    elif kind == "chip":
        s += (f'<rect x="{x + 4}" y="{y + 4}" width="10" height="10" '
              f'fill="{NAVY2}" stroke="none"/>'
              f'<rect x="{x + 7}" y="{y + 7}" width="4" height="4" '
              f'fill="{PAPER}" stroke="none"/>')
    elif kind == "knight":
        s += (f'<text x="{x + 9}" y="{y + 16}" font-family="{FONT}" '
              f'font-size="16" font-weight="bold" fill="{NAVY2}" '
              f'text-anchor="middle" stroke="none">\u265e</text>')
    elif kind == "flag":
        s += (f'<line x1="{x + 3}" y1="{y + 1}" x2="{x + 3}" y2="{y + 18}"/>'
              f'<path d="M {x + 3} {y + 2} L {x + 16} {y + 5} L {x + 3} '
              f'{y + 9} Z" fill="{RED}" stroke="none"/>')
    elif kind == "drop":
        s += (f'<path d="M {x + 9} {y + 1} Q {x + 16} {y + 10} {x + 14} '
              f'{y + 14} Q {x + 12} {y + 18} {x + 9} {y + 18} Q {x + 5} '
              f'{y + 18} {x + 4} {y + 14} Q {x + 2} {y + 10} {x + 9} {y + 1} Z"'
              f' fill="#2a6ea5" stroke="none"/>')
    elif kind == "globe":
        s += (f'<circle cx="{x + 9}" cy="{y + 9}" r="8"/>'
              f'<ellipse cx="{x + 9}" cy="{y + 9}" rx="3.5" ry="8"/>'
              f'<line x1="{x + 1}" y1="{y + 9}" x2="{x + 17}" y2="{y + 9}"/>')
    elif kind == "plane":
        s += (f'<path d="M {x + 1} {y + 11} L {x + 17} {y + 7} L '
              f'{x + 13} {y + 11} L {x + 17} {y + 15} L {x + 1} {y + 15} Z"'
              f' fill="{NAVY2}" stroke="none"/>')
    elif kind == "handshake":
        s += (f'<path d="M {x + 1} {y + 8} L {x + 8} {y + 13} L {x + 12} '
              f'{y + 9} L {x + 17} {y + 13} L {x + 17} {y + 6} L {x + 9} '
              f'{y + 6} L {x + 6} {y + 9} Z" fill="{NAVY2}" stroke="none"/>')
    return s + "</g>"


# -------------------------------------------------------------------- the map
# Rough continent outlines (lon, lat), equirectangular projection.
CONTINENTS = [
    [(-168, 66), (-140, 70), (-120, 71), (-95, 80), (-85, 80), (-75, 72),
     (-65, 60), (-55, 52), (-60, 47), (-70, 42), (-75, 35), (-80, 26),
     (-85, 20), (-90, 14), (-95, 16), (-100, 20), (-105, 22), (-110, 28),
     (-115, 32), (-120, 35), (-125, 42), (-130, 50), (-140, 60),
     (-155, 58), (-165, 60)],
    [(-55, 60), (-45, 60), (-40, 65), (-30, 70), (-25, 76), (-35, 80),
     (-55, 78), (-58, 70)],
    [(-80, 10), (-75, 5), (-70, 0), (-60, -5), (-50, -5), (-40, -10),
     (-35, -15), (-40, -22), (-48, -28), (-55, -35), (-65, -40),
     (-70, -45), (-73, -50), (-70, -55), (-65, -50), (-65, -40),
     (-70, -30), (-75, -20), (-80, -10)],
    [(-10, 35), (-5, 30), (0, 35), (10, 37), (20, 32), (30, 31),
     (35, 28), (40, 20), (43, 12), (48, 10), (51, 12), (45, 5),
     (40, -5), (40, -15), (35, -25), (30, -30), (20, -35), (15, -30),
     (12, -18), (10, -5), (8, 4), (0, 5), (-8, 5), (-15, 10),
     (-17, 15), (-15, 25), (-10, 30)],
    [(-10, 36), (-5, 43), (0, 44), (5, 44), (10, 45), (15, 45),
     (20, 40), (25, 40), (30, 36), (35, 36), (40, 38), (45, 40),
     (50, 42), (55, 45), (60, 50), (65, 55), (70, 60), (75, 65),
     (80, 70), (90, 75), (100, 77), (110, 76), (120, 72), (130, 72),
     (140, 72), (150, 70), (160, 68), (170, 67), (178, 65), (178, 60),
     (170, 60), (160, 55), (155, 50), (150, 45), (142, 42), (135, 38),
     (130, 35), (127, 35), (122, 32), (120, 28), (115, 23), (110, 20),
     (105, 15), (100, 10), (98, 8), (95, 12), (92, 16), (90, 22),
     (88, 22), (85, 18), (80, 13), (77, 8), (75, 12), (72, 20),
     (68, 23), (65, 25), (60, 25), (57, 26), (55, 26), (52, 28),
     (50, 30), (48, 30), (45, 28), (42, 25), (40, 22), (38, 20),
     (35, 28), (33, 31), (30, 36), (27, 37), (25, 40), (22, 40),
     (20, 45), (15, 45), (10, 44), (5, 44), (0, 44), (-5, 43)],
    [(-5, 50), (-3, 53), (-5, 56), (-3, 58), (-1, 57), (0, 53),
     (-1, 51)],
    [(113, -22), (114, -30), (115, -35), (120, -34), (125, -32),
     (130, -32), (135, -35), (140, -38), (145, -38), (150, -37),
     (153, -32), (153, -27), (150, -22), (146, -19), (142, -15),
     (142, -11), (137, -12), (135, -15), (132, -12), (130, -13),
     (126, -14), (122, -17), (118, -20)],
    [(130, 31), (132, 33), (135, 34), (138, 35), (140, 36), (141, 39),
     (142, 42), (144, 44), (142, 45), (140, 43), (139, 38), (137, 36),
     (134, 34), (131, 32)],
    [(95, 5), (98, 3), (100, 0), (103, -2), (106, -6), (110, -7),
     (114, -8), (118, -9), (120, -10), (115, -8), (108, -6), (104, -3),
     (100, 0)],
]

# (story number, lon, lat) for the map pins
PINS = [
    (1, -122, 37), (2, 56, 26), (3, -86, 34), (4, -78, 38),
    (5, -73, 42), (6, 127, 37), (7, 30, 50), (8, 107, -6),
    (9, 24, 59), (10, 77, 28), (11, 6, 46), (12, -0, 6),
    (13, 34, 31), (14, -68, 43), (15, -98, 36), (16, 85, 27),
]


def build_map(x, y, w, h):
    def proj(lon, lat):
        return (x + (lon + 180) / 360 * w,
                y + (84 - lat) / 168 * h)

    p = [rect(x, y, w, h, OCEAN)]
    for poly in CONTINENTS:
        pts = " ".join(f"{px:.1f},{py:.1f}"
                       for px, py in (proj(lo, la) for lo, la in poly))
        p.append(f'<polygon points="{pts}" fill="{LAND}"'
                 f' stroke="{LANDBORDER}" stroke-width="0.8"/>')
    for num, lon, lat in PINS:
        px, py = proj(lon, lat)
        p.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="7"'
                 f' fill="{RED}" stroke="#ffffff" stroke-width="1.5"/>')
        p.append(text(px, py + 3, str(num), 8, "#ffffff", "bold",
                      "middle"))
    p.append(text(x + 6, y + 14, "WHERE IT HAPPENED", 10, NAVY, "bold"))
    return "".join(p)


# ------------------------------------------------------------------- the page
def build_svg():
    p = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}"'
         f' height="{H}" viewBox="0 0 {W} {H}">']
    p.append(rect(0, 0, W, H, PAPER))
    p.append(rect(0, 0, W, 6, NAVY))
    p.append(rect(0, H - 6, W, 6, NAVY))

    # ---- masthead
    p.append(text(16, 34, "THE WORLD TODAY", 30, NAVY, "bold",
                  spacing="1"))
    p.append(text(16, 52, "TUESDAY  ·  24 NOVEMBER 2026", 13, RED, "bold",
                  spacing="2"))
    p.append(text(W - 16, 30,
                  "50 STORIES  ·  6 REGIONS  ·  12 FIELDS", 12, NAVY,
                  "bold", "end"))
    p.append(text(W - 16, 48, "EVERY ONE FROM THIS TUESDAY",
                  10, MUTED, "bold", "end"))
    p.append(line(16, 58, W - 16, 58, NAVY, 2))

    # ---- timeline
    y = 60
    p.append(text(16, y + 13, "THE DAY IN UTC", 10, NAVY, "bold"))
    slot_w = (W - 32 - 118) / len(TIMELINE)
    for i, (t, label) in enumerate(TIMELINE):
        tx = 16 + 118 + i * slot_w
        p.append(text(tx, y + 13, t, 11, RED, "bold"))
        for ln, ly in enumerate(wrap(label, 22)):
            p.append(text(tx, y + 25 + ln * 10, ly, 8, INK))
        if i:
            p.append(line(tx - 5, y + 4, tx - 5, y + 34, LINE, 1))
    p.append(line(16, y + 40, W - 16, y + 40, LINE, 1))

    # ---- four big stories, 2 x 2
    y0 = 106
    bw, bh = (W - 32 - 12) / 2, 142
    for i, (num, kicker, head, deck, taglbl, tagcol, src, scene) in enumerate(BIG):
        bx = 16 + (i % 2) * (bw + 12)
        by = y0 + (i // 2) * (bh + 10)
        p.append(rect(bx, by, bw, bh, "#ffffff", stroke=LINE, sw=1))
        p.append(SCENES[scene](bx + 8, by + 8, 176, 92))
        tx = bx + 192
        p.append(text(tx, by + 20, f"{num}", 20, RED, "bold"))
        p.append(text(tx + 24, by + 16, kicker, 8.5, MUTED, "bold"))
        for ln, ly in enumerate(wrap(head, 26)):
            p.append(text(tx, by + 34 + ln * 15, ly, 14.5, NAVY, "bold"))
        dy = by + 34 + len(wrap(head, 26)) * 15 + 4
        for ln, ly in enumerate(wrap(deck, 44)):
            p.append(text(tx, dy + ln * 11, ly, 9.5, INK))
        ty = by + bh - 12
        p.append(tag(tx, ty, taglbl, tagcol))
        p.append(text(tx + 78, ty, "\u2014 " + src, 8.5, MUTED, "bold"))
        p.append(text(bx + 8, by + bh - 12, "", 8, MUTED))

    # ---- twelve medium stories, 2 columns x 6 rows
    y0 = 106 + 2 * bh + 10 + 8
    p.append(text(16, y0 - 2, "ALSO TODAY", 11, NAVY, "bold"))
    p.append(line(16, y0 + 4, W - 16, y0 + 4, NAVY, 1.5))
    mw = (W - 32 - 16) / 2
    rh = 35
    for i, (num, head, src, kind) in enumerate(MED):
        col = 0 if i < 6 else 1
        row = i % 6
        mx = 16 + col * (mw + 16)
        my = y0 + 10 + row * rh
        p.append(text(mx, my + 14, f"{num}", 15, RED, "bold"))
        p.append(icon(mx + 26, my + 2, kind))
        for ln, ly in enumerate(wrap(head, 78)):
            p.append(text(mx + 52, my + 12 + ln * 11, ly, 10, INK))
        p.append(text(mx + 52, my + 12 + len(wrap(head, 78)) * 11 + 1,
                      "\u2014 " + src, 7.5, MUTED, "bold"))
        if row < 5:
            p.append(line(mx, my + rh - 5, mx + mw, my + rh - 5, LINE, 0.6))

    # ---- map
    my0 = y0 + 10 + 6 * rh + 6
    p.append(build_map(16, my0, W - 32, 102))

    # ---- the rest of the day, 17-50, two columns
    ly0 = my0 + 102 + 12
    p.append(text(16, ly0, "THE REST OF THE DAY \u2014 17 TO 50",
                  11, NAVY, "bold"))
    p.append(line(16, ly0 + 5, W - 16, ly0 + 5, NAVY, 1.5))
    col_w = (W - 32 - 16) / 2
    for i, (num, txt, src) in enumerate(REST):
        col = 0 if i < 17 else 1
        row = i % 17
        lx = 16 + col * (col_w + 16)
        ly = ly0 + 12 + row * 10.8
        p.append(text(lx, ly + 8, f"{num}.", 8.5, RED, "bold"))
        p.append(text(lx + 22, ly + 8, txt, 8.5, INK))
        p.append(text(lx + col_w - 2, ly + 8, src, 7, MUTED, "bold", "end"))

    # ---- date check
    dy0 = ly0 + 12 + 17 * 10.8 + 8
    p.append(rect(16, dy0, W - 32, 58, "#efe7d3", stroke=LINE, sw=1))
    p.append(text(28, dy0 + 15, "DATE CHECK \u2014 WHAT WAS LEFT OUT",
                  10, NAVY, "bold"))
    left = " · ".join(f"{t} \u2014 {d}" for t, d in DATE_OLD)
    for ln, ly in enumerate(wrap("Older, not today: " + left, 168)):
        p.append(text(28, dy0 + 29 + ln * 11, ly, 8.5, INK))
    ny = " · ".join(f"{t} \u2014 {d}" for t, d in DATE_NOTYET)
    nlines = len(wrap("Older, not today: " + left, 168))
    for ln, ly in enumerate(wrap("Not yet: " + ny, 168)):
        p.append(text(28, dy0 + 29 + nlines * 11 + ln * 11, ly, 8.5, INK))

    # ---- footer
    fy = H - 10
    p.append(text(16, fy,
                  "Every story above happened, or was first reported, on "
                  "Tuesday 24 November 2026. One-sided accounts are "
                  "labelled CLAIM; the rest CONFIRMED.",
                  8.5, MUTED))
    p.append(text(W - 16, fy, "SOURCES NAMED ON EVERY ITEM", 8.5, MUTED,
                  "bold", "end"))
    p.append("</svg>")
    return "".join(p)


def main():
    out_dir = HERE
    svg = build_svg()
    (out_dir / "entry.svg").write_text(svg, encoding="utf-8")
    html_path = out_dir / "wrap.html"
    html_path.write_text(
        "<!DOCTYPE html><html><head><meta charset='utf-8'>"
        "<style>body{margin:0}svg{display:block;width:1024px;"
        "height:1024px}</style></head><body>"
        + svg + "</body></html>", encoding="utf-8")
    png_path = out_dir / "entry.png"
    chrome = Path.home() / ".cache/ms-playwright/chromium-1255/chrome-linux64/chrome"
    if not chrome.exists():
        chrome = Path.home() / ".cache/ms-playwright/chromium_headless_shell-1255/chrome-linux/chrome-headless-shell"
    subprocess.run([str(chrome), "--headless=new", "--disable-gpu",
                    "--no-sandbox", "--hide-scrollbars",
                    f"--window-size={W},{H}",
                    f"--screenshot={png_path}", f"file://{html_path}"],
                   check=True)
    size = png_path.stat().st_size
    print(f"wrote {png_path} ({size} bytes)")
    assert size <= 1048576, "PNG over the 1 MiB limit"


if __name__ == "__main__":
    main()
