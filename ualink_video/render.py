"""SVG scene renderer. frame_svg(t) -> SVG string for global time t (seconds). 1920x1080 canvas.

Holds the drawing primitives shared by every scene, scenes 1-3, and the frame dispatcher. Scenes 4-21 live in the
scenes_*.py modules and import everything from here.
"""
import json, math, os, sys, textwrap
from xml.sax.saxutils import escape

W, H = 1920, 1080

# Fonts. The layout was tuned on Windows with Segoe UI + Consolas. On other systems (or to use other fonts) override:
#   UALINK_FONT_SANS, UALINK_FONT_MONO   font family names installed on the system
#   UALINK_MONO_ADVANCE                  monospace glyph advance as a fraction of the font size
#                                        (Consolas 0.55, DejaVu Sans Mono / Menlo 0.602, Inconsolata 0.5)
_FONT_DEFAULTS = {"win32": ("Segoe UI", "Consolas", 0.55), "darwin": ("Helvetica Neue", "Menlo", 0.602)}
_fs, _fm, _fa = _FONT_DEFAULTS.get(sys.platform, ("DejaVu Sans", "DejaVu Sans Mono", 0.602))
SANS = os.environ.get("UALINK_FONT_SANS", _fs)
MONO = os.environ.get("UALINK_FONT_MONO", _fm)
MONO_ADV = float(os.environ.get("UALINK_MONO_ADVANCE", _fa))

BG1, BG2 = "#0b1220", "#12203a"
ASPH, ROAD = "#1a2436", "#2a3547"
GOLD, BLUE, GREEN, RED = "#fbbf24", "#38bdf8", "#34d399", "#f87171"
TXT, MUTE = "#e2e8f0", "#94a3b8"
PAPER, INK = "#f8fafc", "#0f172a"
GOLD_INK, BLUE_INK, GREEN_INK, RED_INK = "#b45309", "#1d4ed8", "#047857", "#b91c1c"
CARC = ["#f472b6", "#60a5fa", "#f59e0b", "#a78bfa", "#34d399"]

BAY_CX = [1225 + 170 * i for i in range(4)]
BAY_TOP, BAY_BOT, BAY_CY = 300, 540, 420
LANE_Y = 650
GATE_X = 1100
BOOTH = (990, 795)           # gatekeeper position (tickets leave from here)
DEPOT_PILL = (385, 547)      # where posted permits land (depot)
PARK_TOP = 225

# ------------------------------------------------------------------ helpers
def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def prog(t, start, dur): return clamp((t - start) / dur) if dur > 0 else (1.0 if t >= start else 0.0)
def ease(x): x = clamp(x); return x * x * (3 - 2 * x)
def lerp(a, b, u): return a + (b - a) * u
def fr(t, T0, D0, a, b): return prog(t, T0 + a * D0, (b - a) * D0)   # progress between fractions of a beat
def pop(t, start, dur=0.4):
    u = prog(t, start, dur)
    if u <= 0: return 0.0
    c1 = 1.70158; c3 = c1 + 1
    return 1 + c3 * (u - 1) ** 3 + c1 * (u - 1) ** 2
def pulse(t, period=1.2): return 0.5 + 0.5 * math.sin(2 * math.pi * t / period)

def shade(hexc, f):
    h = hexc.lstrip("#"); r, g, b = [int(h[i:i + 2], 16) for i in (0, 2, 4)]
    return "#%02x%02x%02x" % (int(r * f), int(g * f), int(b * f))

def G(inner, tx=0, ty=0, s=1.0, rot=0.0, op=1.0):
    if op <= 0.01 or not inner: return ""
    return f'<g transform="translate({tx:.1f} {ty:.1f}) rotate({rot:.1f}) scale({s:.3f})" opacity="{op:.3f}">{inner}</g>'

def TX(x, y, s, size=32, fill=TXT, anchor="start", weight=400, fam=SANS, op=1.0, raw=False):
    if op <= 0.01: return ""
    body = s if raw else escape(s)
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-family="{fam}" font-size="{size}" fill="{fill}" '
            f'text-anchor="{anchor}" font-weight="{weight}" opacity="{op:.3f}">{body}</text>')

def spans(parts):
    return "".join(f'<tspan fill="{c}">{escape(s)}</tspan>' for s, c in parts)

def mono_parts(x, y, parts, size, anchor="start", weight=700, op=1.0):
    """Coloured monospace text as separate <text> nodes at exact monospace advances (cairosvg mangles multi-colour tspans)."""
    if op <= 0.01: return ""
    cw = MONO_ADV * size
    x0 = x - (sum(len(p) for p, _ in parts) * cw) / 2 if anchor == "middle" else x
    out = ""
    for p, c in parts:
        lead = len(p) - len(p.lstrip())
        if p.strip():
            out += TX(x0 + lead * cw, y, p.strip(), size, c, "start", weight, MONO, op)
        x0 += len(p) * cw
    return out

def RECT(x, y, w, h, fill="none", rx=0, stroke=None, sw=0, op=1.0, dash=None, sop=1.0):
    if op <= 0.01: return ""
    st = f' stroke="{stroke}" stroke-width="{sw}" stroke-opacity="{sop:.3f}"' if stroke else ""
    da = f' stroke-dasharray="{dash}"' if dash else ""
    return f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{rx}" fill="{fill}" opacity="{op:.3f}"{st}{da}/>'

def PILL(x, y, w, h, s, fill, color, size=28, weight=700, stroke=None, op=1.0, fam=SANS):
    if op <= 0.01: return ""
    return (RECT(x, y, w, h, fill, rx=h / 2, stroke=stroke, sw=3 if stroke else 0, op=op) +
            TX(x + w / 2, y + h / 2 + size * 0.35, s, size, color, "middle", weight, fam, op))

