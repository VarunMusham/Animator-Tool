"""Part 2: scenes 10-17 (the fix, ordering subtlety, two car parks, mapping, golden rule in code, the defect, two counters, clue)."""
import re
from .scenes_4_9 import *

NB = " "

# ------------------------------------------------------------------ helpers
def _nb(s):
    lead = len(s) - len(s.lstrip(" "))
    s = NB * lead + s.lstrip(" ")
    return re.sub(r" {2,}", lambda m: NB * len(m.group()), s)

HLC = dict(red=RED, green=GREEN, gold=GOLD, blue=BLUE)

def code_block(x, y, w, lines, size=22, lh=38, hl=None, alpha=None, pad=16, stroke="#334155", op=1.0, dim=1.0):
    """dark code panel; `hl` maps line index -> colour name; `alpha` optional per-line opacity. Returns (svg, height)."""
    cw = MONO_ADV * size
    h = 2 * pad + lh * len(lines)
    o = RECT(x, y, w, h, "#020617", rx=14, stroke=stroke, sw=3)
    for i, ln in enumerate(lines):
        a = 1.0 if alpha is None else alpha[i]
        if a <= 0.01: continue
        yy = y + pad + lh * i
        if hl and i in hl:
            o += RECT(x + 8, yy, w - 16, lh, HLC[hl[i]], rx=8, op=.22 * a)
        code, sep, comment = ln.partition("//")
        x0 = x + pad + 6
        o += TX(x0, yy + lh * 0.72, _nb(code.rstrip()), size, "#e2e8f0", "start", 500, MONO, a * dim)
        if sep:
            o += TX(x0 + len(code) * cw, yy + lh * 0.72, _nb("//" + comment), size, "#64748b", "start", 500, MONO, a * dim)
    return G(o, op=op), h

def line_y(y, i, lh=38, pad=16): return y + pad + lh * i + lh / 2

def shield(x, y, s, color, op=1.0):
    p = f'<path d="M0 -40 L34 -26 V6 C34 28 14 40 0 48 C-14 40 -34 28 -34 6 V-26 Z" fill="{color}" opacity=".25" stroke="{color}" stroke-width="5" stroke-linejoin="round"/>' + check(0, 6, 40, color)
    return G(p, x, y, s, 0, op)

def poly_partial(pts, u):
    """SVG path through pts up to fraction u of its length."""
    segs = [abs(b[0] - a[0]) + abs(b[1] - a[1]) for a, b in zip(pts, pts[1:])]
    left = sum(segs) * u
    d = f"M{pts[0][0]:.0f} {pts[0][1]:.0f}"; cur = pts[0]
    for p, sg in zip(pts[1:], segs):
        if left >= sg: d += f" L{p[0]:.0f} {p[1]:.0f}"; left -= sg; cur = p
        else:
            f_ = left / sg if sg else 0
            d += f" L{cur[0] + (p[0] - cur[0]) * f_:.0f} {cur[1] + (p[1] - cur[1]) * f_:.0f}"; break
    return d

def arrow_right(x0, x1, y, color, op=1.0, w=6):
    return (f'<line x1="{x0}" y1="{y}" x2="{x1 - 14}" y2="{y}" stroke="{color}" stroke-width="{w}" stroke-linecap="round" opacity="{op:.3f}"/>'
            f'<polygon points="{x1 - 22},{y - 13} {x1},{y} {x1 - 22},{y + 13}" fill="{color}" opacity="{op:.3f}"/>')

def step_pill(x, y, w, n, text, colr, op=1.0):
    if op <= 0.01: return ""
    return (RECT(x, y, w, 70, "#0f172a", rx=16, stroke=colr, sw=4, op=op) +
            f'<circle cx="{x + 40}" cy="{y + 35}" r="22" fill="{colr}" opacity="{op:.3f}"/>' + TX(x + 40, y + 45, str(n), 28, "#0f172a", "middle", 800, op=op) +
            TX(x + 80, y + 46, text, 30, TXT, "start", 700, op=op))

# ================================================================== SCENE 10  the fix
def total_chart(a, u):
    if a <= 0.01: return ""
    x0, y0, w, h = 960, 30, 920, 210
    o = RECT(x0, y0, w, h, "#0f172a", rx=20, stroke="#334155", sw=3)
    o += TX(x0 + 26, y0 + 44, "TOTAL  =  permits out + parked", 26, TXT, "start", 700)
    o += TX(x0 + w - 26, y0 + 40, "before: dips to 3", 24, RED, "end", 700) + TX(x0 + w - 26, y0 + 70, "after: never dips", 24, GREEN, "end", 700)
    xs = [x0 + 120 + i * 230 for i in range(4)]
    yv = lambda v: y0 + 118 + (4 - v) * 50
    o += f'<line x1="{x0 + 50}" y1="{yv(4)}" x2="{x0 + w - 50}" y2="{yv(4)}" stroke="#475569" stroke-width="2" stroke-dasharray="8 8"/>'
    o += TX(x0 + 46, yv(4) - 10, "4", 24, MUTE, "end", 700) + TX(x0 + 46, yv(3) + 8, "3", 24, MUTE, "end", 700)
    for x, n in zip(xs, ["idle", "at gate", "trailers", "lorry parks"]):
        o += TX(x, y0 + h - 14, n, 20, MUTE, "middle", 600)
    old = [(xs[i], yv(v)) for i, v in enumerate([4, 3, 3, 4])]
    new = [(xs[i], yv(4)) for i in range(4)]
    o += f'<path d="{poly_partial(old, u)}" stroke="{RED}" stroke-width="5" fill="none" stroke-dasharray="14 9" stroke-linecap="round"/>'
    o += f'<path d="{poly_partial(new, clamp(u * 1.0))}" stroke="{GREEN}" stroke-width="7" fill="none" stroke-linecap="round" opacity=".95"/>'
    for (x, yy) in new: o += f'<circle cx="{x}" cy="{yy}" r="9" fill="{GREEN}" opacity="{clamp(u * 3):.2f}"/>'
    return G(o, op=a)

