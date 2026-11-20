"""Clock generator test bench: edge timing of every phase, with the modulator's switch loads attached.
usage: python3 tb_clk.py [corner] [temp] [vdd] [key=value ...]   (keys: gap_ln, gap_cl, early_ln, early_cl, cmp_ln, cmp_cl, cmp_st)"""
import sys, os, json, numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'v2', 'sim'))
import cells, simlib, v2
def main(corner='tt', temp=27, vdd=3.3, fclk=1.024e6, kv=None, ncyc=4):
    kv = kv or {}; T = 1/fclk
    dk = dict(gap=dict(ln=kv.get('gap_ln', 4.0), lp=kv.get('gap_ln', 4.0), cload=kv.get('gap_cl', 20e-15)),
              early=dict(ln=kv.get('early_ln', 4.0), lp=kv.get('early_ln', 4.0), cload=kv.get('early_cl', 20e-15)),
              cmp=dict(ln=kv.get('cmp_ln', 4.0), lp=kv.get('cmp_ln', 4.0), cload=kv.get('cmp_cl', 60e-15), stages=int(kv.get('cmp_st', 4))))
    net = f"Vdda vdda 0 {vdd}\nVclk clk 0 PULSE(0 {vdd} 5n 2n 2n {T/2-2e-9:.6g} {T:.6g})\n"
    net += cells.clockgen('g', 'clk', **dk)
    v2.TG_WN, v2.TG_WP = 8.0, 24.0                       # switch loads as in the modulator: sin (p1), st1 (p1a), sb2 + st2 (p2)
    net += v2.tg('ls', 'la', 'lb', 'p1', 'p1b') + v2.tg('l1', 'lc', 'ld', 'p1a', 'p1ab')
    net += v2.tg('l2', 'le', 'lf', 'p2', 'p2b') + v2.tg('l3', 'lg', 'lh', 'p2', 'p2b')
    for x in 'abcdefgh': net += f"Cl{x} l{x} 0 100f\n"
    net += f".options reltol=1e-4 vntol=1e-7\n.control\ntran 0.2n {ncyc*T:.6g}\nwrdata OUT v(clk) v(p1a) v(p1ab) v(p1) v(p1b) v(p2) v(p2b) v(cc) i(Vdda)\n.endc\n"
    a, so = simlib.run(net, corner, temp, tag='clk'); t = a[:, 0]
    W = {k: a[:, 2*i+1] for i, k in enumerate(['clk', 'p1a', 'p1ab', 'p1', 'p1b', 'p2', 'p2b', 'cc', 'idd'])}
    h = vdd/2
    def edges(x, tmin):
        s = x > h; r = np.where(~s[:-1] & s[1:])[0]; f = np.where(s[:-1] & ~s[1:])[0]
        interp = lambda i: t[i] + (h - x[i]) * (t[i+1]-t[i]) / (x[i+1]-x[i])
        return [interp(i) for i in r if t[i] > tmin], [interp(i) for i in f if t[i] > tmin]
    E = {k: edges(W[k], 2*T) for k in ['clk', 'p1a', 'p1', 'p2', 'cc']}
    nxt = lambda l, after: min(x for x in l if x > after)
    ck_r = nxt(E['clk'][0], 2*T); p2_f = nxt(E['p2'][1], ck_r - 1e-9); p1a_r = nxt(E['p1a'][0], p2_f)
    p1_r = nxt(E['p1'][0], p2_f); cc_r = nxt(E['cc'][0], p1a_r - 1e-9)
    ck_f = nxt(E['clk'][1], ck_r); p1a_f = nxt(E['p1a'][1], ck_f - 1e-9); p1_f = nxt(E['p1'][1], ck_f - 1e-9)
    cc_f = nxt(E['cc'][1], ck_f - 1e-9); p2_r = nxt(E['p2'][0], p1_f - 1e-9)
    r = dict(corner=corner, temp=temp, vdd=vdd, fclk=fclk)
    ns = lambda x: round(float(x)*1e9, 2)
    r['dead_time_p2fall_to_p1a_rise_ns'] = ns(p1a_r - p2_f)          # must be > 0: top-plate switch closes after the DAC/transfer switches opened
    r['dead_time_p2fall_to_p1_rise_ns']  = ns(p1_r - p2_f)
    r['dead_time_p1fall_to_p2_rise_ns']  = ns(p2_r - p1_f)           # must be > 0: p1 (late, input sampling) vs p2 (DAC, transfer)
    r['early_open_p1a_fall_to_p1_fall_ns'] = ns(p1_f - p1a_f)        # must be > 0: bottom-plate sampling
    r['p2_fall_after_clk_rise_ns'] = ns(p2_f - ck_r)
    r['cc_rise_after_p2_fall_ns'] = ns(cc_r - p2_f)                  # comparator waits this long after the integrator is released
    r['cc_fall_before_p2_rise_ns'] = ns(p2_r - cc_f)
    r['duty_phase_p1a_pct'] = round(100*float(p1a_f - p1a_r)/T, 1); r['duty_phase_p2_pct'] = round(100*float(p2_r - p2_f)/T, 1) if False else None
    def near(l, x): return min(l, key=lambda y: abs(y - x))
    sk = {}
    for p, pb in (('p1', 'p1b'), ('p1a', 'p1ab'), ('p2', 'p2b')):
        rp, fp = edges(W[p], 2*T); rb, fb = edges(W[pb], 2*T)
        x = nxt(rp, 2*T); y = nxt(fp, 2*T)
        sk[p] = dict(on_nfet_minus_pfet_ns=ns(x - near(fb, x)), off_nfet_minus_pfet_ns=ns(y - near(rb, y)))   # on: >0 = pfet gate moves first; off: <0 = nfet turns off first
    r['p_vs_pb_skew'] = sk
    r['iavg_uA'] = float(-W['idd'][t > T].mean()*1e6)
    return {k: (round(v, 2) if isinstance(v, float) else v) for k, v in r.items()}
if __name__ == '__main__':
    kv = {k: float(v) for k, v in (a.split('=') for a in sys.argv[4:])}
    print(json.dumps(main(sys.argv[1] if len(sys.argv) > 1 else 'tt', float(sys.argv[2]) if len(sys.argv) > 2 else 27, float(sys.argv[3]) if len(sys.argv) > 3 else 3.3, kv=kv)))
