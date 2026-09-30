"""Scenes 4-9 (motorbike, lorry, the bug, watch it break, silent failure, why nobody noticed)."""
from .render import *

# ------------------------------------------------------------------ extra objects
def motorbike(x, y, rot=0.0, color="#f472b6", s=1.0, op=1.0, permit=False):
    if op <= 0.01: return ""
    dark = shade(color, .7)
    p = ('<rect x="-46" y="-7" width="24" height="14" rx="7" fill="#0b1220"/>'
         '<rect x="24" y="-7" width="24" height="14" rx="7" fill="#0b1220"/>'
         f'<rect x="-38" y="-10" width="76" height="20" rx="10" fill="{color}"/>'
         '<rect x="20" y="-26" width="8" height="52" rx="4" fill="#cbd5e1"/>'
         f'<circle cx="-6" cy="0" r="15" fill="{dark}"/><circle cx="-6" cy="0" r="10" fill="#fef3c7"/>'
         '<rect x="38" y="-5" width="7" height="10" rx="2" fill="#fde68a"/>')
    if permit:
        p += (f'<rect x="4" y="-9" width="15" height="18" rx="2" fill="{GOLD}" stroke="#78350f" stroke-width="1.5"/>')
    return G(p, x, y, s, rot, op)

def cab_inner(permit=False):
    p = ('<rect x="-50" y="-27" width="60" height="54" rx="8" fill="#9a5b2c"/>'
         '<rect x="4" y="-30" width="46" height="60" rx="12" fill="#fb923c"/>'
         '<rect x="14" y="-24" width="24" height="48" rx="8" fill="#c2410c"/>'
         '<rect x="34" y="-22" width="10" height="44" rx="4" fill="#bae6fd" opacity=".9"/>'
         '<rect x="-40" y="-38" width="28" height="10" rx="3" fill="#0b1220"/><rect x="-40" y="28" width="28" height="10" rx="3" fill="#0b1220"/>'
         '<rect x="14" y="-38" width="28" height="10" rx="3" fill="#0b1220"/><rect x="14" y="28" width="28" height="10" rx="3" fill="#0b1220"/>'
         '<rect x="46" y="-25" width="6" height="11" rx="2" fill="#fde68a"/><rect x="46" y="14" width="6" height="11" rx="2" fill="#fde68a"/>'
         '<rect x="-50" y="-22" width="5" height="10" rx="2" fill="#ef4444"/><rect x="-50" y="12" width="5" height="10" rx="2" fill="#ef4444"/>')
    if permit:
        p += (f'<rect x="-40" y="-14" width="34" height="28" rx="4" fill="{GOLD}" stroke="#78350f" stroke-width="2"/>'
              '<line x1="-28" y1="-9" x2="-28" y2="9" stroke="#b45309" stroke-width="2" stroke-dasharray="4 3"/>')
    return p

def trailer_inner(k):
    p = ('<rect x="-42" y="-30" width="84" height="60" rx="6" fill="#64748b"/>'
         '<rect x="-36" y="-24" width="72" height="48" rx="4" fill="#94a3b8"/>'
         + "".join(f'<line x1="{i}" y1="-24" x2="{i}" y2="24" stroke="#64748b" stroke-width="3"/>' for i in (-24, 24)) +
         '<rect x="-34" y="-38" width="22" height="9" rx="3" fill="#0b1220"/><rect x="-34" y="29" width="22" height="9" rx="3" fill="#0b1220"/>'
         '<rect x="-6" y="-38" width="22" height="9" rx="3" fill="#0b1220"/><rect x="-6" y="29" width="22" height="9" rx="3" fill="#0b1220"/>'
         '<rect x="42" y="-5" width="14" height="10" fill="#475569"/>'
         f'<text x="0" y="12" font-family="{SANS}" font-size="34" font-weight="800" fill="#1e293b" text-anchor="middle">{k}</text>')
    return p

SLOTS = [-(104 + 97 * k) for k in range(4)]          # trailer centres relative to the cab

def cab(x, y, s=1.0, op=1.0, permit=False, rot=0.0):
    return G(cab_inner(permit), x, y, s, rot, op)

def trailer(x, y, k, s=1.0, op=1.0, rot=0.0):
    return G(trailer_inner(k), x, y, s, rot, op)

N_TRAILERS = 3
LORRY_S = 0.58        # scale that fits the whole lorry inside one 240px bay
LORRY_HALF = (50 - (SLOTS[N_TRAILERS - 1] - 42)) / 2   # half the assembled length

def lorry_full(cx, cy, s=1.0, rot=0.0, op=1.0, n=N_TRAILERS):
    """whole lorry centred on (cx,cy)."""
    rear = SLOTS[n - 1] - 42
    shift = -((50 + rear) / 2)
    inner = f'<g transform="translate({shift} 0)">{cab_inner()}' + "".join(G(trailer_inner(k + 1), SLOTS[k], 0) for k in range(n)) + "</g>"
    return G(inner, cx, cy, s, rot, op)