def scene10(t, T, D, L):
    o = world()
    t0 = T[2] + 0.14 * D[2]
    tt = t - t0
    turn = [ease((tt - ARR_T[k]) / TRAIN_TURN) if tt > 0 else 0.0 for k in range(4)]
    park_t = [t0 + ARR_T[k] + TRAIN_TURN for k in range(4)]
    nk = sum(1 for k in range(4) if t >= park_t[k])
    for i in range(4):
        o.append(bay(i, 0.6, res=1 - ease(prog(t, park_t[i] - 0.1, 0.25)), tag=(PIECES[i] if turn[i] > 0.95 else None)))
    # vehicles
    cab_x = lerp(-120, 1000, ease(fr(t, T[0], D[0], 0.25, 0.95)))
    arr = [(T[1], D[1], 0.30, 0.52), (T[1], D[1], 0.52, 0.72), (T[1], D[1], 0.72, 0.92)]
    chk0, chk1 = T[1] + 0.02 * D[1], T[1] + 0.32 * D[1]
    if tt <= 0:
        o.append(cab(cab_x, LANE_Y, 1.0, 1.0, not (chk0 <= t < chk1)))
        for k, (Tb, Db, a, b) in enumerate(arr):
            if t >= Tb + a * Db:
                o.append(trailer(lerp(-120, 1000 + SLOTS[k], ease(fr(t, Tb, Db, a, b))), LANE_Y, k + 1))
    else:
        d = train_dist(tt)
        for k in range(4):
            o.append(piece_svg(k, min(TRAIN_START[k] + d, BAY_CX[k]), lerp(LANE_Y, BAY_CY, turn[k]), lerp(1.0, 1.15, turn[k]), -90 * turn[k]))
    o.append(barrier(ease(prog(t, t0 - 0.6, 0.4)) * (1 - ease(prog(t, t0 + 1.0, 0.4)))))
    # gate check: permit goes to the gatekeeper and comes straight back -- nothing is torn
    if chk0 <= t < chk1:
        u = (t - chk0) / (chk1 - chk0)
        if u < 0.42: o.append(fly(t, chk0, 0.42 * (chk1 - chk0), (1000, LANE_Y), (990, 770), (1050, 700), 1.0, 1.3))
        elif u < 0.58: o.append(ticket(990, 775, 1.3) + check(1070, 770, 40, GREEN))
        else: o.append(fly(t, chk0 + 0.58 * (chk1 - chk0), 0.42 * (chk1 - chk0), (990, 770), (1000, LANE_Y), (1050, 700), 1.3, 1.0))
    pa = pop(t, chk0 + 0.4, 0.4) * (1 - ease(prog(t, T[2], 0.4)))
    if pa > 0.01:
        o.append(G(PILL(-250, -24, 500, 48, "PERMIT OK  —  CHECK ONLY", GREEN, "#052e16", 26, 800), 700, 530, min(pa, 1), 0, min(pa, 1)))
    for k in range(4):
        o.append(tear(BAY_CX[k], BAY_CY - 20, prog(t, park_t[k], 0.9), 1.0))
    # clipboard (four rows, total never changes)
    a_c = ease(prog(t, T[0], 0.9)); ty = -(1 - a_c) * 520
    pl = 0.4 + 0.6 * pulse(t, .9)
    gl = {"total": (GREEN, pl)} if t >= T[3] else {}
    bump = max([max(0.0, 1 - (t - pt) / 0.3) for pt in park_t if t >= pt] or [0.0])
    rows = [
        dict(label="idle", permits="4", parked="0", total="4", mark="ok", op=ease(prog(t, T[0] + 0.6, .5)), glow=gl),
        dict(label="cab at gate (check only)", permits="4", parked="0", total="4", mark="ok", op=ease(prog(t, T[1] + 0.35 * D[1], .5)), glow=gl),
        dict(label="trailers arriving", permits="4", parked="0", total="4", mark="ok", op=ease(prog(t, T[1] + 0.6 * D[1], .5)), glow=gl),
        dict(label="lorry parks — torn + marked", permits=str(4 - nk), parked=str(nk), total="4", mark="ok",
             op=ease(prog(t, t0 - 0.2, .4)), pop={"permits": 1 + .25 * bump, "parked": 1 + .25 * bump, "total": 1.0}, glow=gl),
    ]
    led_op = 1 - ease(prog(t, T[5], 0.4))
    o.append(G(ledger(rows, h=352, ty=ty), op=led_op))
    o.append(label_pill(60, 790, 500, "gate = check only   ·   tear at the bay", pop(t, T[0] + 1.0, 0.4), "#bbf7d0"))
    # chart (beat 3)
    ch = pop(t, T[3] + 0.2, 0.4) * (1 - ease(prog(t, T[4], 0.4)))
    o.append(total_chart(min(ch, 1), ease(fr(t, T[3], D[3], 0.15, 0.75))))
    # gate check becomes a formality (beat 4)
    fa = pop(t, T[4] + 0.2, 0.5) * (1 - ease(prog(t, T[5], 0.4)))
    if fa > 0.01:
        inner = (TX(0, -6, "THE GATE CHECK IS NOW", 34, MUTE, "middle", 700) + TX(0, 52, "A FORMALITY", 66, GREEN, "middle", 800) +
                 TX(0, 86, "can_receive_request() should never fail again", 24, "#7dd3fc", "middle", 500, MONO))
        o.append(top_box(fa, inner, GREEN, "#052e16"))
    # trapdoor vs assertion (beat 5)
    c5 = pop(t, T[5] + 0.1, 0.5)
    if c5 > 0.01:
        pa_ = RECT(40, 90, 480, 450, "#2a0f10", rx=24, stroke=RED, sw=4) + TX(280, 150, "BEFORE", 30, RED, "middle", 800) + \
              TX(280, 192, "A TRAPDOOR", 40, TXT, "middle", 800) + \
              RECT(150, 280, 260, 70, "#020617", rx=8, stroke=RED, sw=3) + car(280, 315, 0, CARC[2], .75, 1.0) + \
              f'<polygon points="262,390 298,390 280,425" fill="{RED}"/>' + \
              TX(280, 480, "silently swallows cars", 28, TXT, "middle", 600) + TX(280, 516, "return;   // silent drop", 22, "#fca5a5", "middle", 500, MONO)
        pb = RECT(540, 90, 480, 450, "#052e16", rx=24, stroke=GREEN, sw=4) + TX(780, 150, "AFTER", 30, GREEN, "middle", 800) + \
             TX(780, 192, "A SAFETY ASSERTION", 38, TXT, "middle", 800) + shield(780, 330, 2.0, GREEN) + \
             TX(780, 480, "a check that never fires", 28, TXT, "middle", 600) + TX(780, 516, "if (!can_receive_request())", 22, "#86efac", "middle", 500, MONO)
        o.append(G(pa_, 0, 0, 1, 0, min(c5, 1)) + G(pb, 0, 0, 1, 0, min(ease(prog(t, T[5] + 0.5, 0.5)), 1)))
    return "".join(o)

# ================================================================== SCENE 11  why just before parking
ORDER_LINES = ["void update_request_receive_trans(int n) {",
               "    if (get_request_buffer_size() + n <= max_buffer_size) {",
               "        remote_request_credit_count -= n;",
               "    } else {",
               '        log_LOW() << "UPLI RX ERROR: Buffer is full!";',
               "    }",
               "}"]
