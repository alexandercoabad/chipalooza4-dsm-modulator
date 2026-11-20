"""Summary plots for the v2 amplifier (pre-layout, ngspice + Sky130 models).

Runs the simulations it needs (about 100 short ngspice runs, a few minutes on 2 cores), caches the data in
plot_cache.pkl, and writes PNG files to ../../results/plots/.
  python3 make_plots.py            # simulate (or reuse the cache) and plot
  python3 make_plots.py --fresh    # ignore the cache and re-simulate
Needs SKY130PR (see README) and matplotlib. Run from this directory so ngspice reads .spiceinit.
"""
import os, sys, json, pickle, time
import numpy as np
from multiprocessing import Pool
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import simlib, v2, sims2

RIN = json.load(open('rin_design.json'))
OUT = os.path.join('..', '..', 'results', 'plots')
CACHE = 'plot_cache.pkl'
CODES = range(8)
CC_LIST = [10e-12, 30e-12, 50e-12]              # on-chip coupling bank
CORNERS = [('tt', 3.3, 27), ('ss', 2.97, 110), ('ff', 3.63, -40)]
TARGET = v2.GAIN_TARGETS_DB

def curve(a):
    code, corner, vdd, temp = a
    b = v2.netlist(RIN, code, vdd=vdd) + ".control\nop\nac dec 20 1e3 1e9\nlet g=db(v(out)/v(in))\nwrdata OUT g\n.endc\n"
    d, _ = simlib.run(b, corner, temp)
    return a, d[:, 0], d[:, 1]

def mid(a):
    code, corner, vdd, temp = a
    b = v2.netlist(RIN, code, vdd=vdd) + ".control\nop\nac lin 1 1e5 1e5\nlet g=db(v(out)/v(in))\nwrdata OUT g\n.endc\n"
    d, _ = simlib.run(b, corner, temp)
    d = np.atleast_2d(d)
    return a, float(d[0, 1])

def simulate():
    data = {}
    with Pool(2) as p:
        t0 = time.time()
        data['curves'] = p.map(curve, [(k, 'tt', 3.3, 27) for k in CODES])
        data['mid'] = p.map(mid, [(k, c, v, T) for (c, v, T) in CORNERS for k in CODES])
        print('gain done', round(time.time() - t0), 's', flush=True)
        data['hp'] = p.map(sims2.acjob, [('hp', k, cc, 0, 'tt', None) for cc in CC_LIST for k in CODES])
        data['lp'] = p.map(sims2.acjob, [('lp', k, 1e-6, lp, 'tt', None) for lp in (0, 1, 2, 3) for k in CODES])
        print('corners done', round(time.time() - t0), 's', flush=True)
        data['noise'] = p.map(sims2.noisejob, [(k, 'tt', 27, 3.3) for k in CODES])
        data['settle'] = p.map(sims2.settle, [(0, cc, c, v, T) for cc in CC_LIST for (c, v, T) in
                                              (('tt', 3.3, 27), ('ss', 2.97, 110), ('ss', 2.97, -40), ('ff', 3.63, -40))])
        print('noise/settling done', round(time.time() - t0), 's', flush=True)
    return data

def save(fig, name):
    os.makedirs(OUT, exist_ok=True)
    fig.tight_layout(); fig.savefig(os.path.join(OUT, name), dpi=150); plt.close(fig)
    print('wrote', os.path.join(OUT, name))

