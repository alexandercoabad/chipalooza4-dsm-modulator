"""Pseudo-resistor candidates for the integrator DC bias path (replaces Rleak = 10 Gohm between OTA out and g in dsm1.py).
Anti-parallel pair of diode-connected PMOS (g5v0d10v5), each bulk tied to its own source:  M1 S=a D=b G=b B=a,  M2 S=b D=a G=a B=b.
usage: python3 pseudo_res.py W L [corner] [temp] [rc]   -> I(V) for V = va - vb, with vb = vcm = 1.624 V; prints R = V/I at each V"""
import sys, os, json, numpy as np
H = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(H, '..', 'common'))
import simlib, mylib
def pr(name, a, b, W, L, nf=1, N=1, bulk='src', wmax=16.0):
    """N anti-parallel pairs in series between a and b; each device of total width W is emitted as parallel copies of <= wmax um (as v2.mos does).
    bulk='src' (each bulk at its own source) or 'vdda' (all bulks on the supply)."""
    s = ''; nodes = [a] + [f"{name}m{i}" for i in range(1, N)] + [b]; n = int(np.ceil(W/wmax - 1e-9)); w = W/n
    for i in range(N):
        x, y = nodes[i], nodes[i+1]
        for j in range(n):
            s += (f"X{name}{i}p{j} {y} {y} {x} {x if bulk=='src' else 'vdda'} sky130_fd_pr__pfet_g5v0d10v5 w={w:.4f} l={L} nf=1\n"      # D G S B : diode-connected
                  f"X{name}{i}q{j} {x} {x} {y} {y if bulk=='src' else 'vdda'} sky130_fd_pr__pfet_g5v0d10v5 w={w:.4f} l={L} nf=1\n")
    return s
def iv(W, L, corner='tt', temp=27, rc=None, vs=None, nf=1, N=1, bulk='src'):
    vs = vs if vs is not None else np.array([-0.5, -0.3, -0.1, -0.025, 0.025, 0.1, 0.3, 0.5])
    net = "Vdda vdda 0 3.3\nVb b 0 1.624\n"
    for k, v in enumerate(vs):   # one source + one pseudo-R per bias point (independent operating points, one run)
        net += f"Va{k} a{k} 0 {1.624+v:.6f}\n" + pr(f"r{k}", f"a{k}", "b", W, L, nf, N, bulk)
        net += "".join(f".nodeset v(r{k}m{i})={1.624+v*(1-i/N):.6f}\n" for i in range(1, N))
    net += ".options gmin=1e-15 abstol=1e-16 reltol=1e-5 vntol=1e-9 itl1=500\n.op\n.control\nop\nwrdata OUT " + " ".join(f"i(Va{k})" for k in range(len(vs))) + "\n.endc\n"
    a, so = simlib.run(net, corner, temp, tag='pr', rc=rc)
    row = np.atleast_2d(a)[0]; I = -row[1::2]       # current flowing from a-source into the pseudo-R  (wrdata col pairs: x,y)
    return vs, I
if __name__ == '__main__':
    W, L = float(sys.argv[1]), float(sys.argv[2]); c = sys.argv[3] if len(sys.argv) > 3 else 'tt'; T = float(sys.argv[4]) if len(sys.argv) > 4 else 27
    rc = sys.argv[5] if len(sys.argv) > 5 and sys.argv[5] != '-' else None
    N = int(sys.argv[6]) if len(sys.argv) > 6 else 1; bulk = sys.argv[7] if len(sys.argv) > 7 else 'src'
    vs, I = iv(W, L, c, T, rc, N=N, bulk=bulk)
    for v, i in zip(vs, I): print(f"V={v:+.3f} V  I={i:+.3e} A  R={abs(v/i) if i else float('inf'):.3e} ohm")
