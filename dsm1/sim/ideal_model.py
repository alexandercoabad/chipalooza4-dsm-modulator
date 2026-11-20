"""Ideal discrete-time reference for the same modulator (no circuit non-idealities).
Vout[n+1] = Vout[n] + (Cs/Ci)(Vin[n]-Vdac[n]); Vdac[n] = +/-Vref from the bit decided on Vout[n-1] side (same 1-cycle delay as the circuit)."""
import numpy as np, analyze
def ideal(N=8192, M=17, osr=128, cs=2e-12, ci=4e-12, vref=0.8, amp=0.4, skip=256, leak=0.0, a0=None):
    n = np.arange(N+skip+2); x = amp*np.sin(2*np.pi*M*n/N)
    y = 0.0; q = 1.0; bits = np.zeros(len(n)); g = cs/ci
    for i in range(len(n)):
        bits[i] = q
        y = (1-leak)*y + g*(x[i] - q*vref)
        q = 1.0 if y > 0 else -1.0
    return analyze.sndr(bits[skip:skip+N], M, N, osr)
if __name__=='__main__':
    for N, M in ((8192, 17), (4096, 5)):
        r = ideal(N=N, M=M); print("ideal 1st-order, OSR128, -6 dBFS, N=%d M=%d: SNDR %.1f dB, ENOB %.2f, tone %.2f dBFS"%(N,M,r['SNDR'],r['ENOB'],r['amp_dBFS']))
    print("leak sensitivity (N=8192, M=17):")
    for L in (1e-4,1e-3,1e-2,3e-2):
        r=ideal(leak=L); print(" integrator leak per cycle %.0e -> SNDR %.1f dB"%(L,r['SNDR']))
