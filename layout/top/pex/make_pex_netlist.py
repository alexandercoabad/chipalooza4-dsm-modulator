"""Build the simulation netlist of the laid-out modulator: pex/dsm_top_pex.spice (Magic, flat, C only) wrapped as .subckt dsm_top_pex with the ports of topdef.TOP_PORTS.
The extractor also reports metal3/metal4 plate overlap capacitance *inside* cap_array (it reports it on top of the cap_mim_m3_1 device, which already contains it), measured by
extracting cap_array alone (pex/ca/cap_array_pex.spice).  Those array-internal values are subtracted pair by pair from the top-level C so that only routing and the plates' capacitance to substrate/other nets remain.
Substrate/ground: Magic names the substrate node gnd here (p-substrate tied to the gnd net), so caps to it are caps to gnd."""
import re, os, sys
H = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(H, '..')); import topdef
SC = {'f': 1e-15, 'p': 1e-12, 'a': 1e-18, 'n': 1e-9, '': 1}
def val(s): m = re.match(r'([\d.eE+-]+)([a-z]?)$', s); return float(m.group(1)) * SC[m.group(2)]
sub = {}   # pair of top nets -> array internal overlap C
amap = {'cs_t': 't', 'cs_b': 'b', 'g': 'g', 'ci_b': 'out'}
for ln in open(os.path.join(H, 'ca', 'cap_array_pex.spice')):
    t = ln.split()
    if t and t[0][0] == 'C' and 'VSUBS' not in t[1:3] and t[1] in amap and t[2] in amap: sub[frozenset((amap[t[1]], amap[t[2]]))] = val(t[3])
# node names of the top nets in the extracted file (same resolution as net_caps.py)
exec(open(os.path.join(H, 'net_caps.py')).read().split("res = {}")[0].replace("print(", "(lambda *a: None)("))
name2net = {n: net for net, f in node_of.items() for n in set(f)}
L = []; removed = 0.0; kept = 0.0
for ln in open(os.path.join(H, 'dsm_top_pex.spice')):
    t = ln.split()
    if not t or t[0].startswith('*'): continue
    if t[0][0] == 'C':
        v = val(t[3]); a, b = name2net.get(t[1]), name2net.get(t[2])
        if a and b and frozenset((a, b)) in sub:
            s = sub[frozenset((a, b))]; v2 = v - s; removed += min(v, s)
            if v2 < 0.01e-15: continue
            t[3] = '%.5gf' % (v2 * 1e15)
        kept += val(t[3]); L.append(' '.join(t[:4]))
    else: L.append(' '.join(t))
ports = ' '.join(topdef.TOP_PORTS)
open(os.path.join(H, 'dsm_top_pex_sim.spice'), 'w').write(f"* dsm_top, extracted wiring capacitance (no wire R), cap_array plate overlap removed ({removed*1e15:.1f} fF); see make_pex_netlist.py\n.subckt dsm_top_pex {ports}\n" + '\n'.join(L).replace(' VSUBS', ' gnd') + "\n.ends\n")
open(os.path.join(H, 'dsm_top_nopar_sim.spice'), 'w').write(f"* dsm_top, extracted devices only (the same layout, no wiring capacitance): control for the parasitic comparison\n.subckt dsm_top_pex {ports}\n" + '\n'.join(l for l in L if l[0] != 'C').replace(' VSUBS', ' gnd') + "\n.ends\n")
print('removed array-internal overlap C: %.1f fF; remaining C: %.1f fF; devices+caps lines %d' % (removed * 1e15, kept * 1e15, len(L)))
