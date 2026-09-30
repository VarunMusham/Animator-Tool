"""Part 3: scene 18 (the numbers), 19 (the takeaway), appendix A (reproducing it), appendix B (checking the fix)."""
from .scenes_10_17 import *
from .scenes_10_17 import _nb

def typed(s, u): return s[:int(len(s) * clamp(u) + 0.0001)]

# ================================================================== SCENE 18  the numbers
BASE_Y, MAXH, MAXV = 540, 300, 1234

def bar_set(xs, vals, colr, us, label_col, bw=58):
    o = ""
    for x, v, u in zip(xs, vals, us):
        if u <= 0.01: continue
        h = max(6.0, MAXH * v / MAXV * u) if v else 6.0
        o += RECT(x - bw / 2, BASE_Y - h, bw, h, colr, rx=6, op=.95)
        shown = int(round(v * u)) if v else 0
        o += TX(x, BASE_Y - h - 12, f"{shown}", 28, label_col, "middle", 800, MONO, min(1.0, u * 2))
    return o

def panel18(x, y, w, h, title, sub):
    return (RECT(x, y, w, h, "#0f172a", rx=22, stroke="#334155", sw=3) + TX(x + w / 2, y + 52, title, 30, TXT, "middle", 700) +
            TX(x + w / 2, y + 88, sub, 22, MUTE, "middle", 600, MONO) +
            f'<line x1="{x + 30}" y1="{BASE_Y}" x2="{x + w - 30}" y2="{BASE_Y}" stroke="#475569" stroke-width="3"/>')

CHECKS = [("req_DROPPED = 0      orgbeat_DROPPED = 0", True), ("delivery_deficit (sent − received) = 0", True),
          ("all residual queues empty at end of simulation", False), ("credits returned to full at end of simulation", False),
          ("full unit regression: no new failures", False)]