def tear(x, y, u, s=1.4):
    if u <= 0 or u >= 1: return ""
    e = ease(u); d = e * 46; a = 1 - clamp((u - .45) / .55)
    st = f'fill="{GOLD}" stroke="#92400e" stroke-width="2.5" stroke-linejoin="round"'
    left = f'<path d="M-34 -20 L0 -20 L4 -10 L-4 0 L4 10 L0 20 L-34 20 Z" {st}/>'
    right = f'<path d="M0 -20 L34 -20 L34 20 L0 20 L4 10 L-4 0 L4 -10 Z" {st}/>'
    return (G(left, x - d * s, y + e * 26, s, -e * 28, a) + G(right, x + d * s, y + e * 20, s, e * 24, a))

def tri(x, y, up, color, op=1.0):
    pts = f"{x - 12},{y + 9} {x + 12},{y + 9} {x},{y - 11}" if up else f"{x - 12},{y - 9} {x + 12},{y - 9} {x},{y + 11}"
    return f'<polygon points="{pts}" fill="{color}" opacity="{op:.3f}"/>'

# ------------------------------------------------------------------ ledger table
HDR = dict(permits="PERMITS OUT", parked="PARKED", inbound="INBOUND", total="TOTAL")
COLX = dict(permits=515, parked=632, inbound=738, total=850)
DEFCOL = dict(permits=GOLD_INK, parked=BLUE_INK, inbound=RED_INK, total=GREEN_INK)

def paper(y0, h, title=None, clip=True, mono=False):
    o = RECT(60, y0, 860, h, PAPER, rx=26, stroke="#cbd5e1", sw=3)
    if clip: o += RECT(400, y0 - 28, 180, 56, "#475569", rx=14) + RECT(450, y0 - 14, 80, 18, "#1e293b", rx=9)
    if title: o += TX(490, y0 + 70, title, 26 if mono else 27, "#475569", "middle", 700, MONO if mono else SANS)
    return o

def ledger(rows, y0=90, h=350, title="GATEKEEPER'S CLIPBOARD", cols=("permits", "parked", "total"), ty=0.0, clip=True):
    o = paper(y0, h, title, clip)
    hy = y0 + (118 if title else 42)
    for c in cols: o += TX(COLX[c], hy, HDR[c], 18, "#64748b", "middle", 700)
    for i, r in enumerate(rows):
        a = r.get("op", 1.0)
        if a <= 0.01: continue
        y = hy + 14 + i * 56
        row = RECT(88, y, 804, 48, "#e2e8f0", rx=10)
        if r.get("tint"): row += RECT(88, y, 804, 48, r["tint"], rx=10, op=.16, stroke=r["tint"], sw=3)
        row += TX(104, y + 32, r["label"], 22, INK, "start", 700)
        for c in cols:
            v = r.get(c)
            pu = r.get("pop", {}).get(c, 1.0)
            if v is None or pu <= 0.01: continue
            col = r.get("colors", {}).get(c, DEFCOL[c])
            size = r.get("size", {}).get(c, 32)
            row += G(TX(0, 0, v, size, col, "middle", 700), COLX[c], y + 35, pu, 0, min(pu, 1))
            gl = r.get("glow", {}).get(c)
            if gl: row += RECT(COLX[c] - 44, y + 2, 88, 44, "none", rx=8, stroke=gl[0], sw=4, op=gl[1])
            ar = r.get("arrow", {}).get(c)
            if ar: row += tri(COLX[c] + 40, y + 24, ar[0] == "up", ar[1], ar[2])
        mk = r.get("mark")
        if mk and r.get("pop", {}).get("total", 1.0) > 0.5:
            row += check(COLX["total"] + 48, y + 24, 22, GREEN_INK) if mk == "ok" else cross(COLX["total"] + 48, y + 24, 22, RED_INK)
        if r.get("note"):
            txt, colr = r["note"]
            na = r.get("note_op", 1.0)
            w = len(txt) * 14 + 34
            row += PILL(930, y + 4, w, 40, txt, colr, "#fff", 21, 800, op=na)
        o += G(row, op=a)
    return G(o, 0, ty)

def top_box(a, inner, stroke=GOLD, fill="#1c1608"):
    if a <= 0.01: return ""
    return G(RECT(-460, -95, 920, 190, fill, rx=24, stroke=stroke, sw=4) + inner, 1420, 125, max(a, 0.01), 0, min(a, 1))

def bubble_up(x, y, w, h, s, size=30):
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="18" fill="#f8fafc"/>'
            f'<polygon points="-14,{y + 2} 14,{y + 2} 0,{y - 44}" fill="#f8fafc"/>'
            + TX(x + w / 2, y + h / 2 + size * .35, s, size, INK, "middle", 600))

def world(depot_on=True):
    return [background(), road(1.0), depot(1.0) if depot_on else "", booth(1.0), park_frame(1.0)]

def label_pill(x, y, w, text, op, colr="#a5f3fc"):
    return PILL(x, y, w, 40, text, colr, "#0f172a", 22, 800, op=min(op, 1))

