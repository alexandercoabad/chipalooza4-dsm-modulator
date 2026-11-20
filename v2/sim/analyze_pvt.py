import numpy as np, pickle, json, collections
res=pickle.load(open('pvt_res.pkl','rb'))
R={}
for (c,v,T,k),d,P in res:
    f,g,z,ph=d[:,0],d[:,1],d[:,2],d[:,3]
    # d columns from wrdata: freq gdb freq zin freq ph -> [f,g,f,z,f,ph]
    f=d[:,0]; g=d[:,1]; z=d[:,3]; ph=d[:,5]
    i=np.argmin(abs(f-1e5))
    mid=g[i]
    pk=g.max()
    # upper -3 dB corner relative to midband (100kHz)
    j=np.where((f>1e5)&(g<mid-3))[0]; fh=f[j[0]] if len(j) else np.nan
    R[(c,v,T,k)]=dict(g=mid,pk=pk-mid,fh=fh,zin=z[i],vb=P['vb'],idd=P['idd'])
pickle.dump(R,open('pvt_sum.pkl','wb'))
nom={k:R[('tt',3.3,27,k)]['g'] for k in range(8)}
print("Nominal (tt,3.3V,27C):  gain per code",[round(nom[k],2) for k in range(8)])
print("steps",np.round(np.diff([nom[k] for k in range(8)]),2))
print("code | nom  | min   max  | worst err (dB) | worst-corner")
for k in range(8):
    vals={key:R[key]['g'] for key in R if key[3]==k}
    mn=min(vals,key=vals.get); mx=max(vals,key=vals.get)
    print(f" {k}  | {nom[k]:.2f} | {vals[mn]:.2f} {vals[mx]:.2f} | {vals[mn]-nom[k]:+.2f} / {vals[mx]-nom[k]:+.2f} | min@{mn[:3]} max@{mx[:3]}")
# monotonic across codes at each condition, step min/max
conds=sorted({key[:3] for key in R})
steps=[]
mono=True
for c in conds:
    gs=[R[c+(k,)]['g'] for k in range(8)]
    st=np.diff(gs); steps+=list(st)
    if (st<=0).any(): mono=False
print("adjacent-code step over ALL PVT: min %.2f max %.2f dB; monotonic everywhere: %s"%(min(steps),max(steps),mono))
vb=[R[c+(0,)]['vb'] for c in conds]; idd=[R[c+(0,)]['idd'] for c in conds]
print("bias V: min %.3f max %.3f nominal %.3f"%(min(vb),max(vb),R[('tt',3.3,27,0)]['vb']))
print("Idd mA: min %.3f max %.3f nominal %.3f"%(min(idd)*1e3,max(idd)*1e3,R[('tt',3.3,27,0)]['idd']*1e3))
# bias as fraction of vdd
fr=[R[c+(0,)]['vb']/c[1] for c in conds]; print("bias/VDD range %.3f..%.3f"%(min(fr),max(fr)))
print("Zin@100k kohm per code nominal:",[round(R[('tt',3.3,27,k)]['zin']/1e3,2) for k in range(8)])
zs=[R[c+(k,)]['zin'] for c in conds for k in range(8)]
print("Zin overall range kohm %.2f .. %.2f"%(min(zs)/1e3,max(zs)/1e3))
print("upper -3dB corner MHz nominal per code:",[round(R[('tt',3.3,27,k)]['fh']/1e6,2) for k in range(8)])
fh_all=[R[c+(k,)]['fh'] for c in conds for k in range(8)]
print("fh overall min %.2f MHz max %.2f MHz"%(np.nanmin(fh_all)/1e6,np.nanmax(fh_all)/1e6))
pk=[R[c+(k,)]['pk'] for c in conds for k in range(8)]; print("peaking over mid max %.2f dB"%max(pk))
# per-corner for code 7 and 0 at 3.3V/27
for k in (0,7):
    print("code",k,{c:round(R[(c,3.3,27,k)]['g'],2) for c in ['tt','ss','ff','sf','fs']})
    print("    temp",{T:round(R[('tt',3.3,T,k)]['g'],2) for T in (-40,0,27,110)}, "vdd",{v:round(R[('tt',v,27,k)]['g'],2) for v in (2.97,3.3,3.63)})