def check(x, y, s, color, op=1.0):
    return (f'<path d="M{x - s * .5:.1f} {y:.1f} L{x - s * .12:.1f} {y + s * .38:.1f} L{x + s * .55:.1f} {y - s * .42:.1f}" '
            f'stroke="{color}" stroke-width="{s * .2:.1f}" fill="none" stroke-linecap="round" stroke-linejoin="round" opacity="{op:.3f}"/>')

def cross(x, y, s, color, op=1.0):
    a = s * .45
    return (f'<path d="M{x - a:.1f} {y - a:.1f} L{x + a:.1f} {y + a:.1f} M{x + a:.1f} {y - a:.1f} L{x - a:.1f} {y + a:.1f}" '
            f'stroke="{color}" stroke-width="{s * .2:.1f}" fill="none" stroke-linecap="round" opacity="{op:.3f}"/>')

def bubble(x, y, w, h, s, tail_x, tail_y, op=1.0, size=30):
    if op <= 0.01: return ""
    return (f'<g opacity="{op:.3f}"><rect x="{x}" y="{y}" width="{w}" height="{h}" rx="18" fill="#f8fafc"/>'
            f'<polygon points="{tail_x - 14},{y + h - 2} {tail_x + 14},{y + h - 2} {tail_x},{tail_y}" fill="#f8fafc"/>'
            f'{TX(x + w / 2, y + h / 2 + size * .35, s, size, INK, "middle", 600)}</g>')

# ------------------------------------------------------------------ objects
def car(x, y, rot=0.0, color="#60a5fa", s=1.0, op=1.0, permit=False):
    if op <= 0.01: return ""
    roof = shade(color, .78)
    p = (f'<rect x="-64" y="-31" width="128" height="62" rx="16" fill="{color}"/>'
         '<rect x="-46" y="-39" width="26" height="10" rx="3" fill="#0b1220"/>'
         '<rect x="-46" y="29" width="26" height="10" rx="3" fill="#0b1220"/>'
         '<rect x="26" y="-39" width="26" height="10" rx="3" fill="#0b1220"/>'
         '<rect x="26" y="29" width="26" height="10" rx="3" fill="#0b1220"/>'
         f'<rect x="-30" y="-24" width="54" height="48" rx="10" fill="{roof}"/>'
         '<rect x="20" y="-22" width="16" height="44" rx="5" fill="#bae6fd" opacity=".9"/>'
         '<rect x="-42" y="-20" width="9" height="40" rx="4" fill="#93c5fd" opacity=".7"/>'
         '<rect x="56" y="-25" width="8" height="12" rx="3" fill="#fde68a"/>'
         '<rect x="56" y="13" width="8" height="12" rx="3" fill="#fde68a"/>'
         '<rect x="-64" y="-25" width="6" height="12" rx="2" fill="#ef4444"/>'
         '<rect x="-64" y="13" width="6" height="12" rx="2" fill="#ef4444"/>')
    if permit:
        p += (f'<rect x="-24" y="-16" width="40" height="32" rx="5" fill="{GOLD}" stroke="#78350f" stroke-width="2"/>'
              '<line x1="-10" y1="-11" x2="-10" y2="11" stroke="#b45309" stroke-width="2" stroke-dasharray="4 3"/>'
              '<rect x="0" y="-8" width="10" height="16" rx="2" fill="#b45309"/>')
    return G(p, x, y, s, rot, op)

def ticket_svg():
    return (f'<rect x="-34" y="-20" width="68" height="40" rx="7" fill="{GOLD}" stroke="#92400e" stroke-width="2.5"/>'
            '<rect x="-29" y="-15" width="58" height="30" rx="4" fill="none" stroke="#b45309" stroke-width="2" stroke-dasharray="5 4"/>'
            f'<text x="0" y="9" font-family="{SANS}" font-size="26" font-weight="700" fill="#78350f" text-anchor="middle">P</text>')

def ticket(x, y, s=1.0, rot=0.0, op=1.0):
    return G(ticket_svg(), x, y, s, rot, op)

def bez(u, p0, c, p1):
    x = (1 - u) ** 2 * p0[0] + 2 * (1 - u) * u * c[0] + u ** 2 * p1[0]
    y = (1 - u) ** 2 * p0[1] + 2 * (1 - u) * u * c[1] + u ** 2 * p1[1]
    return x, y

def fly(t, start, dur, p0, p1, ctrl=None, s0=1.0, s1=0.75):
    """A permit ticket flying p0 -> p1; '' outside the flight window."""
    u = prog(t, start, dur)
    if u <= 0 or u >= 1: return ""
    e = ease(u)
    c = ctrl or ((p0[0] + p1[0]) / 2, min(p0[1], p1[1]) - 120)
    x, y = bez(e, p0, c, p1)
    return ticket(x, y, lerp(s0, s1, e), math.sin(e * math.pi) * 12, 1.0)

def depot_pill(n, op=1.0, bump=0.0):
    if op <= 0.01: return ""
    x, y = DEPOT_PILL[0] - 55, DEPOT_PILL[1] - 26
    s = 1 + 0.18 * bump
    inner = (RECT(-55, -26, 110, 52, "#1e293b", rx=26, stroke=GOLD, sw=3) +
             ticket(-24, 0, .48) + TX(8, 11, f"×{n}", 32, GOLD, "start", 700))
    return G(inner, DEPOT_PILL[0], DEPOT_PILL[1], s, 0, op)