# ================================================================== SCENE 4
def scene4(t, T, D, L):
    o = world()
    tp = T[2] + 0.30 * D[2]
    r0 = 1 - ease(prog(t, tp, 0.5))
    for i in range(4):
        o.append(bay(i, 0.6, res=(r0 if i == 0 else 1.0)))
    # bike pose
    gate = 1030
    x = lerp(-140, gate, ease(fr(t, T[0], D[0], 0.2, 1.0))); y, rot = LANE_Y, 0.0
    b_open = 0.0
    if t >= T[1]:
        b_open = ease(fr(t, T[1], D[1], 0.2, 0.35)) * (1 - ease(fr(t, T[1], D[1], 0.6, 0.75)))
        x = lerp(gate, BAY_CX[0], ease(fr(t, T[1], D[1], 0.4, 1.0)))
    if t >= T[2]:
        b_open = 0.0
        turn = ease(fr(t, T[2], D[2], 0.0, 0.3)); y = lerp(LANE_Y, BAY_CY, turn); rot = -90 * turn
    o.append(motorbike(x, y, rot, CARC[0], 1.9, ease(prog(t, T[0] + 0.1, 0.4)), t < tp))
    fa = pop(t, T[1], 0.5) * (1 - ease(fr(t, T[1], D[1], 0.28, 0.4)))
    if fa > 0.01 and t >= T[1]:
        o.append(ticket(1030, 545, 1.5 * fa, 0, min(fa, 1)) + check(1100, 530, 34, GREEN, min(fa, 1)))
    o.append(barrier(b_open))
    # tear + flash
    o.append(tear(BAY_CX[0], BAY_CY - 20, prog(t, tp, 1.0)))
    fl = 1 - prog(t, tp, 0.9)
    if 0 < fl < 1:
        o.append(RECT(BAY_CX[0] - 71, BAY_TOP + 4, 142, 232, "none", rx=6, stroke=GREEN, sw=6, op=fl))
    # clipboard
    a_c = ease(prog(t, T[0], 0.9)); ty = -(1 - a_c) * 520
    pv = pop(t, tp, 0.5)
    g3 = t >= T[3] and t < T[4]; g4 = t >= T[4]
    pl = 0.4 + 0.6 * pulse(t, 0.9)
    rows = [
        dict(label="before", permits="4", parked="0", total="4", mark="ok", op=ease(prog(t, T[0] + 0.8, 0.5)),
             glow={"total": (GREEN, pl)} if g4 else {}),
        dict(label="motorbike parks", permits="3", parked="1", total="4", mark="ok", op=ease(prog(t, T[2] - 0.2, 0.5)),
             pop={"permits": pv, "parked": pv, "total": pv},
             glow=({"permits": (GOLD, pl), "parked": (BLUE, pl)} if g3 else ({"total": (GREEN, pl)} if g4 else {})),
             arrow={"permits": ("down", RED, 1.0), "parked": ("up", GREEN, 1.0)} if (g3 and pv > 0.9) else {}),
    ]
    o.append(ledger(rows, h=270, ty=ty))
    o.append(label_pill(60, 760, 560, "MOTORBIKE  =  READ request (no data)", pop(t, T[0] + D[0] * 0.5, 0.4), "#fbcfe8"))
    # golden banner (beat 4)
    ba = pop(t, T[4] + 0.2, 0.5)
    if ba > 0.01:
        inner = (PILL(-150, -84, 300, 40, "THE GOLDEN RULE", GOLD, "#0f172a", 24, 800) +
                 mono_parts(0, 8, [("PERMITS", GOLD), (" + ", TXT), ("PARKED", BLUE), (" ≤ ", TXT), ("4", GREEN)], 64, "middle") +
                 TX(-30, 68, "holds at every instant", 36, TXT, "middle", 600) + check(225, 56, 30, GREEN))
        o.append(top_box(ba, inner))
    return "".join(o)

# ================================================================== SCENE 5
def timeline5(t, ev, op, gap_u, pulse_u):
    xs = [120, 360, 540, 720, 980]
    names = ["CAB", "TRAILER 1", "TRAILER 2", "TRAILER 3", "LORRY PARKS"]
    y = 150
    o = f'<line x1="90" y1="{y}" x2="1040" y2="{y}" stroke="#475569" stroke-width="5" stroke-linecap="round"/>'
    o += f'<polygon points="1036,{y - 10} 1058,{y} 1036,{y + 10}" fill="#475569"/>'
    lit_to = max([i for i in range(len(xs)) if t >= ev[i]], default=-1)
    if lit_to >= 0:
        o += f'<line x1="{xs[0]}" y1="{y}" x2="{xs[lit_to]}" y2="{y}" stroke="{GOLD}" stroke-width="5" stroke-linecap="round"/>'
    for i, (x, n) in enumerate(zip(xs, names)):
        on = t >= ev[i]
        big = 1 + 0.25 * pulse_u * pulse(t, .8) if i in (0, 4) else 1
        col = (GREEN if i == 4 else GOLD) if on else "#475569"
        o += f'<circle cx="{x}" cy="{y}" r="{13 * big:.1f}" fill="{col}" stroke="#0b1220" stroke-width="3"/>'
        o += TX(x, y - 30, n, 21, TXT if on else MUTE, "middle", 700)
    if gap_u > 0.01:
        d = f"M{xs[0]} {y + 24} V{y + 40} H{xs[0] + (xs[4] - xs[0]) * gap_u:.0f}" + (f" V{y + 24}" if gap_u > .99 else "")
        o += f'<path d="{d}" stroke="#fb923c" stroke-width="5" fill="none" stroke-linejoin="round"/>'
        o += TX(550, y + 88, "LONG GAP", 34, "#fb923c", "middle", 800, op=gap_u) + \
             TX(550, y + 122, "at the gate, but not in a bay", 26, TXT, "middle", 500, op=gap_u)
    return G(o, op=op)

