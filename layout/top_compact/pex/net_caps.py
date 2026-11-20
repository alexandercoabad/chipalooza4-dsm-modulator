"""Per-net wiring capacitance of the extracted dsm_top (pex/dsm_top_pex.spice, Magic, C only).
Maps the 21 top-level nets of topdef.NETS to extracted node names (block label with instance prefix, or pad label), then totals: C to substrate/gnd, coupling to the other 20 nets, coupling to internal/other nodes."""
import re, sys, os, collections, json
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')); import topdef
SC = {'f': 1e-15, 'p': 1e-12, 'a': 1e-18, 'n': 1e-9, '': 1}
C = []; nodes = set()
for ln in open(os.path.join(os.path.dirname(os.path.abspath(__file__)), os.environ.get('PEXFILE', 'dsm_top_pex.spice'))):
    t = ln.split()
    if t and t[0][0] == 'C':
        m = re.match(r'([\d.eE+-]+)([a-z]?)$', t[3]); C.append((t[1], t[2], float(m.group(1)) * SC[m.group(2)])); nodes.update(t[1:3])
    elif t and t[0][0] == 'X':
        nodes.update(t[1:5])
# Magic names the six TG uses tg_x0p5_mf_N; the .ext 'use' lines give their positions, matched to topdef.FLOORPLAN (nm/5 -> um)
tgname = {}
for ln in open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dsm_top.ext')):
    t = ln.split()
    if t[:1] == ['use'] and t[1] == 'tg_x0p5_mf':
        x, y = int(t[5]) * 0.005, int(t[8]) * 0.005
        tgname[[i for i, (c, fx, fy) in topdef.FLOORPLAN.items() if c == 'tg_x0p5_mf' and abs(fx - x) < 0.01 and abs(fy - y) < 0.01][0]] = t[2]
pref = {**tgname, 'xclk': 'clkgen_0', 'xcmp': 'comp_compact_0', 'xota': 'ota_core_0', 'xvcm': 'vcm_replica_0', 'xcap': 'cap_array_0'}
def names(net):
    out = []
    for inst, pin in topdef.NETS[net]:
        if inst == 'TOP': out.append(pin)
        elif inst in pref: out.append(f'{pref[inst]}/{pin}')
        else: out.append(f'{pref[inst]}/{pin}')
    return out
node_of = {}
for net in topdef.NETS:
    f = [n for n in names(net) if n in nodes]
    node_of[net] = f
bad = {n: f for n, f in node_of.items() if len(set(f)) != 1}
inv = {f[0]: n for n, f in node_of.items() if f}
print('nets with a single extracted name:', 21 - len(bad), '; ambiguous or missing:', {k: v for k, v in bad.items()})
res = {}
for net, f in node_of.items():
    if not f: continue
    me = f[0]; tot = 0; gnd = 0; coup = collections.Counter(); other = 0
    for a, b, v in C:
        if me not in (a, b): continue
        o = b if a == me else a; tot += v
        if o == 'gnd' or o == inv.get('gnd'): gnd += v
        elif o in inv: coup[inv[o]] += v
        else: other += v
    res[net] = dict(node=me, total_fF=round(tot * 1e15, 2), to_gnd_fF=round(gnd * 1e15, 2), to_other_nets_fF=round(sum(coup.values()) * 1e15, 2), to_internal_fF=round(other * 1e15, 2), top_coupled={k: round(v * 1e15, 2) for k, v in coup.most_common(3)})
json.dump(res, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'net_caps.json'), 'w'), indent=1)
print(f"{'net':5} {'total':>8} {'gnd':>8} {'nets':>8} {'intern':>8}  strongest coupling (fF)")
for n, r in sorted(res.items(), key=lambda x: -x[1]['total_fF']): print(f"{n:5} {r['total_fF']:8.2f} {r['to_gnd_fF']:8.2f} {r['to_other_nets_fF']:8.2f} {r['to_internal_fF']:8.2f}  {r['top_coupled']}")
print('all C in file: %.1f fF' % (sum(v for *_, v in C) * 1e15))
