"""Generate the OTA core layout (Magic .mag) from Magic pcells + scripted wiring.  Units: 1 = 5 nm.
Chain (top to bottom):  hp header PMOS (S=vdda, D=vcp) / mp core PMOS (S=vcp, D=out, B=vcp) / mn core NMOS (D=out, S=vcn, B=gnd) / hn footer NMOS (D=vcn, S=gnd).
Same devices and sizes as common/amp_core.py (L, WN, WP, HDR_W, FTR_W), split into fingers."""
import sys, os, shutil
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import magparse as mp
B = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'build')
DEV = dict(mp='sky130_fd_pr__pfet_g5v0d10v5_8T3SAF', mn='sky130_fd_pr__nfet_g5v0d10v5_5P4MW7', hp='sky130_fd_pr__pfet_g5v0d10v5_7N2TME', hn='sky130_fd_pr__nfet_g5v0d10v5_XDK3YF')
GAP = 800            # 4 um between devices
BARH = 200           # M2 bar / strap width 1 um
R = []               # (layer, x1, y1, x2, y2)
LAB = []             # (layer, x, y, text)
def rect(layer, x1, y1, x2, y2): R.append((layer, int(x1), int(y1), int(x2), int(y2)))
def stack_m1_m2(cx, cy):
    """li pad, mcon, M1 pad, via1, M2 pad centred on (cx, cy)"""
    rect('locali', cx-70, cy-70, cx+70, cy+70); rect('viali', cx-29, cy-29, cx+29, cy+29)
    rect('metal1', cx-60, cy-60, cx+60, cy+60); rect('via1', cx-26, cy-26, cx+26, cy+26); rect('metal2', cx-60, cy-60, cx+60, cy+60)
def via_on_strip(cx, cy):
    rect('metal1', cx-40, cy-40, cx+40, cy+40); rect('via1', cx-26, cy-26, cx+26, cy+26)