# uncoupling run: the coupled train drives along the lane; each piece peels off into its own bay
TRAIN_START = [1000] + [1000 + SLOTS[k] for k in range(3)]     # cab, trailer 1..3 at the gate
TRAIN_V, TRAIN_TURN = 620.0, 0.45

def train_dist(tt):
    """distance travelled after tt seconds (speed ramps up over the first 0.4 s)."""
    return TRAIN_V * tt * ease(tt / 0.4) if tt < 0.4 else TRAIN_V * tt

def _arrival_times():
    out = []
    for k in range(4):
        need = BAY_CX[k] - TRAIN_START[k]
        tt = 0.0
        while train_dist(tt) < need: tt += 0.002
        out.append(tt)
    return out

ARR_T = _arrival_times()                      # seconds after the train starts moving
PARK_LEN = ARR_T[3] + TRAIN_TURN              # until the last trailer is in its bay
PIECES = [("HEADER", "#fdba74"), ("DATA 1", "#cbd5e1"), ("DATA 2", "#cbd5e1"), ("DATA 3", "#cbd5e1")]

def piece_svg(k, x, y, s, rot, op=1.0):
    return cab(x, y, s, op, False, rot) if k == 0 else trailer(x, y, k, s, op, rot)

def scene5(t, T, D, L):
    o = world()
    cab_x = lerp(-120, 1000, ease(prog(t, T[2] - 0.1, T[3] + 0.9 - (T[2] - 0.1))))
    arr = [(T[3], D[3], 0.05, 0.42), (T[3], D[3], 0.5, 0.9), (T[5], D[5], 0.0, 0.2)]
    t0 = T[5] + 0.34 * D[5]                          # the coupled lorry starts to roll
    ev = [T[3] + 0.9] + [Tb + b * Db for Tb, Db, a, b in arr] + [t0 + PARK_LEN]
    tt = t - t0
    # how far each piece has turned into its bay (0 = on the lane, 1 = parked)
    turn = [ease((tt - ARR_T[k]) / TRAIN_TURN) if tt > 0 else 0.0 for k in range(4)]
    # bays: reservations dissolve as each piece parks
    for i in range(4):
        tag = PIECES[i] if turn[i] > 0.95 else None
        o.append(bay(i, 0.6, res=1 - turn[i], tag=tag))
    # ghosts: nothing is in a bay until the lorry is assembled
    gh = ease(fr(t, T[4], D[4], 0.3, 0.6)) * (1 - ease(prog(t, T[5], 0.4))) * 0.28
    for k in range(4):
        o.append(piece_svg(k, BAY_CX[k], BAY_CY, 1.15, -90, gh))
    nb = ease(fr(t, T[4], D[4], 0.3, 0.6)) * (1 - ease(prog(t, T[5], 0.4)))
    if nb > 0.01:
        o.append(PILL(BAY_CX[0] + 70, 566, 240, 40, "NOT IN A BAY YET", RED, "#fff", 22, 800, op=nb))
    # opening text (beat 0)
    ta = pop(t, T[0] + 0.2, 0.5) * (1 - ease(prog(t, T[1], 0.4)))
    if ta > 0.01:
        o.append(G(TX(0, 0, "Not everything is a motorbike.", 56, TXT, "middle", 800), 600, 330, min(ta, 1), 0, min(ta, 1)))
        o.append(G(motorbike(0, 0, 0, CARC[0], 2.2) + cross(0, 0, 130, RED), 600, 470, 1, 0, min(ta, 1)))
    # timeline
    tl_a = ease(prog(t, T[1], 0.6))
    o.append(timeline5(t, ev, tl_a, ease(fr(t, T[6], D[6], 0.15, 0.6)), ease(fr(t, T[6], D[6], 0.2, 0.4))))
    # vehicles
    if tt <= 0:
        if t >= T[2]:
            o.append(cab(cab_x, LANE_Y, 1.0, 1.0, t < T[6]))
        for k, (Tb, Db, a, b) in enumerate(arr):
            if t >= Tb + a * Db:
                o.append(trailer(lerp(-120, 1000 + SLOTS[k], ease(fr(t, Tb, Db, a, b))), LANE_Y, k + 1))
        cf = pop(t, ev[3] + 0.1, 0.5) * (1 - ease(prog(t, ev[3] + 0.9, 0.4)))
        if cf > 0.01:
            o.append(G(PILL(-100, -22, 200, 44, "COUPLED!", GREEN, "#052e16", 26, 800), 800, 545, cf, 0, min(cf, 1)))
    else:
        d = train_dist(tt)
        for k in range(4):
            x = min(TRAIN_START[k] + d, BAY_CX[k])
            y = lerp(LANE_Y, BAY_CY, turn[k]); rot = -90 * turn[k]; s = lerp(1.0, 1.15, turn[k])
            o.append(piece_svg(k, x, y, s, rot))
    # barrier: open while the train passes the gate
    b_open = ease(prog(t, t0 - 0.6, 0.4)) * (1 - ease(prog(t, t0 + 1.0, 0.4)))
    o.append(barrier(b_open))
    # the car park is full
    fa = pop(t, ev[4] + 0.15, 0.5)
    if fa > 0.01:
        o.append(G(PILL(-190, -30, 380, 60, "CAR PARK FULL  ·  4 / 4", GOLD, "#0f172a", 30, 800), 1490, 640, max(fa, 0.01), 0, min(fa, 1)))
    o.append(label_pill(60, 760, 420, "LORRY  =  WRITE request", pop(t, T[2] + 0.5, 0.4), "#fed7aa"))
    o.append(label_pill(60, 815, 620, "cab = header   ·   3 trailers = 3 data beats", pop(t, T[3] + 0.3, 0.4), "#fed7aa"))
    return "".join(o)

