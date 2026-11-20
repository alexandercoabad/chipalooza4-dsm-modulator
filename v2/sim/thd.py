import numpy as np, simlib, v2, json, pickle
from multiprocessing import Pool
RIN=json.load(open('rin_design.json'))
GN=v2.GAIN_TARGETS_DB
def job(a):
    code,vopp,corner,vdd,temp=a
    gl=10**(GN[code]/20)
    vin_pk=vopp/2/gl
    f0=1e5; T=1/f0; ncyc=14
    b=v2.netlist(RIN,code,vdd=vdd,ain=f"dc 0 sin(0 {vin_pk} {f0})")+f""".control
tran 10n {ncyc*T}
meas tran dummy find v(out) at={ncyc*T}
wrdata OUT v(out)
.endc
"""
    d,so=simlib.run(b,corner,temp)
    t,v=d[:,0],d[:,1]
    tt=np.linspace(4*T,ncyc*T,10*2**9,endpoint=False)   # last 10 cycles, 5120 pts
    y=np.interp(tt,t,v); y-=y.mean()
    F=np.abs(np.fft.rfft(y*np.hanning(len(y))))
    k=10  # fundamental bin (10 cycles)
    h=lambda n: F[n*k-1:n*k+2].max()
    thd=np.sqrt(sum(h(n)**2 for n in range(2,8)))/h(1)
    vpp=(np.max(v[t>4*T])-np.min(v[t>4*T]))
    fund_pk=h(1)*2/np.sum(np.hanning(len(y)))
    return (a,20*np.log10(thd),vpp,fund_pk/vin_pk)
if __name__=='__main__':
    jobs=[(c,v,'tt',3.3,27) for c in (0,3,7) for v in (0.1,0.5,1.0,1.5,2.0)]
    jobs+=[(7,v,cr,vd,T) for v in (0.1,1.0) for (cr,vd,T) in (('ss',2.97,110),('ff',3.63,-40))]
    with Pool(2) as p: res=p.map(job,jobs)
    pickle.dump(res,open('thd.pkl','wb'))
    for a,th,vpp,g in res: print(a,f"THD {th:.1f} dB  vpp_meas {vpp:.3f}  gain {20*np.log10(g):.2f} dB",flush=True)
