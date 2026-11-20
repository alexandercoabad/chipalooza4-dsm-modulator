"""Capacitance of Cs and Ci from the extracted netlist (cap_array_ext.spice) in ngspice, per process corner (AC at 1 kHz), and the Cs/Ci ratio.
Usage: python3 cap_values.py   (needs PDK_ROOT, ngspice)"""
import os, subprocess, re, math, tempfile
PDK = os.environ.get('PDK_ROOT', os.path.expanduser('~/openeda/pdk/share/pdk')) + '/sky130A/libs.tech/ngspice/sky130.lib.spice'
ext = os.path.abspath('cap_array_ext.spice')
ports = re.search(r'^\.subckt cap_array (.*)$', open(ext).read(), re.M).group(1)     # port order of the extracted netlist
rows = []
for corner in ['tt', 'll', 'hh', 'ss', 'ff', 'hl', 'lh']:
    nl = f""".lib {PDK} {corner}
.include {ext}
Xdut {ports} cap_array
Vac g 0 dc 0 ac 1
Vact cs_t 0 dc 0 ac 1
Vcs cs_b 0 0
Vci ci_b 0 0
.control
ac lin 1 1k 1k
print mag(i(vcs)) mag(i(vci))
.endc
.end
"""
    d = tempfile.mkdtemp(); open(d + '/t.cir', 'w').write(nl)
    out = subprocess.run(['ngspice', '-b', d + '/t.cir'], capture_output=True, text=True).stdout
    v = {k: float(re.search(re.escape(k) + r'\)\)\s*=\s*([0-9.eE+-]+)', out).group(1)) / (2 * math.pi * 1e3) for k in ('i(vcs', 'i(vci')}
    rows.append((corner, v['i(vcs'], v['i(vci']))
print('corner   Cs (pF)   Ci (pF)   Cs/Ci')
for c, cs, ci in rows: print(f'{c:6s}  {cs*1e12:8.4f}  {ci*1e12:8.4f}  {cs/ci:7.5f}')