def ghost_pieces(a, ks=(0, 1, 2, 3)):
    """faint cab/trailers sitting in their (future) bays: cab -> bay 1, trailers 1..3 -> bays 2..4."""
    if a <= 0.01: return ""
    return "".join(piece_svg(k, BAY_CX[k], BAY_CY, 1.15, -90, a) for k in ks)

# ================================================================== SCENE 6
def scene6(t, T, D, L):
    o = world()
    tear_t = T[1] + 0.50 * D[1]
    fly_t = T[1] + 0.14 * D[1]
    r0 = 1 - ease(prog(t, tear_t, 0.4))
    for i in range(4):
        tag = ("EMPTY", "#94a3b8") if (i == 0 and t >= T[2] + 0.3 * D[2]) else None
        o.append(bay(i, 0.6, res=(r0 if i == 0 else 1.0), tag=tag))
    gh = ease(fr(t, T[2], D[2], 0.4, 0.8)) * 0.28
    o.append(ghost_pieces(gh))
    # lorry: cab in at beat 0, trailers trickling in
    cab_x = lerp(-120, 1000, ease(prog(t, T[0], T[1] + 0.1 * D[1] - T[0])))
    o.append(cab(cab_x, LANE_Y, 1.0, 1.0, t < fly_t))
    for k, (Tb, Db) in enumerate([(T[2], D[2]), (T[3], D[3])]):      # 3rd trailer never arrives: still assembling
        if t >= Tb + 0.3 * Db:
            o.append(trailer(lerp(-120, 1000 + SLOTS[k], ease(fr(t, Tb, Db, 0.3, 0.7))), LANE_Y, k + 1))
    o.append(barrier(0.0))
    # permit flies to the gatekeeper and is torn up
    o.append(fly(t, fly_t, 0.28 * D[1], (1000, LANE_Y), (990, 770), (1050, 700), 1.0, 1.3))
    o.append(tear(990, 775, prog(t, tear_t, 1.0)))
    tp = pop(t, tear_t, 0.4) * (1 - ease(prog(t, T[2] + 0.6, 0.4)))
    if tp > 0.01:
        o.append(G(PILL(-190, -24, 380, 48, "TORN UP AT THE GATE", RED, "#fff", 26, 800), 700, 530, min(tp, 1), 0, min(tp, 1)))
    # clipboard
    a_c = ease(prog(t, T[0], 0.9)); ty = -(1 - a_c) * 520
    pl = 0.4 + 0.6 * pulse(t, .9)
    pv = pop(t, tear_t, 0.5)
    pk = pop(t, T[3] + 0.35 * D[3], 0.5)
    tt = pop(t, T[4] + 0.15 * D[4], 0.5)
    gl = {}
    if T[3] + 0.2 * D[3] <= t < T[3] + 0.5 * D[3]: gl = {"permits": (GOLD, pl)}
    elif T[3] + 0.5 * D[3] <= t < T[4]: gl = {"parked": (BLUE, pl)}
    elif t >= T[4]: gl = {"total": (RED, pl)}
    rows = [
        dict(label="idle", permits="4", parked="0", total="4", mark="ok", op=ease(prog(t, T[0] + 0.8, 0.5))),
        dict(label="cab at gate — permit torn up", permits="3", parked="0", total="3", mark="bad",
             op=ease(prog(t, T[1] - 0.2, 0.5)), pop={"permits": pv, "parked": pk, "total": tt},
             colors={"total": RED_INK}, glow=gl, tint=RED if t >= T[4] else None,
             note=("THE LIE", RED) if t >= T[3] + 0.7 * D[3] else None,
             note_op=pop(t, T[3] + 0.7 * D[3], 0.4)),
    ]
    o.append(ledger(rows, h=270, ty=ty))
    # still needs a bay
    ar = ease(fr(t, T[4], D[4], 0.45, 0.85))
    if ar > 0.01:
        o.append(f'<path d="M1060 630 Q1215 640 1225 566" stroke="{RED}" stroke-width="6" fill="none" stroke-dasharray="14 10" opacity="{ar:.2f}"/>'
                 f'<polygon points="1211,572 1239,572 1225,546" fill="{RED}" opacity="{ar:.2f}"/>')
        o.append(TX(1500, 650, "the cab still needs its bay", 30, RED, "middle", 700, op=ar))
    # banners
    ba = pop(t, T[5] + 0.2, 0.5)
    if ba > 0.01:
        right = t >= T[6]
        if not right:
            inner = (PILL(-170, -84, 340, 40, "GOLDEN RULE BROKEN", RED, "#fff", 24, 800) +
                     TX(-40, 22, "3 + 0 = 3", 74, RED, "middle", 800) + cross(200, 0, 44, RED) +
                     TX(0, 72, "the total should stay 4", 32, MUTE, "middle", 500))
        else:
            inner = (TX(0, 8, "RIGHT NOW", 74, RED, "middle", 800) +
                     TX(0, 64, "he is about to do his arithmetic", 32, TXT, "middle", 500))
        o.append(top_box(ba, inner, RED, "#2a0f10"))
    if t >= T[6]:
        o.append(booth(1.0, pl))
        qa = pop(t, T[6] + 0.3, 0.5)
        o.append(G(bubble_up(-190, -38, 380, 76, "Time to do the sum...", 28), 990, 905, max(qa, 0.01), 0, min(qa, 1)) if qa > 0.01 else "")
    return "".join(o)

