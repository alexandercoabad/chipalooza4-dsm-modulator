import sys, os, numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'common'))
import cells, simlib
vcm=1.624; T=1/1.024e6; vdd=3.3
dvs=[10e-3,10e-3,-10e-3,-10e-3,10e-3]
pw="PWL("+" ".join(f"{k*T:.6g} {vcm+d} {(k+1)*T-1e-9:.6g} {vcm+d}" for k,d in enumerate(dvs))+")"
net=f"Vdda vdda 0 {vdd}\nVclk clk 0 PULSE(0 {vdd} {0.10*T:.6g} 2n 2n {0.40*T:.6g} {T:.6g})\nVinp inp 0 {pw}\nVinn inn 0 {vcm}\n"
net+=cells.strongarm('c','inp','inn','clk','q','qb')+"Cq q 0 50f\nCqb qb 0 50f\n"
net+=f".control\ntran 1n {len(dvs)*T:.6g}\nwrdata OUT v(cop) v(con) v(cx1) v(cx2) v(ctail) v(cQ) v(cQb) v(q)\n.endc\n"
a,so=simlib.run(net,'tt',27,tag='dbg'); t=a[:,0]
for k in range(len(dvs)):
    for f in (0.12,0.2,0.3,0.45,0.7):
        i=np.argmin(abs(t-(k+f)*T)); print(k,dvs[k]*1e3,f,' '.join(f"{a[i,2*j+1]:.2f}" for j in range(8)))
