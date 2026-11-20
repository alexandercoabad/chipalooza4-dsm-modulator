import sys, os, numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'common'))
import cells, simlib
vdd=3.3; vcm=1.624; T=1/1.024e6; step=1e-3; up=-20e-3+step*np.arange(41); seq=np.concatenate([up,up[::-1]])
def off(**kw):
    pw="PWL("+" ".join(f"{k*T:.6g} {vcm+d:.6f} {(k+1)*T-1e-9:.6g} {vcm+d:.6f}" for k,d in enumerate(seq))+")"
    net=f"Vdda vdda 0 {vdd}\nVclk clk 0 PULSE(0 {vdd} {0.10*T:.6g} 2n 2n {0.40*T:.6g} {T:.6g})\nVinp inp 0 {pw}\nVinn inn 0 {vcm}\n"
    net+=cells.strongarm('c','inp','inn','clk','q','qb',**kw)+"Cq q 0 50f\nCqb qb 0 50f\n"
    net+=f".options reltol=1e-4 vntol=1e-7\n.control\ntran 1n {(len(seq)+1)*T:.6g}\nwrdata OUT v(q)\n.endc\n"
    a,so=simlib.run(net,'tt',27,tag='var'); t=a[:,0]; q=a[:,1]
    b=np.array([np.interp((k+0.45)*T,t,q) for k in range(len(seq))])>vdd/2
    bu=b[:41]; bd=b[41:][::-1]
    fu=np.where(bu[1:]!=bu[:-1])[0]; fd=np.where(bd[1:]!=bd[:-1])[0]
    return [round(up[i]*1e3+step*500,1) for i in fu], [round(up[i]*1e3+step*500,1) for i in fd]
for kw in [dict(w_sr=(1.0,2.0)), dict(w_sr=(1.0,2.0), w_buf=(2.0,6.0)), dict(w_sr=(1.0,2.0), c_out=50e-15), dict(w_sr=(1.0,2.0), w_buf=(2.0,6.0), c_out=50e-15)]:
    print(kw, off(**kw), flush=True)