# ================================================================== SCENE 7
def scene7(t, T, D, L):
    o = world(depot_on=False)
    post_t = T[2] + 0.45 * D[2]
    res0 = ease(prog(t, post_t + 0.6, 0.5))
    for i in range(4):
        if i == 0:
            o.append(bay(0, 0.6, res=res0, res_pop=pop(t, post_t + 0.6, 0.5)))
            lie = ease(prog(t, T[0], 0.5)) * (1 - res0)
            if lie > 0.01:
                o.append(RECT(BAY_CX[0] - 67, BAY_TOP + 8, 134, 224, "none", rx=6, stroke=RED, sw=4, op=lie, dash="16 10") +
                         TX(BAY_CX[0], 440, "?", 90, RED, "middle", 800, op=lie))
            if res0 > 0.01:
                pass
                o.append(RECT(BAY_CX[0] - 71, BAY_TOP + 4, 142, 232, "none", rx=6, stroke=RED, sw=6, op=res0 * (0.5 + 0.5 * pulse(t, .8))))
        else:
            o.append(bay(i, 0.6, res=1.0))
    ga = ease(prog(t, T[0] + 0.3, 0.6))
    o.append(ghost_pieces(0.22 * ga, (1, 2, 3)))
    o.append(ghost_pieces(ga * (0.22 + 0.25 * res0), (0,)))
    # lorries: A at the gate, B and C arrive in the last beat
    o.append(cab(1000, LANE_Y) + trailer(1000 + SLOTS[0], LANE_Y, 1) + trailer(1000 + SLOTS[1], LANE_Y, 2))
    bt = T[5] + 0.15 * D[5]; ct = T[5] + 0.5 * D[5]
    for (t0, cx) in ((bt, 660), (ct, 430)):
        u = ease(prog(t, t0, 0.9))
        if u > 0.01:
            dx = -(1 - u) * 500
            o.append(cab(cx + dx, LANE_Y) + trailer(cx + dx - 104, LANE_Y, 1))
            o.append(PILL(cx + dx - 120, 744, 240, 38, "not on his clipboard", RED, "#fff", 20, 700, op=u))
    o.append(barrier(0.0))
    # left: formula panel + table
    a_c = ease(prog(t, T[0], 0.9)); ty = -(1 - a_c) * 520
    f1 = ease(fr(t, T[1], D[1], 0.15, 0.5)); f2 = ease(fr(t, T[2], D[2], 0.1, 0.4)); f3 = ease(fr(t, T[2], D[2], 0.45, 0.75))
    p = paper(90, 240, "check_and_release_request_credits()", True, True)
    p += mono_parts(100, 226, [("free_space", GREEN_INK), (" = 4 - ", INK), ("0", BLUE_INK), (" = 4", GREEN_INK)], 34, "start", 700, f1)
    p += TX(560, 226, "← 0 cars parked", 22, "#64748b", "start", 600, op=f1)
    p += mono_parts(100, 276, [("new_permits", GREEN_INK), (" = 4 - ", INK), ("3", GOLD_INK), (" = 1", GREEN_INK)], 34, "start", 700, f2)
    p += TX(590, 276, "← 3 permits out", 22, "#64748b", "start", 600, op=f2)
    p += TX(100, 318, "→ posts 1 more permit", 30, RED_INK, "start", 800, MONO, f3)
    o.append(G(p, 0, ty))
    pv = pop(t, post_t + 0.2, 0.5); tv = pop(t, T[3] + 0.3, 0.5)
    rows = [
        dict(label="cab at gate (the lie)", permits="3", parked="0", inbound="1", total="3", op=ease(prog(t, T[0] + 0.8, 0.5)),
             colors={"total": RED_INK}),
        dict(label="after issuing", permits="4", parked="0", inbound="1", total="5 on 4 bays", op=ease(prog(t, post_t, 0.5)),
             pop={"permits": pv, "parked": pv, "inbound": pv, "total": tv}, colors={"total": RED_INK}, size={"total": 22},
             tint=RED if t >= T[3] else None),
    ]
    o.append(ledger(rows, y0=350, h=210, title=None, cols=("permits", "parked", "inbound", "total"), ty=ty, clip=False))
    # ticket leaves for the depot
    o.append(fly(t, post_t, 1.4, BOOTH, (-80, 470), (500, 900), 1.0, 0.8))
    # banners
    ba = pop(t, T[3] + 0.1, 0.5)
    if ba > 0.01:
        n = 5 + (1 if t >= bt + 0.6 else 0) + (1 if t >= ct + 0.6 else 0)
        inner = (TX(0, 30, f"{n} CLAIMS ON 4 BAYS", 66, RED, "middle", 800) +
                 TX(0, 76, "4 permits out  +  the lorry he crossed off" if n == 5 else "4 permits out  +  every lorry he crossed off", 30, TXT, "middle", 500))
        o.append(top_box(ba, inner, RED, "#2a0f10"))
    # crossed-off arrow (beat 4)
    ca = ease(fr(t, T[4], D[4], 0.35, 0.75))
    if ca > 0.01:
        o.append(f'<path d="M1060 630 Q1215 640 1225 566" stroke="{RED}" stroke-width="6" fill="none" stroke-dasharray="14 10" opacity="{ca:.2f}"/>'
                 f'<polygon points="1211,572 1239,572 1225,546" fill="{RED}" opacity="{ca:.2f}"/>')
        o.append(TX(1500, 640, "same bay, promised twice", 30, RED, "middle", 700, op=ca))
    return "".join(o)

