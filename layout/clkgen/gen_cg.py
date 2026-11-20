"""Clock generator layout (same circuit and device sizes as clkgen_sch.spice = analog/cells.py clockgen()) from multifinger PDK cells.
Inverters/NOR/NAND as in the schematic; consecutive delay-chain inverters share one 2-finger cell (shared supply strip); delay capacitors are MIM cells.
Writes build/clkgen.mag."""
import os, sys, re, collections
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import autolay3 as A
B = os.path.join(HERE, 'build')
# ---- read the reference schematic (the single source of truth for connectivity and sizes) ----
dev = {}; caps = []
for ln in open(os.path.join(HERE, 'clkgen_sch.spice')):
    t = ln.split()
    if not t or t[0].startswith(('*', '.')): continue
    if 'cap_mim' in ln:
        caps.append((t[0], t[1], float(re.search(r'w=(\S+)', ln).group(1))))
    else:
        dev[t[0][1:]] = dict(d=t[1], g=t[2], s=t[3], b=t[4], k='n' if 'nfet' in t[5] else 'p', w=float(re.search(r' w=(\S+)', ln).group(1)), l=float(re.search(r' l=(\S+)', ln).group(1)))
def S(name, kind, w, nf, strips, gates, l=0.5):
    return dict(name=name, kind=kind, w=w, l=l, nf=nf, strips=strips, gates=gates, bulk='gnd' if kind == 'n' else 'vdda')
def D(n): return dev[n]
specs = []
def inv(tag, nn, pn):
    """inverter: nfet instance name list nn, pfet instance names pn (parallel copies); fingers of the same width in one multifinger cell"""
    for kind, names in (('n', nn), ('p', pn)):
        d = D(names[0]); out, gate, rail = d['d'], d['g'], d['s']; nf = len(names)
        strips = [out if i % 2 == 0 else rail for i in range(nf + 1)]
        specs.append(S(f'{kind}_{tag}', kind, d['w'], nf, strips, [gate] * nf, d['l']))
def pair_delay(tag, n0, n1):
    """two consecutive delay inverters (names n0, n1 = instance prefixes, e.g. 'gdg1i0'): [out0, rail, out1] with gates [in0, out0]"""
    for kind, suf, rail in (('n', 'n_0', 'gnd'), ('p', 'p_0', 'vdda')):
        a, b = D(n0 + suf), D(n1 + suf)
        specs.append(S(f'{kind}_{tag}', kind, a['w'], 2, [a['d'], rail, b['d']], [a['g'], b['g']], a['l']))
def single_delay(tag, n0):
    for kind, suf, rail in (('n', 'n_0', 'gnd'), ('p', 'p_0', 'vdda')):
        a = D(n0 + suf); specs.append(S(f'{kind}_{tag}', kind, a['w'], 1, [a['d'], rail], [a['g']], a['l']))
inv('ck', ['gckn_0'], ['gckp_0'])
for t in ('a1', 'a2', 'a3', 'e1', 'e2', 'e3', 'b1', 'b2', 'b3'):
    inv(t, [f'g{t}n_0'], [k for k in dev if k.startswith(f'g{t}p_')])
inv('cb', ['gcbn_0'], ['gcbp_0'])
for t in ('n1', 'n2'):                                     # NOR2: parallel nfets, series pfets
    a, b = D(f'g{t}na_0'), D(f'g{t}nb_0'); pa, pb = D(f'g{t}pa_0'), D(f'g{t}pb_0')
    specs.append(S(f'n_{t}', 'n', a['w'], 2, ['gnd', a['d'], 'gnd'], [a['g'], b['g']]))
    specs.append(S(f'p_{t}', 'p', pa['w'], 2, ['vdda', pa['d'], pb['d']], [pa['g'], pb['g']]))
na, nb, pa, pb = D('gcnna_0'), D('gcnnb_0'), D('gcnpa_0'), D('gcnpb_0')   # NAND2: series nfets, parallel pfets
specs.append(S('n_cn', 'n', na['w'], 2, [na['d'], na['s'], 'gnd'], [na['g'], nb['g']]))
specs.append(S('p_cn', 'p', pa['w'], 2, ['vdda', pa['d'], 'vdda'], [pa['g'], pb['g']]))
pair_delay('dg1', 'gdg1i0', 'gdg1i1'); pair_delay('dg2', 'gdg2i0', 'gdg2i1'); pair_delay('de', 'gdei0', 'gdei1')
pair_delay('dc01', 'gdci0', 'gdci1'); pair_delay('dc23', 'gdci2', 'gdci3')
# capacitors: alternate rows to balance the row widths
for i, (nm, net, w) in enumerate(caps):
    specs.append(dict(name=f'c_{nm}', kind='c', w=w, l=w, nf=0, strips=[net, 'gnd'], gates=[], bulk=None, row='n' if i % 2 == 0 else 'p'))
cells_ = [s for s in specs if s['kind'] != 'c']
nt = sum(1 for s in cells_ for _ in range(s['nf']))                           # fingers
print('cells', len(cells_), 'caps', len(caps), 'fingers', nt)
PORTS = ('clk', 'p1a', 'p1ab', 'p1', 'p1b', 'p2', 'p2b', 'cc', 'vdda', 'gnd')
GAP_N = int(os.environ.get('GAP_N', 300)); GAP_P = int(os.environ.get('GAP_P', 760))
env = dict(os.environ); env['PDK'] = 'sky130A'
magic = f"magic -dnull -noconsole -rcfile {env['PDK_ROOT']}/sky130A/libs.tech/magic/sky130A.magicrc"
plan = A.Plan(specs, B, magic, env)
on = [s['name'] for s in specs if s['kind'] == 'n']; op = [s['name'] for s in specs if s['kind'] == 'p']
c, on, op = A.anneal(plan, on, op, GAP_N, GAP_P)
print('order N', on); print('order P', op); print('wirelength cost', c)
SEED = int(os.environ.get('SEED', 2)); ITERS = int(os.environ.get('ITERS', 12000))
res, nb = A.optimise(plan, on, op, GAP_N, GAP_P, PORTS, seed=SEED, iters=ITERS)
print('seed', SEED, 'conflicts', nb)
print('cells', len(cells_), 'caps', len(plan.caps), 'tracks', len(res['ytr']), 'width um', res['width']*0.005)
for bad in A.check(res): print('CONFLICT', bad)
for bad in A.check(res):
    for cn, (cx, cy) in res['pos'].items():
        for net, dx in plan.net_pins(cn):
            if abs(cx + dx - bad[1][0]) < 400 and net in (bad[1][4], bad[2][4]): print('  near', cn, net, 'cell centre x', cx, 'pin dx', dx, 'at y', cy, 'L', plan.specs[cn]['l'], 'nf', plan.specs[cn]['nf'], 'strips', plan.specs[cn]['strips'], 'gates', plan.specs[cn]['gates'])
A.write_mag(res, os.path.join(B, 'clkgen.mag'))
