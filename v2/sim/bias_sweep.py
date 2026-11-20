"""DC bias point and supply current, code 0, 5 corners x 3 supplies x 4 temps."""
import simlib,v2,json
from multiprocessing import Pool
RIN=json.load(open('rin_design.json'))
def job(a):
    c,v,T=a
    b=v2.netlist(RIN,0,vdd=v)+".control\nop\nlet vb=v(out)\nlet idd=-i(Vdda)\nprint vb idd\nwrdata OUT vb\n.endc\n"
    d,so=simlib.run(b,c,T); P=simlib.parse(so); return a,P['vb'],P['idd']
if __name__=='__main__':
    jobs=[(c,v,T) for c in ['tt','ss','ff','sf','fs'] for v in (2.97,3.3,3.63) for T in (-40,0,27,110)]
    with Pool(2) as p: r=p.map(job,jobs)
    vb=[x[1] for x in r]; fr=[x[1]/x[0][1] for x in r]; idd=[x[2]*1e3 for x in r]
    print("vb %.3f..%.3f V; vb/VDD %.3f..%.3f; idd %.3f..%.3f mA"%(min(vb),max(vb),min(fr),max(fr),min(idd),max(idd)))
