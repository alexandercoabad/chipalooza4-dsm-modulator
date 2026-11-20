"""Short real-block run for the overlay figure: 8 kHz tone = fclk/128 (128 clocks per period), 0.56 V peak = 70 % of full scale, 4 periods after a 128-clock start-up."""
import numpy as np, run_dsm
t,c,T=run_dsm.run(ncyc=128*5+2, corner='tt', temp=27, vdd=3.3, fin=1.024e6/128, vin_amp=0.56, real_clk=True, real_comp=True, tg_scale=0.5, pts_per_cycle=200, reltol=1e-4, vntol=1e-7)
np.savez('../results/wave_overlay_8kHz_realblocks.npz', t=t, q=c['q'], out=c['out'], vcm=c['vcm'], T=T); print('done', len(t))
