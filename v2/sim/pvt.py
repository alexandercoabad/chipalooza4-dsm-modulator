import numpy as np, simlib, v2, json, itertools, time, pickle
from multiprocessing import Pool
RIN=json.load(open('rin_design.json'))
CORNERS=['tt','ss','ff','sf','fs']; VDDS=[2.97,3.3,3.63]; TEMPS=[-40,0,27,110]
def job(a):
    corner,vdd,temp,code=a
    b=v2.netlist(RIN,code,vdd=vdd)+""".control
op
let idd=-i(Vdda)
let vb=v(out)
print vb idd
ac dec 20 1k 3e9
let gdb=db(v(out)/v(in))
let zin=mag(v(in)/i(Vin))
let ph=phase(v(out)/v(in))*180/pi
wrdata OUT gdb zin ph
.endc
"""
    try:
        d,so=simlib.run(b,corner,temp,tag=f"{corner}_{vdd}_{temp}_{code}")
    except Exception as e:
        return (a,None,str(e)[:300])
    P=simlib.parse(so)
    return (a,d,P)
if __name__=='__main__':
    t=time.time()
    jobs=[(c,v,T,k) for c in CORNERS for v in VDDS for T in TEMPS for k in range(8)]
    with Pool(8) as p: res=p.map(job,jobs,chunksize=4)
    bad=[r for r in res if r[1] is None]
    print(len(res),'runs',len(bad),'failed',time.time()-t)
    if bad: print(bad[0][2])
    pickle.dump(res,open('pvt_res.pkl','wb'))
