import numpy as np
def sndr(bits, M, N, osr, nsig=3):
    """bits: +/-1 sequence length N, coherent with M cycles. Hann window. Returns dict (dB)."""
    x = bits - bits.mean()
    w = np.hanning(N); X = np.fft.rfft(x*w)
    P = (np.abs(X)**2); P[0] = 0
    nb = N//(2*osr)                                  # in-band bins 1..nb
    sig = P[M-nsig:M+nsig+1].sum()
    band = P[1:nb+1].copy()
    inband = band.sum()
    noise = inband - sig
    # tone amplitude relative to full scale (bit amplitude 1), by Parseval over the tone's window bins
    A = 2*np.sqrt(sig/(N*np.sum(w**2)))
    # worst spur in band (excluding tone), for SFDR
    mask = np.ones(nb+1, bool); mask[0]=False; mask[max(M-nsig,0):M+nsig+1]=False
    spur = P[:nb+1][mask].max()
    return dict(SNDR=10*np.log10(sig/noise), amp_dBFS=20*np.log10(A), SFDR=10*np.log10(sig/spur),
                ENOB=(10*np.log10(sig/noise)-1.76)/6.02, nb=nb, P=P)
def bits_from(t, q, T, vdd, n, skip, frac=0.4):
    idx = (np.arange(skip, skip+n)+frac)*T
    return np.where(np.interp(idx, t, q) > vdd/2, 1.0, -1.0)
