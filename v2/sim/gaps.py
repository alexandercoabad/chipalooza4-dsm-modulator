import json, sys, time, numpy as np, simlib, v2, design, thd, sims2
from multiprocessing import Pool
RIN=json.load(open('rin_design.json'))
def gain_rc(a):
    code,corner,temp,vdd,rc,load=a
    b=v2.netlist(RIN,code,vdd=vdd,load=load)+""".control
op
let vb=v(out)
print vb
ac lin 1 100k 100k
let gdb=db(v(out)/v(in))
wrdata OUT gdb
.endc
"""
    d,so=simlib.run(b,corner,temp,rc=rc)
    P=simlib.parse(so)
    return a,float(np.atleast_2d(d)[-1,-1]),P.get('vb')
def main(which):
    t0=time.time(); out={}
    with Pool(2) as p:
        if which=='thd':
            jobs=[(7,1.0,c,v,T) for c,v,T in [('ss',2.97,110),('ff',3.63,-40),('ff',3.63,110),('ss',2.97,-40),('sf',3.3,27),('fs',3.3,27),('ff',3.63,27)]]
            jobs+=[(0,1.0,'ff',3.63,110),(0,1.0,'ff',3.63,-40),(3,1.0,'ff',3.63,110),(3,1.0,'ff',3.63,-40)]
            out['thd']=p.map(thd.job,jobs)
        if which=='settle':
            jobs=[(0,50e-12,c,v,T) for c,v,T in [('ss',2.97,110),('ss',2.97,-40),('ff',3.63,-40),('ss',2.97,27)]]
            out['settle']=p.map(sims2.settle,jobs)
        if which=='rc':
            R=['r+c/res_typical__cap_typical.spice','r+c/res_high__cap_high.spice','r+c/res_low__cap_low.spice']
            jobs=[(k,'tt',27,3.3,rc,True) for rc in R for k in range(8)]
            jobs+=[(k,c,T,v,rc,True) for (c,T,v) in [('ss',110,2.97),('ff',-40,3.63)] for rc in R[1:] for k in (0,7)]
            out['rc']=p.map(gain_rc,jobs)
        if which=='load':
            jobs=[(k,'tt',27,3.3,None,l) for l in (True,'dc_gnd') for k in (0,7)]
            out['load']=p.map(gain_rc,jobs)
        if which=='pvt':
            conds=[(c,v,T) for c in ('ss','ff','sf','fs') for v,T in ((2.97,110),(3.63,-40),(2.97,-40),(3.63,110))]
            jobs=[(k,c,T,v,None,True) for (c,v,T) in conds for k in range(8)]+[(k,'tt',27,3.3,None,True) for k in range(8)]
            out['pvt']=p.map(gain_rc,jobs)
    json.dump(out,open(f'gaps_{which}.json','w'),default=lambda o:o.tolist() if hasattr(o,'tolist') else str(o))
    print(which,'done',round(time.time()-t0),flush=True)
if __name__=='__main__': main(sys.argv[1])
