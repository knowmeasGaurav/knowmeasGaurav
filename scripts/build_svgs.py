#!/usr/bin/env python3
"""Builds the animated SVG panels in assets/ for the profile README.

Concept: mission control. Header is a live console (orbit view, boot log,
MET clock, telemetry ticker), then section rules, a state-flow schematic,
a payload bay and a loss-of-signal footer.

Plain SVG animated with SMIL. No JavaScript, no web fonts, so GitHub renders
everything straight from an <img> tag.

    python scripts/build_svgs.py
"""
import math
import random
from pathlib import Path
from xml.sax.saxutils import escape

OUT = Path(__file__).resolve().parent.parent / "assets"

MONO = "'JetBrains Mono','SF Mono','Cascadia Code',Menlo,Consolas,'DejaVu Sans Mono',monospace"

BG = "#060A13"
PANEL = "#0A111E"
EDGE = "#1A2640"
TEXT = "#E4ECF8"
DIM = "#6B7C99"
MUTE = "#4A5B7C"
FAINT = "#26344F"
BLUE = "#7AA2FF"
AMBER = "#F5B94A"
GREEN = "#5EE6A8"
VIOLET = "#B69CFF"
CYAN = "#62D4F0"
RED = "#FF6B6B"

GLOW = (
    '<filter id="glow" x="-100%" y="-100%" width="300%" height="300%">'
    '<feGaussianBlur stdDeviation="2.2" result="b"/>'
    '<feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>'
)


def text(x, y, s, size=12, fill=TEXT, weight=400, anchor="start", ls=0, extra="", raw=False):
    body = s if raw else escape(s)
    return (
        f'<text x="{x}" y="{y}" font-family="{MONO}" font-size="{size}" font-weight="{weight}" '
        f'fill="{fill}" text-anchor="{anchor}" letter-spacing="{ls}" xml:space="preserve" {extra}>{body}</text>'
    )


def tspan(s, fill, weight=None):
    w = f' font-weight="{weight}"' if weight else ""
    return f'<tspan fill="{fill}"{w}>{escape(s)}</tspan>'


