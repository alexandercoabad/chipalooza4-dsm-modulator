import pickle, time
from multiprocessing import Pool
import sims2
def main():
    t0=time.time(); out={}
    with Pool(2) as p:
        out['hp']=p.map(sims2.acjob,[('hp',k,30e-12,0,'tt',None) for k in (0,3,7)])
        out['combo']=p.map(sims2.acjob,[('hp',k,cc,2,'tt',None) for k in (0,7) for cc in (10e-12,30e-12,50e-12)])
        rcs=['r+c/res_high__cap_high.spice','r+c/res_low__cap_low.spice','r+c/res_high__cap_low.spice','r+c/res_low__cap_high.spice']
        out['rc']=p.map(sims2.acjob,[('rc',k,30e-12,2,'tt',rc) for rc in rcs for k in (0,7)])
        out['settle_tt']=p.map(sims2.settle,[(k,30e-12,'tt',3.3,27) for k in (0,7)])
        out['settle_pvt']=p.map(sims2.settle,[(0,30e-12,c,v,T) for c,v,T in [('ss',2.97,-40),('ff',3.63,-40),('ss',2.97,110)]])
    pickle.dump(out,open('rerun30.pkl','wb')); print('done',time.time()-t0)
if __name__=='__main__': main()
