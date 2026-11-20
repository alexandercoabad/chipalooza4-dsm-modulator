"""INL / DNL from the DC staircase (inl_run.py). Output code on a 10-bit scale: code = 1024 * (density of ones over the last 1024 clocks of each level).
INL: deviation from the least-squares line (and from the end-point line), in LSB10 = 1.6 V / 1024 = 1.5625 mV of input.
DNL: step DNL between adjacent DC levels (steps of ~31 LSB with all 33 levels (~62 LSB with the 17 even levels), NOT 1-LSB code-width DNL, which a 1st-order sigma-delta cannot be measured to with DC averaging)."""
import sys, json, glob, numpy as np, matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
PFX = sys.argv[1] if len(sys.argv) > 1 else 'inl'; OUT = 'inl_dnl' if PFX == 'inl' else PFX + '_dnl'     # 'inl' (ideal caps) or 'inl_par' (with array parasitics)
d = sorted([json.load(open(f)) for f in glob.glob(f'../results/{PFX}_level_*.json')], key=lambda r: r['k'])   # whatever levels have finished
x = np.array([r['vin'] for r in d]); code = 1024*np.array([r['ones_density'] for r in d]); LSB = 1.6/1024
b, a = np.polyfit(x, code, 1); fit = a + b*x; inl = code - fit
ep = code[0] + (code[-1]-code[0])*(x-x[0])/(x[-1]-x[0]); inl_ep = code - ep
step = np.diff(x)/LSB; mean_step = (code[-1]-code[0])/(len(x)-1); dnl = np.diff(code)/mean_step - 1
ideal_slope = 1024/1.6
res = dict(points=len(x), vin_range_V=[float(x[0]), float(x[-1])], slope_codes_per_V=float(b), ideal_slope=ideal_slope, gain_error_pct=float(100*(abs(b)/ideal_slope-1)),
           offset_LSB10=float(a-512), inl_lsq_max_LSB=float(np.abs(inl).max()), inl_lsq_pp_LSB=float(inl.max()-inl.min()), inl_endpoint_max_LSB=float(np.abs(inl_ep).max()),
           dnl_step_max_LSB=float(np.abs(dnl).max()), dnl_step_size_LSB=float(step.mean()), measurement_resolution_LSB=1.0,
           integrator_out_V=[min(r['out_min'] for r in d), max(r['out_max'] for r in d)])
json.dump(res, open(f'../results/{OUT}_summary.json', 'w'), indent=1); print(json.dumps(res, indent=1))
fig, ax = plt.subplots(3, 1, figsize=(9, 9), sharex=True)
ax[0].plot(x, code, 'o-', ms=3); ax[0].plot(x, fit, 'k--', lw=.8, label='least-squares line'); ax[0].set_ylabel('output code (10-bit scale)'); ax[0].legend(); ax[0].set_title('DC transfer, transistor-level modulator (all TGs x0.5, ideal comparator/clock, TT/27 C/3.3 V' + (', with Cs/Ci array parasitics)' if PFX != 'inl' else ')'), fontsize=9)
ax[1].axhspan(-1, 1, color='0.9', label='about +/-1 LSB measurement resolution'); ax[1].plot(x, inl, 'o-', ms=3, label='vs least-squares line'); ax[1].plot(x, inl_ep, 's--', ms=3, lw=.7, label='vs end-point line'); ax[1].set_ylabel('INL (LSB10)'); ax[1].legend(fontsize=8)
ax[2].axhspan(-1/mean_step*1, 1/mean_step*1, color='0.9'); ax[2].bar((x[:-1]+x[1:])/2, dnl, width=0.03, color='C2'); ax[2].set_ylabel('step DNL (LSB, %.0f-LSB steps)' % step.mean()); ax[2].set_xlabel('DC input relative to vcm (V)')
for a_ in ax: a_.grid(alpha=.3)
fig.tight_layout(); fig.savefig(f'../results/{OUT}.png', dpi=120)
