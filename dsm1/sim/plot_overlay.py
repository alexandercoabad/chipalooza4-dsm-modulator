"""Thesis-style overlay (Fig. 3.8 style): one period of the input sine over the modulator bitstream (+/-1), from wave_run_overlay.py.
The sine is the ideal source (0.56 V peak) normalised to full scale (Vref 0.8 V) = +/-0.7 of the bit amplitude."""
import numpy as np, matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
d=np.load('../results/wave_overlay_8kHz_realblocks.npz'); t,q,T=d['t'],d['q'],float(d['T']); n=128
fig,axs=plt.subplots(2,1,figsize=(11,7))
for ax,k0,ttl in ((axs[0],128*2,'period 3'),(axs[1],128*3,'period 4')):
    idx=(np.arange(k0,k0+n)+0.4)*T; bits=np.where(np.interp(idx,t,q)>1.65,1.0,-1.0)
    tm=np.linspace(k0*T,(k0+n)*T,1500); sine=0.7*np.sin(2*np.pi*(1.024e6/128)*tm)
    ax.step((idx-k0*T)*1e6,bits,where='mid',color='#1f2fa8',lw=.9,label='Output bitstream (q)')
    ax.plot((tm-k0*T)*1e6,sine,color='#d62728',lw=2.2,label='Input sine (ideal source, normalised to full scale)')
    ax.set_xlim(0,n*T*1e6); ax.set_ylim(-1.1,1.1); ax.set_xlabel('time (us)'); ax.set_yticks([-1,-.7,0,.7,1]); ax.grid(ls=':',alpha=.6); ax.set_ylabel('normalised to full scale'); ax.set_title(ttl,fontsize=8,loc='left')
axs[0].legend(loc='lower left',fontsize=8,framealpha=.95)
fig.suptitle('Input sine and output bitstream, 1st-order SC delta-sigma modulator\n(transistor-level comparator + clock generator, all TGs x0.5, TT/27 C/3.3 V, 8 kHz tone, 70 % of full scale, 128 clocks per period)',fontsize=9)
fig.tight_layout(rect=(0,0,1,.95)); fig.savefig('../results/sine_and_bitstream_overlay.png',dpi=130)
# first-order check: local density of ones follows the sine
idx=(np.arange(128*2,128*4)+0.4)*T; b=np.where(np.interp(idx,t,q)>1.65,1.0,-1.0); s=np.sin(2*np.pi*(1.024e6/128)*idx)
print('corr(16-clock moving average of bits, sine) = %.3f'%np.corrcoef(np.convolve(b,np.ones(16)/16,'same')[8:-8],s[8:-8])[0,1])