def scene18(t, T, D, L):
    o = [background()]
    # ---- panel 1: before / after
    a1 = ease(prog(t, T[0], 0.6))
    xb = [150, 240, 330, 420, 510]; xa = [650, 740, 830]
    usb = [ease(fr(t, T[0], D[0], 0.14 + 0.05 * i, 0.30 + 0.05 * i)) for i in range(5)]
    usa = [ease(fr(t, T[0], D[0], 0.72 + 0.05 * i, 0.85 + 0.05 * i)) for i in range(3)]
    p1 = panel18(60, 110, 880, 490, "Unmatched packets per run", "request-channel checker   max_buffer_size = 4")
    p1 += bar_set(xb, [4, 611, 873, 1182, 1234], RED, usb, "#fecaca") + bar_set(xa, [0, 0, 0], GREEN, usa, "#bbf7d0")
    p1 += TX(330, BASE_Y + 44, "BEFORE  ·  debit at the gate", 24, "#fca5a5", "middle", 700, op=ease(fr(t, T[0], D[0], 0.3, 0.45)))
    p1 += TX(740, BASE_Y + 44, "AFTER  ·  debit at the push", 24, "#86efac", "middle", 700, op=ease(fr(t, T[0], D[0], 0.85, 0.95)))
    o.append(G(p1, op=a1))
    # ---- panel 2: controlled A/B
    a2 = ease(prog(t, T[1], 0.6))
    xg = [1110, 1200, 1290]; xp = [1560, 1650, 1740]
    usg = [ease(fr(t, T[1], D[1], 0.30 + 0.07 * i, 0.50 + 0.07 * i)) for i in range(3)]
    usp = [ease(fr(t, T[1], D[1], 0.70 + 0.05 * i, 0.82 + 0.05 * i)) for i in range(3)]
    p2 = panel18(980, 110, 880, 490, "Controlled A/B", "only the request debit location changed — data debit untouched")
    p2 += bar_set(xg, [734, 537, 874], RED, usg, "#fecaca") + bar_set(xp, [0, 0, 0], GREEN, usp, "#bbf7d0")
    p2 += TX(1200, BASE_Y + 44, "debit at the admission gate", 22, "#fca5a5", "middle", 700, op=ease(fr(t, T[1], D[1], 0.45, 0.6)))
    p2 += TX(1650, BASE_Y + 44, "debit immediately before the push", 22, "#86efac", "middle", 700, op=ease(fr(t, T[1], D[1], 0.8, 0.95)))
    o.append(G(p2, op=a2))
    # ---- supporting measurements
    for i, (txt, mono) in enumerate(CHECKS):
        ts = T[2] + 0.4 + D[2] * 0.14 * i
        u = ease(prog(t, ts, 0.45))
        if u <= 0.01: continue
        col = 0 if i < 3 else 1; row = i if i < 3 else i - 3
        x = 60 + col * 900; y = 640 + row * 66
        card = RECT(x, y, 860, 54, "#052e16", rx=14, stroke=GREEN, sw=3) + check(x + 38, y + 28, 28, GREEN) + \
               TX(x + 76, y + 37, _nb(txt), 24 if mono else 26, "#bbf7d0", "start", 600, MONO if mono else SANS)
        o.append(G(card, (1 - u) * 40, 0, 1, 0, u))
    # ---- the signature of a race
    wob = ease(fr(t, T[3], D[3], 0.0, 0.5))
    if wob > 0.01 and t < T[4] + D[4] * 0.05:
        o.append(RECT(100, 222, 450, 326, "none", rx=18, stroke=GOLD, sw=5, op=wob * (0.45 + 0.55 * pulse(t, .9)), dash="16 10"))
        o.append(TX(820, 290, "same build · same config", 26, GOLD, "middle", 800, op=wob))
        o.append(TX(820, 326, "4  …  1234", 34, GOLD, "middle", 800, MONO, op=wob))
    if t >= T[3]:
        two = t >= T[4] + D[4] * 0.3
        txt = "REASON ABOUT THE INVARIANT — NOT ONE BAD PACKET" if two else ("THE SIGNATURE OF A RACE" if t < T[4] else "TRIGGERED BY TIMING, NOT BY A PACKET")
        ba = pop(t, T[3] + 0.2, 0.5) if t < T[4] else 1.0
        w = 1000 if two else 820
        o.append(G(PILL(-w / 2, -30, w, 60, txt, "#1c1608", GOLD, 30, 800, stroke=GOLD), 960, 56, max(min(ba, 1.0), 0.01), 0, min(ba, 1)))
    return "".join(o)

# ================================================================== SCENE 19  the takeaway
def quote_svg(op=1.0):
    lines = [("Every credit debit belongs", TXT), ("immediately before the push", GOLD), ("that creates the occupancy it accounts for.", TXT)]
    return "".join(TX(0, -70 + 80 * i, s, 62, c, "middle", 800, op=op) for i, (s, c) in enumerate(lines))

def cyc(x): return 0.5 - 0.5 * math.cos(2 * math.pi * x)

def gauge(x, top, bot, level, colr, label):
    h = bot - top
    o = RECT(x - 65, top, 130, h, "#0f172a", rx=16, stroke="#475569", sw=3)
    fh = h * level / 4.0
    o += RECT(x - 57, bot - fh - 8, 114, max(fh, 0.1), colr, rx=10, op=.85) if fh > 1 else ""
    o += TX(x, top - 22, label, 28, colr, "middle", 800)
    return o

