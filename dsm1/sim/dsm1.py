"""First-order switched-capacitor delta-sigma modulator built on the v2 inverter core (Sky130, ngspice).
Transistor level: inverter OTA (v2 core incl. header/footer), all switches (v2 transmission gates), vcm replica,
bit latch/buffers.  Ideal/behavioural (declared, see README): clock phases, comparator decision, Vin/Vref sources,
integrator leak resistor (stands in for a pseudo-resistor)."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'v2', 'sim'))
import v2
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'analog'))
import cells

def phases(T, vdd):
    """PULSE sources for the non-overlapping phases (fractions of period T).
    p1a = early-opening top-plate sampling switch (bottom-plate sampling), p1 = input sampling,
    p2 = integrate/transfer, pl = comparator latch window (after p2 is off)."""
    tr = T/400
    def pul(name, a, b, hi=vdd, lo=0.0):
        td, pw = a*T, (b-a)*T - tr
        return f"V{name} {name} 0 PULSE({lo} {hi} {td:.6g} {tr:.3g} {tr:.3g} {pw:.6g} {T:.6g})\n"
    s  = pul('p1a', 0.02, 0.44) + pul('p1', 0.02, 0.47) + pul('p2', 0.52, 0.97) + pul('pl', 0.10, 0.20)
    s += pul('p1ab', 0.02, 0.44, hi=0, lo=vdd) + pul('p1b', 0.02, 0.47, hi=0, lo=vdd)
    s += pul('p2b', 0.52, 0.97, hi=0, lo=vdd) + pul('plb', 0.10, 0.20, hi=0, lo=vdd)
    # p2e = bottom-plate (DAC) switch phase, opens early so its injection is absorbed while the top-plate switch is still closed
    s += pul('p2e', 0.52, 0.93) + pul('p2eb', 0.52, 0.93, hi=0, lo=vdd)
    return s

def netlist(fclk=1.024e6, vdd=3.3, cs=2e-12, ci=4e-12, rleak=1e10, vref=0.8, vin_amp=0.4, fin=1.9375e3, vin_levels=None, hold_cycles=1024,
            cpar_g=0.0, cpar_t=0.0, cpar_b=0.0, cpar_out=0.0, comp_gain=300.0, ncyc=64, ideal_clk=True, tg_scale=1.0, p2_early=0.0, sc_sin=None, sc_st1=None, sc_sb2=None, sc_st2=None, sc_dac=None, real_clk=False, real_comp=False):
    T = 1.0/fclk
    def tg(name, a, b, en, enb, sc):                       # v2 transmission gate, size scaled per switch (v2 default 8/24 um)
        sc = tg_scale if sc is None else sc
        v2.TG_WN, v2.TG_WP = 8.0*sc, 24.0*sc
        return v2.tg(name, a, b, en, enb)
    s  = f"Vdda vdda 0 {vdd}\n"
    if real_clk:      # transistor-level clock generator from a 50 % master clock (analog/cells.py): p1a, p1, p2 (+ complements) and cc
        s += f"Vclk clk 0 PULSE(0 {vdd} 0 {T/400:.3g} {T/400:.3g} {T/2 - T/400:.6g} {T:.6g})\n" + cells.clockgen('g', 'clk')
    else:
        s += phases(T, vdd)
    # --- vcm replica: v2 core (1/8 width) with out tied to input (self-bias), header/footer on ---
    k = 8.0
    s += v2.mos("rhp",'p','rcp','0','vdda','vdda', v2.HDR_W/k, 0.5)
    s += v2.mos("rp", 'p','vcm','vcm','rcp','rcp', v2.WP/k, v2.L)
    s += v2.mos("rn", 'n','vcm','vcm','rcn','0',   v2.WN/k, v2.L)
    s += v2.mos("rhn",'n','rcn','vdda','0','0',    v2.FTR_W/k, 0.5)
    # --- inverter OTA: v2 core, enabled ---
    s += v2.mos("hp",'p','vcp','0','vdda','vdda', v2.HDR_W, 0.5)
    s += v2.mos("p", 'p','out','g','vcp','vcp',   v2.WP, v2.L)
    s += v2.mos("n", 'n','out','g','vcn','0',     v2.WN, v2.L)
    s += v2.mos("hn",'n','vcn','vdda','0','0',    v2.FTR_W, 0.5)
    # --- SC integrator: Vout[n+1] = Vout[n] + (Cs/Ci)(Vin - Vdac) ---
    s += f"Cs t b {cs}\nCi g out {ci}\n"
    if cpar_g: s += f"Cpg g 0 {cpar_g}\n"
    if cpar_t: s += f"Cpt t 0 {cpar_t}\n"            # layout parasitics to substrate (layout/mim/cap_array_para.spice): Cs top plate, Cs bottom plate, Ci bottom plate (OTA output)
    if cpar_b: s += f"Cpb b 0 {cpar_b}\n"
    if cpar_out: s += f"Cpo out 0 {cpar_out}\n"
    s += f"Rleak out g {rleak}\n"                     # DC self-bias path (ideal, stand-in for pseudo-resistor)
    s += tg("sin","vin","b","p1","p1b",sc_sin)             # sample input on bottom plate
    s += tg("st1","vcm","t","p1a","p1ab",sc_st1)           # top plate to vcm (opens first)
    s += tg("sb2","dac","b",*(("p2e","p2eb") if p2_early else ("p2","p2b")),sc_sb2)   # bottom plate to DAC level (opens before st2 if p2_early)
    s += tg("st2","t","g","p2","p2b",sc_st2)               # top plate to virtual ground
    s += tg("dp","vrp","dac","q","qb",sc_dac)              # 1-bit DAC mux
    s += tg("dn","vrn","dac","qb","q",sc_dac)
    # --- behavioural sources (ideal) ---
    if vin_levels is not None:      # staircase of DC levels (V relative to vcm), each held hold_cycles clocks (INL/DNL sweep)
        H = hold_cycles/fclk; pts = ",".join(f"{k*H:.9g},{l:.6f},{(k+1)*H-2e-9:.9g},{l:.6f}" for k, l in enumerate(vin_levels))
        s += f"Bvin vin 0 V = v(vcm) + pwl(time,{pts})\n"
    else:
        s += f"Bvin vin 0 V = v(vcm) + {vin_amp}*sin(2*3.14159265358979*{fin}*time)\n"
    s += f"Bvrp vrp 0 V = v(vcm) + {vref}\nBvrn vrn 0 V = v(vcm) - {vref}\n"
    if real_comp:     # StrongARM + SR latch + buffers (analog/cells.py); needs the generated comparator clock cc
        assert real_clk, "real_comp needs real_clk (comparator clock cc)"
        s += cells.strongarm('c', 'out', 'vcm', 'cc', 'q', 'qb')
    else:
        # --- comparator (ideal decision, threshold = vcm) -> latch TG + hold cap -> inverter buffers (transistor level) ---
        s += f"Bcmp cmp 0 V = {vdd}/2*(1+tanh({comp_gain}*(v(out)-v(vcm))))\n"
        s += tg("lat","cmp","h","pl","plb",None)
        s += "Ch h 0 50f\n"
        s += v2.mos("i1p",'p','qb','h','vdda','vdda', 4.0, 0.5) + v2.mos("i1n",'n','qb','h','0','0', 2.0, 0.5)
        s += v2.mos("i2p",'p','q','qb','vdda','vdda', 4.0, 0.5) + v2.mos("i2n",'n','q','qb','0','0', 2.0, 0.5)
    return s