PARKED_COLS = ["#94a3b8", "#a1a1aa", "#78716c"]

def order_row(y, first, second, ok, a):
    colr = GREEN if ok else RED
    o = RECT(60, y, 800, 104, "#0f172a", rx=18, stroke=colr, sw=4)
    o += PILL(90, y + 26, 210, 52, first, colr if ok else "#475569", "#0f172a" if ok else "#e2e8f0", 28, 800)
    o += arrow_right(314, 390, y + 52, MUTE, 1.0, 5)
    o += PILL(404, y + 26, 210, 52, second, "#475569" if ok else colr, "#e2e8f0" if ok else "#0f172a", 28, 800)
    o += check(740, y + 52, 46, GREEN) if ok else cross(740, y + 52, 46, RED)
    return G(o, op=a)

def scene11(t, T, D, L):
    o = world(depot_on=False)
    # the test car: waits at the gate, then drives into bay 4
    x = lerp(-120, 1000, ease(fr(t, T[0], D[0], 0.3, 0.95))); y, rot = LANE_Y, 0.0
    drive = ease(fr(t, T[2], D[2], 0.05, 0.45)); trn = ease(fr(t, T[2], D[2], 0.45, 0.65))
    if t >= T[2]:
        x = lerp(1000, BAY_CX[3], drive); y = lerp(LANE_Y, BAY_CY, trn); rot = -90 * trn
    parked = t >= T[2] + 0.65 * D[2]
    for i in range(3):
        o.append(bay(i, 0.6, car_color=PARKED_COLS[i]))
    o.append(bay(3, 0.6, res=(1 - trn) if t >= T[1] - 0.5 else 0.0, res_pop=1.0))
    o.append(car(x, y, rot, CARC[2], 1.0, ease(prog(t, T[0] + 0.2, 0.4)), t < T[2] + 0.45 * D[2]))
    o.append(barrier(ease(fr(t, T[2], D[2], 0.0, 0.1)) * (1 - ease(fr(t, T[2], D[2], 0.4, 0.55)))))
    # beat 0: the two orders
    a0 = ease(prog(t, T[0] + 0.3, 0.5)) * (1 - ease(prog(t, T[1], 0.4)))
    o.append(order_row(100, "TEAR", "PARK", True, a0) + order_row(230, "PARK", "TEAR", False, ease(prog(t, T[0] + D[0] * 0.55, 0.5)) * (1 - ease(prog(t, T[1], 0.4)))))
    jb = pop(t, T[0] + D[0] * 0.3, 0.4) * (1 - ease(prog(t, T[1], 0.4)))
    if jb > 0.01: o.append(TX(450, 390, "just before — not just after", 34, GOLD, "middle", 800, op=min(jb, 1)))
    # beat 1+: the code
    ca = ease(prog(t, T[1], 0.5)) * (1 - 0.75 * ease(prog(t, T[4], 0.5)))
    hl = {}
    if T[1] <= t < T[3]: hl = {1: "gold"}
    if T[2] + 0.5 * D[2] <= t < T[3]: hl = {1: "red"}
    if T[3] <= t < T[4]: hl = {3: "red", 4: "red", 1: "red"}
    cb, hh = code_block(60, 90, 800, ORDER_LINES, 22, 38, hl)
    o.append(G(cb, 0, (1 - ease(prog(t, T[1], 0.5))) * 40, 1, 0, ca))
    q = pop(t, T[1] + D[1] * 0.45, 0.4) * (1 - ease(prog(t, T[2], 0.4)))
    if q > 0.01:
        o.append(G(PILL(-370, -26, 740, 52, "\"is there room for the n I'm about to add?\"", "#1e293b", GOLD, 28, 700, stroke=GOLD), 460, 440, min(q, 1), 0, min(q, 1)))
    sk = pop(t, T[3] + D[3] * 0.25, 0.4) * (1 - ease(prog(t, T[4], 0.4)))
    if sk > 0.01:
        o.append(G(PILL(-110, -24, 220, 48, "silently skips!", RED, "#fff", 24, 800), 960, line_y(90, 4, 38, 16), min(sk, 1), 0, min(sk, 1)))
    # chips in the car park
    c1 = pop(t, T[1] + D[1] * 0.5, 0.4) * (1 - ease(prog(t, T[2] + 0.3 * D[2], 0.3)))
    if c1 > 0.01:
        o.append(G(PILL(-300, -28, 600, 56, "3 parked + 1 about to park  =  4  ≤  4", "#052e16", GREEN, 28, 800, stroke=GREEN) + check(270, 0, 34, GREEN),
                   1490, 620, min(c1, 1), 0, min(c1, 1)))
    c2 = pop(t, T[2] + D[2] * 0.62, 0.4) * (1 - ease(prog(t, T[4], 0.4)))
    if c2 > 0.01:
        o.append(G(PILL(-300, -28, 600, 56, "4 already parked + 1  =  5  >  4", "#2a0f10", RED, 28, 800, stroke=RED) + cross(270, 0, 34, RED),
                   1490, 600, min(c2, 1), 0, min(c2, 1)))
        gone = 1 - ease(prog(t, T[3], 0.3))
        d1 = ease(fr(t, T[2], D[2], 0.78, 0.9)) * gone; d2 = ease(fr(t, T[2], D[2], 0.88, 1.0)) * gone
        o.append(PILL(1180, 650, 290, 44, "the bay it's already in", "#1e293b", BLUE, 22, 700, stroke=BLUE, op=d1))
        o.append(PILL(1520, 650, 340, 44, "+ the bay you're asking for", "#1e293b", GOLD, 22, 700, stroke=GOLD, op=d2))
    # phantom permit (beat 3)
    ph = pop(t, T[3] + D[3] * 0.4, 0.5) * (1 - ease(prog(t, T[4], 0.4)))
    if ph > 0.01:
        o.append(G(ticket_svg(), 1490, 690, 1.7 * max(ph, 0.01), 0, min(ph, 1)))
        o.append(RECT(1400, 650, 180, 80, "none", rx=10, stroke=RED, sw=4, op=min(ph, 1) * (0.4 + 0.6 * pulse(t, .8)), dash="10 8"))
        o.append(TX(1490, 752, "PHANTOM PERMIT  —  forever", 26, RED, "middle", 800, op=min(ph, 1)))
    # beat 4: the exact order
    s4 = [ease(prog(t, T[4] + 0.3 + 0.9 * k, 0.4)) for k in range(3)]
    o.append(step_pill(60, 110, 820, 1, "CHECK at the gate", GREEN, s4[0]) + step_pill(60, 200, 820, 2, "TEAR immediately before parking", GOLD, s4[1]) +
             step_pill(60, 290, 820, 3, "PARK", BLUE, s4[2]))
    return "".join(o)

