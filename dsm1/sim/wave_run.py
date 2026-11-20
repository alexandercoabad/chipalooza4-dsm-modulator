import sys, numpy as np, run_dsm
t,c,T=run_dsm.run(ncyc=1800, corner='tt', temp=27, vdd=3.3, fin=2000.0, real_clk=True, real_comp=True, tg_scale=0.5, pts_per_cycle=200, reltol=1e-4, vntol=1e-7)
np.savez('../results/wave_realblocks_allTGx0p5.npz', t=t, q=c['q'], out=c['out'], vcm=c['vcm'], g=c['g'], T=T)
print('done', len(t))
