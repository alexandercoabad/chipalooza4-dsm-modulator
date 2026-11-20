"""Reference schematic for the layout, generated from analog/cells.py clockgen() (the circuit as simulated, default delay settings as in dsm1.py).
The ideal delay capacitors (20 fF, 60 fF to ground) become MIM capacitors (cap_mim_m3_1), sized by cap_size.py to the same value at TT.
Writes clkgen_sch.spice (subckt clkgen) and clkgen_ideal.spice (same circuit with the ideal capacitors, for the comparison run)."""
import os, sys, re
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'analog')); import cells
MIM = {2e-14: 3.0, 6e-14: 5.32}          # farads -> square side (um), from cap_size.py
PORTS = 'clk p1a p1ab p1 p1b p2 p2b cc vdda gnd'
def build(ideal):
    out = []
    for ln in cells.clockgen('g', 'clk').splitlines():
        t = ln.split()
        if t[0].startswith('C'):
            v = float(t[3])
            if ideal: out.append(f"{t[0]} {t[1]} gnd {t[3]}")
            else: s = MIM[v]; out.append(f"X{t[0]} {t[1]} gnd sky130_fd_pr__cap_mim_m3_1 w={s} l={s}")
        else:
            t = [('gnd' if x == '0' else x) for x in t]; out.append(' '.join(t))
    return f".subckt clkgen {PORTS}\n" + '\n'.join(out) + "\n.ends\n"
open(os.path.join(HERE, 'clkgen_sch.spice'), 'w').write("* Clock generator reference: analog/cells.py clockgen('g','clk') as simulated; ideal delay capacitors replaced by cap_mim_m3_1 (sizes from cap_size.py)\n" + build(False))
open(os.path.join(HERE, 'clkgen_ideal.spice'), 'w').write("* Same circuit with the ideal delay capacitors (as in analog/ simulations)\n" + build(True))
