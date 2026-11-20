"""Compare each simulated integrator step with the ideal (Cs/Ci)(Vin_sampled - Vdac). Reports gain error, offset, 3rd-order term, residual."""
import sys, numpy as np, dsm1, run_dsm
def check(ncyc=900, M=5, N=4096, **kw):   # 900 cycles ~ one full period of the M=5/N=4096 tone (819 cycles)
    fclk = kw.get('fclk', 1.024e6); fin = M*fclk/N
    t, c, T = run_dsm.run(ncyc=ncyc, fin=fin, **kw)
    vref = kw.get('vref', 0.8); A = kw.get('vin_amp', 0.4); cs, ci = kw.get('cs',2e-12), kw.get('ci',4e-12)
    n = np.arange(60, ncyc-2)
    vcm = c['vcm'][-1]
    out_end = lambda k: np.interp((k+0.95)*T, t, c['out'])
    step = out_end(n) - out_end(n-1)
    q = np.interp((n+0.4)*T, t, c['q']) > kw.get('vdd',3.3)/2
    vin = A*np.sin(2*np.pi*fin*(n+0.47)*T); vd = np.where(q, vref, -vref)
    exp = (cs/ci)*(vin - vd)
    X = np.vstack([exp, exp**3, np.ones_like(exp)]).T
    coef, *_ = np.linalg.lstsq(X, step, rcond=None)
    res = step - X@coef
    lvl = out_end(n-1) - vcm                                  # where the output sits before the step
    X2 = np.vstack([exp, exp**3, np.ones_like(exp), lvl, lvl**3]).T
    c2, *_ = np.linalg.lstsq(X2, step, rcond=None); res2 = step - X2@c2
    gerr = np.interp((n+0.95)*T, t, c['g']) - vcm          # virtual-ground error at end of phi2
    return dict(res_with_level_terms_mV=1e3*res2.std(), c_step3=c2[1], c_lvl1=c2[3], c_lvl3=c2[4], lvl_pp=float(np.ptp(lvl)), gain=coef[0], cubic=coef[1], offset_mV=1e3*coef[2], resid_rms_mV=1e3*res.std(),
                step_rms_mV=1e3*exp.std(), g_err_mV=(1e3*gerr.mean(), 1e3*gerr.std()), corr_gerr_vs_exp=np.corrcoef(gerr, exp)[0,1])
if __name__ == '__main__':
    kw = {k:float(v) for k,v in (a.split('=') for a in sys.argv[1:])}
    r = check(**kw); print(kw, {k:(round(float(v),4) if not isinstance(v,tuple) else tuple(round(x,3) for x in v)) for k,v in r.items()})
