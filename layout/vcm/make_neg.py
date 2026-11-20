"""Fault-injected copies of vcm_replica_sch.spice; each must make LVS fail: header gate on vdda (header off), core gate not tied to the output (open loop), core PMOS width halved, footer gate on gnd."""
import re
s = open('vcm_replica_sch.spice').read()
def put(name, new):
    assert new != s, name; open(f'ref/{name}.spice', 'w').write(new)
put('neg_header_off', s.replace('XMhp rcp enb', 'XMhp rcp vdda'))
put('neg_gate_untied', s.replace('XMn  vcm vcm rcn', 'XMn  vcm gx rcn'))
put('neg_wrong_width', s.replace('w=16 l=2', 'w=8 l=2'))
put('neg_footer_off', s.replace('XMhn rcn en', 'XMhn rcn gnd'))
