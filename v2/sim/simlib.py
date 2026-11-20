import subprocess, tempfile, os, numpy as np, mylib
def run(body, corner='tt', temp=27, outs=(), tag='x', rc=None, timeout=300):
    """body: circuit + analysis lines (inside .control, ending with wrdata to file named OUT).
    Returns numpy array loaded from OUT."""
    d=tempfile.mkdtemp(dir=os.environ.get('SIMTMP') or None)
    out=os.path.join(d,'out.txt')
    net=f"* {tag}\n"+mylib.lib(corner,rc)+f".temp {temp}\n"+body.replace('OUT',out)+"\n.end\n"
    p=os.path.join(d,'t.cir'); open(p,'w').write(net)
    r=subprocess.run(['ngspice','-b',p],capture_output=True,text=True,timeout=timeout)
    if not os.path.exists(out):
        raise RuntimeError(r.stdout[-1500:]+r.stderr[-500:])
    a=np.loadtxt(out)
    return a, r.stdout

def parse(stdout):
    """parse 'name = value' lines printed by ngspice (real values only)"""
    d={}
    for l in stdout.splitlines():
        if ' = ' in l:
            k,v=l.split(' = ',1)
            try: d[k.strip().lower()]=float(v.split(',')[0])
            except: pass
    return d
