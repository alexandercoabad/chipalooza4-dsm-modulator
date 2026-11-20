"""Fault-injected copies of comp_sch.spice; each must make LVS fail: inputs swapped, tail device width changed, one reset PMOS gate moved to vdda."""
import re
s = open('comp_sch.spice').read()
swap = re.sub(r'(Xcm1_0 \S+ )inp', r'\1inn', s); swap = re.sub(r'(Xcm2_0 \S+ )inn', r'\1inp', swap)
assert swap != s; open('ref/neg_inputs_swapped.spice', 'w').write(swap)
w = re.sub(r'(Xcmt_0 .*? w=)[0-9.]+', r'\g<1>4.0000', s, count=1); assert w != s; open('ref/neg_tail_width.spice', 'w').write(w)
g = re.sub(r'(Xcm7_0 \S+ )clk', r'\1vdda', s, count=1); assert g != s; open('ref/neg_reset_gate.spice', 'w').write(g)
