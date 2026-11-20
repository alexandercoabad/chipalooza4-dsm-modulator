"""Chipalooza #4 v2 inverter-amplifier: pre-layout schematic netlist generator (ngspice, SkyWater sky130 models)."""
import numpy as np
RF = 100e3          # fixed feedback resistor
L, WN, WP = 2.0, 32.0, 128.0      # core inverter (thick-oxide 3.3 V devices)
TG_WN, TG_WP, TG_L = 8.0, 24.0, 0.5   # gain-select transmission gates
HDR_W, FTR_W = 300.0, 100.0           # enable header (pfet) / footer (nfet)
RES_W = 5.73                          # xhigh_po wide resistor model (same family as v1)
LPC = [0.0, 1e-12, 4e-12, 16e-12]     # Cf bank (across Rf) -> 4 settings (LP)
HPC = [None, 10e-12, 30e-12, 50e-12] # Cc bank: None = off, external cap on CEXT
GAIN_TARGETS_DB = [11.5, 13.5, 15.5, 17.5, 19.5, 21.5, 23.5, 25.5]   # 8 codes, 2 dB steps
def split(W,wmax=16.0):
    n=int(np.ceil(W/wmax-1e-9)); return W/n, n
def mos(name,kind,d,g,s_,b,W,l,wmax=16.0):
    """emit parallel copies (this PDK model ignores mult)"""
    w,n=split(W,wmax); mod='nfet' if kind=='n' else 'pfet'
    return ''.join(f"X{name}_{i} {d} {g} {s_} {b} sky130_fd_pr__{mod}_g5v0d10v5 w={w:.4f} l={l} nf=1\n" for i in range(n))
def rl(R): return R/2000.0*RES_W     # resistor length in um for res_xhigh_po_5p73 (2 kohm/sq nominal)
IDEAL_RES=False   # noise runs: sky130 poly-R model has no thermal noise in ngspice -> use ideal R
def res(name,a,b,R):
    if IDEAL_RES: return f"R{name} {a} {b} {R:.6g}\n"
    return f"X{name} {a} {b} 0 sky130_fd_pr__res_xhigh_po_5p73 w={RES_W} l={rl(R):.4f}\n"
def tg(name,a,b,en,enb,vdd_node='vdda'):
    return (f"Xtn{name} {a} {en} {b} 0 sky130_fd_pr__nfet_g5v0d10v5 w={TG_WN} l={TG_L} nf=1\n"
            f"Xtp{name} {a} {enb} {b} {vdd_node} sky130_fd_pr__pfet_g5v0d10v5 w={TG_WP} l={TG_L} nf=1\n")
def netlist(Rin, code, vdd=3.3, cc=1e-6, lp=0, en=1, load=True, ain='dc 0 ac 1', extra='', tgs=True, core_wn=None, core_wp=None, core_l=None):
    """Rin: list of 8 branch resistors (series with TG). code: 0..7 selected branch.
    cc: coupling cap (F); lp: index into LPC"""
    wn=core_wn or WN; wp=core_wp or WP; l=core_l or L
    s=f"Vdda vdda 0 {vdd}\n"
    s+=f"Ven en 0 {3.3 if en else 0}\nVenb enb 0 {0 if en else 3.3}\n"
    s+=f"Vin in 0 {ain}\n"
    s+=f"Cc in a {cc}\n"
    for k,R in enumerate(Rin):
        on=(k==code)
        s+=f"Vs{k} s{k} 0 {vdd if on else 0}\nVsb{k} sb{k} 0 {0 if on else vdd}\n"
        s+=res(f"rin{k}",'a',f"b{k}",R)
        s+=tg(f"g{k}",f"b{k}",'g',f"s{k}",f"sb{k}")
    s+=res("rf",'g','out',RF)
    if LPC[lp]>0:
        s+=f"Cf g out {LPC[lp]}\n"
    # core with header / footer
    s+=mos("hp",'p','vcp','enb','vdda','vdda',HDR_W,0.5)
    s+=mos("p",'p','out','g','vcp','vcp',wp,l)
    s+=mos("n",'n','out','g','vcn','0',wn,l)
    s+=mos("hn",'n','vcn','en','0','0',FTR_W,0.5)
    s+=f"Xpd out enb 0 0 sky130_fd_pr__nfet_g5v0d10v5 w=5 l=0.5 nf=1\n"
    if load=='dc_gnd': s+="Rload out 0 100k\nCload out 0 20p\n"
    elif load: s+=f"Vmid vmid 0 {vdd/2}\nRload out vmid 100k\nCload out 0 20p\n"   # load returned to mid-supply (== AC-coupled load)
    s+=extra
    return s