# ================================================================== SCENE 12  two car parks
MB = (1390, 542)            # centre of the (park + booth) block in scene-1 coordinates
def mini_park(cx, cy, s, bays_fn, glow=0.0, op=1.0):
    inner = park_frame(1.0) + "".join(bays_fn(i) for i in range(4)) + booth(1.0, glow, 0.0) + barrier(0.0) + road_stub()
    return G(inner, cx - MB[0] * s, cy - MB[1] * s, s, 0, op)

def road_stub():
    return RECT(840, 580, 264, 140, ROAD) + RECT(840, 574, 264, 6, "#3b485e") + RECT(840, 720, 264, 6, "#3b485e")

def booth_pt(cx, cy, s): return cx + (BOOTH[0] - MB[0]) * s, cy + (BOOTH[1] - MB[1]) * s

def scene12(t, T, D, L):
    o = [background()]
    s = 0.6; cy = 480; cxa, cxb = 480, 1440
    a1 = ease(prog(t, T[0] + 0.3, 0.8)); a2 = ease(prog(t, T[0] + D[0] * 0.5, 0.8))
    # state per beat
    glow = 0.0
    if T[1] <= t < T[2]: glow = 0.4 + 0.6 * pulse(t, .9)
    full = [lambda i: bay(i, 0.6, car_color=None, res=0.0)] * 4
    bad_a = ease(fr(t, T[2], D[2], 0.0, 0.25)); fixed_a = ease(fr(t, T[2], D[2], 0.45, 0.65))
    # right park: nothing is ever more than one car (beat 4); otherwise promised bays
    cyc = 0.0
    def bays_a(i): return bay(i, 0.6, res=1.0)
    def bays_b(i):
        if t >= T[4]:
            ph = (t - T[4]) * 1.5; idx = int(ph) % 4; fr_ = ph % 1
            return bay(i, 0.6, car_color=(CARC[1] if i == idx else None), car_op=math.sin(math.pi * fr_) if i == idx else 1.0)
        return bay(i, 0.6, res=1.0)
    o.append(mini_park(cxa, cy, s, bays_a, glow, a1))
    o.append(mini_park(cxb, cy, s, bays_b, glow, a2))
    # labels
    for cx, ttl, path, cls, a, colr in ((cxa, "MODEL", "src/upli/upli_if.cpp", "CompletorCreditManager", a1, GOLD),
                                         (cxb, "TESTBENCH", "tb/common/ualink_top/application_layer.hpp", "CompletorCreditManagerAI", a2, BLUE)):
        o.append(PILL(cx - 130, 214, 260, 46, ttl, "#1e293b", colr, 28, 800, stroke=colr, op=a))
        o.append(TX(cx, 290, path, 20 if len(path) > 30 else 24, MUTE, "middle", 500, MONO, a))
        o.append(TX(cx, 725, cls, 24, "#7dd3fc", "middle", 600, MONO, a * ease(prog(t, T[1], 0.6))))
    # chain arrow
    ca = ease(fr(t, T[0], D[0], 0.6, 1.0))
    if ca > 0.01:
        o.append(arrow_right(800, 1120, cy, GOLD, ca, 8) + TX(960, cy - 26, "chained", 30, GOLD, "middle", 800, op=ca))
    # same procedure (beat 1)
    eq = ease(fr(t, T[1], D[1], 0.5, 0.8))
    if eq > 0.01:
        o.append(TX(960, cy + 70, "same gatekeeper", 28, TXT, "middle", 700, op=eq) + TX(960, cy + 104, "same procedure", 28, TXT, "middle", 700, op=eq))
    # stamps (beats 2-4)
    if t >= T[2]:
        la_ = (RED, "BUG") if fixed_a < 0.5 else (GREEN, "FIXED")
        o.append(G(PILL(-120, -26, 240, 52, la_[1], la_[0], "#fff" if la_[1] == "BUG" else "#052e16", 30, 800) + (check(70, 0, 26, "#052e16") if la_[1] == "FIXED" else ""), cxa, 780, max(bad_a, 0.01), 0, min(bad_a, 1)))
        o.append(G(PILL(-190, -26, 380, 52, "BUG  —  STILL OVER-BOOKING", RED, "#fff", 28, 800), cxb, 780, max(bad_a, 0.01), 0, min(bad_a, 1) * (0.7 + 0.3 * pulse(t, .8))))
    # no procedure (beat 3)
    np_ = pop(t, T[3] + D[3] * 0.3, 0.5)
    if np_ > 0.01:
        bx, by = booth_pt(cxb, cy, s)
        o.append(cross(bx, by, 60, RED, min(np_, 1)))
        o.append(G(PILL(-130, -24, 260, 48, "NO PROCEDURE", RED, "#fff", 26, 800), bx - 215, by + 28, max(np_, 0.01), 0, min(np_, 1)))
    # tests still passed (beat 4)
    tp = pop(t, T[4] + 0.3, 0.5)
    if tp > 0.01:
        o.append(G(PILL(-170, -26, 340, 52, "TEST PASSED", GREEN, "#052e16", 28, 800) + check(132, 0, 26, "#052e16"), cxb, 835, max(tp, 0.01), 0, min(tp, 1)))
        o.append(TX(cxb, 880, "peak occupancy 1 / 4  —  it never fills up", 24, "#fcd34d", "middle", 700, MONO, ease(prog(t, T[4] + 1.0, 0.5))))
        o.append(TX(cxb, 916, "green test ≠ complete fix", 28, RED, "middle", 800, op=ease(fr(t, T[4], D[4], 0.6, 0.85))))
    return "".join(o)

# ================================================================== SCENE 13  the mapping (silent table)
MAP_ROWS = [
    ("Car park with 4 bays", "RX buffer  req_in_buffer,  max_buffer_size = 4", True),
    ("A bay", "One buffer slot", False),
    ("Permit", "A credit", False),
    ("Permits posted out, unused", "remote_request_credit_count", True),
    ("Cars parked", "req_in_buffer.size()", True),
    ("Depot", "The transmitting node's UPLI originator", False),
    ("Gatekeeper's arithmetic", "check_and_release_request_credits()", True),
    ("Gate check", "can_receive_request()", True),
    ("Tearing up the permit", "update_request_receive_trans(1)", True),
    ("Motorbike (arrive = park)", "READ / no-data request", False),
    ("Articulated lorry (cab + trailers)", "WRITE request;  header + numBeats data beats", False),
    ("Lorry rolls into the bay", "forward_request_packet() → req_in_buffer.push()", True),
    ("Car turned away, no record", "return;   — silent drop, one lost packet", True),
    ("Enormous 128-bay car park", "The old max_buffer_size = 128 / 1024", False),
]

