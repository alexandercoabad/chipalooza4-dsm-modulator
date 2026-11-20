"""DC check of the extracted vcm replica against the extracted (full-size) OTA core with its output tied to its input and the same header/footer enables:
both are self-biased inverters, so the replica's vcm should sit at the OTA's trip point.  TT / SS / FF device corners, 27 C, 3.3 V.  Usage: python3 bias_check.py (needs PDK_ROOT, ngspice)"""
import os, re, subprocess, tempfile
PDK = os.environ.get('PDK_ROOT', os.path.expanduser('~/openeda/pdk/share/pdk')) + '/sky130A/libs.tech/ngspice/sky130.lib.spice'
HERE = os.path.dirname(os.path.abspath(__file__))
def ports(f, name): return re.search(rf'^\.subckt {name} (.*)$', open(f).read(), re.M).group(1).split()
def op(corner, f, name, nodemap):
    pl = ports(f, name)
    x = ' '.join(nodemap[p] for p in pl)
    nl = f".lib {PDK} {corner}\n.include {f}\nVdd vdda 0 3.3\nVen en 0 3.3\nVenb enb 0 0\nXu {x} {name}\n.nodeset v(o)=1.6\n.options reltol=1e-4\n.control\nop\nprint v(o)\n.endc\n.end\n"
    d = tempfile.mkdtemp(); open(d + '/t.cir', 'w').write(nl)
    out = subprocess.run(['ngspice', '-b', d + '/t.cir'], capture_output=True, text=True).stdout
    return float(re.search(r'^v\(o\)\s*=\s*([-0-9.eE+]+)', out, re.M).group(1))
print('corner   vcm replica   OTA core self-bias   difference (mV)')
for c in ('tt', 'ss', 'ff'):
    r = op(c, f'{HERE}/vcm_replica_ext.spice', 'vcm_replica', dict(vdda='vdda', gnd='0', vcm='o', en='en', enb='enb'))
    o = op(c, f'{HERE}/../ota/ota_core_ext.spice', 'ota_core', dict(vdda='vdda', gnd='0', g='o', out='o', en='en', enb='enb'))
    print(f'{c:6s}  {r:9.4f} V  {o:12.4f} V  {1e3*(r-o):+8.1f}')
