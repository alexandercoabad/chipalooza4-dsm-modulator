"""Clock generator post-layout test bench: the same edge-timing measurements as tb_clk.py, on three versions of the circuit.
usage: python3 tb_clk_pex.py KIND [corner] [temp] [vdd] [rc]
KIND = sch_ideal : analog/cells.py clockgen (ideal delay capacitors; what dsm1/ simulated)
       sch_mim   : layout/clkgen/clkgen_sch.spice (real MIM capacitors, no wiring)
       pex       : layout/clkgen/pex/clkgen_pex.spice (Magic extraction: devices + wiring capacitance, NO wire resistance)
rc = res/cap corner file of the PDK models (default res_typical__cap_typical); only the MIM and wire capacitance depend on it.
Appends to ../results/analog/clk_postlayout.jsonl."""
import sys, os, json, re
H = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, H); sys.path.insert(0, os.path.join(H, '..', 'common'))
import cells, mylib, tb_clk
kind = sys.argv[1]; corner = sys.argv[2] if len(sys.argv) > 2 else 'tt'; temp = float(sys.argv[3]) if len(sys.argv) > 3 else 27
vdd = float(sys.argv[4]) if len(sys.argv) > 4 else 3.3; rc = sys.argv[5] if len(sys.argv) > 5 else None
F = {'sch_mim': os.path.join(H, '..', 'layout', 'clkgen', 'clkgen_sch.spice'), 'pex': os.path.join(H, '..', 'layout', 'clkgen', 'pex', 'clkgen_pex.spice')}
if rc: mylib.RC[corner] = f'r+c/{rc}.spice'
if kind != 'sch_ideal':
    f = os.path.abspath(F[kind]); txt = open(f).read()
    ports = re.search(r'^\.subckt\s+clkgen\s+(.*)$', txt, re.M).group(1).split()
    pm = {'gnd': '0'}
    cells.clockgen = lambda n, clk, vdd='vdda', **dk: f'.include "{f}"\nXdut {" ".join(pm.get(p, p) for p in ports)} clkgen\n'
r = tb_clk.main(corner, temp, vdd); r.pop('duty_phase_p2_pct', None)
r = dict(kind=kind, rc=rc or 'typical', **r)
print(json.dumps(r)); os.makedirs(os.path.join(H, '..', 'results', 'analog'), exist_ok=True)
open(os.path.join(H, '..', 'results', 'analog', 'clk_postlayout.jsonl'), 'a').write(json.dumps(r) + '\n')