MAP_GROUPS = [(1, [0, 1, 2]), (2, [3, 4, 5]), (3, [6, 7, 8]), (4, [9, 10]), (5, [11, 12]), (6, [13])]

def scene13(t, T, D, L):
    o = [background()]
    h = ease(prog(t, T[0] + 0.3, 0.6))
    o.append(TX(60, 100, "THE CAR PARK", 26, GOLD, "start", 800, op=h) + TX(820, 100, "THE REAL SYSTEM", 26, BLUE, "start", 800, op=h))
    o.append(f'<line x1="60" y1="116" x2="1860" y2="116" stroke="#334155" stroke-width="3" opacity="{h:.2f}"/>')
    when = {}
    for b_, rows in MAP_GROUPS:
        for k, i in enumerate(rows): when[i] = T[b_] + 0.2 + k * 0.30 * D[b_]
    for i, (l, r, code) in enumerate(MAP_ROWS):
        ts = when[i]
        u = ease(prog(t, ts, 0.5))
        if u <= 0.01: continue
        y = 132 + i * 52
        hot = 1 - ease(prog(t, ts + 1.2, 0.6))
        row = RECT(60, y, 1800, 46, "#0f172a" if i % 2 == 0 else "#0b1424", rx=10) + RECT(60, y, 1800, 46, GOLD, rx=10, op=.16 * hot, stroke=GOLD, sw=3, sop=hot)
        row += TX(84, y + 32, l, 26, TXT, "start", 600)
        row += arrow_right(740, 800, y + 23, "#475569", 1.0, 4)
        row += TX(820, y + 32, r, 25 if code else 26, "#7dd3fc" if code else TXT, "start", 600 if code else 500, MONO if code else SANS)
        o.append(G(row, (1 - u) * -60, 0, 1, 0, u))
    return "".join(o)

# ================================================================== SCENE 14  the golden rule in code
RELEASE_LINES = ["int CompletorCreditManager::check_and_release_request_credits() {",
                 "    int free_space = max_buffer_size - request_buffer_pointer.size();",
                 "    int credits_to_release = free_space - remote_request_credit_count;",
                 "    if (credits_to_release > 3) credits_to_release = 3;  // max per message",
                 "    remote_request_credit_count += credits_to_release;",
                 "    return credits_to_release;",
                 "}"]

def scene14(t, T, D, L):
    o = [background()]
    # --- the rule (beats 0-1)
    ra = ease(prog(t, T[0], 0.6)) * (1 - ease(prog(t, T[2] - 0.1, 0.5)))
    if ra > 0.01:
        size = 40; cw = MONO_ADV * size
        parts = [("remote_request_credit_count", GOLD), (" + ", TXT), ("req_in_buffer.size()", BLUE), (" <= ", TXT), ("max_buffer_size", GREEN)]
        total = sum(len(p) for p, _ in parts) * cw; x0 = 960 - total / 2
        o.append(mono_parts(960, 150, parts, size, "middle", 800, ra))
        cx = lambda a, b: x0 + (a + b) / 2 * cw
        o.append(TX(cx(0, 27), 200, "(permits out)", 26, GOLD, "middle", 700, op=ra) + TX(cx(30, 50), 200, "(cars parked)", 26, BLUE, "middle", 700, op=ra) +
                 TX(cx(54, 69), 200, "(bays)", 26, GREEN, "middle", 700, op=ra))
        # time axis: the rule must hold at every instant
        gx0, gx1, gy = 200, 1720, 760
        o.append(f'<line x1="{gx0}" y1="{gy}" x2="{gx1}" y2="{gy}" stroke="#334155" stroke-width="4" opacity="{ra:.2f}"/>')
        o.append(f'<line x1="{gx0}" y1="{gy - 130}" x2="{gx1}" y2="{gy - 130}" stroke="{GREEN}" stroke-width="3" stroke-dasharray="12 10" opacity="{ra * .8:.2f}"/>')
        o.append(TX(gx0, gy - 146, "≤ 4   (max_buffer_size)", 24, GREEN, "start", 700, MONO, ra))
        o.append(TX(gx1, gy + 44, "time →", 24, MUTE, "end", 600, op=ra))
        # the sum sits on the limit all the way along (continuous)
        cu = ease(fr(t, T[1], D[1], 0.0, 0.95))
        o.append(f'<path d="M{gx0} {gy - 130} L{gx0 + (gx1 - gx0) * cu:.0f} {gy - 130}" stroke="{GREEN}" stroke-width="10" stroke-linecap="round" opacity="{ra:.2f}"/>')
        if cu > 0.01: o.append(f'<circle cx="{gx0 + (gx1 - gx0) * cu:.0f}" cy="{gy - 130}" r="14" fill="{GREEN}" opacity="{ra:.2f}"/>')
        # "on average" / "eventually" crossed out, "continuously" confirmed
        for k, (txt, ts) in enumerate((("on average", T[0] + D[0] * 0.5), ("eventually", T[0] + D[0] * 0.8))):
            u = pop(t, ts, 0.4)
            if u > 0.01:
                xx = 560 + 400 * k
                o.append(G(PILL(-150, -28, 300, 56, txt, "#2a0f10", RED, 30, 700, stroke=RED), xx, 330, max(u, 0.01), 0, min(u, 1) * ra))
                o.append(f'<line x1="{xx - 130}" y1="330" x2="{xx + 130}" y2="330" stroke="{RED}" stroke-width="5" opacity="{min(u, 1) * ra:.2f}"/>')
        cn = pop(t, T[1] + 0.2, 0.5)
        if cn > 0.01:
            o.append(G(PILL(-260, -36, 520, 72, "CONTINUOUSLY", GREEN, "#052e16", 44, 800), 960, 470, max(cn, 0.01), 0, min(cn, 1) * ra))
    # --- the code (beats 2-4)
    ca = ease(prog(t, T[2], 0.6))
    hl = {}
    if T[3] <= t < T[4]: hl = {1: "blue", 2: "gold"}
    if t >= T[4]: hl = {1: "blue", 2: "red"}
    if T[2] <= t < T[3] and t >= T[2] + 0.4 * D[2]: hl = {1: "green", 2: "green", 4: "green"}
    cb, hh = code_block(60, 120, 1280, RELEASE_LINES, 24, 46, hl)
    o.append(G(cb, 0, (1 - ca) * 40, 1, 0, ca))
    nw = pop(t, T[2] + 0.5, 0.5) * (1 - ease(prog(t, T[3], 0.4)))
    if nw > 0.01:
        o.append(G(PILL(-250, -34, 500, 68, "NOT WRONG", GREEN, "#052e16", 36, 800) + check(150, 0, 34, "#052e16"), 1600, 260, max(nw, 0.01), 0, min(nw, 1)))
        o.append(TX(1600, 330, "it was never wrong", 28, TXT, "middle", 600, op=min(nw, 1)))
    # inputs are honest?
    for idx, colr, txt in ((1, BLUE, "input 1:  cars parked"), (2, GOLD, "input 2:  permits out")):
        u = pop(t, T[3] + 0.3 + 0.5 * (idx - 1), 0.4)
        if u > 0.01:
            o.append(G(PILL(0, -24, 360, 48, txt, "#1e293b", colr, 26, 800, stroke=colr), 1380, line_y(120, idx, 46, 16), max(u, 0.01), 0, min(u, 1)))
            o.append(TX(1810, line_y(120, idx, 46, 16) + 10, "honest?", 30, TXT, "middle", 800, op=min(u, 1) * (0 if t >= T[4] and idx == 2 else 1)))
    dis = pop(t, T[4] + 0.3, 0.5)
    if dis > 0.01:
        o.append(G(PILL(-215, -26, 430, 52, "torn up too early", RED, "#fff", 28, 800) + cross(175, 0, 26, "#fff"), 1600, line_y(120, 2, 46, 16) + 78, max(dis, 0.01), 0, min(dis, 1)))
        o.append(G(TX(0, 0, "DISHONEST at the moment it runs", 40, RED, "middle", 800), 960, 620, max(dis, 0.01), 0, min(dis, 1)))
        o.append(TX(960, 668, "the formula was fine — one input was a lie", 30, TXT, "middle", 500, op=ease(prog(t, T[4] + 1.0, 0.5))))
    return "".join(o)