# ------------------------------------------------------------------ world
def background():
    return (f'<defs><linearGradient id="bg" x1="0" y1="0" x2="0" y2="1">'
            f'<stop offset="0" stop-color="{BG1}"/><stop offset="1" stop-color="{BG2}"/></linearGradient></defs>'
            f'<rect width="{W}" height="{H}" fill="url(#bg)"/>')

def road(op=1.0):
    if op <= 0.01: return ""
    dash = "".join(f'<rect x="{x}" y="{LANE_Y - 3}" width="46" height="6" rx="3" fill="#fff" opacity=".28"/>' for x in range(20, 1080, 90))
    return G(f'<rect x="0" y="580" width="{GATE_X + 4}" height="140" fill="{ROAD}"/>'
             f'<rect x="0" y="574" width="{GATE_X + 4}" height="6" fill="#3b485e"/><rect x="0" y="720" width="{GATE_X + 4}" height="6" fill="#3b485e"/>'
             + dash, op=op)

def depot(op=1.0, dx=0.0):
    if op <= 0.01: return ""
    inner = (f'<rect x="20" y="490" width="280" height="86" fill="#475569"/>'
             f'<polygon points="10,490 160,440 310,490" fill="#64748b"/>'
             f'<rect x="105" y="518" width="110" height="58" rx="6" fill="#0f172a"/>'
             + "".join(f'<line x1="105" y1="{y}" x2="215" y2="{y}" stroke="#1e293b" stroke-width="3"/>' for y in (532, 546, 560))
             + TX(160, 480, "DEPOT", 30, "#f1f5f9", "middle", 700))
    return G(inner, dx, 0, 1, 0, op)

def booth(op=1.0, glow=0.0, label_op=1.0):
    if op <= 0.01: return ""
    o = ""
    if glow > 0.01:
        o += RECT(910, 736, 160, 118, "none", rx=16, stroke=GOLD, sw=5, op=glow)
    o += (RECT(930, 754, 120, 86, "#475569", rx=10) +
          RECT(916, 744, 148, 22, "#ef4444", rx=8) +
          RECT(946, 782, 88, 44, "#0ea5e9", rx=6, op=.35) +
          f'<circle cx="990" cy="800" r="16" fill="#fcd9b6"/>'
          f'<path d="M973 796 A17 17 0 0 1 1007 796 Z" fill="#1e40af"/><rect x="972" y="794" width="36" height="6" rx="3" fill="#1e3a8a"/>'
          f'<rect x="972" y="814" width="36" height="22" rx="9" fill="#2563eb"/>')
    o += TX(908, 806, "GATEKEEPER", 22, MUTE, "end", 600, op=label_op)
    return G(o, op=op)

def barrier(open_u=0.0, op=1.0):
    """arm pivots at (GATE_X,725); closed = pointing up across the road, open = pointing right along the lane edge."""
    ang = 90 * ease(open_u)
    segs = "".join(f'<rect x="-8" y="{-150 + 25 * i}" width="16" height="25" fill="{"#ef4444" if i % 2 == 0 else "#f8fafc"}"/>' for i in range(6))
    arm = f'<g transform="translate({GATE_X} 725) rotate({ang:.1f})">{segs}</g>'
    post = f'<circle cx="{GATE_X}" cy="725" r="15" fill="#64748b" stroke="#334155" stroke-width="3"/>'
    return G(arm + post, op=op)

def bay(i, num=0.0, car_color=None, car_op=1.0, res=0.0, res_pop=1.0, tag=None, tag_op=1.0, glow=None, glow_op=1.0):
    cx = BAY_CX[i]; x0, x1 = cx - 75, cx + 75
    o = [RECT(x0, BAY_TOP, 150, 240, "#243044", rx=6)]
    if res > 0.01:
        o.append(RECT(x0, BAY_TOP, 150, 240, GOLD, rx=6, op=.12 * res))
        o.append(RECT(x0 + 8, BAY_TOP + 8, 134, 224, "none", rx=6, stroke=GOLD, sw=4, op=res, dash="16 10"))
        o.append(ticket(cx, BAY_CY, 1.05 * max(res_pop, 0.01), 0, res))
    if glow:
        o.append(RECT(x0 + 4, BAY_TOP + 4, 142, 232, "none", rx=6, stroke=glow, sw=6, op=glow_op))
    o.append(f'<path d="M{x0} {BAY_BOT} V{BAY_TOP} H{x1} V{BAY_BOT}" stroke="#cbd5e1" stroke-width="4" fill="none" stroke-opacity=".75" stroke-linejoin="round"/>')
    if num > 0.01:
        o.append(G(TX(0, 0, str(i + 1), 42, "#cbd5e1", "middle", 700), cx, 342, max(num, 0.01), 0, min(num, 1) * .8))
    if car_color:
        o.append(car(cx, BAY_CY, -90, car_color, 1.0, car_op))
    if tag:
        text, colr = tag
        o.append(PILL(cx - 66, 494, 132, 34, text, colr, "#0f172a", 19, 800, op=tag_op))
    return "".join(o)

def park_frame(op=1.0, ty=0.0):
    return G(RECT(GATE_X, PARK_TOP, 780, 545, ASPH, rx=26, stroke="#334155", sw=4), 0, ty, 1, 0, op)