def scene19(t, T, D, L):
    o = [background()]
    # ---- beat 0 + 1: the takeaway and where it does NOT belong
    q_in = ease(prog(t, T[0], 0.7))
    shrink = ease(prog(t, T[1], 0.7)); q_out = 1 - ease(prog(t, T[2], 0.5))
    cy = lerp(450, 150, shrink); s = lerp(1.0, 0.5, shrink)
    o.append(G(quote_svg(), 960, cy, s, 0, q_in * q_out))
    if t < T[2] + 0.5:
        for k, (txt, colr, ok, tk) in enumerate((("AT ADMISSION", RED, False, 0.05), ("“SOMEWHERE LATER”", RED, False, 0.4), ("AT THE PUSH", GREEN, True, 0.7))):
            u = pop(t, T[1] + D[1] * tk, 0.45) * q_out
            if u > 0.01:
                w = 540 if ok else (640 if k == 1 else 520)
                pill = PILL(-w / 2, -40, w, 80, txt, "#052e16" if ok else "#2a0f10", GREEN if ok else RED, 34, 800, stroke=colr) + \
                       (check(w / 2 - 44, 0, 38, GREEN) if ok else cross(w / 2 - 44, 0, 38, RED))
                o.append(G(pill, 340 + 620 * k, 520, max(u, 0.01) * (1.12 if ok else 1.0), 0, min(u, 1)))
    # ---- beat 2: two halves of one number
    g_in = ease(prog(t, T[2], 0.6)) * (1 - ease(prog(t, T[3], 0.5)))
    if g_in > 0.01:
        tt = t - T[2]
        lagu = ease(fr(t, T[2], D[2], 0.45, 0.95))
        sync_phase = t < T[2] + D[2] * 0.45
        ph = tt / 2.4
        lag = 0.0 if sync_phase else 0.10 + 0.32 * lagu
        A = 4 * cyc(ph); B = 4 * cyc(ph - lag)
        top, bot = 250, 640
        gs = gauge(700, top, bot, A, GOLD, "CREDIT COUNTER") + gauge(1220, top, bot, B, BLUE, "BUFFER")
        diff = abs(A - B)
        ya = bot - (bot - top) * A / 4 - 8; yb = bot - (bot - top) * B / 4 - 8
        if diff > 0.25:
            gs += f'<line x1="1285" y1="{ya:.0f}" x2="1400" y2="{ya:.0f}" stroke="{GOLD}" stroke-width="3" stroke-dasharray="8 6"/>'
            gs += f'<line x1="1285" y1="{yb:.0f}" x2="1400" y2="{yb:.0f}" stroke="{BLUE}" stroke-width="3" stroke-dasharray="8 6"/>'
            gs += f'<path d="M1380 {ya:.0f} V{yb:.0f}" stroke="{RED}" stroke-width="8" stroke-linecap="round"/>'
            gs += TX(1420, (ya + yb) / 2 + 10, "the lie", 34, RED, "start", 800)
        eq = ("=" if diff < 0.25 else "≠")
        gs += TX(960, 470, eq, 110, GREEN if diff < 0.25 else RED, "middle", 800)
        gs += TX(960, 190, "two halves of ONE number", 40, TXT, "middle", 800)
        gs += TX(960, 740, "move together  →  no lie" if sync_phase else "the bigger the gap, the bigger the lie", 34,
                 GREEN if sync_phase else RED, "middle", 700)
        o.append(G(gs, op=g_in))
    # ---- beat 3: hidden behind 124 spare bays
    c_in = ease(prog(t, T[3], 0.6))
    if c_in > 0.01:
        gx0, gy0 = 496, 210
        spare = 1 - ease(fr(t, T[3], D[3], 0.62, 0.86))
        hi = ease(fr(t, T[3], D[3], 0.28, 0.45))
        grid = ""
        for r in range(8):
            for c in range(16):
                idx = r * 16 + c
                x = gx0 + c * 58; y = gy0 + r * 54
                u = ease(prog(t, T[3] + 0.1 + idx * 0.004, 0.3))
                if idx < 4:
                    grid += RECT(x, y, 52, 46, "#422006", rx=6, stroke=GOLD, sw=4, op=u)
                elif idx == 4:
                    bad = ease(fr(t, T[3], D[3], 0.45, 0.6))
                    grid += RECT(x, y, 52, 46, RED if bad > .5 else ("#1e3a34" if hi > .5 else "#243044"), rx=6, stroke=RED if bad > .5 else "#cbd5e1", sw=3 if bad > .5 else 2, op=u * (1 if bad > .5 else spare), sop=1)
                    grid += TX(x + 26, y + 33, "+1", 26, "#fff", "middle", 800, op=bad * u)
                else:
                    fill = "#1e3a34" if hi > .5 else "#243044"
                    grid += RECT(x, y, 52, 46, fill, rx=6, stroke="#cbd5e1", sw=2, op=u * spare, sop=.6)
        o.append(G(grid, op=c_in))
        o.append(TX(960, 150, "SHRINKING THE BUFFER EXPOSED THE BUG — IT DIDN'T CREATE IT", 34, GOLD, "middle", 800, op=c_in))
        s1 = hi * spare
        o.append(TX(960, 700, "124 spare bays  =  the padding that hid it", 34, GREEN, "middle", 700, op=s1 * c_in))
        s2 = ease(fr(t, T[3], D[3], 0.86, 0.98))
        o.append(TX(960, 700, "4 bays  ·  the defect was always there", 38, RED, "middle", 800, op=s2))
    return "".join(o)