def plot_all(D):
    cmap = plt.get_cmap('viridis')
    col = lambda k: cmap(k / 7)
    # 1 gain vs frequency per code (ideal coupling, Cf off)
    fig, ax = plt.subplots(figsize=(7, 4.2))
    for a, f, g in D['curves']:
        ax.semilogx(f, g, color=col(a[0]), label=f'code {a[0]}')
    ax.set_xlabel('Frequency (Hz)'); ax.set_ylabel('Gain (dB)'); ax.set_ylim(-10, 30); ax.grid(True, which='both', alpha=.3)
    ax.set_title('Gain vs frequency per code (tt, 27 °C, 3.3 V, ideal coupling, Cf off)'); ax.legend(ncol=4, fontsize=8)
    save(fig, 'gain_vs_frequency.png')
    # 2 midband gain vs code, three corners
    fig, ax = plt.subplots(figsize=(6.5, 4.2))
    ax.plot(list(CODES), TARGET, 'k--', label='design target')
    for (c, v, T) in CORNERS:
        y = [g for (a, g) in D['mid'] if a[1] == c and a[2] == v and a[3] == T]
        ax.plot(list(CODES), y, 'o-', label=f'{c}, {v} V, {T} °C')
    ax.set_xlabel('Gain code'); ax.set_ylabel('Gain at 100 kHz (dB)'); ax.grid(True, alpha=.3); ax.legend(fontsize=8)
    ax.set_title('Gain vs code at three corners')
    save(fig, 'gain_vs_code_corners.png')
    # 3 high-pass corner vs code per Cc
    fig, ax = plt.subplots(figsize=(6.5, 4.2))
    for cc in CC_LIST:
        pts = [(a[1], fl) for (a, m, fl, fh, pk) in D['hp'] if abs(a[2] - cc) < 1e-15]
        ax.semilogy([p[0] for p in pts], [p[1] / 1e3 for p in pts], 'o-', label=f'Cc = {cc*1e12:.0f} pF')
    ax.axhline(100, color='r', ls=':'); ax.axhline(1500, color='r', ls=':')
    ax.text(0.05, 110, 'spec limits 100 kHz and 1.5 MHz', color='r', fontsize=8)
    ax.set_xlabel('Gain code'); ax.set_ylabel('Low-frequency -3 dB corner (kHz)'); ax.grid(True, which='both', alpha=.3)
    ax.legend(fontsize=8); ax.set_title('On-chip high-pass corner (tt, 27 °C, 3.3 V, Cf off)')
    save(fig, 'highpass_corner_vs_code.png')
    # 4 low-pass corner vs code per Cf
    fig, ax = plt.subplots(figsize=(6.5, 4.2))
    for lp in (0, 1, 2, 3):
        pts = [(a[1], fh) for (a, m, fl, fh, pk) in D['lp'] if a[3] == lp]
        ax.semilogy([p[0] for p in pts], [p[1] / 1e6 for p in pts], 'o-', label=f'Cf = {v2.LPC[lp]*1e12:.0f} pF')
    ax.set_xlabel('Gain code'); ax.set_ylabel('Upper -3 dB corner (MHz)'); ax.grid(True, which='both', alpha=.3)
    ax.legend(fontsize=8); ax.set_title('Upper corner vs feedback capacitor (tt, 27 °C, 3.3 V)')
    save(fig, 'lowpass_corner_vs_code.png')
    # 5 input-referred noise (midband; the rise at low frequency is the 1 uF coupling-cap roll-off, not device noise)
    fig, ax = plt.subplots(figsize=(7, 4.2))
    for a, f, n in D['noise']:
        m = f >= 1e4
        ax.loglog(f[m], n[m] * 1e9, color=col(a[0]), label=f'code {a[0]}')
    ax.axvline(1e5, color='gray', ls='--'); ax.text(1.1e5, 6, '100 kHz (spec point)', fontsize=8, color='gray')
    ax.axhline(35, color='r', ls=':'); ax.text(1.2e4, 37, 'max limit 35 nV/√Hz at 100 kHz', color='r', fontsize=8)
    ax.set_xlabel('Frequency (Hz)'); ax.set_ylabel('Input-referred noise (nV/√Hz)'); ax.set_ylim(5, 60); ax.grid(True, which='both', alpha=.3)
    ax.set_title('Input-referred noise (tt, 27 °C, 3.3 V, ideal resistors)'); ax.legend(ncol=4, fontsize=8)
    save(fig, 'input_referred_noise.png')
    # 6 enable settling, code 0
    fig, ax = plt.subplots(figsize=(7, 4.2))
    labels = ['tt 27 °C', 'ss 110 °C', 'ss −40 °C', 'ff −40 °C']
    x = np.arange(len(labels)); w = 0.27
    for i, cc in enumerate(CC_LIST):
        y = [ts * 1e6 for (a, fin, ts, te) in D['settle'] if abs(a[1] - cc) < 1e-15]
        ax.bar(x + (i - 1) * w, y, w, label=f'Cc = {cc*1e12:.0f} pF')
    ax.axhline(50, color='r', ls=':'); ax.text(-0.4, 51.5, 'max limit 50 µs', color='r', fontsize=8)
    ax.set_xticks(x); ax.set_xticklabels(labels); ax.set_ylabel('Settling time after enable (µs)'); ax.set_ylim(0, 60)
    ax.legend(fontsize=8); ax.set_title('Enable settling, code 0, on-chip coupling'); ax.grid(True, axis='y', alpha=.3)
    save(fig, 'enable_settling.png')

if __name__ == '__main__':
    if '--fresh' in sys.argv or not os.path.exists(CACHE):
        D = simulate(); pickle.dump(D, open(CACHE, 'wb'))
    else:
        D = pickle.load(open(CACHE, 'rb'))
    plot_all(D)
