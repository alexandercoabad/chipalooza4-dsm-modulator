"""Compact comparator layout (same circuit and device sizes as ../comp/comp_sch.spice) from multifinger PDK cells: pairs that share a terminal share diffusion and a well.
Writes build/comp_compact.mag."""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import autolay2 as A
B = os.path.join(HERE, 'build')
def S(name, kind, w, nf, strips, gates, l=0.5):
    return dict(name=name, kind=kind, w=w, l=l, nf=nf, strips=strips, gates=gates, bulk='gnd' if kind == 'n' else 'vdda')
specs = [
 S('n_tail', 'n', 8.0, 1, ['ctail', 'gnd'], ['clk']),
 S('n_pair', 'n', 8.0, 2, ['cx1', 'ctail', 'cx2'], ['inp', 'inn']),
 S('n_x3',   'n', 4.0, 1, ['con', 'cx1'], ['cop']),
 S('n_x4',   'n', 4.0, 1, ['cop', 'cx2'], ['con']),
 S('n_iso',  'n', 1.0, 2, ['conn', 'gnd', 'copn'], ['con', 'cop']),
 S('n_cs1',  'n', 1.0, 2, ['gnd', 'cQ', 'gnd'], ['copn', 'cQb']),
 S('n_cs2',  'n', 1.0, 2, ['gnd', 'cQb', 'gnd'], ['conn', 'cQ']),
 S('n_buf',  'n', 8.0, 2, ['qb', 'gnd', 'q'], ['cQ', 'cQb']),
 S('p_x',    'p', 8.0, 2, ['con', 'vdda', 'cop'], ['cop', 'con']),
 S('p_rs1',  'p', 2.0, 2, ['con', 'vdda', 'cop'], ['clk', 'clk']),
 S('p_rs2',  'p', 2.0, 2, ['cx1', 'vdda', 'cx2'], ['clk', 'clk']),
 S('p_iso',  'p', 2.0, 2, ['conn', 'vdda', 'copn'], ['con', 'cop']),
 S('p_cs1',  'p', 4.0, 2, ['vdda', 'cs1_m', 'cQ'], ['copn', 'cQb']),
 S('p_cs2',  'p', 4.0, 2, ['vdda', 'cs2_m', 'cQb'], ['conn', 'cQ']),
 S('p_b1',   'p', 12.0, 2, ['qb', 'vdda', 'qb'], ['cQ', 'cQ']),
 S('p_b2',   'p', 12.0, 2, ['q', 'vdda', 'q'], ['cQb', 'cQb']),
]
PORTS = ('inp', 'inn', 'clk', 'q', 'qb', 'vdda', 'gnd')
GAP_N = int(os.environ.get('GAP_N', 300)); GAP_P = int(os.environ.get('GAP_P', 760))
env = dict(os.environ); env['PDK'] = 'sky130A'
magic = f"magic -dnull -noconsole -rcfile {env['PDK_ROOT']}/sky130A/libs.tech/magic/sky130A.magicrc"
plan = A.Plan(specs, B, magic, env)
on = [s['name'] for s in specs if s['kind'] == 'n']; op = [s['name'] for s in specs if s['kind'] == 'p']
c, on, op = A.anneal(plan, on, op, GAP_N, GAP_P)
print('order N', on); print('order P', op); print('wirelength cost', c)
res, nb = A.optimise(plan, on, op, GAP_N, GAP_P, PORTS)
print('devices(cells)', len(specs), 'tracks', len(res['ytr']), 'width um', res['width']*0.005)
A.write_mag(res, os.path.join(B, 'comp_compact.mag'))
