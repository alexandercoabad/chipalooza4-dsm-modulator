"""Reference netlist of the vcm replica from the simulated circuit's own constants (dsm1/sim/dsm1.py: inverter core at 1/8 width, out tied to in)."""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, '..', '..', 'common'))
import amp_core
k = 8.0   # as in dsm1.py
n, p = 'sky130_fd_pr__nfet_g5v0d10v5', 'sky130_fd_pr__pfet_g5v0d10v5'
s = f"""* vcm replica: inverter core at 1/8 width, output tied to input (self-biased), header on (gate enb, tied to gnd by the top level), footer on (gate en, tied to vdda by the top level) -- dsm1/sim/dsm1.py
.subckt vcm_replica vcm vdda gnd en enb
XMhp rcp enb vdda vdda {p} w={amp_core.HDR_W/k:g} l=0.5
XMp  vcm vcm rcp  rcp  {p} w={amp_core.WP/k:g} l={amp_core.L:g}
XMn  vcm vcm rcn  gnd  {n} w={amp_core.WN/k:g} l={amp_core.L:g}
XMhn rcn en gnd gnd  {n} w={amp_core.FTR_W/k:g} l=0.5
.ends
"""
open(os.path.join(HERE, 'vcm_replica_sch.spice'), 'w').write(s); print(s)
