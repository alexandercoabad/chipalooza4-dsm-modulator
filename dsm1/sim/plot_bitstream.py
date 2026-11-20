"""Input sine and output bitstream of the transistor-level modulator over one sine period.
usage: python3 plot_bitstream.py [cycles_per_period=128] [amp_fraction_of_fullscale=0.7] [key=value ...]   -> ../results/bitstream_vs_sine.png"""
import sys, numpy as np, matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
import dsm1, run_dsm
P = int(sys.argv[1]) if len(sys.argv) > 1 else 128
frac = float(sys.argv[2]) if len(sys.argv) > 2 else 0.7
kw = {k: float(v) for k, v in (a.split('=') for a in sys.argv[3:])}
fclk = kw.pop('fclk', 1.024e6); vref = kw.pop('vref', 0.8); vdd = kw.get('vdd', 3.3)
fin = fclk/P; A = frac*vref
t, c, T = run_dsm.run(ncyc=3*P, fclk=fclk, fin=fin, vin_amp=A, vref=vref, **kw)
t0, t1 = P*T, 2*P*T                                    # second period: start-up settled, phase 0 at t0
m = (t >= t0) & (t <= t1)
x = (t[m]-t0)/T                                        # clock cycles
bits = (c['q'][m] - vdd/2)/(vdd/2)                     # q normalised to +/-1 (= +/-Vref)
vin = frac*np.sin(2*np.pi*x/P)                         # input normalised to full scale (+/-Vref)
b = np.where(np.interp((np.arange(P)+0.4)*T+t0, t, c['q']) > vdd/2, 1.0, -1.0)
k = 16; y = np.convolve(np.r_[b[-k+1:], b], np.ones(k)/k, 'valid')            # 16-cycle moving average (crude decimator)
xs = np.arange(P)+0.4-(k-1)/2                          # centre of each averaging window
corr = np.corrcoef(np.interp(xs, np.arange(P)+0.4, frac*np.sin(2*np.pi*(np.arange(P)+0.4)/P)), y)[0, 1]
fig, ax = plt.subplots(figsize=(13, 5.2))
ax.plot(x, bits, color='#1f3fbf', lw=1.1, label='Output bitstream'); ax.plot(x, vin, color='#e01010', lw=1.8, label='Input sine wave')
ax.set_xlim(0, P); ax.set_ylim(-1.1, 1.1); ax.set_xticks(np.linspace(0, P, 9)); ax.set_yticks(np.linspace(-1, 1, 7))
ax.grid(ls=':', c='k', alpha=.7); ax.set_xlabel('clock cycles (T = %.3f us)' % (T*1e6)); ax.set_ylabel('normalised to full scale (+/-Vref = +/-%.1f V)' % vref)
ax.annotate('Input Sine Wave', xy=(P*0.25, frac), xytext=(P*0.18, 1.18), ha='center', annotation_clip=False, arrowprops=dict(arrowstyle='->', lw=.8), fontsize=11)
ax.annotate('Output Bitstream', xy=(P*0.56, 0.95), xytext=(P*0.70, 1.18), ha='center', annotation_clip=False, arrowprops=dict(arrowstyle='->', lw=.8), fontsize=11)
fig.text(0.5, 0.01, 'Input sine wave and output bitstream of the first-order SC delta-sigma modulator (Sky130 transistor-level, TT 27 C 3.3 V; '
         '%d clock cycles per sine period, input %.0f%% of full scale)' % (P, 100*frac), ha='center', fontsize=9)
plt.tight_layout(rect=(0, 0.04, 1, 0.94)); out = '../results/bitstream_vs_sine.png'; plt.savefig(out, dpi=110)
print('wrote', out, '| ones density: %.2f | corr(16-cycle moving average of bits, input) = %.4f | out swing %.2f..%.2f V' % ((b > 0).mean(), corr, c['out'][m].min(), c['out'][m].max()))
