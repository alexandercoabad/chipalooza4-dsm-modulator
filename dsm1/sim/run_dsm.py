import os, sys, numpy as np
import dsm1   # (adds ../../common to sys.path)
import simlib
def run(ncyc=64, corner='tt', temp=27, pts_per_cycle=40, reltol=None, vntol=None, **kw):
    fclk = kw.get('fclk', 1.024e6); T = 1/fclk
    net = dsm1.netlist(**kw)
    opt = f".options reltol={reltol:g} vntol={vntol if vntol else 1e-6:g}\n" if reltol else ""   # tighter tolerances for real_clk/real_comp runs
    body = net + opt + ".save v(q) v(out) v(vcm) v(g)\n" + f".control\ntran {T/pts_per_cycle:.4g} {ncyc*T:.6g} 0 {T/pts_per_cycle:.4g}\nwrdata OUT v(q) v(out) v(vcm) v(g)\n.endc\n"
    a, so = simlib.run(body, corner, temp, tag='dsm1', timeout=40000)
    t = a[:,0]
    assert t[-1] >= 0.999*ncyc*T, f"simulation ended early at cycle {t[-1]/T:.1f} of {ncyc} (ngspice aborted); results would be invalid"
    cols = {n: a[:,2*i+1] for i,n in enumerate(['q','out','vcm','g'])}
    return t, cols, T
if __name__ == '__main__':
    t, c, T = run(ncyc=int(sys.argv[1]) if len(sys.argv)>1 else 40)
    print("points", len(t), "vcm", c['vcm'][-1], "out range", c['out'].min(), c['out'].max(), "g", c['g'].min(), c['g'].max())
    # sample q mid-cycle
    n = int(t[-1]/T)
    bits = np.array([np.interp((i+0.4)*T, t, c['q']) for i in range(n)]) > 1.65
    print("ones density", bits.mean(), bits[:40].astype(int))
