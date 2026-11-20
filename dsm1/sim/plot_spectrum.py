"""Plot the output spectrum saved by run_sndr.py (<name>_P.npy).  usage: python3 plot_spectrum.py ../results/sndr_tt_P.npy N M [osr] [fclk]"""
import sys, numpy as np, matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
P = np.load(sys.argv[1]); N = int(sys.argv[2]); M = int(sys.argv[3])
osr = int(sys.argv[4]) if len(sys.argv) > 4 else 128; fclk = float(sys.argv[5]) if len(sys.argv) > 5 else 1.024e6
ref = P[M-3:M+4].sum(); f = np.arange(len(P))*fclk/N
plt.figure(figsize=(10, 4.5)); plt.semilogx(f[1:]/1e3, 10*np.log10(P[1:]/ref + 1e-30), lw=.6)
plt.axvline(fclk/(2*osr)/1e3, c='r', ls='--', lw=.8); plt.xlabel('kHz'); plt.ylabel('dB rel. tone'); plt.ylim(-110, 5); plt.grid(alpha=.3)
plt.title(sys.argv[1]); out = sys.argv[1].replace('_P.npy', '_spectrum.png'); plt.savefig(out, dpi=90); print('wrote', out)
