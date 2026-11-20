"""Runs the per-step accuracy comparison (step_check.check) for the configurations discussed in the README.
Writes ../results/step_check.txt.  About 35 s per case (900 cycles = one full tone period)."""
import os, step_check
CASES = [
 ("baseline (original switch sizes)",              {}),
 ("fclk = 512 kHz (half clock)",             dict(fclk=512000.0)),
 ("p2_early=1 (DAC switch opens early)",     dict(p2_early=1.0)),
 ("all TGs x0.5",                            dict(tg_scale=0.5)),
 ("Vref 0.5 V, Vin 0.25 V peak",             dict(vref=0.5, vin_amp=0.25)),
 ("sin x0.5",                                dict(sc_sin=0.5)),
 ("st1 x0.5",                                dict(sc_st1=0.5)),
 ("sb2 x0.5",                                dict(sc_sb2=0.5)),
 ("st2 x0.5",                                dict(sc_st2=0.5)),
 ("dac mux x0.5",                            dict(sc_dac=0.5)),
 ("sin+st2 x0.5",                            dict(sc_sin=0.5, sc_st2=0.5)),
 ("sin+st1+st2 x0.5",                        dict(sc_sin=0.5, sc_st1=0.5, sc_st2=0.5)),
 ("sin+st1+st2 x0.25",                       dict(sc_sin=0.25, sc_st1=0.25, sc_st2=0.25)),
]
os.makedirs('../results', exist_ok=True)
hdr = f"{'case':40s} {'gain':>7s} {'cubic':>8s} {'resid mV':>9s} {'resid mV (+level terms)':>24s} {'step-cubic':>11s}\n"
out = ["TT, 27 C, 3.3 V, 1.024 MHz unless stated; ~840 cycles analysed per case (one full tone period); step = out(end of phi2) difference per cycle\n", hdr]
for name, kw in CASES:
    r = step_check.check(**kw)
    out.append(f"{name:40s} {r['gain']:7.4f} {r['cubic']:8.4f} {r['resid_rms_mV']:9.2f} {r['res_with_level_terms_mV']:24.2f} {r['c_step3']:11.4f}\n")
    print(out[-1], end='', flush=True)
open('../results/step_check.txt', 'w').write(''.join(out))
