"""Sine-input SNDR of the laid-out modulator (extracted netlist, wiring capacitance, no wire R): vin = vcm + A sin(2 pi fin t), A = 0.4 V, vref 0.8 V, 1.024 MHz, q sampled 0.4 T after each clock edge.
N = 4096 samples (+ 64 start-up), fin = 7 bins = 1.75 kHz (coherent), Hann window, band 0..4 kHz (OSR 128, as the CIC2 decimator), signal = peak bin +-2, DC and bin 1 excluded from the noise.
usage: tb_top_sndr.py pexp|pex|nopar [corner] [temp] [vdd] [N]   -> results/top_sndr_<kind>_<corner>.json ; ~0.7 s per clock cycle on the 2-core cloud machine (about 50 min for N = 4096)"""
import sys, os, json, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, '..', '..', 'common')); import simlib
def sndr(bits, f, fin_bin, osr=128, amp_ref=None):
    N = len(bits); x = np.asarray(bits, float)*2 - 1; w = np.hanning(N); X = np.abs(np.fft.rfft((x - x.mean())*w))**2
    band = N//(2*osr); k0 = fin_bin
    sig = X[k0-2:k0+3].sum(); mask = np.ones(band+1, bool); mask[:2] = False; mask[k0-2:k0+3] = False
    noise = X[:band+1][mask].sum(); return 10*np.log10(sig/noise), band
def run(kind='pexp', corner='tt', temp=27, vdd=3.3, N=4096, A=0.4, vref=0.8, f=1.024e6, fin_bin=7, start=64):
    T = 1/f; fin = fin_bin*f/N; ncyc = N + start
    inc = os.path.join(HERE, 'pex', {'pexp': 'dsm_top_pex_pruned.spice', 'pex': 'dsm_top_pex_sim.spice', 'nopar': 'dsm_top_nopar_sim.spice'}[kind])
    b = f".include {inc}\nVdda vdda 0 {vdd}\nVclk clk 0 PULSE(0 {vdd} 0 {T/400:.3g} {T/400:.3g} {T/2 - T/400:.6g} {T:.6g})\n"
    b += f"Bvin vin 0 V = v(vcm) + {A}*sin(2*3.14159265358979*{fin:.9g}*time)\nBvrp vrp 0 V = v(vcm) + {vref}\nBvrn vrn 0 V = v(vcm) - {vref}\nRleak out g 1e10\n"
    b += f"Xd vdda 0 clk vin vrp vrn vcm q qb g out dsm_top_pex\n.options reltol=1e-4 vntol=1e-7\n.control\nsave v(q) v(out)\ntran {T/50:.6g} {ncyc*T:.6g} 0 {T/50:.6g}\nwrdata OUT v(q) v(out)\n.endc\n"
    a, _ = simlib.run(b, corner, temp, tag='sndr', timeout=20000); t = a[:, 0]; q = a[:, 1]
    bits = [float(np.interp((c + 0.4)*T, t, q)) > vdd/2 for c in range(start, ncyc)]
    s, band = sndr(bits, f, fin_bin)
    return dict(kind=kind, corner=corner, temp=temp, vdd=vdd, N=N, amp_V=A, fin_Hz=fin, band_bins=band, sndr_dB=round(float(s), 2), mean_density=round(float(np.mean(bits)), 4)), bits
if __name__ == '__main__':
    kind = sys.argv[1]; c = sys.argv[2] if len(sys.argv) > 2 else 'tt'; temp = float(sys.argv[3]) if len(sys.argv) > 3 else 27; vdd = float(sys.argv[4]) if len(sys.argv) > 4 else 3.3; N = int(sys.argv[5]) if len(sys.argv) > 5 else 4096
    r, bits = run(kind, c, temp, vdd, N); print(json.dumps(r))
    os.makedirs(os.path.join(HERE, 'results'), exist_ok=True)
    json.dump(r, open(os.path.join(HERE, 'results', f'top_sndr_{kind}_{c}.json'), 'w')); open(os.path.join(HERE, 'results', f'top_bits_{kind}_{c}.txt'), 'w').write(''.join('1' if x else '0' for x in bits))