def svg(w, h, title, desc, body, defs=""):
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img" aria-labelledby="t d">
<title id="t">{escape(title)}</title>
<desc id="d">{escape(desc)}</desc>
<defs>
<clipPath id="frame"><rect width="{w}" height="{h}" rx="12"/></clipPath>
{defs}
</defs>
<g clip-path="url(#frame)">
<rect width="{w}" height="{h}" fill="{BG}"/>
{body}
</g>
<rect x="0.5" y="0.5" width="{w - 1}" height="{h - 1}" rx="12" fill="none" stroke="{EDGE}"/>
</svg>
"""


def stars(rng, w, y0, y1, n, dim_left=0):
    out = []
    for _ in range(n):
        x = rng.uniform(8, w - 8)
        y = rng.uniform(y0, y1)
        r = rng.choice([0.5, 0.6, 0.7, 0.9, 1.1, 1.4])
        o = rng.uniform(0.15, 0.7)
        if x < dim_left:
            o *= 0.45
        anim = ""
        if rng.random() < 0.4:
            d = rng.uniform(2.5, 6)
            anim = (
                f'<animate attributeName="opacity" values="{o:.2f};{o * 0.15:.2f};{o:.2f}" '
                f'dur="{d:.1f}s" begin="-{rng.uniform(0, d):.1f}s" repeatCount="indefinite"/>'
            )
        out.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="#CFE0FF" opacity="{o:.2f}">{anim}</circle>')
    return "\n".join(out)


# ---------------------------------------------------------------- header


def met_clock(defs, x, y):
    """T+ HH:MM:SS counting up from page load. Each digit is a clipped strip."""
    out = [text(x - 50, y, "MET", 11, DIM, ls=1.5), text(x - 22, y, "T+", 12, DIM)]
    layout = ["0", "0", ":", (600, 6), (60, 10), ":", (10, 6), (1, 10)]
    for i, slot in enumerate(layout):
        sx = x + i * 9
        if slot == ":":
            out.append(text(sx, y, ":", 12, DIM))
        elif isinstance(slot, str):
            out.append(text(sx, y, slot, 12, TEXT))
        else:
            period, n = slot
            cid = f"met{i}"
            defs.append(f'<clipPath id="{cid}"><rect x="{sx - 1}" y="{y - 11}" width="10" height="15"/></clipPath>')
            strip = "".join(text(sx, y + k * 20, str(k), 12, TEXT) for k in range(n))
            values = ";".join(f"0 {-20 * k}" for k in range(n))
            kt = ";".join(f"{k / n:.4f}" for k in range(n))
            out.append(
                f'<g clip-path="url(#{cid})"><g>'
                f'<animateTransform attributeName="transform" type="translate" values="{values}" '
                f'keyTimes="{kt}" calcMode="discrete" dur="{period * n}s" repeatCount="indefinite"/>'
                f"{strip}</g></g>"
            )
    return "\n".join(out)


def ellipse_paths(cx, cy, rx, ry, deg):
    """Full orbit plus its front (lower) half, both starting at the right end."""
    a = math.radians(deg)
    p0 = f"{cx + rx * math.cos(a):.2f},{cy + rx * math.sin(a):.2f}"
    p1 = f"{cx - rx * math.cos(a):.2f},{cy - rx * math.sin(a):.2f}"
    arc = f"A{rx},{ry} {deg} 1 1"
    return f"M{p0} {arc} {p1} {arc} {p0}", f"M{p0} {arc} {p1}"


def satellite(tag, name, color, station):
    label = text(10, -8, tspan(tag + " ", color) + tspan(name, DIM, 400), 9.5, color, 700, ls=1, raw=True)
    if station:
        body = (
            f'<rect x="-14" y="-2.5" width="8" height="5" fill="none" stroke="{color}" stroke-width="1"/>'
            f'<rect x="6" y="-2.5" width="8" height="5" fill="none" stroke="{color}" stroke-width="1"/>'
            f'<rect x="-3.5" y="-3.5" width="7" height="7" fill="{color}" filter="url(#glow)"/>'
        )
    else:
        body = (
            f'<circle r="7" fill="{color}" opacity=".16"/>'
            f'<circle r="2.8" fill="{color}" filter="url(#glow)"/>'
        )
    return body + label


def header():
    W, H = 900, 420
    rng = random.Random(7)
    defs = [GLOW]
    b = []

    b.append(stars(rng, W, 42, 372, 95, dim_left=460))

    # meteor, once every 11s
    defs.append(
        '<linearGradient id="meteor" x1="0" x2="1" y1="0" y2="0">'
        '<stop offset="0" stop-color="#CFE0FF" stop-opacity="0"/><stop offset="1" stop-color="#FFFFFF"/></linearGradient>'
    )
    b.append(
        '<g opacity="0">'
        '<animateTransform attributeName="transform" type="translate" values="540 70;540 70;790 160;790 160" '
        'keyTimes="0;0.6;0.67;1" dur="11s" begin="3s" repeatCount="indefinite"/>'
        '<animate attributeName="opacity" values="0;0;1;0;0" keyTimes="0;0.6;0.62;0.67;1" dur="11s" begin="3s" repeatCount="indefinite"/>'
        '<line x1="-46" y1="-16" x2="0" y2="0" stroke="url(#meteor)" stroke-width="1.4" stroke-linecap="round"/></g>'
    )

    # top bar
    b.append(f'<rect width="{W}" height="36" fill="{PANEL}"/><line x1="0" y1="36" x2="{W}" y2="36" stroke="{EDGE}"/>')
    b.append(
        f'<circle cx="22" cy="18" r="3.5" fill="{RED}">'
        '<animate attributeName="opacity" values="1;0.2;1" dur="1.6s" repeatCount="indefinite"/></circle>'
    )
    b.append(text(32, 22, "LIVE", 11, RED, 700, ls=1.5))
    b.append(text(76, 22, "GROUND CONTROL  //  KNOWMEASGAURAV", 11, DIM, ls=1.5))
    b.append(met_clock(defs, 810, 22))

    # callsign + name
    b.append(text(40, 84, "CALLSIGN", 10, DIM, ls=3.5))
    defs.append(
        f'<linearGradient id="sheen" gradientUnits="userSpaceOnUse" x1="-260" y1="0" x2="0" y2="0">'
        f'<stop offset="0" stop-color="{TEXT}"/><stop offset="0.42" stop-color="{TEXT}"/>'
        f'<stop offset="0.5" stop-color="{BLUE}"/><stop offset="0.58" stop-color="{TEXT}"/>'
        f'<stop offset="1" stop-color="{TEXT}"/>'
        '<animateTransform attributeName="gradientTransform" type="translate" values="0 0;720 0;720 0" '
        'keyTimes="0;0.4;1" dur="7s" begin="1.4s" repeatCount="indefinite"/></linearGradient>'
    )
    defs.append(
        '<clipPath id="nameclip"><rect x="30" y="90" width="0" height="72">'
        '<animate attributeName="width" from="0" to="400" dur="0.9s" begin="0.3s" fill="freeze"/></rect></clipPath>'
    )
    b.append(
        f'<g clip-path="url(#nameclip)">'
        + text(36, 148, "GAURAV", 64, "url(#sheen)", 800, ls=10, extra='textLength="330" lengthAdjust="spacing"')
        + "</g>"
    )
    b.append(
        f'<line x1="30" y1="94" x2="30" y2="160" stroke="{BLUE}" stroke-width="2" opacity="0" filter="url(#glow)">'
        '<animate attributeName="opacity" values="0;1;1;0" keyTimes="0;0.05;0.9;1" dur="0.9s" begin="0.3s"/>'
        '<animateTransform attributeName="transform" type="translate" from="0 0" to="400 0" dur="0.9s" begin="0.3s" fill="freeze"/></line>'
    )
    b.append(
        text(40, 182, "SOFTWARE ENGINEER  ·  FLUTTER DEVELOPER", 12, AMBER, 600, ls=2.2,
             extra='opacity="0"').replace(
            "</text>", '<animate attributeName="opacity" from="0" to="1" dur="0.6s" begin="1s" fill="freeze"/></text>')
    )
    b.append(
        f'<line x1="40" y1="200" x2="440" y2="200" stroke="{FAINT}" stroke-dasharray="400" stroke-dashoffset="400">'
        '<animate attributeName="stroke-dashoffset" from="400" to="0" dur="0.8s" begin="1.2s" fill="freeze"/></line>'
    )

    # boot log
    log = [
        ("uplink", "established", "OK", GREEN),
        ("station", "CampusLink", "ACTIVE", AMBER),
        ("frontend crew", "just me", "OK", GREEN),
        ("telemetry", "nominal", "OK", GREEN),
        ("cleared to ship", "always", "GO", BLUE),
    ]
    for i, (key, val, tag, color) in enumerate(log):
        y = 230 + i * 24
        t0 = 1.6 + i * 0.5
        prefix = f"> {key} " + "." * (17 - len(key)) + " "
        cid = f"log{i}"
        defs.append(
            f'<clipPath id="{cid}"><rect x="36" y="{y - 14}" width="0" height="20">'
            f'<animate attributeName="width" from="0" to="320" dur="0.45s" begin="{t0}s" fill="freeze"/></rect></clipPath>'
        )
        b.append(
            f'<g clip-path="url(#{cid})">'
            + text(40, y, tspan(prefix, DIM) + tspan(val, TEXT), 12, TEXT, raw=True)
            + "</g>"
        )
        b.append(
            text(440, y, f"[ {tag} ]", 12, color, 700, anchor="end", extra='opacity="0"').replace(
                "</text>", f'<set attributeName="opacity" to="1" begin="{t0 + 0.45:.2f}s" fill="freeze"/></text>')
        )
    b.append(text(40, 350, ">", 12, DIM))
    b.append(
        f'<rect x="56" y="339" width="8" height="14" fill="{BLUE}" opacity="0">'
        '<animate attributeName="opacity" values="1;1;0;0" keyTimes="0;0.5;0.5;1" dur="1s" begin="4.2s" repeatCount="indefinite"/></rect>'
    )

    # orbital view
    for (x, y, dx, dy) in [(478, 48, 1, 1), (882, 48, -1, 1), (478, 368, 1, -1), (882, 368, -1, -1)]:
        b.append(f'<path d="M{x},{y + 14 * dy} L{x},{y} L{x + 14 * dx},{y}" fill="none" stroke="{FAINT}" stroke-width="1.5"/>')
    b.append(text(494, 66, "ORBITAL VIEW", 9.5, DIM, ls=2))
    b.append(text(866, 66, "4 OBJECTS TRACKED", 9.5, DIM, anchor="end", ls=2))
    b.append(text(494, 358, "TILT -14°  ·  EPOCH: NOW", 9, MUTE, ls=1.5))

    cx, cy, tilt = 680, 214, -14
    orbits = [
        ("CAMPUSLINK", "ACTIVE", 84, 27, 13, AMBER, -2, True),
        ("M-01", "SHELL", 118, 38, 19, BLUE, -11, False),
        ("M-02", "AGENTS", 154, 50, 26, GREEN, -4, False),
        ("M-03", "COACH", 190, 61, 34, VIOLET, -21, False),
    ]

    b.append(
        f'<circle cx="{cx}" cy="{cy}" r="40" fill="none" stroke="{BLUE}" stroke-width="1">'
        '<animate attributeName="r" from="40" to="100" dur="4s" repeatCount="indefinite"/>'
        '<animate attributeName="stroke-opacity" from="0.5" to="0" dur="4s" repeatCount="indefinite"/></circle>'
    )

    fronts, back_sats, front_sats = [], [], []
    for tag, name, rx, ry, dur, color, phase, station in orbits:
        full, front = ellipse_paths(cx, cy, rx, ry, tilt)
        b.append(f'<path d="{full}" fill="none" stroke="{color}" stroke-opacity=".22" stroke-dasharray="2 5"/>')
        fronts.append(f'<path d="{front}" fill="none" stroke="{color}" stroke-opacity=".32" stroke-dasharray="2 5"/>')
        timing = f'dur="{dur}s" begin="{phase}s" repeatCount="indefinite"'
        motion = f'<animateMotion {timing} path="{full}"/>'
        sat = satellite(tag, name, color, station)
        # the back copy sits under the planet all the time; the front copy only shows on the near half
        back_sats.append(
            f'<g>{motion}<animate attributeName="opacity" values="1;0.5" keyTimes="0;0.5" calcMode="discrete" {timing}/>{sat}</g>'
        )
        front_sats.append(
            f'<g>{motion}<animate attributeName="opacity" values="1;0" keyTimes="0;0.5" calcMode="discrete" {timing}/>{sat}</g>'
        )
    b.extend(back_sats)

    defs.append(
        '<radialGradient id="planet" cx=".36" cy=".32" r=".8">'
        '<stop offset="0" stop-color="#4C72D6"/><stop offset=".45" stop-color="#1D3470"/>'
        '<stop offset="1" stop-color="#060C1A"/></radialGradient>'
        '<radialGradient id="shade" cx=".3" cy=".28" r=".95">'
        '<stop offset=".55" stop-color="#02050C" stop-opacity="0"/>'
        '<stop offset="1" stop-color="#02050C" stop-opacity=".85"/></radialGradient>'
        f'<clipPath id="planetclip"><circle cx="{cx}" cy="{cy}" r="40"/></clipPath>'
    )
    bands = []
    for rep in (0, 120):
        for (ox, oy, erx, ery) in [(-50, -18, 22, 6), (-12, -4, 30, 5), (28, 12, 18, 7), (-30, 20, 26, 4), (40, -22, 14, 5)]:
            bands.append(f'<ellipse cx="{cx + ox + rep}" cy="{cy + oy}" rx="{erx}" ry="{ery}" fill="#A9C2FF" opacity=".09"/>')
    b.append(f'<circle cx="{cx}" cy="{cy}" r="40" fill="url(#planet)"/>')
    b.append(
        '<g clip-path="url(#planetclip)"><g>'
        '<animateTransform attributeName="transform" type="translate" from="0 0" to="-120 0" dur="24s" repeatCount="indefinite"/>'
        + "".join(bands) + "</g></g>"
    )
    b.append(f'<circle cx="{cx}" cy="{cy}" r="40" fill="url(#shade)"/>')
    b.append(
        f'<circle cx="{cx}" cy="{cy}" r="42" fill="none" stroke="{BLUE}" stroke-opacity=".35" stroke-width="2" filter="url(#glow)"/>'
    )
    b.extend(fronts)
    b.extend(front_sats)

    # telemetry ticker
    b.append(f'<rect y="376" width="{W}" height="44" fill="{PANEL}"/><line x1="0" y1="376" x2="{W}" y2="376" stroke="{EDGE}"/>')
    segs = [
        ("STATUS", "NOMINAL", GREEN),
        ("ACTIVE MISSION", "CAMPUSLINK", AMBER),
        ("PAYLOAD", "FLUTTER · DART · BLOC · C++ · PYTHON", TEXT),
        ("LAST DEPLOY", "MULTI-AGENT RESEARCH ASSISTANT", GREEN),
        ("FRONTEND CREW", "1", TEXT),
        ("LAUNCH WINDOW", "OPEN", BLUE),
    ]
    one, n = "", 0
    for label, val, color in segs:
        sep = "     ///     "
        one += tspan(label + ": ", DIM) + tspan(val, color) + tspan(sep, FAINT)
        n += len(label) + 2 + len(val) + len(sep)
    L = round(n * 7.0, 1)
    b.append(
        '<g><animateTransform attributeName="transform" type="translate" from="0 0" '
        f'to="-{L} 0" dur="{L / 30:.1f}s" repeatCount="indefinite"/>'
        + text(24, 403, one + one, 11.5, TEXT, 500, raw=True, extra=f'textLength="{2 * L}" lengthAdjust="spacing"')
        + "</g>"
    )
    defs.append(
        f'<linearGradient id="fadeL"><stop offset="0" stop-color="{PANEL}"/><stop offset="1" stop-color="{PANEL}" stop-opacity="0"/></linearGradient>'
        f'<linearGradient id="fadeR"><stop offset="0" stop-color="{PANEL}" stop-opacity="0"/><stop offset="1" stop-color="{PANEL}"/></linearGradient>'
    )
    b.append('<rect x="0" y="377" width="70" height="43" fill="url(#fadeL)"/>')
    b.append(f'<rect x="{W - 70}" y="377" width="70" height="43" fill="url(#fadeR)"/>')

    return svg(
        W, H,
        "Gaurav. Software engineer, Flutter developer.",
        "Animated mission-control console. A boot log comes online for callsign Gaurav: station CampusLink "
        "active, frontend crew of one, cleared to ship. An orbital view tracks CampusLink and three launched "
        "missions: a Unix shell, a multi-agent research assistant and an AI fitness coach. A telemetry ticker "
        "lists the payload: Flutter, Dart, BLoC, C++, Python.",
        "\n".join(b), "\n".join(defs),
    )


# ---------------------------------------------------------------- section rules


def rule(num, title, sub):
    W, H = 900, 56
    x1 = 70 + len(title) * 10.8 + 18
    x2 = 880 - len(sub) * 6.7 - 18
    b = [
        text(22, 33, num, 13, AMBER, 700, ls=1),
        text(46, 33, "//", 13, FAINT, 700),
        text(70, 33, title, 13, TEXT, 700, ls=3),
        text(880, 33, sub, 11, DIM, anchor="end"),
        f'<line x1="{x1:.0f}" y1="28" x2="{x2:.0f}" y2="28" stroke="{FAINT}"/>',
    ]
    for x in range(int(x1), int(x2), 24):
        b.append(f'<line x1="{x}" y1="25" x2="{x}" y2="31" stroke="{FAINT}"/>')
    b.append(
        f'<circle cx="{x1:.0f}" cy="28" r="2.6" fill="{BLUE}" filter="url(#glow)">'
        f'<animate attributeName="cx" from="{x1:.0f}" to="{x2:.0f}" dur="3.2s" repeatCount="indefinite"/>'
        '<animate attributeName="opacity" values="0;1;1;0" keyTimes="0;0.1;0.85;1" dur="3.2s" repeatCount="indefinite"/></circle>'
    )
    return svg(W, H, f"{num} {title}", sub, "\n".join(b), GLOW)


# ---------------------------------------------------------------- flight systems


def flight():
    W, H, T, B = 900, 340, 7, 1.8
    defs = [GLOW, f'<pattern id="grid" width="20" height="20" patternUnits="userSpaceOnUse"><circle cx="1" cy="1" r=".8" fill="{EDGE}"/></pattern>']
    for name, c in [("amber", AMBER), ("blue", BLUE), ("green", GREEN)]:
        defs.append(
            f'<marker id="m{name}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
            f'<path d="M0,0 L10,5 L0,10 z" fill="{c}" fill-opacity=".7"/></marker>'
        )
    b = [f'<rect width="{W}" height="{H}" fill="url(#grid)"/>']
    b.append(text(30, 34, "SCHEMATIC  //  FLUTTER APP, BLOC PATTERN", 10, DIM, ls=2))
    b.append(text(870, 34, "one direction. no surprises.", 11, TEXT, anchor="end"))
    b.append(f'<line x1="30" y1="50" x2="870" y2="50" stroke="{EDGE}"/>')

    def node(x, y, w, h, title, sub, note, color, delay, small=False):
        ts, ss = (11, 9.5) if small else (14, 11)
        ty, sy = (y + 21, y + 37) if small else (y + 32, y + 52)
        inner = (
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" fill="{PANEL}" stroke="{EDGE}"/>'
            f'<rect x="{x}" y="{y + 10}" width="2.5" height="{h - 20}" fill="{color}"/>'
            + text(x + 16, ty, title, ts, TEXT, 700, ls=2)
            + text(x + 16, sy, sub, ss, DIM)
            + (text(x + 16, y + 70, note, 10, MUTE) if note else "")
        )
        return (
            f'<g opacity="0"><animate attributeName="opacity" from="0" to="1" dur=".5s" begin="{delay}s" fill="freeze"/>{inner}</g>'
        )

    def flash(x, y, w, h, color, a, z):
        return (
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" fill="{color}" fill-opacity=".07" '
            f'stroke="{color}" stroke-width="1.5" opacity="0">'
            f'<animate attributeName="opacity" values="0;0;1;0;0" keyTimes="0;{a};{a + 0.01:.2f};{z};1" '
            f'dur="{T}s" begin="{B}s" repeatCount="indefinite"/></rect>'
        )

    def packet(path, color, a, z, reverse=False):
        kp = "1;1;0;0" if reverse else "0;0;1;1"
        timing = f'dur="{T}s" begin="{B}s" repeatCount="indefinite"'
        return (
            f'<g opacity="0"><animateMotion path="{path}" {timing} calcMode="linear" keyPoints="{kp}" keyTimes="0;{a};{z};1"/>'
            f'<animate attributeName="opacity" values="0;1;0" keyTimes="0;{a};{z}" calcMode="discrete" {timing}/>'
            f'<circle r="7" fill="{color}" opacity=".2"/><circle r="3.2" fill="{color}" filter="url(#glow)"/></g>'
        )

    ui, bloc, repo = (40, 110, 200, 84), (350, 110, 200, 84), (660, 110, 200, 84)
    api, cache = (620, 252, 110, 48), (750, 252, 110, 48)

    e1 = "M240,132 L350,132"
    e2 = "M350,172 L240,172"
    e3 = "M550,132 L660,132"
    e4 = "M660,172 L550,172"
    e5 = "M720,194 C720,224 675,222 675,252"
    e6 = "M800,194 C800,224 805,222 805,252"

    edges = [
        (e1, AMBER, "amber", "add(Event)", 295, 122, False),
        (e2, GREEN, "green", "emit(State)", 295, 190, False),
        (e3, BLUE, "blue", "fetch()", 605, 122, False),
        (e4, BLUE, "blue", "data", 605, 190, False),
        (e5, BLUE, "blue", "", 0, 0, True),
        (e6, BLUE, "blue", "", 0, 0, True),
    ]
    eg = []
    for path, color, m, label, lx, ly, both in edges:
        start = f' marker-start="url(#m{m})"' if both else ""
        eg.append(f'<path d="{path}" fill="none" stroke="{color}" stroke-opacity=".45" stroke-width="1.4" marker-end="url(#m{m})"{start}/>')
        if label:
            eg.append(text(lx, ly, label, 10.5, color, anchor="middle"))
    b.append(
        '<g opacity="0"><animate attributeName="opacity" from="0" to="1" dur=".6s" begin="1.1s" fill="freeze"/>'
        + "".join(eg) + "</g>"
    )

    b.append(node(*ui, "UI", "widgets · screens", "BlocBuilder / BlocListener", AMBER, 0.2))
    b.append(node(*bloc, "BLOC", "events in. states out.", "Stream<State>", VIOLET, 0.45))
    b.append(node(*repo, "REPOSITORY", "one source of truth", "hides where data lives", BLUE, 0.7))
    b.append(node(*api, "REMOTE API", "REST / JSON", "", BLUE, 0.9, small=True))
    b.append(node(*cache, "LOCAL CACHE", "offline reads", "", BLUE, 0.95, small=True))

    # the loop: tap, event, fetch, fan out, come back, emit state, rebuild
    b.append(
        f'<circle cx="222" cy="152" r="2" fill="none" stroke="{AMBER}" stroke-width="1.5" opacity="0">'
        f'<animate attributeName="r" values="2;2;14;14" keyTimes="0;0.01;0.08;1" dur="{T}s" begin="{B}s" repeatCount="indefinite"/>'
        f'<animate attributeName="opacity" values="0;0;1;0;0" keyTimes="0;0.01;0.02;0.08;1" dur="{T}s" begin="{B}s" repeatCount="indefinite"/></circle>'
    )
    b.append(packet(e1, AMBER, 0.03, 0.15))
    b.append(flash(*bloc, VIOLET, 0.15, 0.24))
    b.append(packet(e3, BLUE, 0.17, 0.28))
    b.append(flash(*repo, BLUE, 0.28, 0.36))
    b.append(packet(e5, BLUE, 0.29, 0.37))
    b.append(packet(e6, BLUE, 0.29, 0.37))
    b.append(flash(*api, BLUE, 0.37, 0.43))
    b.append(flash(*cache, BLUE, 0.37, 0.43))
    b.append(packet(e5, BLUE, 0.40, 0.48, reverse=True))
    b.append(packet(e6, BLUE, 0.40, 0.48, reverse=True))
    b.append(packet(e4, BLUE, 0.49, 0.60))
    b.append(flash(*bloc, VIOLET, 0.60, 0.68))
    b.append(packet(e2, GREEN, 0.62, 0.74))
    b.append(flash(*ui, GREEN, 0.74, 0.86))
    b.append(
        text(140, 100, "rebuild()", 10.5, GREEN, 700, anchor="middle", extra='opacity="0"').replace(
            "</text>",
            f'<animate attributeName="opacity" values="0;1;0" keyTimes="0;0.74;0.9" calcMode="discrete" '
            f'dur="{T}s" begin="{B}s" repeatCount="indefinite"/></text>')
    )

    # legend
    for i, (label, color) in enumerate([("event", AMBER), ("data", BLUE), ("state", GREEN)]):
        y = 244 + i * 22
        b.append(f'<circle cx="46" cy="{y - 4}" r="3.2" fill="{color}" filter="url(#glow)"/>')
        b.append(text(60, y, label, 10.5, DIM))

    b.append(text(450, 326, "the ui only reads state. only the bloc writes it. that's the whole trick.", 10.5, MUTE, anchor="middle"))

    return svg(
        W, H,
        "Flight systems: how I wire a Flutter app",
        "Animated schematic of a Flutter app using the BLoC pattern. A tap in the UI sends an event to the "
        "BLoC, the BLoC fetches from a repository, the repository reads from a remote API and a local cache, "
        "data flows back, the BLoC emits a new state and the UI rebuilds.",
        "\n".join(b), "\n".join(defs),
    )


# ---------------------------------------------------------------- payload


def payload():
    W, H = 900, 232
    defs = [
        GLOW,
        f'<linearGradient id="beam" x1="0" x2="1"><stop offset="0" stop-color="{BLUE}" stop-opacity="0"/>'
        f'<stop offset=".5" stop-color="{BLUE}" stop-opacity=".35"/><stop offset="1" stop-color="{BLUE}" stop-opacity="0"/></linearGradient>',
    ]
    b = [
        text(30, 32, "PAYLOAD BAY  //  5 MODULES", 10, DIM, ls=2),
        text(870, 32, tspan("MASS: ", DIM) + tspan("LOW", TEXT) + tspan("   ·   STATUS: ", DIM) + tspan("DOCKED", GREEN),
             10, TEXT, anchor="end", ls=2, raw=True),
        f'<rect x="30" y="48" width="840" height="158" rx="10" fill="{PANEL}" stroke="{EDGE}"/>',
        f'<line x1="46" y1="60" x2="854" y2="60" stroke="{FAINT}" stroke-dasharray="3 6"/>',
        f'<line x1="46" y1="194" x2="854" y2="194" stroke="{FAINT}" stroke-dasharray="3 6"/>',
    ]
    mods = [
        ("MOD-01", "FLUTTER", "every screen I ship", "PRIMARY", BLUE, 208),
        ("MOD-02", "DART", "runs the primary", "ONLINE", CYAN, 138),
        ("MOD-03", "BLOC", "state, predictable", "ONLINE", VIOLET, 138),
        ("MOD-04", "C++", "systems. the shell", "ONLINE", AMBER, 138),
        ("MOD-05", "PYTHON", "agents and ai", "ONLINE", GREEN, 138),
    ]
    x = 46
    for i, (mid, name, role, status, color, w) in enumerate(mods):
        t0 = 0.3 + i * 0.25
        y = 72
        inner = (
            f'<rect x="{x}" y="{y}" width="{w}" height="110" rx="6" fill="{BG}" stroke="{EDGE}"/>'
            f'<rect x="{x}" y="{y}" width="{w}" height="2" fill="{color}"/>'
            + text(x + 12, y + 20, mid, 9, MUTE, ls=1.5)
            + text(x + 12, y + 52, name, 18, TEXT, 700, ls=2)
            + text(x + 12, y + 72, role, 10, DIM)
            + f'<circle cx="{x + 16}" cy="{y + 94}" r="3" fill="{color}" filter="url(#glow)">'
            f'<animate attributeName="opacity" values="1;0.35;1" dur="{2.2 + i * 0.35:.2f}s" begin="{t0 + 0.5:.2f}s" repeatCount="indefinite"/></circle>'
            + text(x + 26, y + 97, status, 9, color, 700, ls=1.5)
        )
        b.append(
            f'<g opacity="0">'
            f'<animateTransform attributeName="transform" type="translate" values="0 -26;0 0" dur=".55s" begin="{t0:.2f}s" '
            'calcMode="spline" keyTimes="0;1" keySplines=".2 .8 .2 1" fill="freeze"/>'
            f'<animate attributeName="opacity" from="0" to="1" dur=".35s" begin="{t0:.2f}s" fill="freeze"/>'
            f"{inner}</g>"
        )
        x += w + 12
    b.append(
        '<rect x="0" y="62" width="60" height="130" fill="url(#beam)" opacity="0">'
        '<animate attributeName="x" values="30;810" dur="4s" begin="2s" repeatCount="indefinite"/>'
        '<animate attributeName="opacity" values="0;1;1;0" keyTimes="0;0.1;0.9;1" dur="4s" begin="2s" repeatCount="indefinite"/></rect>'
    )
    return svg(
        W, H,
        "Payload: Flutter, Dart, BLoC, C++, Python",
        "A payload bay with five modules docking one after another. Flutter is the primary module, every screen "
        "I ship. Dart runs it. BLoC keeps state predictable. C++ for systems work like the shell. Python for "
        "agents and AI.",
        "\n".join(b), "\n".join(defs),
    )


# ---------------------------------------------------------------- footer


def footer():
    W, H, P, A, Y = 900, 140, 60, 12, 46
    xs = list(range(0, W + P + 1, 5))
    wave = "M" + " L".join(f"{x},{Y + A * math.sin(2 * math.pi * x / P):.2f}" for x in xs)
    flat = "M" + " L".join(f"{x},{Y}" for x in xs)
    defs = [
        # userSpaceOnUse so the glow survives the flat line, whose bounding box has zero height
        f'<filter id="glowline" filterUnits="userSpaceOnUse" x="0" y="0" width="{W + P}" height="{H}">'
        '<feGaussianBlur stdDeviation="2.2" result="b"/>'
        '<feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>',
        '<linearGradient id="edge" x1="0" x2="1"><stop offset="0" stop-color="#000"/><stop offset=".2" stop-color="#fff"/>'
        '<stop offset=".8" stop-color="#fff"/><stop offset="1" stop-color="#000"/></linearGradient>',
        f'<mask id="fade" maskUnits="userSpaceOnUse" x="0" y="0" width="{W}" height="{H}"><rect width="{W}" height="{H}" fill="url(#edge)"/></mask>',
    ]
    cycle = 'dur="9s" repeatCount="indefinite"'
    b = [
        f'<g mask="url(#fade)"><g>'
        f'<animateTransform attributeName="transform" type="translate" from="0 0" to="-{P} 0" dur="1.1s" repeatCount="indefinite"/>'
        f'<path d="{wave}" fill="none" stroke="{GREEN}" stroke-width="1.6" filter="url(#glowline)">'
        f'<animate attributeName="d" values="{wave};{wave};{flat};{flat};{wave};{wave}" keyTimes="0;0.52;0.58;0.84;0.9;1" {cycle}/>'
        f'<animate attributeName="stroke" values="{GREEN};{AMBER};{GREEN}" keyTimes="0;0.56;0.88" calcMode="discrete" {cycle}/>'
        "</path></g></g>",
        text(450, 92, "END OF TRANSMISSION", 12, TEXT, 700, anchor="middle", ls=5),
        text(450, 114, "SIGNAL ACQUIRED  ·  GAURAV STANDING BY", 10, GREEN, anchor="middle", ls=2).replace(
            "</text>", f'<animate attributeName="opacity" values="1;0;1" keyTimes="0;0.56;0.88" calcMode="discrete" {cycle}/></text>'),
        text(450, 114, "LOSS OF SIGNAL  ·  NEXT PASS SOON", 10, AMBER, anchor="middle", ls=2, extra='opacity="0"').replace(
            "</text>", f'<animate attributeName="opacity" values="0;1;0" keyTimes="0;0.56;0.88" calcMode="discrete" {cycle}/></text>'),
        text(24, 128, "CH 01", 9, MUTE, ls=2),
        text(876, 128, "OVER AND OUT", 9, MUTE, anchor="end", ls=2),
    ]
    return svg(
        W, H,
        "End of transmission",
        "A signal waveform that drops to a flat line, reads loss of signal, then reacquires. Over and out.",
        "\n".join(b), "\n".join(defs),
    )


def main():
    OUT.mkdir(exist_ok=True)
    files = {
        "header.svg": header(),
        "rule-missions.svg": rule("01", "ACTIVE MISSIONS", "what's in orbit"),
        "rule-systems.svg": rule("02", "FLIGHT SYSTEMS", "how I wire a flutter app"),
        "rule-payload.svg": rule("03", "PAYLOAD", "what goes up with me"),
        "rule-comms.svg": rule("04", "COMMS", "channel open"),
        "flight-systems.svg": flight(),
        "payload.svg": payload(),
        "footer.svg": footer(),
    }
    for name, content in files.items():
        (OUT / name).write_text(content, encoding="utf-8")
        print(f"assets/{name}  {len(content) / 1024:.1f} KB")


if __name__ == "__main__":
    main()
