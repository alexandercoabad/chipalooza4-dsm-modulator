import pickle, time, numpy as np
from multiprocessing import Pool
import sims2, thd
def main():
    t0=time.time(); out={}
    with Pool(2) as p:
        jobs=[(k,cc,'tt',3.3,27) for k in (0,7) for cc in (10e-12,50e-12)]+[(7,50e-12,'ss',2.97,110)]
        out['settle']=p.map(sims2.settle,jobs); print('settle',time.time()-t0,flush=True)
        pickle.dump(out,open('rest.pkl','wb'))
        jobs=[(7,1.5,'tt',3.3,27),(0,1.5,'tt',3.3,27),(7,1.0,'tt',3.3,27),(7,1.5,'ss',2.97,110),(7,1.5,'ff',3.63,-40),(7,1.5,'ff',3.63,110)]
        out['thd']=p.map(thd.job,jobs); print('thd',time.time()-t0,flush=True)
        pickle.dump(out,open('rest.pkl','wb'))
if __name__=='__main__': main()
