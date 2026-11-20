"""Comparator test bench (StrongARM + SR latch + buffers, 3.3 V, Sky130 g5v0d10v5).
 1. ramp the differential input up and then down in 0.5 mV steps, one step per clock: offset, hysteresis, single transition
 2. alternating +/-20 mV: decision delay from clock edge, complementary outputs
 3. supply current averaged over a clock period
usage: [COMP_TEMP=125 COMP_VDD=3.0] python3 tb_comp_pex.py LABEL KIND [PEXFILE SUBCKT] [corner]
KIND = sch50 (schematic with the 50 fF placeholder loads), sch0 (schematic, no placeholder), pex (extracted netlist: devices + wiring capacitance to substrate, no wire resistance).
Same test bench as tb_comp.py; appends the result to ../results/analog/comp_postlayout.jsonl."""
import sys, os, json, numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'common'))
import cells, simlib
label, kind = sys.argv[1], sys.argv[2]; pexf = sys.argv[3] if kind == 'pex' else None; sub = sys.argv[4] if kind == 'pex' else None
corner = sys.argv[-1] if sys.argv[-1] in ('tt','ss','ff','sf','fs') else 'tt'; temp = float(os.environ.get('COMP_TEMP', 27)); vdd = float(os.environ.get('COMP_VDD', 3.3))   # optional overrides, defaults as before
vcm = 1.624 * vdd / 3.3; T = 1/1.024e6
if kind == 'pex':       # port order of the extracted subckt differs between layouts: map by name
    import re
    PORTS = re.search(r'^\.subckt\s+' + re.escape(sub) + r'\s+(.*)$', open(pexf).read(), re.M).group(1).split()
    PORTMAP = {'gnd': '0', 'qb': 'qb', 'q': 'q', 'inn': 'inn', 'inp': 'inp', 'clk': 'clk', 'vdda': 'vdda'}
def run(dvs):
    pw = "PWL(" + " ".join(f"{k*T:.6g} {vcm+d:.6f} {(k+1)*T-1e-9:.6g} {vcm+d:.6f}" for k, d in enumerate(dvs)) + ")"
    net = f"Vdda vdda 0 {vdd}\nVclk clk 0 PULSE(0 {vdd} {0.10*T:.6g} 2n 2n {0.40*T:.6g} {T:.6g})\nVinp inp 0 {pw}\nVinn inn 0 {vcm}\n"
    if kind == 'pex': net += f'.include "{os.path.abspath(pexf)}"\nXdut {" ".join(PORTMAP[p] for p in PORTS)} {sub}\n'
    else: net += cells.strongarm('c', 'inp', 'inn', 'clk', 'q', 'qb', c_out=50e-15 if kind == 'sch50' else 0)
    net += "Cq q 0 50f\nCqb qb 0 50f\n"
    net += f".options reltol=1e-4 vntol=1e-7\n.control\ntran 1n {(len(dvs)+1)*T:.6g}\nwrdata OUT v(q) v(qb) i(Vdda)\n.endc\n"
    a, so = simlib.run(net, corner, temp, tag='comp')
    assert a[-1, 0] > len(dvs)*T, "simulation ended early"
    return a[:, 0], a[:, 1], a[:, 3], -a[:, 5]
def bits_of(t, q, n): return np.array([np.interp((k+0.45)*T, t, q) for k in range(n)]) > vdd/2
step = 0.5e-3; up = -20e-3 + step*np.arange(81); seq = np.concatenate([up, up[::-1]])
t, q, qb, idd = run(seq); b = bits_of(t, q, len(seq)); bu, bd = b[:81], b[81:][::-1]
fu = np.where(bu[1:] != bu[:-1])[0]; fd = np.where(bd[1:] != bd[:-1])[0]
off_up = up[fu[0]] + step/2 if len(fu) == 1 else float('nan'); off_dn = up[fd[0]] + step/2 if len(fd) == 1 else float('nan')
alt = np.array([20e-3, -20e-3] * 4); t2, q2, qb2, idd2 = run(alt)
dl = []
for k in range(1, len(alt)):
    tc = (k + 0.10) * T; m = (t2 > tc) & (t2 < tc + 0.4*T); tgt = alt[k] > 0
    hit = np.where((q2[m] > vdd/2) == tgt)[0]; dl.append(t2[m][hit[0]] - tc if len(hit) else np.nan)
comp = max(abs(np.interp((k+0.45)*T, t2, q2) + np.interp((k+0.45)*T, t2, qb2) - vdd) for k in range(len(alt)))
res = dict(label=label, kind=kind, corner=corner, temp=temp, vdd=vdd, single_transition_up=len(fu) == 1, single_transition_down=len(fd) == 1,
           offset_up_mV=round(float(off_up)*1e3, 2), offset_down_mV=round(float(off_dn)*1e3, 2),
           decision_delay_max_ns=round(float(np.nanmax(dl))*1e9, 1), q_plus_qb_error_V=round(float(comp), 3),
           iavg_uA=round(float(idd2[t2 > T].mean())*1e6, 2), power_uW=round(float(idd2[t2 > T].mean())*vdd*1e6, 1))
print(json.dumps(res))
os.makedirs('../results/analog', exist_ok=True); open('../results/analog/comp_postlayout.jsonl', 'a').write(json.dumps(res) + '\n')