def caption(text, op=1.0):
    if op <= 0.01 or not text: return ""
    n_lines = -(-len(text) // 84)
    lines = textwrap.wrap(text, -(-len(text) // n_lines) + 8)
    w = min(1760, max(len(l) for l in lines) * 17.5 + 70)
    h = 26 + 44 * len(lines)
    y0 = 1056 - h
    o = RECT(960 - w / 2, y0, w, h, "#020617", rx=16, op=.72)
    for k, l in enumerate(lines):
        o += TX(960, y0 + 44 + 44 * k - 6, l, 32, "#f1f5f9", "middle", 500)
    return G(o, op=op)

def chip(text, op=1.0):
    w = len(text) * 13.2 + 40
    return PILL(60, 18, w, 38, text, "#1e293b", MUTE, 20, 700, stroke="#334155", op=op)

def code_line(text, y, op=1.0, w=None):
    w = w or len(text) * 15.6 + 60
    return RECT(960 - w / 2, y, w, 46, "#020617", rx=10, stroke="#334155", sw=2, op=op * .9) + TX(960, y + 32, text, 26, "#7dd3fc", "middle", 400, MONO, op)

# ------------------------------------------------------------------ clipboard (scene 2)
def clip_frame(ty=0.0, title="GATEKEEPER'S CLIPBOARD", h=310, mono=False):
    o = RECT(60, 90, 860, h, PAPER, rx=26, stroke="#cbd5e1", sw=3)
    o += RECT(400, 62, 180, 56, "#475569", rx=14) + RECT(450, 76, 80, 18, "#1e293b", rx=9)
    o += TX(490, 160, title, 26 if mono else 27, "#475569", "middle", 700, MONO if mono else SANS)
    return G(o, 0, ty)

def clip_row(idx, label, sub, val, color, active=0.0, val_pop=0.0, ty=0.0):
    y = 185 + idx * 110
    fill = "#e2e8f0"
    o = RECT(88, y, 804, 90, fill, rx=14)
    if active > 0.01:
        o += RECT(88, y, 804, 90, color, rx=14, op=.16 * active, stroke=color, sw=5, sop=active)
    o += f'<circle cx="132" cy="{y + 45}" r="22" fill="#334155"/>' + TX(132, y + 54, str(idx + 1), 26, "#fff", "middle", 700)
    if sub:
        o += TX(175, y + 41, label, 29, INK, "start", 700) + TX(175, y + 72, sub, 23, "#64748b", "start", 500)
    else:
        o += TX(175, y + 56, label, 29, INK, "start", 700)
    if val_pop > 0.01:
        o += G(TX(0, 0, val, 76, {GOLD: GOLD_INK, BLUE: BLUE_INK}.get(color, INK), "end", 700), 868, y + 72, val_pop, 0, min(val_pop, 1))
    else:
        o += TX(868, y + 68, "—", 56, "#94a3b8", "end", 700)
    return G(o, 0, ty)

# ================================================================== SCENES
# each scene fn: (t, T, D, L) -> (svg_layers_string, active_beat_index)
def scene_title(t, L, info=None):
    info = info or dict(title="The Parking Permit Bug", sub="UPLI credit accounting, explained with a car park", tag="Part 1  ·  The Car Park")
    a = ease(prog(t, 0.2, 0.8)); b = ease(prog(t, 0.9, 0.8)); c = ease(prog(t, 1.5, 0.8))
    o = G(TX(960, 470, info["title"], 104, "#f8fafc", "middle", 700), 0, (1 - a) * 30, 1, 0, a)
    o += G(TX(960, 555, info["sub"], 42, GOLD, "middle", 500), 0, (1 - b) * 24, 1, 0, b)
    o += TX(960, 640, info["tag"], 30, MUTE, "middle", 600, op=c)
    # little icon row
    ic = car(860, 760, 0, CARC[1], .8, c) + ticket(960, 760, 1.0, 0, c) + car(1060, 760, 0, CARC[0], .8, c)
    return background() + o + ic

def _queue_cars(t, T, D):
    """static-ish queue cars 1..3 (car 0 handled separately). appear during scene-1 beat 1."""
    xs = [660, 480, 300]
    o = ""
    for k, x in enumerate(xs):
        u = ease(prog(t, T[1] + 0.9 + 0.35 * k, 0.8))
        o += car(x - (1 - u) * 260, LANE_Y, 0, CARC[(k + 1) % 5], 1.0, u)
    return o

def scene1(t, T, D, L):
    o = [background()]
    o.append(road(ease(prog(t, 0.1, 0.6))))
    # --- park (beat 0)
    a_park = ease(prog(t, T[0], 0.8))
    o.append(park_frame(a_park, (1 - a_park) * 50))
    o.append(booth(ease(prog(t, T[0] + 0.5, 0.7))))
    # bay content
    fill_u = ease(fr(t, T[2], D[2], 0.0, 0.12))
    out_u = ease(fr(t, T[2], D[2], 0.9, 1.0))
    car_alpha = fill_u * (1 - out_u)
    bays = []
    for i in range(4):
        num = pop(t, T[0] + D[0] * (0.42 + 0.13 * i), 0.4)
        parked = (i == 0 and t >= T[4] + D[4] * 0.9)
        cc = None; co = 1.0
        if parked:
            cc, co = CARC[0], 1.0
        elif car_alpha > 0.01 and T[2] <= t <= T[3]:
            cc, co = ["#64748b", "#94a3b8", "#78716c", "#a1a1aa"][i], car_alpha
        bays.append(G(bay(i, num * a_park, cc, co), 0, (1 - a_park) * 50, 1, 0, max(a_park, 0.01) if a_park > 0.01 else 0))
    o += bays
    # 'EXACTLY 4 BAYS' pill
    pill_a = pop(t, T[0] + D[0] * 0.30, 0.5) * (1 - ease(prog(t, T[5] - 0.1, 0.4)))
    if pill_a > 0.01:
        o.append(G(PILL(-200, -32, 400, 64, "EXACTLY 4 BAYS", "#1e293b", GOLD, 34, 800, stroke=GOLD), 1490, 175, pill_a, 0, min(pill_a, 1)))
    # --- depot + doubt (beat 1)
    dep_a = ease(prog(t, T[1], 0.7))
    o.append(depot(dep_a, -(1 - dep_a) * 220))
    # sight line + question
    sl = ease(fr(t, T[1], D[1], 0.35, 0.7)) * (1 - ease(prog(t, T[3] - 0.1, 0.4)))
    if sl > 0.01:
        o.append(f'<line x1="315" y1="505" x2="{315 + 770 * sl:.0f}" y2="505" stroke="{MUTE}" stroke-width="4" stroke-dasharray="14 10" opacity=".7"/>')
        o.append(cross(700, 505, 40, RED, min(1, sl * 1.4)))
        o.append(TX(700, 465, "can't see the car park", 26, MUTE, "middle", 600, op=min(1, sl * 1.4)))
    q_a = pop(t, T[1] + D[1] * 0.6, 0.5) * (1 - ease(prog(t, T[3] - 0.1, 0.4)))
    if q_a > 0.01:
        o.append(G(bubble(-150, -35, 300, 70, "Is there space?", -100, 55, 1.0, 30), 470, 385, q_a, 0, min(q_a, 1)))
    # queue cars
    o.append(_queue_cars(t, T, D))
    # --- beat 2: lead car turned away
    # car0 pose
    if t < T[4]:
        car0_x = 840
        if t >= T[2]:
            go = ease(fr(t, T[2], D[2], 0.14, 0.42)); back = ease(fr(t, T[2], D[2], 0.62, 0.9))
            car0_x = lerp(840, 1010, go) - (1010 - 840) * back
        pose = (car0_x, LANE_Y, 0.0)
        has_permit = False
    else:
        u1 = ease(fr(t, T[4], D[4], 0.18, 0.45))
        u2 = ease(fr(t, T[4], D[4], 0.55, 0.75))
        u3 = ease(fr(t, T[4], D[4], 0.75, 0.92))
        x = lerp(840, 1010, u1)
        x = lerp(x, BAY_CX[0], u2)
        y = lerp(LANE_Y, BAY_CY, u3)
        rot = -90 * u3
        pose = (x, y, rot)
        has_permit = (t < T[4] + D[4] * 0.9) and t >= T[4] + D[4] * 0.10
    car0_alpha = ease(prog(t, T[1] + 0.7, 0.8))
    parked_final = (t >= T[4] + D[4] * 0.9)
    if not parked_final:
        o.append(car(pose[0], pose[1], pose[2], CARC[0], 1.0, car0_alpha, has_permit))
    # NO BAY sign
    nb = pop(t, T[2] + D[2] * 0.42, 0.4) * (1 - ease(fr(t, T[2], D[2], 0.7, 0.8)))
    if nb > 0.01 and T[2] <= t < T[3]:
        o.append(G(PILL(-110, -28, 220, 56, "NO BAY!", RED, "#fff", 32, 800), 1000, 555, nb, 0, min(nb, 1)))
        o.append(cross(1010, LANE_Y, 62, RED, min(nb, 1)))
        # flying-away label
    if T[2] <= t < T[3]:
        ta = ease(fr(t, T[2], D[2], 0.62, 0.72)) * (1 - ease(fr(t, T[2], D[2], 0.9, 1.0)))
        o.append(TX(760, 565, "TURNED AWAY", 36, RED, "middle", 800, op=ta))
    # --- barrier
    if t < T[4]:
        b_open = 0.0
    else:
        b_open = ease(fr(t, T[4], D[4], 0.42, 0.55)) * (1 - ease(fr(t, T[4], D[4], 0.94, 1.0)))
    o.append(barrier(b_open, ease(prog(t, T[0] + 0.5, 0.7))))
    # --- beat 3: permits posted
    gl = 0.0
    if T[3] <= t < T[4]:
        gl = pulse(t, 0.9) * .8 + .2
    if gl > 0: o.append(booth(1.0, gl))   # draws the glow ring over
    land = [T[3] + D[3] * (0.12 + 0.17 * k) + 1.0 for k in range(4)]
    n_posted = sum(1 for k in range(4) if t >= land[k])
    if t >= T[4] + D[4] * 0.10:
        n_posted -= 1
    for k in range(4):
        st = land[k] - 1.0
        o.append(fly(t, st, 1.0, BOOTH, DEPOT_PILL, (700, 900)))
    if any(t >= land[k] for k in range(4)):
        last = max((tt for tt in land if t >= tt), default=0)
        b = max(0.0, 1 - (t - last) / 0.3)
        o.append(depot_pill(n_posted, 1.0, b))
    # permit moving pill -> car0 in beat 4
    if T[4] <= t:
        st = T[4] + D[4] * 0.02
        o.append(fly(t, st, D[4] * 0.16, DEPOT_PILL, (840, LANE_Y - 10), (650, 470), 0.75, 0.6))
    # '1 permit = 1 car'
    pa = pop(t, T[4] + D[4] * 0.14, 0.5) * (1 - ease(prog(t, T[5] - 0.1, 0.4)))
    if pa > 0.01:
        o.append(G(PILL(-190, -32, 380, 64, "1 permit = 1 car", "#1e293b", GOLD, 34, 800, stroke=GOLD), 700, 175, pa, 0, min(pa, 1)))
    # --- beat 5: credits concept
    c_a = ease(fr(t, T[5], D[5], 0.0, 0.1))
    if c_a > 0.01:
        card = (RECT(120, 70, 920, 170, "#0f2744", rx=24, stroke=BLUE, sw=3) +
                TX(580, 128, "CREDIT-BASED FLOW CONTROL", 44, GOLD, "middle", 800) +
                TX(580, 177, "The receiver tells the sender", 32, TXT, "middle", 500) +
                TX(580, 218, "how much room it has — in advance.", 32, TXT, "middle", 500))
        o.append(G(card, 0, (1 - c_a) * -30, 1, 0, c_a))
        # credits path: booth -> depot (booth bottom, along under the label, up into the depot)
        arrow_u = ease(fr(t, T[5], D[5], 0.25, 0.55))
        if arrow_u > 0.01:
            pts = [(990, 842), (990, 870), (160, 870), (160, 600)]
            total = sum(abs(b[0] - a[0]) + abs(b[1] - a[1]) for a, b in zip(pts, pts[1:]))
            left = total * arrow_u; d = f"M{pts[0][0]} {pts[0][1]}"; cur = pts[0]
            for p in pts[1:]:
                seg = abs(p[0] - cur[0]) + abs(p[1] - cur[1])
                if left >= seg: d += f" L{p[0]} {p[1]}"; left -= seg; cur = p
                else:
                    f_ = left / seg; d += f" L{cur[0] + (p[0] - cur[0]) * f_:.0f} {cur[1] + (p[1] - cur[1]) * f_:.0f}"; break
            o.append(f'<path d="{d}" stroke="{GOLD}" stroke-width="6" fill="none" stroke-dasharray="18 12" opacity=".85"/>')
            if arrow_u >= 0.999:
                o.append(f'<polygon points="146,612 174,612 160,584" fill="{GOLD}"/>')
            o.append(TX(560, 856, "credits  (permits)", 28, GOLD, "middle", 700, op=min(1, arrow_u * 1.5)))
        for k, (x, y, w, text, colr) in enumerate([
                (30, 398, 270, "DEPOT = TX NODE", "#a5f3fc"),
                (1330, 172, 440, "CAR PARK = RX BUFFER", "#bfdbfe"),
                (1090, 792, 340, "PERMIT = CREDIT", "#fde68a")]):
            u = pop(t, T[5] + D[5] * (0.55 + 0.1 * k), 0.4)
            o.append(PILL(x, y, w, 40, text, colr, "#0f172a", 22, 800, op=min(u, 1)))
    return "".join(str(x) for x in o)

# ---------------------------------------------------------------- scene 2
def _reserved_bays(t, T, D, res_times, extra_glow=None, tags=None, cars=None):
    out = []
    for i in range(4):
        r = ease(prog(t, res_times[i], 0.5)) if res_times[i] is not None else 0.0
        rp = pop(t, res_times[i], 0.5) if res_times[i] is not None else 0.0
        out.append(bay(i, 0.0, None, 1.0, r, rp, None, 1.0, extra_glow[i][0] if extra_glow and extra_glow[i] else None,
                       extra_glow[i][1] if extra_glow and extra_glow[i] else 1.0))
    return "".join(out)

def scene2(t, T, D, L):
    o = [background(), road(1.0), depot(1.0), booth(1.0), park_frame(1.0), barrier(0.0, 1.0)]
    # clipboard
    a_c = ease(prog(t, T[0], 0.9))
    ty = -(1 - a_c) * 520
    # row highlights
    act = [0.0, 0.0]
    if T[1] <= t < T[3]: act[0] = 1.0
    if T[3] <= t < T[4]: act[1] = 1.0
    act[0] *= 0.6 + 0.4 * pulse(t, 1.0)
    act[1] *= 0.6 + 0.4 * pulse(t, 1.0)
    # bays
    res_times = [T[2] + D[2] * (0.30 + 0.14 * i) for i in range(4)]
    glows = [None] * 4
    if T[3] <= t < T[4]:
        g = 0.35 + 0.65 * pulse(t, 1.0)
        glows = [(BLUE, g)] * 4
    o.append("".join(bay(i, 0.6, None, 1.0,
                         ease(prog(t, res_times[i], 0.5)), pop(t, res_times[i], 0.5), None, 1.0,
                         glows[i][0] if glows[i] else None, glows[i][1] if glows[i] else 1.0) for i in range(4)))
    o.append(clip_frame(ty))
    v1 = pop(t, T[1] + 0.9, 0.5)
    v2 = pop(t, T[3] + D[3] * 0.55, 0.5)
    o.append(clip_row(0, "PERMITS POSTED OUT", "(not yet used)", "4", GOLD, act[0], v1, ty))
    o.append(clip_row(1, "CARS ACTUALLY PARKED", None, "0", BLUE, act[1], v2, ty))
    # permits flying to depot (beat 1)
    land = [T[1] + D[1] * (0.15 + 0.16 * k) + 1.0 for k in range(4)]
    for k in range(4):
        o.append(fly(t, land[k] - 1.0, 1.0, BOOTH, DEPOT_PILL, (700, 900)))
    n = sum(1 for k in range(4) if t >= land[k])
    if n > 0:
        last = max(tt for tt in land if t >= tt)
        o.append(depot_pill(n, 1.0, max(0.0, 1 - (t - last) / 0.3)))
    # golden rule banner
    b_a = pop(t, T[4] + 0.3, 0.5)
    formula_a = ease(fr(t, T[5], D[5], 0.0, 0.2))
    over = ease(fr(t, T[6], D[6], 0.35, 0.5))
    if b_a > 0.01:
        bcol = lerp(0, 1, over)
        stroke = RED if over > 0.5 else GOLD
        banner = RECT(-460, -100, 920, 190, "#1c1608" if over < 0.5 else "#2a0f10", rx=24, stroke=stroke, sw=4)
        banner += PILL(-150, -84, 300, 40, "THE GOLDEN RULE", GOLD, "#0f172a", 24, 800)
        if formula_a > 0.01:
            banner += mono_parts(0, 8, [("PERMITS", GOLD), (" + ", TXT), ("PARKED", BLUE), (" ≤ ", TXT), ("4", GREEN)],
                                 64, "middle", 800, formula_a)
            if over < 0.5:
                s_op = ease(fr(t, T[5], D[5], 0.5, 0.7))
                banner += TX(-40, 68, "4 + 0 = 4", 38, TXT, "middle", 700, op=s_op) + check(75, 56, 30, GREEN, s_op)
            else:
                banner += TX(-40, 68, "5 + 0 = 5  >  4", 38, RED, "middle", 700) + cross(150, 56, 30, RED)
        else:
            banner += TX(0, 30, "must never be violated", 40, MUTE, "middle", 500, op=ease(fr(t, T[4], D[4], 0.6, 0.9)))
        o.append(G(banner, 1420, 125, max(b_a, 0.01), 0, min(b_a, 1)))
    # code footer
    cf = ease(fr(t, T[5], D[5], 0.55, 0.85))
    if cf > 0.01:
        o.append(code_line("remote_request_credit_count + req_in_buffer.size() <= max_buffer_size", 872, cf))
    # 5th permit
    f5 = pop(t, T[6] + D[6] * 0.12, 0.5)
    if f5 > 0.01:
        o.append(ticket(1490, LANE_Y, 1.3 * f5, 0, min(f5, 1)))
        s5 = ease(fr(t, T[6], D[6], 0.3, 0.42))
        o.append(cross(1490, LANE_Y, 80, RED, s5))
        o.append(PILL(1350, 690, 280, 44, "NO BAY FOR IT", RED, "#fff", 26, 800, op=s5) if False else "")
        o.append(TX(1490, 728, "no bay for the 5th permit", 30, RED, "middle", 700, op=s5))
        o.append(TX(1490, 600, "5th claim", 26, GOLD, "middle", 700, op=min(f5, 1)))
    return "".join(str(x) for x in o)

# ---------------------------------------------------------------- scene 3
def scene3(t, T, D, L):
    o = [background(), road(1.0), depot(1.0), booth(1.0), park_frame(1.0), barrier(0.0, 1.0)]
    a_c = ease(prog(t, T[0], 0.9))
    ty = -(1 - a_c) * 560
    # bay tags / states
    land = T[3] + D[3] * 0.15 + 1.1                       # the extra permit lands
    res3 = ease(prog(t, T[3] + D[3] * 0.15 + 0.9, 0.5))
    tags = [None] * 4
    if t >= T[1] + D[1] * 0.35:
        tags[0] = ("PARKED", BLUE)
    if t >= T[2] + D[2] * 0.35:
        tags[1] = tags[2] = ("PROMISED", GOLD)
    left_glow = None
    if T[2] + D[2] * 0.7 <= t < T[3] + D[3] * 0.3:
        left_glow = (GREEN, 0.4 + 0.6 * pulse(t, .8))
    for i in range(4):
        cc = CARC[0] if i == 0 else None
        res = 1.0 if i in (1, 2) else (res3 if i == 3 else 0.0)
        tg = tags[i]
        if i == 3 and t >= T[2] + D[2] * 0.7 and t < T[3] + D[3] * 0.3:
            tg = ("LEFT OVER", GREEN)
        if i == 3 and res3 > 0.5:
            tg = ("PROMISED", GOLD)
        gl = left_glow if i == 3 else None
        o.append(G(bay(i, 0.6, cc, 1.0, res, pop(t, T[3] + D[3] * 0.15 + 0.9, 0.5) if i == 3 else 1.0,
                       tg, 1.0, gl[0] if gl else None, gl[1] if gl else 1.0), op=1.0))
    # brackets under the bays
    br = ease(fr(t, T[1], D[1], 0.55, 0.85))
    if br > 0.01 and t < T[3] + D[3] * 0.3:
        x0, x1 = BAY_CX[1] - 75, BAY_CX[3] + 75
        o.append(f'<path d="M{x0} 552 V566 H{x0 + (x1 - x0) * br:.0f} V552" stroke="{GREEN}" stroke-width="5" fill="none" opacity="{br:.2f}"/>')
        o.append(TX((x0 + x1) / 2, 606, "free space = 3", 32, GREEN, "middle", 700, op=br))
    br2 = ease(fr(t, T[2], D[2], 0.5, 0.8))
    if br2 > 0.01 and t < T[3] + D[3] * 0.3:
        x0, x1 = BAY_CX[1] - 75, BAY_CX[2] + 75
        o.append(f'<path d="M{x0} 288 V274 H{x0 + (x1 - x0) * br2:.0f} V288" stroke="{GOLD}" stroke-width="5" fill="none" opacity="{br2:.2f}"/>')
        o.append(TX((x0 + x1) / 2, 258, "already promised = 2", 28, GOLD, "middle", 700, op=br2))
    # panel
    o.append(clip_frame(ty, "check_and_release_request_credits()", 340, True))
    pa = ease(prog(t, T[0] + 0.6, 0.6))
    hon = 0.0
    if T[4] <= t: hon = 0.5 + 0.5 * pulse(t, 1.0)
    c1 = (RECT(88, 172, 372, 42, "#fef3c7", rx=10, stroke=GOLD_INK if hon > 0 else None, sw=4, sop=hon) +
          TX(274, 202, "permits_already_out = 2", 24, GOLD_INK, "middle", 700, MONO))
    c2 = (RECT(480, 172, 288, 42, "#dbeafe", rx=10, stroke=BLUE_INK if hon > 0 else None, sw=4, sop=hon) +
          TX(624, 202, "cars_parked = 1", 24, BLUE_INK, "middle", 700, MONO))
    o.append(G(c1 + c2, 0, ty, 1, 0, pa))
    f1 = ease(fr(t, T[1], D[1], 0.45, 0.7)); r1 = ease(fr(t, T[1], D[1], 0.75, 0.95))
    f2 = ease(fr(t, T[2], D[2], 0.25, 0.5)); r2 = ease(fr(t, T[2], D[2], 0.6, 0.85))
    dim = 1 - 0.25 * ease(prog(t, T[4], 0.5))
    form1 = mono_parts(100, 268, [("free_space", GREEN_INK), (" = 4 - ", INK), ("cars_parked", BLUE_INK)], 30, "start", 700, f1 * dim)
    res1 = TX(600, 268, "= 4 - 1 = 3", 30, GREEN_INK, "start", 700, MONO, r1 * dim)
    form2 = mono_parts(100, 328, [("new_permits", GREEN_INK), (" = ", INK), ("free_space", GREEN_INK), (" - ", INK),
                                  ("permits_already_out", GOLD_INK)], 30, "start", 700, f2 * dim)
    res2 = TX(100, 370, "= 3 - 2 = 1", 30, GREEN_INK, "start", 700, MONO, r2 * dim)
    p3 = ease(fr(t, T[3], D[3], 0.05, 0.3))
    post = TX(100, 414, "→ post 1 permit", 30, GREEN_INK, "start", 800, MONO, p3 * dim) + \
           TX(430, 414, "(capped at 3 per release message)", 20, "#64748b", "start", 500, SANS, p3 * dim)
    o.append(G(form1 + res1 + form2 + res2 + post, 0, ty))
    # question bubble at booth
    qa = pop(t, T[0] + 0.8, 0.5) * (1 - ease(prog(t, T[1] + 0.5, 0.5)))
    if qa > 0.01:
        o.append(G(bubble(-190, -38, 380, 76, "Post more permits?", 170, 60, 1.0, 30), 820, 690, qa, 0, min(qa, 1)))
    # depot pill: 2 -> 3 when the new permit lands
    fl_start = T[3] + D[3] * 0.15
    o.append(fly(t, fl_start, 1.0, BOOTH, DEPOT_PILL, (700, 900)))
    landed = t >= fl_start + 1.0
    b = max(0.0, 1 - (t - (fl_start + 1.0)) / 0.3) if landed else 0.0
    o.append(depot_pill(3 if landed else 2, ease(prog(t, T[0], 0.6)), b))
    # honesty box (beats 4-5)
    h_a = pop(t, T[4] + 0.4, 0.5)
    if h_a > 0.01:
        rem = ease(prog(t, T[5], 0.5))
        box = RECT(-460, -95, 920, 190, "#1c1608", rx=24, stroke=GOLD, sw=4)
        if rem < 0.5:
            box += TX(0, -10, "Both numbers must be HONEST", 50, TXT, "middle", 800)
            box += TX(0, 52, "at the very moment he does the sum", 32, MUTE, "middle", 500)
        else:
            box += TX(0, -6, "REMEMBER THIS", 62, GOLD, "middle", 800)
            box += TX(0, 54, "It's the whole story.", 36, TXT, "middle", 500)
        o.append(G(box, 1420, 125, max(h_a, 0.01), 0, min(h_a, 1)))
    return "".join(str(x) for x in o)

# ================================================================== timeline / frame
TL = None
TL_PATH = None
def load_timeline(path):
    """Load the timeline JSON written by `python -m ualink_video timeline`."""
    global TL, TL_PATH
    TL = json.load(open(path, encoding="utf-8")); TL_PATH = str(path)

def frame_svg(t):
    sc = None
    for s in TL["scenes"]:
        if s["start"] <= t < s["start"] + s["len"] + 1e-9:
            sc = s; break
    if sc is None: sc = TL["scenes"][-1]
    lt = t - sc["start"]
    if sc["id"] == "title":
        body = scene_title(lt, sc["len"], sc.get("info"))
        cap = ""; chp = ""
    else:
        from . import scenes_4_9 as scenes_b, scenes_10_17 as scenes_c, scenes_18_21 as scenes_d
        fn = {"s18": scenes_d.scene18, "s19": scenes_d.scene19, "s20": scenes_d.scene20, "s21": scenes_d.scene21,
              "s10": scenes_c.scene10, "s11": scenes_c.scene11, "s12": scenes_c.scene12, "s13": scenes_c.scene13,
              "s14": scenes_c.scene14, "s15": scenes_c.scene15, "s16": scenes_c.scene16, "s17": scenes_c.scene17,
              "s1": scene1, "s2": scene2, "s3": scene3, "s4": scenes_b.scene4, "s5": scenes_b.scene5, "s6": scenes_b.scene6,
              "s7": scenes_b.scene7, "s8": scenes_b.scene8, "s9": scenes_b.scene9}[sc["id"]]
        body = fn(lt, sc["T"], sc["D"], sc["len"])
        # active caption
        cap = ""
        for i, (Ti, Di) in enumerate(zip(sc["T"], sc["D"])):
            if Ti - 0.05 <= lt < Ti + Di + 0.3:
                cap = caption(sc["texts"][i], ease(prog(lt, Ti - 0.05, 0.25)) * (1 - ease(prog(lt, Ti + Di + 0.1, 0.2))))
                break
        chp = chip(sc["chip"], ease(prog(lt, 0.2, 0.5)))
    fade = 1 - ease(prog(lt, 0, 0.4)) if sc["id"] != "title" else 1 - ease(prog(lt, 0, 0.3))
    fade = max(fade, ease(prog(lt, sc["len"] - 0.4, 0.4)))
    ov = f'<rect width="{W}" height="{H}" fill="#000" opacity="{fade:.3f}"/>' if fade > 0.005 else ""
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">'
            f'{body}{chp}{cap}{ov}</svg>')
