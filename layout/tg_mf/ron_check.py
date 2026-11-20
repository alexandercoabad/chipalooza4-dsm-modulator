"""On-resistance of the TG versus signal level, three netlists of the same transmission gate, each in its own ngspice run:
  schematic : as simulated in the modulator (nfet W, pfet W, one device each, nf=1),
  nf        : the pfet written with the finger count of the layout (w = total width, nf = fingers; in the sky130 wrapper w is the TOTAL width),
  extracted : the layout-extracted netlist from Magic (devices w = finger width, nf=1; no parasitic R or C, only the ad/as/pd/ps areas Magic writes).
Ron = 10 mV / I with 10 mV across the TG, swept over the common-mode level 0.2..3.1 V; gates en = 3.3 V, enb = 0 V.
Needs ngspice and the sky130 models (SKY130PR, see ../../common/mylib.py).  usage: python3 ron_check.py [cell=tg_x0p5_mf] [pfet fingers=3] [corners=tt,ss,ff]
Known quirk (ngspice 42, sky130 5 V models, TT): a pfet_g5v0d10v5 with nf > 1 and 2 um fingers (w=6 nf=3, w=4 nf=2) makes ngspice abort a DC sweep;
nf=1 devices (what the extracted netlist contains) and 4 um fingers (w=12 nf=3) work, so the 'nf' variant is reported as n/a when it aborts."""
import sys, os, re, numpy as np
here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(here, '..', '..', 'common'))
import simlib
cell = sys.argv[1] if len(sys.argv) > 1 else 'tg_x0p5_mf'
NFP = int(sys.argv[2]) if len(sys.argv) > 2 else 3
corners = (sys.argv[3] if len(sys.argv) > 3 else 'tt,ss,ff').split(',')
sch_txt = open(f'{here}/{cell}_sch.spice').read()
WN = re.search(r'XMN.*? w=([0-9.]+)', sch_txt).group(1); WP = re.search(r'XMP.*? w=([0-9.]+)', sch_txt).group(1)
open('/tmp/_sch.spice', 'w').write(sch_txt.replace(f'.subckt {cell}', f'.subckt {cell}_SCH'))
open('/tmp/_ext.spice', 'w').write(open(f'{here}/{cell}_ext.spice').read().replace(f'.subckt {cell} ', f'.subckt {cell}_EXT '))
# subcircuit port orders: schematic a b en enb vdd vss ; extracted a b en enb vss vdd
INST = {'schematic': f'X1 a b en enb vdd 0 {cell}_SCH', 'nf': 'X1 a b en enb vdd 0 tgnf', 'extracted': f'X1 a b en enb 0 vdd {cell}_EXT'}
def ron(corner, which):
    b  = '.include /tmp/_sch.spice\n.include /tmp/_ext.spice\n'
    b += f'.subckt tgnf a b en enb vdd vss\nXMN a en b vss sky130_fd_pr__nfet_g5v0d10v5 w={WN} l=0.5 nf=1\nXMP a enb b vdd sky130_fd_pr__pfet_g5v0d10v5 w={WP} l=0.5 nf={NFP}\n.ends\n'
    b += 'Vdd vdd 0 3.3\nVen en 0 3.3\nVenb enb 0 0\nVx x 0 0\nV1 a x 0\nBb b 0 V = v(x)-0.01\n' + INST[which] + '\n'
    b += '.control\ndc Vx 0 3.3 0.1\nlet i1=-i(V1)\nwrdata OUT v(x) i1\n.endc\n'
    try: a, _ = simlib.run(b, corner, 27, tag='ron')
    except RuntimeError: return None
    return a[:, 1], 0.01/np.maximum(np.abs(a[:, 3]), 1e-15)
for corner in corners:
    res = {w: ron(corner, w) for w in INST}
    v, Rs = res['schematic']; m = (v >= 0.2) & (v <= 3.1)
    def diff(w):
        if res[w] is None: return 'n/a (ngspice aborts)'
        return f'{np.max(np.abs(res[w][1][m]/Rs[m]-1))*100:.2f} %'
    print(f'{cell} {corner}: Ron schematic {Rs[m].min():.0f}..{Rs[m].max():.0f} ohm over 0.2..3.1 V | extracted layout vs schematic: max diff {diff("extracted")} | nf={NFP} form vs schematic: max diff {diff("nf")}')
