import numpy as np, simlib, itertools, sys
from multiprocessing import Pool
def body(L,Wn,Wp,vdd):
    return f"""
Vdd vdd 0 {vdd}
Vin vin 0 dc 0 ac 1
Cin vin g 10u
Rf g out 1e9
Xp out g vdd vdd sky130_fd_pr__pfet_g5v0d10v5 w={Wp} l={L} nf=1 mult=1
Xn out g 0 0 sky130_fd_pr__nfet_g5v0d10v5 w={Wn} l={L} nf=1 mult=1
.control
op
let idd=-i(Vdd)
let vb=v(out)
print vb idd
ac dec 10 100 1e9
let gdb=db(v(out)/v(vin))
wrdata OUT gdb
.endc
"""
def job(a):
    L,Wn,r=a
    try:
        d,so=simlib.run(body(L,Wn,Wn*r,3.3),'tt',27)
    except Exception as e: return (L,Wn,r,None)
    f,g=d[:,0],d[:,1]
    P=simlib.parse(so); vals=[P['vb'],P['idd']]
    i1=np.argmin(abs(f-1e3)); 
    # unity-gain freq
    k=np.where(g<0)[0]; fu=f[k[0]] if len(k) else np.nan
    return (L,Wn,r,vals[0],vals[1]*1e3,g[i1],fu)
if __name__=='__main__':
    jobs=[(L,Wn,r) for L in (0.5,1,2) for Wn in (4,8,16) for r in (2,3,4)]
    with Pool(8) as p: res=p.map(job,jobs)
    print("L  Wn  Wp/Wn  Vbias   Idd(mA)  A0(dB)@1k  fu(Hz)")
    for r in res:
        if r[3] is None or len(r)<7: print(r); continue
        print(f"{r[0]:<4}{r[1]:<4}{r[2]:<5} {r[3]:.3f}  {r[4]:.3f}   {r[5]:.1f}   {r[6]:.3g}")
