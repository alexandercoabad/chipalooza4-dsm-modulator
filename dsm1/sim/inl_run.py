"""INL/DNL sweep, pre-layout: DC inputs through the transistor-level modulator (all TGs x0.5, ideal comparator and clock, TT 27 C 3.3 V).
One simulation per level (256 clocks settle + 1024 clocks averaged), saved level by level. Usage: inl_run.py [par]  ("par" = with the extracted Cs/Ci array parasitics, results inl_par_level_*.json). Run ONE instance at a time: two parallel ngspice runs
on 2 cores were about 7x slower each (5 s vs 35 s per 100 clocks). Even levels first (a complete 17-point sweep), then the odd ones (33 points)."""
import sys, json, numpy as np, run_dsm
PAR = len(sys.argv) > 1 and sys.argv[1] == "par"     # "par": add the extracted capacitor-array parasitics (layout/mim): g 19.4 fF, Cs top 10.0 fF, Cs bottom 26.1 fF, Ci bottom/out 51.0 fF to substrate
KW = dict(cpar_g=19.4e-15, cpar_t=10.03e-15, cpar_b=26.1e-15, cpar_out=51.05e-15) if PAR else {}
PFX = "inl_par" if PAR else "inl"
SETTLE, MEAS = 256, 1024
levels = np.linspace(-0.78, 0.78, 33)
for k in list(range(0, 33, 2)) + list(range(1, 33, 2)):
    v = float(levels[k]); n = SETTLE + MEAS
    t, c, T = run_dsm.run(ncyc=n, corner='tt', temp=27, vin_levels=[v], hold_cycles=n, tg_scale=0.5, **KW)
    bits = (np.interp((np.arange(n)+0.4)*T, t, c['q']) > 1.65).astype(int)[SETTLE:]
    o = np.interp((np.arange(SETTLE, n)+0.3)*T, t, c['out'])
    json.dump({'k': k, 'vin': v, 'ones_density': float(bits.mean()), 'meas_cycles': MEAS, 'out_min': float(o.min()), 'out_max': float(o.max())}, open(f'../results/{PFX}_level_{k:02d}.json', 'w'))
    print('level', k, round(v, 4), round(float(bits.mean()), 4), flush=True)
