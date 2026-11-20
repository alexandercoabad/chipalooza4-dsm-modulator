import numpy as np, simlib, v2, json, pickle, time
from multiprocessing import Pool
RIN=json.load(open('rin_design.json'))
AC=""".control
op
ac dec 20 {f0} {f1}
let gdb=db(v(out)/v(in))
wrdata OUT gdb
.endc
"""
def corners_of(f,g,ref):
    """ref = ideal-coupling, no-Cf midband gain of this code (dB). -3 dB points relative to ref."""
    ok=np.where(g>ref-3)[0]
    if len(ok)==0: return ref,np.nan,np.nan,g.max()-ref
    fl=f[ok[0]]; fh=f[ok[-1]]
    return ref,fl,fh,g.max()-ref
def acjob(a):
    kind,code,cc,lp,corner,rc=a
    b=v2.netlist(RIN,code,cc=cc,lp=lp)+AC.format(f0=1,f1=1e9)
    d,so=simlib.run(b,corner,27,rc=rc)
    mid,fl,fh,pk=corners_of(d[:,0],d[:,1],v2.GAIN_TARGETS_DB[code])
    return (a,mid,fl,fh,pk)
def noisejob(a):
    code,corner,temp,vdd=a
    v2.IDEAL_RES=True
    b=v2.netlist(RIN,code,vdd=vdd)+""".control
op
noise v(out) Vin dec 10 10 1e7 1
setplot noise1
wrdata OUT inoise_spectrum
.endc
"""
    d,so=simlib.run(b,corner,temp)
    f=d[:,0]; n=d[:,1]
    return (a,f,n)
def enjob(a):
    corner,vdd,temp,en=a
    b=v2.netlist(RIN,7,vdd=vdd,en=en)+""".control
op
let idd=-i(Vdda)
let vo=v(out)
print idd vo
.endc
"""
    # need a dummy wrdata target
    b=b.replace(".endc","wrdata OUT idd\n.endc")
    d,so=simlib.run(b,corner,temp)
    P=simlib.parse(so); return (a,P['idd'],P['vo'])
def settle(a):
    code,cc,corner,vdd,temp=a
    # EN rises at 1us. input at DC 0V through Cc.
    b=v2.netlist(RIN,code,vdd=vdd,cc=cc,en=1)
    b=b.replace(f"Ven en 0 3.3\nVenb enb 0 0",f"Ven en 0 pwl(0 0 1u 0 1.01u 3.3)\nVenb enb 0 pwl(0 3.3 1u 3.3 1.01u 0)")
    b+=""".ic v(out)=0 v(g)=0
.control
tran 100n 300u uic
wrdata OUT v(out)
.endc
"""
    d,so=simlib.run(b,corner,temp)
    t=d[:,0]; v=d[:,1]
    fin=v[-1]; band=max(0.01*abs(fin),0.010)
    out=np.where(abs(v-fin)>band)[0]
    ts=(t[out[-1]]-1.01e-6) if len(out) else 0
    return (a,fin,ts,t[-1])
if __name__=='__main__':
    t0=time.time(); out={}
    with Pool(2) as p:
        # 1: HP corner matrix, nominal
        jobs=[('hp',k,cc,0,'tt',None) for cc in (10e-12,30e-12,50e-12,100e-9) for k in (0,3,7)]
        out['hp']=p.map(acjob,jobs); print('hp',time.time()-t0,flush=True)
        # 2: LP corner (Cf bank) with 160pF? use ideal 1u coupling to isolate; codes 0,3,7; lp 0..3
        jobs=[('lp',k,1e-6,lp,'tt',None) for lp in (0,1,2,3) for k in (0,3,7)]
        out['lp']=p.map(acjob,jobs); print('lp',time.time()-t0,flush=True)
        # 2b: R/C process corners: code 0,7 with Cc=30pF, Cf idx2
        rcs=['r+c/res_high__cap_high.spice','r+c/res_low__cap_low.spice','r+c/res_high__cap_low.spice','r+c/res_low__cap_high.spice']
        jobs=[('rc',k,30e-12,2,'tt',rc) for rc in rcs for k in (0,7)]
        out['rc']=p.map(acjob,jobs); print('rc',time.time()-t0,flush=True)
        # 3: noise
        jobs=[(k,'tt',27,3.3) for k in range(8)]+[(k,'ss',110,2.97) for k in (0,7)]+[(k,'ff',-40,3.63) for k in (0,7)]
        out['noise']=p.map(noisejob,jobs); print('noise',time.time()-t0,flush=True)
        # 5: enable/power-down
        jobs=[(c,v,T,en) for (c,v,T) in (('tt',3.3,27),('ff',3.63,110),('ss',2.97,110),('ff',3.63,27),('ff',3.63,-40)) for en in (0,1)]
        out['en']=p.map(enjob,jobs); print('en',time.time()-t0,flush=True)
    pickle.dump(out,open('sims2.pkl','wb'))