# ================================================================== SCENE 8
def code_panel(x, y, w, lines, hl, a):
    if a <= 0.01: return ""
    h = 34 + 44 * len(lines)
    o = RECT(x, y, w, h, "#020617", rx=16, stroke="#334155", sw=3)
    for i, ln in enumerate(lines):
        yy = y + 30 + 44 * i
        if i == hl: o += RECT(x + 10, yy - 4, w - 20, 40, RED, rx=8, op=.22)
        ln = ln.replace("    ", "    ")
        o += TX(x + 26, yy + 26, ln, 25, "#fca5a5" if i == hl else "#e2e8f0", "start", 500, MONO)
    return G(o, op=a)

def scene8(t, T, D, L):
    o = world()
    cols = ["#94a3b8", "#a1a1aa", "#78716c", "#a8a29e"]
    for i in range(4):
        o.append(bay(i, 0.6, car_color=cols[i]))
    # the car: arrives (b0), reverses away (b3)
    x = lerp(-140, 1010, ease(fr(t, T[0], D[0], 0.05, 0.55)))
    op = 1.0
    if t >= T[3]:
        u = ease(fr(t, T[3], D[3], 0.1, 0.9)); x = lerp(1010, 640, u); op = 1 - ease(fr(t, T[3], D[3], 0.45, 1.0))
    if t < T[4] - 0.2:
        o.append(car(x, LANE_Y, 0, CARC[2], 1.0, op * ease(prog(t, T[0], .3)), True))
    o.append(barrier(0.0))
    va = pop(t, T[0] + D[0] * 0.5, 0.4) * (1 - ease(prog(t, T[1], 0.4)))
    if va > 0.01:
        o.append(G(PILL(-170, -24, 340, 48, "VALID PERMIT", GREEN, "#052e16", 26, 800), 930, 540, min(va, 1), 0, min(va, 1)) + check(1120, 520, 30, GREEN, min(va, 1)))
    nb = pop(t, T[0] + D[0] * 0.75, 0.4) * (1 - ease(prog(t, T[3] + 0.5 * D[3], 0.4)))
    if nb > 0.01:
        o.append(G(PILL(-100, -26, 200, 52, "NO BAY", RED, "#fff", 30, 800), 1010, 590, min(nb, 1), 0, min(nb, 1)))
    # what he does NOT do
    lst_a = ease(prog(t, T[1], 0.5)) * (1 - ease(prog(t, T[5] - 0.1, 0.4)))
    if lst_a > 0.01:
        items = [("No alarm", T[1] + 0.8), ("No retry sent back to the depot", T[2] + 0.3), ("No complaint logged", T[2] + 0.3 * D[2] + 1.0)]
        box = RECT(1120, 30, 760, 180, "#0f172a", rx=20, stroke="#334155", sw=3)
        for k, (txt, ts) in enumerate(items):
            u = pop(t, ts, 0.4)
            if u > 0.01:
                box += cross(1160, 82 + 50 * k, 30, RED, min(u, 1)) + TX(1200, 94 + 50 * k, txt, 32, TXT, "start", 600, op=min(u, 1))
        o.append(G(box, op=lst_a))
    gone = pop(t, T[3] + 0.3 * D[3], 0.5)
    if gone > 0.01 and t < T[4]:
        o.append(G(TX(0, 0, "GONE. FOREVER.", 52, RED, "middle", 800), 780, 540, min(gone, 1), 0, min(gone, 1)))
    # code panel
    ca = ease(prog(t, T[3] - 0.2, 0.6))
    lines = ["if (!compl_cm[port]->can_receive_request()) {",
             '    log_LOW() << "Insufficient request credits";',
             "    return;                    // <-- the car drives away",
             "}"]
    hl = 2 if t >= T[3] else -1
    o.append(code_panel(60, 70, 860, lines, hl, ca))
    # depot thinks it arrived (beat 4)
    ba = pop(t, T[4] + 0.2, 0.5)
    if ba > 0.01:
        o.append(G(bubble(-200, -40, 400, 80, "Delivered!", -110, 62, 1.0, 34) + check(120, 0, 34, GREEN),
                   480, 375, max(ba, 0.01), 0, min(ba, 1)))
    # final equation
    fa = pop(t, T[5] + 0.3, 0.5)
    if fa > 0.01:
        inner = (TX(0, -10, "1 dropped request", 48, RED, "middle", 800) +
                 TX(0, 44, "= 1 “Unmatched” packet", 48, TXT, "middle", 800) +
                 TX(0, 82, "clean run: Unmatched = 0", 24, MUTE, "middle", 500, MONO))
        o.append(top_box(fa, inner, RED, "#2a0f10"))
    return "".join(o)

