"""Fault-injected copies of clkgen_sch.spice; each must make LVS fail:
 delay_gate   first inverter of the comparator-clock delay chain driven by p1 instead of p1a
 cap_node     one 20 fF delay capacitor of the early delay moved to another node
 cap_size     one 60 fF capacitor drawn as 20 fF
 driver_w     p1a driver nfet width 8 -> 4
 nand_input   NAND2 (comparator clock) second input tied to p1a instead of the delayed p1a
 nor_rail     NOR2 (p2 core) series pfet tied to the wrong supply node (gnd)"""
import re
s = open('clkgen_sch.spice').read()
def edit(name, pat, rep):
    t, n = re.subn(pat, rep, s, count=1, flags=re.M); assert n == 1 and t != s, name
    open(f'ref/neg_{name}.spice', 'w').write(t)
edit('delay_gate', r'^(Xgdci0n_0 \S+ )p1a', r'\1p1')
edit('cap_node', r'^(XCgde_0 )\S+', r'\1gp1d')
edit('cap_size', r'^(XCgdc_0 \S+ \S+ \S+ )w=5.32 l=5.32', r'\1w=3.0 l=3.0')
edit('driver_w', r'^(Xga2n_0 .* )w=8.0000', r'\1w=4.0000')
edit('nand_input', r'^(Xgcnnb_0 \S+ )gp1c', r'\1p1a')
edit('nor_rail', r'^(Xgn2pa_0 \S+ \S+ )vdda vdda', r'\1gnd vdda')
