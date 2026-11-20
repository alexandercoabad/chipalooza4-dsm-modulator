import pickle, time
from multiprocessing import Pool
import sims2
def main():
    t0=time.time(); out={}
    with Pool(2) as p:
        out['hp']=p.map(sims2.acjob,[('hp',k,50e-12,0,'tt',None) for k in (0,3,7)]); print('hp',time.time()-t0,flush=True)
        out['settle_tt']=p.map(sims2.settle,[(k,50e-12,'tt',3.3,27) for k in (0,7)]); print('settle_tt',time.time()-t0,flush=True)
        out['settle_pvt']=p.map(sims2.settle,[(0,50e-12,c,v,T) for c,v,T in [('ss',2.97,110),('ss',2.97,-40),('ff',3.63,-40),('ss',2.97,27),('ff',3.63,110),('ff',3.63,27)]])
    pickle.dump(out,open('rerun50.pkl','wb')); print('done',time.time()-t0)
if __name__=='__main__': main()