# ================================================================== SCENE 9
CELL_W, CELL_H = 50, 46

def grid_cell(c, r): return 68 + c * 54, 212 + r * 56

def scene9(t, T, D, L):
    o = [background()]
    slide = ease(fr(t, T[3], D[3], 0.0, 0.25))
    dx = 460 * (1 - slide)
    dim = 1 - 0.55 * ease(fr(t, T[4], D[4], 0.0, 0.3))
    la = ease(prog(t, T[0], 0.7))
    left = RECT(60, 200, 880, 470, ASPH, rx=26, stroke="#334155", sw=4)
    lie_c, lie_r = 5, 2
    for r in range(8):
        for c in range(16):
            x, y = grid_cell(c, r)
            u = ease(prog(t, T[1] + D[1] * 0.1 + (r * 16 + c) * 0.012, 0.35))
            if u <= 0.01: continue
            is_lie = (c == lie_c and r == lie_r)
            slack = ease(fr(t, T[2], D[2], 0.5, 0.8))
            fill = "#243044"
            if slack > 0.01 and not is_lie: fill = "#1e3a34"
            left += RECT(x, y, CELL_W, CELL_H, fill, rx=5, stroke="#cbd5e1", sw=2, op=u, sop=.6)
    lie_u = ease(fr(t, T[2], D[2], 0.15, 0.4))
    if lie_u > 0.01:
        x, y = grid_cell(lie_c, lie_r)
        left += RECT(x - 3, y - 3, CELL_W + 6, CELL_H + 6, RED, rx=6, op=.55 * lie_u, stroke=RED, sw=4, sop=lie_u)
        left += TX(x + CELL_W / 2, y + 32, "1", 30, "#fff", "middle", 800, op=lie_u)
    # mini road strip + lorry
    left += RECT(60, 715, 880, 62, ROAD, rx=6)
    lx = 700
    la_ = min(1, lie_u * 1.5)
    left += cab(lx, 746, .55, la_) + "".join(trailer(lx + SLOTS[k] * .55, 746, k + 1, .55, la_) for k in range(3))
    left += TX(500, 812, "1 lorry assembling at the gate", 26, TXT, "middle", 600, op=lie_u)
    o.append(G(left, dx, 0, 1, 0, la * dim))
    # pills / labels on the left block
    p1 = pop(t, T[1] + 0.2, 0.5) * (1 - ease(prog(t, T[2] + 0.2 * D[2], 0.3)))
    if p1 > 0.01:
        o.append(G(PILL(-190, -32, 380, 64, "128 BAYS", "#1e293b", GOLD, 34, 800, stroke=GOLD), 500 + dx, 150, p1, 0, min(p1, 1)))
    p2 = ease(fr(t, T[2], D[2], 0.5, 0.75)) * dim
    if p2 > 0.01:
        o.append(PILL(500 + dx - 260, 118, 520, 64, "always slack  =  invisible", "#0f2a24", GREEN, 32, 800, stroke=GREEN, op=p2))
    # captions under blocks
    c1 = ease(fr(t, T[2], D[2], 0.6, 0.9))
    if c1 > 0.01:
        o.append(mono_parts(500 + dx, 868, [("128 bays", TXT), (" — lie of 1 = ", MUTE), ("0.8%", GREEN)], 30, "middle", 700, c1 * dim))
    # right block: the four-bay car park
    ra = ease(fr(t, T[3], D[3], 0.2, 0.5))
    if ra > 0.01:
        rt = ""
        rt += park_frame(1.0)
        for i in range(4):
            rt += bay(i, 0.6, res=(1.0 if i > 0 else 0.0))
        lu = ease(fr(t, T[3], D[3], 0.45, 0.65))
        x0 = BAY_CX[0] - 75
        rt += RECT(x0 + 3, BAY_TOP + 3, 144, 234, RED, rx=6, op=.55 * lu, stroke=RED, sw=6, sop=lu * (0.6 + 0.4 * pulse(t, .8)))
        rt += TX(BAY_CX[0], 440, "1", 90, "#fff", "middle", 800, op=lu)
        rt += RECT(940, 580, 162, 140, ROAD) + cab(1084, LANE_Y, .4) + "".join(trailer(1084 + SLOTS[k] * .4, LANE_Y, k + 1, .4) for k in range(3))
        o.append(G(rt, op=ra))
        o.append(PILL(1490 - 190, 140, 380, 64, "4 BAYS", "#1e293b", GOLD, 34, 800, stroke=GOLD, op=ra))
        c2 = ease(fr(t, T[3], D[3], 0.6, 0.85))
        o.append(mono_parts(1490, 868, [("4 bays", TXT), (" — lie of 1 = ", MUTE), ("25%", RED)], 30, "middle", 700, c2))
        ov = ease(fr(t, T[3], D[3], 0.8, 0.95))
        if ov > 0.01:
            o.append(TX(1490, 640, "OVERFLOWS CONSTANTLY", 44, RED, "middle", 800, op=ov))
    # closing card
    ba = pop(t, T[4] + 0.2, 0.5)
    if ba > 0.01:
        inner = (TX(0, 8, "THE BUG WAS ALWAYS THERE", 54, GOLD, "middle", 800) +
                 TX(0, 64, "shrinking the buffer just removed the padding", 32, TXT, "middle", 500))
        o.append(top_box(ba, inner))
    return "".join(o)
