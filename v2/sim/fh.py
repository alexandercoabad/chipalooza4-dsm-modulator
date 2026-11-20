import json, numpy as np, simlib, v2
from multiprocessing import Pool
RIN=json.load(open('rin_design.json'))
def job(a):
    code,c,v,T=a
    b=v2.netlist(RIN,code,vdd=v)+""".control
op
ac dec 20 1e3 3e9
let gdb=db(v(out)/v(in))
wrdata OUT gdb
.endc
"""
    d,so=simlib.run(b,c,T); f,g=d[:,0],d[:,1]
    mid=g[np.argmin(abs(f-1e5))]; j=np.where((f>1e5)&(g<mid-3))[0]
    return a,round(mid,2),(f[j[0]] if len(j) else None),round(g.max()-mid,2)
if __name__=='__main__':
    conds=[('tt',3.3,27),('ss',2.97,110),('ss',2.97,-40),('ff',3.63,-40),('ff',3.63,110),('sf',2.97,110),('fs',2.97,110),('sf',3.63,-40)]
    jobs=[(k,)+c for c in conds for k in (0,7)]
    with Pool(2) as p: r=p.map(job,jobs)
    for a,mid,fh,pk in r: print(a,"mid",mid,"fh(MHz)",None if fh is None else round(fh/1e6,2),"peaking",pk)