# ================================================================== terminal helpers
def terminal(x, y, w, h, title, op=1.0):
    o = RECT(x, y, w, h, "#020617", rx=18, stroke="#334155", sw=3) + RECT(x, y, w, 48, "#0f172a", rx=18)
    for k, c in enumerate(("#f87171", "#fbbf24", "#34d399")): o += f'<circle cx="{x + 30 + 28 * k}" cy="{y + 24}" r="9" fill="{c}"/>'
    o += TX(x + w / 2, y + 32, title, 22, MUTE, "middle", 600, MONO)
    return G(o, op=op)

# ================================================================== APPENDIX A  reproducing it
def scene20(t, T, D, L):
    o = [background()]
    a = ease(prog(t, T[0], 0.6))
    o.append(terminal(160, 110, 1600, 640, "bash — ualink_upli", a))
    cmd = "bash run/soak.sh 40"
    u = ease(fr(t, T[0], D[0], 0.08, 0.40))
    o.append(TX(210, 210, "$", 34, GREEN, "start", 800, MONO, a) + TX(250, 210, typed(cmd, u), 34, TXT, "start", 700, MONO, a))
    cur = pulse(t, 0.9) > .5 and u < 1
    if cur: o.append(RECT(250 + len(typed(cmd, u)) * MONO_ADV * 34, 182, 16, 36, GREEN, op=a))
    # run counter
    rc = ease(fr(t, T[0], D[0], 0.42, 0.55))
    if rc > 0.01:
        n = min(40, 1 + int((t - (T[0] + 0.42 * D[0])) * 6.0))
        o.append(TX(210, 290, f"run {n}/40", 30, "#7dd3fc", "start", 600, MONO, rc) + TX(440, 290, "(time-lapse)", 24, MUTE, "start", 500, MONO, rc))
        bw = 1080 * n / 40
        o.append(RECT(210, 315, 1080, 14, "#1e293b", rx=7, op=rc) + RECT(210, 315, bw, 14, GREEN, rx=7, op=rc))
        o.append(G(PILL(-190, -30, 380, 60, "≈ 4–5 s per run", "#0f2744", BLUE, 30, 800, stroke=BLUE) + TX(0, 62, "verbosity = SC_NONE", 22, MUTE, "middle", 600, MONO), 1560, 270, max(rc, 0.01), 0, min(rc, 1)))
    # outputs
    files = [("/tmp/agentstack/anz.out", "summary, per-hit table, failure context", T[1] + 0.2),
             ("/tmp/agentstack/soak_hit_<i>.log", "full output of each failing run", T[1] + D[1] * 0.38),
             ("/tmp/agentstack/clean_probe.log", "a clean run, as a control", T[1] + D[1] * 0.68)]
    for k, (p, d, ts) in enumerate(files):
        uu = pop(t, ts, 0.45)
        if uu > 0.01:
            y = 430 + k * 64
            o.append(G(TX(210, y, p, 28, "#fcd34d", "start", 700, MONO) + TX(800, y, "—  " + d, 28, TXT, "start", 500), (1 - min(uu, 1)) * 30, 0, 1, 0, min(uu, 1)))
    # pre-fix hit rate
    hr = pop(t, T[2] + 0.3, 0.5)
    if hr > 0.01:
        o.append(G(PILL(-470, -34, 940, 68, "pre-fix: reproduces within a handful of runs", "#2a0f10", RED, 36, 800, stroke=RED), 960, 830, max(hr, 0.01), 0, min(hr, 1)))
    return "".join(o)

