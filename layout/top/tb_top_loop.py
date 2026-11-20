"""Short closed-loop check of the laid-out modulator: DC input steps, bit density of q versus the ideal first-order value 0.5*(1 + vin/vref), for the extracted layout devices without wiring C (nopar: pex/dsm_top_nopar_sim.spice, the control) and with it (pex: pex/dsm_top_pex_sim.spice, wiring C, no wire R).
Same stimulus as dsm1/sim/dsm1.py: vref 0.8 V around vcm (vcm from the replica), leak 10 Gohm out-g (ideal, stands in for the pseudo-resistor), 1.024 MHz 50 % clock, transistor-level clock generator and comparator.
usage: tb_top_loop.py nopar|pex [corner] [temp] [vdd] [ncyc]  -> one JSON line"""
import sys, os, json, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, '..', '..', 'common')); import simlib
def run(kind, corner='tt', temp=27, vdd=3.3, ncyc=48, vins=(0.0, 0.3, -0.4), f=1.024e6, vref=0.8):
    T = 1/f; hold = ncyc
    inc, sub = os.path.join(HERE, 'pex', 'dsm_top_pex_pruned.spice' if kind == 'pexp' else 'dsm_top_pex_sim.spice' if kind == 'pex' else 'dsm_top_nopar_sim.spice'), 'dsm_top_pex'   # dsm_top_sch.spice has lumped 300 um header devices that this PDK's ngspice bins cannot take
    pts = ','.join(f"{k*hold*T:.9g},{l},{(k+1)*hold*T-2e-9:.9g},{l}" for k, l in enumerate(vins))
    b = f".include {inc}\nVdda vdda 0 {vdd}\nVclk clk 0 PULSE(0 {vdd} 0 {T/400:.3g} {T/400:.3g} {T/2 - T/400:.6g} {T:.6g})\n"
    b += f"Bvin vin 0 V = v(vcm) + pwl(time,{pts})\nBvrp vrp 0 V = v(vcm) + {vref}\nBvrn vrn 0 V = v(vcm) - {vref}\nRleak out g 1e10\n"
    b += f"Xd vdda 0 clk vin vrp vrn vcm q qb g out {sub}\n"
    b += f".options reltol=1e-4 vntol=1e-7\n.control\ntran {T/50:.6g} {len(vins)*hold*T:.6g} 0 {T/50:.6g}\nwrdata OUT v(q) v(out) v(vcm)\n.endc\n"
    a, _ = simlib.run(b, corner, temp, tag='toploop', timeout=3000); t = a[:, 0]; q = a[:, 1]; out = a[:, 3]; vc = a[:, 5]
    res = dict(kind=kind, corner=corner, temp=temp, vdd=vdd, ncyc=ncyc, vcm_V=round(float(vc[-1]), 3))
    for k, l in enumerate(vins):
        bits = [float(np.interp((k*hold + c + 0.4)*T, t, q)) > vdd/2 for c in range(hold)][16:]       # skip start-up
        res[f'vin_{l:+.1f}'] = dict(density=round(float(np.mean(bits)), 3), ideal=round(0.5*(1 + l/vref), 3), n=len(bits))
    res['out_swing_V'] = [round(float(out[t > 16*T].min()), 2), round(float(out[t > 16*T].max()), 2)]
    return res
if __name__ == '__main__':
    kind = sys.argv[1]; args = sys.argv[2:]
    r = run(kind, *( [args[0]] if args else []) , **({} if len(args) < 4 else dict(temp=float(args[1]), vdd=float(args[2]), ncyc=int(args[3]))))
    print(json.dumps(r))