# ================================================================== SCENE 15  the defect, precisely
BEFORE = ["if (credit_enable) {",
          "    if (compl_cm[port]->can_receive_request()) {",
          "        compl_cm[port]->update_request_receive_trans(1);  // debit HERE, at arrival",
          "    } else {",
          '        log_LOW() << "[ERROR] Insufficient request credits...";',
          "        return;                                           // silent drop",
          "    }",
          "}"]
AFTER_GATE = ["if (credit_enable) {",
              "    if (!compl_cm[port]->can_receive_request()) {",
              '        log_LOW() << "[ERROR] Insufficient request credits...";',
              "        return;",
              "    }",
              "}"]
READ_PATH = ["// READ / no-data path",
             "if (credit_enable) {",
             "    compl_cm[port]->update_request_receive_trans(1);",
             "}",
             "s1_if.forward_request_packet(req_packet);"]
WRITE_PATH = ["// WRITE path — after the final beat",
              "if (credit_enable) {",
              "    compl_cm[port]->update_request_receive_trans(1);      // 1 request slot",
              "    compl_cm[port]->update_orgdata_receive_trans(numBeats); // numBeats data slots",
              "}",
              "s1_if.forward_request_packet(req_packet);"]

def scene15(t, T, D, L):
    o = [background()]
    # ---- beat 0: BEFORE
    a0 = ease(prog(t, T[0], 0.6)) * (1 - ease(prog(t, T[1], 0.5)))
    if a0 > 0.01:
        o.append(G(PILL(0, 0, 820, 50, "BEFORE  ·  upli_if.cpp, at the admission gate  (~line 1291)", "#2a0f10", RED, 24, 800, stroke=RED), 60, 100, 1, 0, a0))
        cb, hh = code_block(60, 170, 1300, BEFORE, 24, 42, {2: "red", 5: "red"}, alpha=[ease(prog(t, T[0] + 0.5 + 0.35 * i, 0.4)) for i in range(8)])
        o.append(G(cb, op=a0))
        # gate --- long gap --- push
        ga = ease(fr(t, T[0], D[0], 0.35, 0.6))
        if ga > 0.01:
            y = 640
            bar = f'<line x1="200" y1="{y}" x2="1720" y2="{y}" stroke="#475569" stroke-width="6" stroke-linecap="round"/>'
            bar += f'<circle cx="200" cy="{y}" r="18" fill="{RED}"/><circle cx="1720" cy="{y}" r="18" fill="{GREEN}"/>'
            bar += TX(200, y - 36, "GATE", 26, RED, "middle", 800) + TX(200, y + 60, "debit happens here", 24, "#fca5a5", "middle", 600)
            bar += TX(1720, y - 36, "PUSH", 26, GREEN, "middle", 800) + TX(1720, y + 60, "forward_request_packet() → upli_s1_if.cpp:88", 22, "#86efac", "end", 500, MONO)
            gap = ease(fr(t, T[0], D[0], 0.55, 0.85))
            bar += f'<path d="M200 {y + 28} V{y + 44} H{200 + 1520 * gap:.0f}" stroke="#fb923c" stroke-width="5" fill="none"/>'
            bar += TX(960, y + 92, "a long gap — for a WRITE, until every data beat has landed", 28, "#fb923c", "middle", 700, op=gap)
            o.append(G(bar, op=ga * a0))
    # ---- beat 1: AFTER (gate)
    a1 = ease(prog(t, T[1] + 0.2, 0.6)) * (1 - ease(prog(t, T[2], 0.5)))
    if a1 > 0.01:
        o.append(G(PILL(0, 0, 720, 50, "AFTER  ·  the gate becomes a pure check", "#052e16", GREEN, 26, 800, stroke=GREEN), 60, 100, 1, 0, a1))
        cb, hh = code_block(60, 170, 1100, AFTER_GATE, 24, 42, {1: "green"})
        o.append(G(cb, op=a1))
        o.append(G(TX(1220, 290, "check only", 40, GREEN, "start", 800) + TX(1220, 336, "nothing changes on the clipboard", 28, TXT, "start", 500) +
                   TX(1220, 380, "the debit line is gone from here", 28, "#fca5a5", "start", 500), op=a1 * ease(fr(t, T[1], D[1], 0.4, 0.7))))
    # ---- beat 2: the debit moves next to the push
    a2 = ease(prog(t, T[2], 0.6)) * (1 - ease(prog(t, T[3], 0.5)))
    if a2 > 0.01:
        o.append(G(PILL(0, 0, 900, 50, "…and the debit moves next to the push, on both paths", "#0f2744", BLUE, 26, 800, stroke=BLUE), 60, 100, 1, 0, a2))
        cr, h1 = code_block(60, 170, 1100, READ_PATH, 22, 38, {2: "green", 4: "gold"}, alpha=[ease(prog(t, T[2] + 0.5 + 0.2 * i, 0.4)) for i in range(5)])
        cw_, h2 = code_block(60, 170 + h1 + 40, 1100, WRITE_PATH, 22, 38, {2: "green", 3: "green", 5: "gold"},
                             alpha=[ease(prog(t, T[2] + D[2] * 0.3 + 0.2 * i, 0.4)) for i in range(6)])
        o.append(G(cr + cw_, op=a2))
        r1 = pop(t, T[2] + 1.5, 0.4); r2 = pop(t, T[2] + D[2] * 0.5, 0.4); r3 = pop(t, T[2] + D[2] * 0.75, 0.4)
        o.append(G(PILL(0, 0, 560, 48, "READ: debit right before the push", "#052e16", GREEN, 24, 700, stroke=GREEN), 1200, line_y(170, 2, 38, 16) - 24 + 0, 1, 0, min(r1, 1) * a2))
        o.append(G(PILL(0, 0, 640, 48, "WRITE: 1 request slot + numBeats data slots", "#052e16", GREEN, 24, 700, stroke=GREEN), 1200, 170 + h1 + 40 + line_y(0, 2, 38, 16) - 48, 1, 0, min(r2, 1) * a2))
        o.append(G(PILL(0, 0, 640, 54, "identical change mirrored in application_layer.hpp", "#1e293b", GOLD, 24, 800, stroke=GOLD), 1200, 170 + h1 + 40 + h2 - 60, 1, 0, min(r3, 1) * a2))
    # ---- beat 3: one call, moved
    a3 = ease(prog(t, T[3], 0.5))
    if a3 > 0.01:
        for x, ttl, colr, sub in ((120, "THE GATE", RED, "admission check"), (1300, "THE PUSH", GREEN, "req_in_buffer.push()")):
            o.append(G(RECT(x, 240, 500, 240, "#0f172a", rx=22, stroke=colr, sw=4) + TX(x + 250, 330, ttl, 44, colr, "middle", 800) +
                       TX(x + 250, 380, sub, 26, MUTE, "middle", 600, MONO), op=a3))
        mv = ease(fr(t, T[3], D[3], 0.15, 0.6))
        px = lerp(370, 1550, mv)
        o.append(G(RECT(-250, -30, 500, 60, "#422006", rx=14, stroke=GOLD, sw=4) + TX(0, 10, "update_request_receive_trans(1);", 26, GOLD, "middle", 700, MONO), px, 560 - 120 * math.sin(math.pi * mv) + 20, 1, 0, a3))
        o.append(arrow_right(380, 1540, 620, "#475569", a3 * 0.6, 4))
        for k, txt in enumerate(["0 new variables", "0 new functions", "0 changed signatures", "1 call moved"]):
            u = pop(t, T[3] + D[3] * (0.12 + 0.2 * k), 0.4)
            o.append(PILL(260 + k * 360 - 20, 730, 330, 56, txt, "#052e16" if k < 3 else "#422006", GREEN if k < 3 else GOLD, 26, 800, stroke=GREEN if k < 3 else GOLD, op=min(u, 1)))
    return "".join(o)