info = {}
for t, f in DEV.items():
    d = mp.parse(f'{B}/{f}.mag'); L = d['layers']; bb = mp.bbox(L)
    dc = [k for k in L if k.endswith('diffc') and 'subdiff' not in k][0]
    xs = sorted((r[0] + r[2]) // 2 for r in L[dc]); ys = (min(r[1] for r in L[dc]), max(r[3] for r in L[dc]))
    ring = [k for k in L if 'subdiffcont' in k][0]; rr = mp.bbox({ring: L[ring]})
    m1 = [r for r in L['metal1'] if r[0] <= xs[0] and r[2] >= xs[0]]      # M1 of the first strip -> its y extent
    info[t] = dict(f=f, bb=bb, xs=xs, ys=ys, ring=rr, m1y=(min(r[1] for r in m1), max(r[3] for r in m1)), L=L)
# vertical placement (centres), bottom to top: hn, mn, mp, hp
cy = {}; y = 0
for t in ('hn', 'mn', 'mp', 'hp'):
    h = info[t]['bb'][3]; hb = -info[t]['bb'][1]
    y = y + hb if t == 'hn' else y + prev_h + GAP + hb
    cy[t] = y; prev_h = h
uses = ''.join(f"use {info[t]['f']}  {t}\ntimestamp 0\ntransform 1 0 0 0 1 {cy[t]}\nbox {info[t]['bb'][0]} {info[t]['bb'][1]} {info[t]['bb'][2]} {info[t]['bb'][3]}\n" for t in cy)
def strips(t):   # (x list of S strips, x list of D strips) by finger parity: D0 S1 D2 ...
    xs = info[t]['xs']; return [x for i, x in enumerate(xs) if i % 2 == 1], [x for i, x in enumerate(xs) if i % 2 == 0]
def bar(t, kind, top):
    """metal2 bar over S or D strips at the top or bottom end of the strips; returns (x1, x2, y)"""
    S, D = strips(t); xs = S if kind == 'S' else D
    m1lo, m1hi = info[t]['ys']           # diffusion-contact extent of the strips (the strip metal ends ~12 units beyond it)
    yv = cy[t] + (m1hi - 110 if top else m1lo + 110)
    for x in xs: via_on_strip(x, yv)
    rect('metal2', min(xs)-60, yv-BARH//2, max(xs)+60, yv+BARH//2)
    return min(xs), max(xs), yv
S_TOP = {'hp', 'mp'}                        # P devices: S top, D bottom;  N devices: D top, S bottom
bars = {}
for t in info:
    top_is_S = t in S_TOP
    bars[(t, 'S')] = bar(t, 'S', top_is_S); bars[(t, 'D')] = bar(t, 'D', not top_is_S)
def straps(netname, lo_bar, hi_bar, n):      # vertical M2 straps between two bars of the same net
    (xa1, xa2, ya), (xb1, xb2, yb) = lo_bar, hi_bar
    x1 = max(xa1, xb1) + 150; x2 = min(xa2, xb2) - 150
    for i in range(n):
        x = x1 + (x2 - x1) * i // (n - 1)
        rect('metal2', x-BARH//2, ya, x+BARH//2, yb)
straps('vcp', bars[('mp', 'S')], bars[('hp', 'D')], 7)
straps('out', bars[('mn', 'D')], bars[('mp', 'D')], 5)
straps('vcn', bars[('hn', 'D')], bars[('mn', 'S')], 5)
# gate net g: M1 strap from the bottom gate pad of mp to the top gate pad of mn, at x = +229 (gate contacts of both devices coincide)
def gate_pad_y(t, top):
    g = [l for l in info[t]['L'] and []]; return None
def pads(t):
    L = info[t]['L']; ys = []
    for r in L['polycont']: ys.append((r[1] + r[3]) // 2)
    return min(ys), max(ys)
mp_lo, mp_hi = pads('mp'); mn_lo, mn_hi = pads('mn')
gx = 229
rect('metal1', gx-30, cy['mn'] + mn_hi, gx+30, cy['mp'] + mp_lo)      # from the top gate pad of mn up to the bottom gate pad of mp
LAB.append(('metal1', gx, (cy['mn'] + mn_hi + cy['mp'] + mp_lo) // 2, 'g'))   # input pin on the M1 strap between the two gates (metal of this cell, so the label attaches)
hn_lo, hn_hi = pads('hn'); hp_lo, hp_hi = pads('hp')
def pad_x(t, ytop):   # x of the gate contact closest to the centre, on the top row
    L = info[t]['L']; xs = [(r[0] + r[2]) // 2 for r in L['polycont'] if (r[1] + r[3]) // 2 == ytop]
    return min(xs, key=abs)
for t, hi, nm in (('hn', hn_hi, 'en'), ('hp', hp_hi, 'enb')):    # pin metal in this cell, overlapping the gate pad of the device
    px = pad_x(t, hi); py = cy[t] + hi
    cand = [r for r in info[t]['L']['viali'] if r[0] <= px <= r[2] and r[1] <= hi <= r[3]]
    r = min(cand, key=lambda r: (r[2]-r[0])*(r[3]-r[1]))                 # the pcell's own gate-pad rectangle: same metal, now also in this cell
    rect('metal1', r[0], cy[t]+r[1], r[2], cy[t]+r[3]); LAB.append(('metal1', px, py, nm))
# rails and ring ties
XL = min(info[t]['bb'][0] for t in info) - 1200; XR = max(info[t]['bb'][2] for t in info) + 1200
def ring_tie(t):
    rr = info[t]['ring']; cx = rr[0] + 40; yc = cy[t] + rr[3] - 20
    stack_m1_m2(cx, yc); return cx, yc
ties = {t: ring_tie(t) for t in info}
# P devices: wire ring tie to the S bar (top) of the same device; S bar extended left to the tie
for t in ('hp', 'mp'):
    x1, x2, yb = bars[(t, 'S')]; cx, yc = ties[t]
    rect('metal2', cx-60, yb-BARH//2, x1, yb+BARH//2); rect('metal2', cx-60, yb-BARH//2, cx+60, yc+60)
# vdda rail: S bar of hp extended to the right
x1, x2, yb = bars[('hp', 'S')]; rect('metal2', x2, yb-BARH//2, XR, yb+BARH//2); LAB.append(('metal2', XR-100, yb, 'vdda'))
# gnd rail: left vertical M2 from hn S bar (bottom) to the mn ring-tie wire, ring-tie wires of hn, mn run left to it
x1, x2, yb = bars[('hn', 'S')]; rect('metal2', XL, yb-BARH//2, x1, yb+BARH//2)
cxm, ycm = ties['mn']; cxh, ych = ties['hn']
rect('metal2', XL, yb-BARH//2, XL+BARH, ycm+60)
rect('metal2', XL, ycm-60, cxm+60, ycm+60); rect('metal2', XL, ych-60, cxh+60, ych+60)
LAB.append(('metal2', XL+100, yb, 'gnd'))
# out pin on the mn/mp D strap region
x1, x2, yb = bars[('mn', 'D')]; LAB.append(('metal2', (x1+x2)//2, yb, 'out'))
out = ['magic', 'tech sky130A', 'magscale 1 2', 'timestamp 0', '<< checkpaint >>', 'rect -2000 -2000 2000 2000']
bylayer = {}
for l, a, b, c, d in R: bylayer.setdefault(l, []).append((a, b, c, d))
for l, rs in bylayer.items():
    out.append(f'<< {l} >>'); out += [f'rect {a} {b} {c} {d}' for a, b, c, d in rs]
out.append('<< labels >>')
for i, (l, x, y, t) in enumerate(LAB):
    out.append(f'flabel {l} {x} {y} {x} {y} 0 FreeSans 120 0 0 0 {t}'); out.append(f'port {i+1} nsew')
out.append('<< end >>')
txt = '\n'.join(out) + '\n'
# insert the use lines before the first '<<' layer section after the header
head, rest = txt.split('<< checkpaint >>', 1)
open(f'{B}/ota_core.mag', 'w').write(head + uses + '<< checkpaint >>' + rest)
print('centres', cy); print('rails XL XR', XL, XR); print('bars', {k: v for k, v in bars.items()})
