"""Generate the Cs/Ci capacitor array (Magic .mag) from unit MIM capacitors.  Units: 1 = 5 nm.
3 columns x 2 rows of identical unit caps (columns Ci | Cs | Ci): Cs = the 2 middle units, Ci = the 4 outer units, so both have the same centroid and the
ratio is a unit count.  Top plates (metal4 over the capm): the four Ci units = g (OTA input, virtual ground), the two Cs units = cs_t (switched between vcm and g); bottom plates (metal3) = cs_b (middle), ci_b (outer)."""
import os, re, glob
B = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'build')
unit = [os.path.basename(f)[:-4] for f in glob.glob(f'{B}/sky130_fd_pr__cap_mim_m3_1_*.mag')]
unit = [u for u in unit if 'FIXED' not in u]
# the unit cell is the one with w=22.2 (the warm-up cell is 5 x 5)
for u in unit:
    if 'w 22.2 l 22.2' in open(f'{B}/{u}.mag').read(): U = u
PX, PY = 5200, 5400          # pitch 26 x 27 um: capm.11 needs capm 1.34 um from the neighbour's metal3
R, LAB, uses = [], [], ''
def rect(l, x1, y1, x2, y2): R.append((l, int(x1), int(y1), int(x2), int(y2)))
cols = [0, 1, 2]; rows = [0, 1]
for c in cols:
    for r in rows:
        uses += f"use {U}  c{c}r{r}\ntimestamp 0\ntransform 1 0 0 0 1 0\nbox -2436 -2260 2436 2260\n".replace('transform 1 0 0 0 1 0', f'transform 1 0 {c*PX} 0 1 {r*PY}')
fx = lambda c: c*PX + 2384            # bottom-plate (via3 column) x of column c
W = 60                                # half width of the m4 stubs (0.6 um wide)
# top plates -> g: vertical stub between the two rows of each column, one stub per column down to a lane below the array
YL = -3000                            # g lane centre (below row 0: m3 plate edge at -2260)
for c in cols:
    x = c*PX - 800
    rect('metal4', x-W, -2000, x+W, 2*0+PY+2000)           # joins the two top plates of the column
    if c != 1: rect('metal4', x-W, YL-100, x+W, -2000)      # stub down to the g lane (Cs, the middle column, has its own top-plate net)
rect('metal4', 0-800-W, YL-100, 2*PX-800+W, YL+100); LAB.append(('metal4', 2*PX-800, YL, 'g'))
# bottom plates: join the rows through the m4 frame at the via3 column
for c in cols: rect('metal4', fx(c)-40, 2248, fx(c)+40, PY-2248)
# ci_b: columns 0 and 2 up to a lane above row 1 (m3 plate edge at PY+2260)
YT = PY + 2260 + 640
for c in (0, 2): rect('metal4', fx(c)-40, PY+2248, fx(c)+40, YT+100)
rect('metal4', fx(0)-40, YT-100, fx(2)+40, YT+100); LAB.append(('metal4', fx(2), YT, 'ci_b'))
# cs_b: m4 pad in the row gap, via4, metal5 stripe up past the ci_b lane (m5 width 1.6 um)
xm, ym = fx(1), (2260 + PY - 2260)//2
rect('metal4', xm-120, ym-120, xm+120, ym+120); rect('via4', xm-118, ym-118, xm+118, ym+118)
rect('metal5', xm-160, ym-160, xm+160, YT+500); LAB.append(('metal5', xm, YT+300, 'cs_b'))
# cs_t: top plates of the two Cs units (switched between vcm and g in the modulator): m4 pad on the column's vertical stub in the row gap, via4, metal5 stripe up past the ci_b lane
xt = PX - 800
rect('metal4', xt-120, ym-120, xt+120, ym+120); rect('via4', xt-118, ym-118, xt+118, ym+118)
rect('metal5', xt-160, ym-160, xt+160, YT+500); LAB.append(('metal5', xt, YT+300, 'cs_t'))
out = ['magic', 'tech sky130A', 'magscale 1 2', 'timestamp 0', '<< checkpaint >>', 'rect -2000 -2000 2000 2000']
by = {}
for l, a, b, c, d in R: by.setdefault(l, []).append((a, b, c, d))
for l, rs in by.items(): out.append(f'<< {l} >>'); out += [f'rect {a} {b} {c} {d}' for a, b, c, d in rs]
out.append('<< labels >>')
for i, (l, x, y, t) in enumerate(LAB):
    out.append(f'flabel {l} {x} {y} {x} {y} 0 FreeSans 120 0 0 0 {t}'); out.append(f'port {i+1} nsew')
out.append('<< end >>')
head, rest = ('\n'.join(out) + '\n').split('<< checkpaint >>', 1)
open(f'{B}/cap_array.mag', 'w').write(head + uses + '<< checkpaint >>' + rest)
print('unit', U)