# ================================================================== SCENE 16  why two counters
def two_park(cx, cy, s, n_occ, names, op=1.0, pops=None):
    """park frame + bays scaled by s; `pops` = per-bay pop values of the occupant pieces."""
    inner = park_frame(1.0)
    for i in range(4):
        inner += bay(i, 0.6)
    if pops:
        for i, (kind, pv) in enumerate(pops):
            if pv > 0.01:
                if kind == "cab": inner += cab(BAY_CX[i], BAY_CY, 1.15 * min(pv, 1.2), min(pv, 1), False, -90)
                elif kind == "tr": inner += trailer(BAY_CX[i], BAY_CY, names[i] if names else i, 1.15 * min(pv, 1.2), min(pv, 1), -90)
                elif kind == "bike": inner += motorbike(BAY_CX[i], BAY_CY, -90, CARC[0], 1.9 * min(pv, 1.2), min(pv, 1))
    return G(inner, cx - 1490 * s, cy - 497 * s, s, 0, op)

def counter_chip(x, y, label, val, colr, bump=0.0, op=1.0):
    if op <= 0.01: return ""
    inner = RECT(-210, -44, 420, 88, "#0f172a", rx=18, stroke=colr, sw=4) + TX(-190, -8, label, 22, MUTE, "start", 700, MONO) + \
            TX(190, 26, str(val), 44, colr, "end", 800)
    return G(inner, x, y, 1 + 0.15 * bump, 0, op)

def scene16(t, T, D, L):
    o = [background()]
    s = 0.62; cy = 400; cxa, cxb = 500, 1420
    # beat 0: the two calls and the suspicion
    a0 = ease(prog(t, T[0], 0.6)) * (1 - ease(prog(t, T[1] + 0.3, 0.5)))
    if a0 > 0.01:
        o.append(G(RECT(260, 300, 1400, 260, "#020617", rx=22, stroke="#334155", sw=3) +
                   TX(960, 410, "update_request_receive_trans(1);", 52, GOLD, "middle", 800, MONO) +
                   TX(960, 500, "update_orgdata_receive_trans(numBeats);", 52, BLUE, "middle", 800, MONO), op=a0))
        q = pop(t, T[0] + D[0] * 0.55, 0.5)
        if q > 0.01:
            o.append(G(bubble(-200, -40, 400, 80, "Charging twice?", 0, 62, 1.0, 36), 960, 250, max(q, 0.01), 0, min(q, 1) * a0))
    # beat 1+: two separate car parks
    a1 = ease(prog(t, T[1], 0.8))
    if a1 > 0.01:
        tA = T[2] + D[2] * 0.30; tB = [T[2] + D[2] * (0.50 + 0.12 * k) for k in range(3)]
        tR = T[3] + D[3] * 0.25
        pA = [("cab", pop(t, tA, 0.4)), ("bike", pop(t, tR, 0.4)), ("", 0), ("", 0)]
        pB = [("tr", pop(t, tB[0], 0.4)), ("tr", pop(t, tB[1], 0.4)), ("tr", pop(t, tB[2], 0.4)), ("", 0)]
        o.append(two_park(cxa, cy, s, 0, None, a1, pA))
        o.append(two_park(cxb, cy, s, 0, [1, 2, 3, 4], a1, pB))
        o.append(PILL(cxa - 200, 168, 400, 50, "REQUEST BUFFER", "#1e293b", GOLD, 28, 800, stroke=GOLD, op=a1))
        o.append(TX(cxa, 252, "req_in_buffer", 24, MUTE, "middle", 600, MONO, a1))
        o.append(PILL(cxb - 200, 168, 400, 50, "DATA BUFFER", "#1e293b", BLUE, 28, 800, stroke=BLUE, op=a1))
        o.append(TX(cxb, 252, "orgdata buffer", 24, MUTE, "middle", 600, MONO, a1))
        o.append(TX(960, cy + 10, "≠", 90, RED, "middle", 800, op=a1))
        o.append(TX(960, cy + 62, "no shared state", 24, MUTE, "middle", 600, op=a1))
        # counters
        bA = max([max(0.0, 1 - (t - tt) / 0.35) for tt in (tA, tR) if t >= tt] or [0.0])
        bB = max([max(0.0, 1 - (t - tt) / 0.35) for tt in tB if t >= tt] or [0.0])
        va = 4 - (1 if t >= tA else 0) - (1 if t >= tR else 0)
        vb = 4 - sum(1 for tt in tB if t >= tt)
        o.append(counter_chip(cxa, 640, "request credits", va, GOLD, bA, a1))
        o.append(counter_chip(cxb, 640, "orgdata credits", vb, BLUE, bB, a1))
        if t >= tR:
            o.append(TX(cxb, 716, "unchanged", 26, "#86efac", "middle", 700, op=ease(prog(t, tR + 0.2, 0.4))))
    # table (beat 3)
    ta = ease(prog(t, T[3] + D[3] * 0.4, 0.6))
    if ta > 0.01:
        tx0, ty0, tw = 360, 740, 1200
        tb = RECT(tx0, ty0, tw, 170, "#0f172a", rx=16, stroke="#334155", sw=3)
        tb += TX(tx0 + 40, ty0 + 38, "path", 20, MUTE, "start", 700) + TX(tx0 + 760, ty0 + 38, "request credits", 20, GOLD, "middle", 700) + TX(tx0 + 1040, ty0 + 38, "orgdata credits", 20, BLUE, "middle", 700)
        for k, (p, a_, b_, c_) in enumerate((("READ / no-data", "1", "0", GREEN), ("WRITE  (numBeats beats)", "1", "numBeats", GOLD))):
            yy = ty0 + 60 + k * 52
            tb += RECT(tx0 + 14, yy, tw - 28, 44, "#1e293b", rx=10) + TX(tx0 + 40, yy + 31, p, 26, TXT, "start", 700) + \
                  TX(tx0 + 760, yy + 32, a_, 32, GOLD, "middle", 800) + TX(tx0 + 1040, yy + 32, b_, 32, BLUE, "middle", 800)
        o.append(G(tb, 0, (1 - ta) * 30, 1, 0, ta))
    return "".join(o)

