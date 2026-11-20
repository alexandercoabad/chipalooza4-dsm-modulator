"""Find the square MIM size (cap_mim_m3_1, w = l) giving a target capacitance at TT with the PDK ngspice model (AC at 1 kHz).
All trial sizes go into one ngspice run (the library parse dominates the run time), then the size is refined by interpolation and checked.
usage: python3 cap_size.py 20e-15 60e-15   (needs PDK_ROOT, ngspice)"""
import os, subprocess, re, math, tempfile, sys
PDK = os.environ.get('PDK_ROOT', os.path.expanduser('~/openeda/pdk/share/pdk')) + '/sky130A/libs.tech/ngspice/sky130.lib.spice'
def caps(sizes, corner='tt'):
    nl = f".lib {PDK} {corner}\n"
    for i, s in enumerate(sizes): nl += f"X{i} a{i} 0 sky130_fd_pr__cap_mim_m3_1 w={s} l={s}\nVac{i} a{i} 0 dc 0 ac 1\n"
    nl += ".control\nac lin 1 1k 1k\n" + ''.join(f"print mag(i(vac{i}))\n" for i in range(len(sizes))) + ".endc\n.end\n"
    d = tempfile.mkdtemp(); open(d + '/t.cir', 'w').write(nl)
    out = subprocess.run(['ngspice', '-b', d + '/t.cir'], capture_output=True, text=True).stdout
    return [float(re.search(rf'i\(vac{i}\)\)\s*=\s*([0-9.eE+-]+)', out).group(1)) / (2 * math.pi * 1e3) for i in range(len(sizes))]
if __name__ == '__main__':
    tg = list(map(float, sys.argv[1:]))
    grid = [2.0, 3.0, 4.0, 5.0, 6.0, 8.0]
    c = caps(grid)
    # C is close to a*s^2 + b*s: fit with the two points that bracket each target, then verify
    res = []
    for t in tg:
        i = max(j for j in range(len(grid) - 1) if c[j] <= t) if t >= c[0] else 0
        s0, s1, c0, c1 = grid[i], grid[i+1], c[i], c[i+1]
        res.append(round(s0 + (t - c0) * (s1 - s0) / (c1 - c0), 2))
    for it in range(3):                                   # refine by secant steps on the true model
        v = caps(res); res = [round(s + (t - cv) / (2 * cv / s), 2) for s, t, cv in zip(res, tg, v)]   # dC/ds ~ 2C/s
    for corner in ('tt', 'll', 'hh'):
        v = caps(res, corner)
        print(corner, ' '.join(f"{s} um -> {cv*1e15:.3f} fF" for s, cv in zip(res, v)))
    print('SIZES', res)