# ================================================================== APPENDIX B  checking the fix
GREP_LINES = ['grep -n "can_receive_request()\\|update_request_receive_trans\\|update_orgdata_receive_trans" \\',
              "  src/upli/upli_if.cpp \\",
              "  tb/common/ualink_top/application_layer.hpp"]

def scene21(t, T, D, L):
    o = [background()]
    a = ease(prog(t, T[0], 0.6))
    o.append(terminal(100, 100, 1720, 230, "bash — ualink_upli", a))
    tot = sum(len(s) for s in GREP_LINES)
    n = int(tot * ease(fr(t, T[0], D[0], 0.1, 0.85)))
    y = 175
    for i, ln in enumerate(GREP_LINES):
        seg = ln[:max(0, min(len(ln), n))]; n -= len(ln)
        if seg or i == 0:
            o.append((TX(146, y, "$", 26, GREEN, "start", 800, MONO, a) if i == 0 else "") + TX(180, y, _nb(seg), 26, TXT, "start", 600, MONO, a))
        y += 42
    # expected shape
    ta = ease(prog(t, T[1], 0.6))
    if ta > 0.01:
        x0, y0, w = 100, 370, 1720
        cols = [(150, "layer", "start"), (920, "gate (check only)", "middle"), (1260, "debit, READ path", "middle"), (1600, "debit, WRITE path", "middle")]
        tb = RECT(x0, y0, w, 250, "#0f172a", rx=20, stroke="#334155", sw=3)
        for cx, name, anc in cols: tb += TX(cx, y0 + 46, name.upper(), 22, MUTE, "start" if anc == "start" else "middle", 700)
        rows = [("upli_if.cpp", "1", "1", "1 request + 1 orgdata"), ("application_layer.hpp", "1", "1", "1 request + 1 orgdata")]
        for k, (nm, g, r, w_) in enumerate(rows):
            yy = y0 + 70 + k * 80
            ru = ease(fr(t, T[1], D[1], 0.25 + 0.25 * k, 0.5 + 0.25 * k))
            row = RECT(x0 + 16, yy, w - 32, 64, "#1e293b", rx=12) + TX(150, yy + 42, nm, 28, "#7dd3fc", "start", 700, MONO) + \
                  TX(920, yy + 44, g, 38, GREEN, "middle", 800) + TX(1260, yy + 44, r, 38, GREEN, "middle", 800) + TX(1600, yy + 42, w_, 28, GREEN, "middle", 700)
            tb += G(row, op=ru)
        o.append(G(tb, 0, (1 - ta) * 30, 1, 0, ta))
    # the two failure modes
    w1 = pop(t, T[2] + 0.2, 0.5)
    if w1 > 0.01:
        inner = RECT(0, 0, 1720, 86, "#2a0f10", rx=18, stroke=RED, sw=4) + cross(54, 43, 34, RED) + \
                TX(100, 38, "a gate but NO debit", 30, "#fecaca", "start", 800) + TX(100, 70, "credits are never returned  →  that side eventually stalls", 26, TXT, "start", 500) + \
                TX(1680, 54, "STALL", 40, RED, "end", 800)
        o.append(G(inner, 100, 670, 1, 0, min(w1, 1)))
    w2 = pop(t, T[3] + 0.2, 0.5)
    if w2 > 0.01:
        inner = RECT(0, 0, 1720, 86, "#2a0f10", rx=18, stroke=RED, sw=4) + cross(54, 43, 34, RED) + \
                TX(100, 38, "a debit INSIDE the gate", 30, "#fecaca", "start", 800) + TX(100, 70, "the debit fires at arrival again  →  the over-booking bug is back", 26, TXT, "start", 500) + \
                TX(1680, 54, "BUG BACK", 40, RED, "end", 800)
        o.append(G(inner, 100, 780, 1, 0, min(w2, 1)))
    return "".join(o)