# ================================================================== SCENE 17  the confirming clue
def channel_row(y, label, sub, colr, debit_at_push, a, t, tstart, dropped):
    """one horizontal pipeline: ARRIVES (gate) ... PUSH, with the debit marker placed at either end."""
    x0, x1 = 650, 1440
    o = RECT(40, y - 100, 1840, 200, "#0f172a", rx=22, stroke=colr, sw=4)
    o += TX(80, y - 10, label, 36, colr, "start", 800) + TX(80, y + 34, sub, 24, MUTE, "start", 600, MONO)
    o += f'<line x1="{x0}" y1="{y}" x2="{x1}" y2="{y}" stroke="#475569" stroke-width="8" stroke-linecap="round"/>'
    o += f'<circle cx="{x0}" cy="{y}" r="16" fill="#94a3b8"/><circle cx="{x1}" cy="{y}" r="16" fill="#94a3b8"/>'
    o += TX(x0, y - 34, "ARRIVES (gate)", 22, MUTE, "middle", 700) + TX(x1, y - 34, "PUSH into buffer", 22, MUTE, "middle", 700)
    mx = x1 if debit_at_push else x0
    u = pop(t, tstart, 0.5)
    if u > 0.01:
        dm = f'<polygon points="0,-30 26,0 0,30 -26,0" fill="{colr}"/>' + TX(0, 8, "−", 28, "#0f172a", "middle", 800)
        o += G(dm, mx, y, max(u, 0.01), 0, min(u, 1)) + TX(mx, y + 62, "DEBIT", 22, colr, "middle", 800, op=min(u, 1))
    if not debit_at_push:
        g = ease(prog(t, tstart + 0.6, 0.6))
        o += f'<path d="M{x0 + 50} {y + 72} H{x0 + 50 + (x1 - x0 - 50) * g:.0f}" stroke="#fb923c" stroke-width="5" stroke-linecap="round" fill="none"/>'
    # verdict
    vx = 1660
    if dropped:
        o += TX(vx, y - 20, "req_DROPPED", 26, MUTE, "middle", 700, MONO) + TX(vx, y + 34, "≠ 0", 60, RED, "middle", 800, MONO)
        for k in range(5):
            pk = pop(t, tstart + 1.2 + 0.25 * k, 0.3)
            if pk > 0.01: o += cross(x0 + 70 + k * 40, y, 26, RED, min(pk, 1))
    else:
        o += TX(vx, y - 20, "orgbeat_DROPPED", 24, MUTE, "middle", 700, MONO) + TX(vx, y + 34, "= 0", 60, GREEN, "middle", 800, MONO)
    return G(o, op=a)

def scene17(t, T, D, L):
    o = [background()]
    # beat 0: title
    t0 = ease(prog(t, T[0] + 0.2, 0.6)) * (1 - ease(prog(t, T[1] + 0.2, 0.5)))
    if t0 > 0.01:
        o.append(TX(960, 470, "THE CONFIRMING CLUE", 88, GOLD, "middle", 800, op=t0) + TX(960, 540, "a controlled comparison, hiding in the code", 34, TXT, "middle", 500, op=t0))
    # beat 1: two channels
    dr = ease(prog(t, T[1], 0.6))
    if dr > 0.01:
        o.append(channel_row(270, "DATA channel", "orgdata", GREEN, True, dr, t, T[1] + 0.5, False))
        o.append(channel_row(560, "REQUEST channel", "req", RED, False, ease(prog(t, T[1] + D[1] * 0.45, 0.6)), t, T[1] + D[1] * 0.45 + 0.4, True))
        o.append(TX(1045, 366, "debit next to the push  —  from an earlier fix", 26, "#86efac", "middle", 700, op=ease(fr(t, T[1], D[1], 0.25, 0.4))))
        o.append(TX(1045, 656, "debit at the gate  —  a long gap before the push", 26, "#fdba74", "middle", 700, op=ease(fr(t, T[1], D[1], 0.8, 0.95))))
    # beat 3: same code base, same load, same buffer size
    ca = pop(t, T[3] + 0.3, 0.5)
    if ca > 0.01:
        inner = (TX(0, -20, "SAME code base   ·   SAME load   ·   SAME buffer size", 38, TXT, "middle", 800) +
                 TX(0, 38, "the only difference: where the debit sits", 34, GOLD, "middle", 700))
        o.append(G(RECT(-700, -66, 1400, 140, "#1c1608", rx=24, stroke=GOLD, sw=4) + inner, 960, 770, max(ca, 0.01), 0, min(ca, 1)))
    return "".join(o)
