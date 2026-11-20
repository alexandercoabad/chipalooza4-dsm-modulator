"""Transistor-level comparator and non-overlapping clock generator for the delta-sigma modulator (Sky130 g5v0d10v5, 3.3 V).
Imports the device emitter from common/ so device naming and model use are identical to the rest of the repo."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'common'))
import amp_core
L0 = 0.5   # minimum drawn length of the g5v0d10v5 devices used here

def inv(n, a, y, wn=2.0, wp=6.0, ln=L0, lp=L0, vdd='vdda'):
    return amp_core.mos(f"{n}n", 'n', y, a, '0', '0', wn, ln) + amp_core.mos(f"{n}p", 'p', y, a, vdd, vdd, wp, lp)

def nand2(n, a, b, y, wn=4.0, wp=6.0, vdd='vdda'):
    m = f"{n}_m"
    return (amp_core.mos(f"{n}na", 'n', y, a, m, '0', wn, L0) + amp_core.mos(f"{n}nb", 'n', m, b, '0', '0', wn, L0)
            + amp_core.mos(f"{n}pa", 'p', y, a, vdd, vdd, wp, L0) + amp_core.mos(f"{n}pb", 'p', y, b, vdd, vdd, wp, L0))

def nor2(n, a, b, y, wn=2.0, wp=12.0, vdd='vdda'):
    m = f"{n}_m"
    return (amp_core.mos(f"{n}na", 'n', y, a, '0', '0', wn, L0) + amp_core.mos(f"{n}nb", 'n', y, b, '0', '0', wn, L0)
            + amp_core.mos(f"{n}pa", 'p', m, a, vdd, vdd, wp, L0) + amp_core.mos(f"{n}pb", 'p', y, b, m, vdd, wp, L0))

def strongarm(n, inp, inn, clk, q, qb, w_in=8.0, w_tail=8.0, w_xn=4.0, w_xp=8.0, w_rs=2.0, vdd='vdda', sr=True, w_sr=(1.0, 2.0), w_buf=(8.0, 24.0), c_out=50e-15, iso=((1.0, 2.0), (1.0, 4.0))):
    """StrongARM latch + NAND SR latch + output buffers.  inp > inn  ->  q = 1 after the clk rising edge.
    clk low = reset (outputs precharged, SR latch holds the previous decision), clk high = evaluate."""
    s  = amp_core.mos(f"{n}mt", 'n', f"{n}tail", clk, '0', '0', w_tail, L0)
    s += amp_core.mos(f"{n}m1", 'n', f"{n}x1", inp, f"{n}tail", '0', w_in, L0)
    s += amp_core.mos(f"{n}m2", 'n', f"{n}x2", inn, f"{n}tail", '0', w_in, L0)
    s += amp_core.mos(f"{n}m3", 'n', f"{n}on", f"{n}op", f"{n}x1", '0', w_xn, L0)
    s += amp_core.mos(f"{n}m4", 'n', f"{n}op", f"{n}on", f"{n}x2", '0', w_xn, L0)
    s += amp_core.mos(f"{n}m5", 'p', f"{n}on", f"{n}op", vdd, vdd, w_xp, L0)
    s += amp_core.mos(f"{n}m6", 'p', f"{n}op", f"{n}on", vdd, vdd, w_xp, L0)
    for nm, node in (('m7', 'on'), ('m8', 'op'), ('m9', 'x1'), ('m10', 'x2')):
        s += amp_core.mos(f"{n}{nm}", 'p', f"{n}{node}", clk, vdd, vdd, w_rs, L0)
    if not sr:      # core only (for debugging): 10 fF on each output, raw outputs are nodes <n>op / <n>on
        return s + f"C{n}lo {n}op 0 10f\nC{n}lp {n}on 0 10f\n"
    if iso:         # isolated variant (default; iso=None gives the earlier NAND latch with ±3.5 mV hysteresis): small inverters decouple the core outputs from the latch; NOR SR latch (active-high inputs)
        s += inv(f"{n}iso1", f"{n}on", f"{n}onn", *iso[0], vdd=vdd) + inv(f"{n}iso2", f"{n}op", f"{n}opn", *iso[0], vdd=vdd)
        s += nor2(f"{n}s1", f"{n}opn", f"{n}Qb", f"{n}Q", *iso[1], vdd=vdd)
        s += nor2(f"{n}s2", f"{n}onn", f"{n}Q", f"{n}Qb", *iso[1], vdd=vdd)
        s += inv(f"{n}b1", f"{n}Q", qb, *w_buf, vdd=vdd) + inv(f"{n}b2", f"{n}Qb", q, *w_buf, vdd=vdd)
        if c_out: s += f"C{n}lo {n}op 0 {c_out}\nC{n}lp {n}on 0 {c_out}\n"
        return s
    # SR latch (active-low inputs): Q = NAND(on, Qb), Qb = NAND(op, Q); then inverting buffers give q (= Q) and qb
    s += nand2(f"{n}s1", f"{n}on", f"{n}Qb", f"{n}Q", *w_sr, vdd)
    s += nand2(f"{n}s2", f"{n}op", f"{n}Q", f"{n}Qb", *w_sr, vdd)
    s += inv(f"{n}b1", f"{n}Q", qb, *w_buf, vdd=vdd) + inv(f"{n}b2", f"{n}Qb", q, *w_buf, vdd=vdd)
    if c_out: s += f"C{n}lo {n}op 0 {c_out}\nC{n}lp {n}on 0 {c_out}\n"
    return s


def delay(n, a, y, stages=2, wn=1.0, wp=2.0, ln=4.0, lp=4.0, cload=20e-15, vdd='vdda'):
    """Non-inverting delay: `stages` (even) slow inverters (long L) each loaded by cload."""
    s = ''; prev = a
    for i in range(stages):
        out = y if i == stages-1 else f"{n}_d{i}"
        s += inv(f"{n}i{i}", prev, out, wn, wp, ln, lp, vdd)
        if cload: s += f"C{n}_{i} {out} 0 {cload}\n"
        prev = out
    return s

def clockgen(n, clk, vdd='vdda', **dk):
    """Master clock (50 % duty, 0..vdd) -> phases used by the modulator (node names are global):
      p1a / p1ab : top-plate sampling switch phase (opens first, bottom-plate sampling)
      p1  / p1b  : input-sampling switch phase (p1a delayed by the 'early' delay, so p1a opens first)
      p2  / p2b  : integrate / transfer phase
      cc         : comparator clock (evaluate while high; rises `cmp` delay after p1a, falls with p1a)
    Cross-coupled NOR non-overlap generator: p1a and p2 cannot overlap, the 'gap' delay sets the dead time."""
    s  = inv(f"{n}ck", clk, f"{n}clkb", 2.0, 6.0, vdd=vdd)
    s += nor2(f"{n}n1", f"{n}clkb", f"{n}p2d", f"{n}p1r", vdd=vdd)          # p1 core: high while clk high and delayed p2 low
    s += nor2(f"{n}n2", clk,        f"{n}p1d", f"{n}p2r", vdd=vdd)          # p2 core: high while clk low and delayed p1 low
    s += delay(f"{n}dg1", "p1", f"{n}p1d", **dk.get('gap', {}))             # non-overlap delays, fed from the FINAL phases:
    s += delay(f"{n}dg2", "p2", f"{n}p2d", **dk.get('gap', {}))             # p2 may rise only after the late p1 has fallen
    # final drivers (each phase drives up to two 8/24 um transmission gates)
    s += inv(f"{n}a1", f"{n}p1r", f"{n}p1an", 4.0, 12.0, vdd=vdd) + inv(f"{n}a2", f"{n}p1an", "p1a", 8.0, 24.0, vdd=vdd)
    s += inv(f"{n}a3", "p1a", "p1ab", 8.0, 24.0, vdd=vdd)
    s += delay(f"{n}de", "p1a", f"{n}p1e", **dk.get('early', {}))
    s += inv(f"{n}e1", f"{n}p1e", f"{n}p1en", 4.0, 12.0, vdd=vdd) + inv(f"{n}e2", f"{n}p1en", "p1", 8.0, 24.0, vdd=vdd)
    s += inv(f"{n}e3", "p1", "p1b", 8.0, 24.0, vdd=vdd)
    s += inv(f"{n}b1", f"{n}p2r", f"{n}p2n", 4.0, 12.0, vdd=vdd) + inv(f"{n}b2", f"{n}p2n", "p2", 8.0, 24.0, vdd=vdd)
    s += inv(f"{n}b3", "p2", "p2b", 8.0, 24.0, vdd=vdd)
    s += delay(f"{n}dc", "p1a", f"{n}p1c", **dk.get('cmp', dict(stages=4, cload=60e-15)))
    s += nand2(f"{n}cn", "p1a", f"{n}p1c", f"{n}ccn", 4.0, 6.0, vdd) + inv(f"{n}cb", f"{n}ccn", "cc", 4.0, 12.0, vdd=vdd)
    return s
