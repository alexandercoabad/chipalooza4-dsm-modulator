"""Coherent-FFT SNDR run.  usage: python3 run_sndr.py [corner] [temp] [vdd] [N] [out.json] [key=val ...]"""
import sys, json, numpy as np, dsm1, run_dsm, analyze
corner = sys.argv[1] if len(sys.argv)>1 else 'tt'; temp = float(sys.argv[2]) if len(sys.argv)>2 else 27
vdd = float(sys.argv[3]) if len(sys.argv)>3 else 3.3; N = int(sys.argv[4]) if len(sys.argv)>4 else 8192
outf = sys.argv[5] if len(sys.argv)>5 else 'sndr_result.json'
kw = {k:float(v) for k,v in (a.split('=') for a in sys.argv[6:])}
M = int(kw.pop('M', 17)); osr = int(kw.pop('osr', 128)); fclk = kw.pop('fclk', 1.024e6); skip = 256
fin = M*fclk/N
t, c, T = run_dsm.run(ncyc=N+skip+2, corner=corner, temp=temp, vdd=vdd, fclk=fclk, fin=fin, **kw)
b = analyze.bits_from(t, c['q'], T, vdd, N, skip)
r = analyze.sndr(b, M, N, osr)
res = dict(corner=corner, temp=temp, vdd=vdd, N=N, M=M, osr=osr, fclk=fclk, fin=fin, **kw,
           SNDR_dB=r['SNDR'], ENOB=r['ENOB'], amp_dBFS=r['amp_dBFS'], SFDR_dB=r['SFDR'],
           vcm=float(c['vcm'][-1]), out_min=float(c['out'][t>skip*T].min()), out_max=float(c['out'][t>skip*T].max()))
print(json.dumps(res)); json.dump(res, open(outf,'w'), indent=1)
np.save(outf.replace('.json','_P.npy'), r['P'])
