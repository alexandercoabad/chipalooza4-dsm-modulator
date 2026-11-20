import numpy as np, simlib, v2, json
from scipy.optimize import brentq
def gain_at(Rin,code,corner='tt',temp=27,vdd=3.3,f=1e5,**kw):
    b=v2.netlist(Rin,code,vdd=vdd,**kw)+f""".control
op
ac lin 1 {f} {f}
let gdb=db(v(out)/v(in))
wrdata OUT gdb
.endc
"""
    a,so=simlib.run(b,corner,temp)
    return float(a[-1]) if a.ndim==1 else float(a[0,-1])
if __name__=='__main__':
    Rin=[3000.0]*8
    out=[]
    for k,t in enumerate(v2.GAIN_TARGETS_DB):
        def f(lr):
            R=list(Rin); R[k]=np.exp(lr)
            return gain_at(R,k)-t
        lr=brentq(f,np.log(500),np.log(200e3),xtol=1e-3)
        Rin[k]=float(np.exp(lr)); print(k,t,round(Rin[k]),flush=True)
    json.dump(Rin,open('rin_design.json','w'))
