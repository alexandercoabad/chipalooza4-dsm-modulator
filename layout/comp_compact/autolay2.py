"""Row-based generator, version 2 (compact): cells are PDK multifinger transistors, so series/shared-terminal pairs share diffusion and one well.
Units: 1 = 5 nm.  A cell spec is a dict: name, kind ('n'|'p'), w (per finger, um), l, nf, strips (nf+1 nets, left to right), gates (nf nets), bulk.
NMOS cells sit in a bottom row, PMOS cells in a top row, routing channel between them with one metal2 track per multi-pin net.
Every strip (S/D) and every finger gate gets a metal3 strap (NMOS) or metal4 strap (PMOS) to its track; the ring (well/substrate tie) is tied from the
corner of the ring that faces away from the channel, with a metal2 jumper to a strap in the gap to the left of the cell.
Compared with layout/comp/autolay.py: multifinger cells, cell order chosen by a wirelength annealer, no per-transistor guard ring."""
import os, re, subprocess, collections, sys, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import magparse as mp


def gen_cells(specs, build, magic, env):
    keys = sorted({(s['kind'], s['w'], s['l'], s['nf']) for s in specs})
    tcl = ['proc mk {tag fet args} {', '  cellname create top_$tag; load top_$tag; box 0 0 0 0', '  eval magic::gencell sky130::$fet inst_$tag $args', '  save top_$tag',
           '  set child [lindex [cellname list children top_$tag] 0]', '  if {$child ne ""} { load $child; save $child }', '  puts "PCELL $tag $child"', '}',
           'mk warm sky130_fd_pr__nfet_g5v0d10v5 w 2.0 l 0.5 nf 1 guard 1']
    for i, (k, w, l, nf) in enumerate(keys):
        tcl.append(f'mk k{i} sky130_fd_pr__{"nfet" if k == "n" else "pfet"}_g5v0d10v5 w {w} l {l} nf {nf} guard 1 conn_gates 0')
    tcl.append('quit -noprompt')
    open(f'{build}/gen.tcl', 'w').write('\n'.join(tcl) + '\n')
    r = subprocess.run(f'cd {build} && timeout 300 {magic} gen.tcl < /dev/null', shell=True, capture_output=True, text=True, env=env).stdout
    names = dict(re.findall(r'PCELL (k\d+) (\S+)', r))
    return {k: names[f'k{i}'] for i, k in enumerate(keys)}


def pin_info(build, cell):
    d = mp.parse(f'{build}/{cell}.mag'); L = d['layers']
    dc = [k for k in L if k.endswith('diffc') and 'subdiff' not in k][0]
    xs = sorted((r[0] + r[2]) // 2 for r in L[dc]); ys = (min(r[1] for r in L[dc]), max(r[3] for r in L[dc]))
    ring = [k for k in L if 'subdiffcont' in k][0]; rr = mp.bbox({ring: L[ring]})
    pc = L['polycont']; yg = max((r[1] + r[3]) // 2 for r in pc)
    gx = sorted((r[0] + r[2]) // 2 for r in pc if (r[1] + r[3]) // 2 > 0)
    cp = d['layers'].get('checkpaint', [None])[0]
    return dict(xs=xs, ys=ys, rr=rr, yg=yg, gx=gx, cp=cp)


class Plan:
    def __init__(self, specs, build, magic, env):
        self.specs = {s['name']: s for s in specs}
        self.cells = gen_cells(specs, build, magic, env)
        self.info = {k: pin_info(build, c) for k, c in self.cells.items()}
        for s in specs:
            i = self.info[(s['kind'], s['w'], s['l'], s['nf'])]
            assert len(i['xs']) == s['nf'] + 1 and len(i['gx']) == s['nf'], (s['name'], i['xs'], i['gx'])

    def inf(self, n):
        s = self.specs[n]; return self.info[(s['kind'], s['w'], s['l'], s['nf'])]

    def hw(self, n):
        r = self.inf(n)['rr']; return max(abs(r[0]), abs(r[2]))

    def net_pins(self, name):
        """terminals as (net, dx, kind) relative to the cell centre, used by the placement annealer"""
        s = self.specs[name]; i = self.inf(name); out = []
        for net, x in zip(s['strips'], i['xs']): out.append((net, x))
        for net, x in zip(s['gates'], i['gx']): out.append((net, x))
        return out


def anneal(plan, order_n, order_p, gap_n, gap_p, iters=60000, seed=3, power=('vdda', 'gnd')):
    """minimise the sum over (non-supply) nets of the x-extent of their pins; positions follow from the order and gaps"""
    rnd = random.Random(seed)
    def xs_of(order, gap):
        x = 0; pos = {}
        for n in order:
            hw = plan.hw(n); pos[n] = x + hw; x += 2 * hw + gap
        return pos, x
    def cost(on, op):
        pn, wn = xs_of(on, gap_n); pp, wp = xs_of(op, gap_p); pos = {**pn, **pp}; ext = collections.defaultdict(lambda: [1e9, -1e9])
        for n, cx in pos.items():
            for net, dx in plan.net_pins(n):
                if net in power: continue
                e = ext[net]; e[0] = min(e[0], cx + dx); e[1] = max(e[1], cx + dx)
        return sum(b - a for a, b in ext.values() if b > a) + 4 * abs(wn - wp)
    on, op = list(order_n), list(order_p); c = cost(on, op); best = (c, on[:], op[:]); T = c * 0.05
    for it in range(iters):
        T *= 0.9998
        a, b = (on, op)[rnd.random() < 0.5 and 1 or 0], None
        row = a; i, j = rnd.sample(range(len(row)), 2); row[i], row[j] = row[j], row[i]
        c2 = cost(on, op)
        if c2 <= c or rnd.random() < pow(2.718281828, (c - c2) / max(T, 1e-9)): c = c2; 
        else: row[i], row[j] = row[j], row[i]
        if c < best[0]: best = (c, on[:], op[:])
    return best


def route(plan, order_n, order_p, extra, torder=None, gap_n=300, gap_p=760, trk_pitch=140, ports=(), skip_single=True):
    R, LAB, uses = [], [], ''
    def rect(l, x1, y1, x2, y2, net=None): R.append((l, int(x1), int(y1), int(x2), int(y2), net))
    specs = plan.specs
    def place(order, y, gap, ex):
        x = 0; out = {}
        for k, n in enumerate(order):
            x += ex[k]; hw = plan.hw(n); out[n] = (x + hw, y); x += 2 * hw + gap
        return out, x
    nn = len(order_n)
    posn, wn_ = place(order_n, 0, gap_n, extra[:nn])
    ntop = max(plan.inf(n)['rr'][3] for n in order_n)
    cnt = collections.Counter()
    for s in specs.values():
        for net in list(s['strips']) + list(s['gates']) + [s['bulk']]: cnt[net] += 1
    pcnt = collections.Counter()
    for s in specs.values():
        for net in list(s['strips']) + list(s['gates']) + [s['bulk']]:
            if s['kind'] == 'p': pcnt[net] += 1
    nets = [n for n in cnt if (cnt[n] > 1 or n in ports)] if skip_single else list(cnt)
    tracknets = sorted(nets, key=lambda n: (pcnt[n] / cnt[n], n))
    if torder: tracknets = [n for n in torder if n in nets]
    y0 = ntop + 250; ytr = {n: y0 + i * trk_pitch for i, n in enumerate(tracknets)}; ytop = y0 + len(tracknets) * trk_pitch
    pbot = max(-plan.inf(n)['rr'][1] for n in order_p); ypc = ytop + 250 + pbot
    posp, wp_ = place(order_p, ypc, gap_p, extra[nn:])
    pos = {**posn, **posp}
    for n, (x, y) in pos.items():
        s = specs[n]; k = (s['kind'], s['w'], s['l'], s['nf']); i = plan.info[k]; cp = i['cp']
        uses += f"use {plan.cells[k]}  {n}\ntimestamp 0\ntransform 1 0 {x} 0 1 {y}\nbox {cp[0]} {cp[1]} {cp[2]} {cp[3]}\n"
    xs_ = {}; kinds_ = {}
    def to_track(x, y, net, ytk, up):
        rect('via2', x-28, y-28, x+28, y+28, net); rect('metal3', x-36, y-40, x+36, y+40, net)
        rect('via2', x-28, ytk-28, x+28, ytk+28, net); rect('metal3', x-36, ytk-40, x+36, ytk+40, net); rect('metal2', x-50, ytk-50, x+50, ytk+50, net)
        if up: rect('metal3', x-30, min(y, ytk), x+30, max(y, ytk), net)
        else:
            for yy in (y, ytk): rect('via3', x-32, yy-32, x+32, yy+32, net); rect('metal3', x-36, yy-80, x+36, yy+80, net); rect('metal4', x-36, yy-36, x+36, yy+36, net)
            rect('metal4', x-30, min(y, ytk), x+30, max(y, ytk), net)
        xs_.setdefault(net, []).append(x); kinds_.setdefault((net, x), up)
    for n, (x, y) in pos.items():
        s = specs[n]; i = plan.inf(n); sgn = 1 if s['kind'] == 'n' else -1; up = sgn == 1
        py = y + sgn * (i['ys'][1] - 110)
        for net, dx in zip(s['strips'], i['xs']):
            xx = x + dx
            if net not in ytr: continue                         # net private to this cell (shared strip between two fingers): no wire needed
            rect('metal1', xx-40, py-40, xx+40, py+40, net); rect('via1', xx-26, py-26, xx+26, py+26, net); rect('metal2', xx-50, py-50, xx+50, py+50, net)
            to_track(xx, py, net, ytr[net], up)
        for f, (net, dx) in enumerate(zip(s['gates'], i['gx'])):
            xg = x + dx; gy = y + sgn * i['yg']; gv = gy + sgn * 12
            rect('metal1', xg-40, min(gy-sgn*23, gy+sgn*50), xg+40, max(gy-sgn*23, gy+sgn*50), net); rect('via1', xg-26, gv-26, xg+26, gv+26, net)
            xj = xg + (229 if (s['nf'] == 1 or f >= s['nf'] // 2 and s['nf'] > 1) else -229)
            if s['nf'] > 1 and f < s['nf'] // 2: xj = xg - 229
            lo, hi = min(xg, xj), max(xg, xj); rect('metal2', lo-50, gv-50, hi+50, gv+50, net)
            to_track(xj, gv, net, ytr[net], up)
        # ring tie at the ring corner facing away from the channel, jumper to a strap in the gap on the left
        net = s['bulk']; cx = x + i['rr'][0] + 22; yc = y + (i['rr'][1] + 20 if sgn == 1 else i['rr'][3] - 20)
        rect('locali', cx-70, yc-70, cx+70, yc+70, net); rect('viali', cx-29, yc-29, cx+29, yc+29, net)
        rect('metal1', cx-60, yc-60, cx+60, yc+60, net); rect('via1', cx-26, yc-26, cx+26, yc+26, net)
        xslot = x + i['rr'][0] - 150
        rect('metal2', xslot-60, yc-60, cx+60, yc+60, net)
        to_track(xslot, yc, net, ytr[net], up)
    XL = -700
    for net, yt in ytr.items():
        xs = xs_.get(net, [0]); a = min(xs) - 50; b = max(xs) + 50
        if net in ports: a = min(a, XL)
        rect('metal2', a, yt-30, b, yt+30, net)
        sx = sorted(set(xs))
        for u, v in zip(sx, sx[1:]):                  # two pads of the same net closer than the spacing rule: fill the notch
            if v - u - 100 < 30: rect('metal2', u-50, yt-50, v+50, yt+50, net)
            if v - u - 72 < 62:
                hh = 80 if not (kinds_.get((net, u), True) and kinds_.get((net, v), True)) else 40
                rect('metal3', u-36, yt-hh, v+36, yt+hh, net)
        if net in ports: LAB.append(('metal2', a + 60, yt, net))
    return dict(R=R, LAB=LAB, uses=uses, pos=pos, ytr=ytr, width=max(wn_, wp_), plan=plan)


def check(res, sp=60):
    SP = {'metal2': 30, 'metal3': sp, 'metal4': sp}
    bad = []; by = collections.defaultdict(list)
    for l, a, b, c, d, net in res['R']:
        if net is not None and l in SP: by[l].append((a, b, c, d, net))
    for l, rs in by.items():
        rs.sort()
        for i in range(len(rs)):
            A = rs[i]
            for j in range(i + 1, len(rs)):
                B = rs[j]; q = SP[l]
                if B[0] >= A[2] + q: break
                if A[4] != B[4] and A[1] < B[3] + q and B[1] < A[3] + q: bad.append((l, A, B))
    return bad


def optimise(plan, order_n, order_p, gap_n, gap_p, ports, seed=1, iters=6000):
    rnd = random.Random(seed); n = len(order_n) + len(order_p); extra = [0] * n; torder = None
    def go(): r = route(plan, order_n, order_p, extra, torder, gap_n, gap_p, ports=ports); return len(check(r)), r
    nb, r = go(); it = 0
    while nb > 0 and it < iters:
        it += 1
        if it % 7 == 0:
            cur = list(torder or sorted(r['ytr'], key=lambda q: r['ytr'][q])); i, j = rnd.sample(range(len(cur)), 2); new = cur[:]; new[i], new[j] = new[j], new[i]
            keep = torder; torder = new; n2, r2 = go()
            if n2 <= nb: nb, r = n2, r2
            else: torder = keep
            continue
        k = rnd.randrange(n); old = extra[k]; extra[k] = rnd.randrange(0, 800, 10); n2, r2 = go()
        if n2 <= nb: nb, r = n2, r2
        else: extra[k] = old
    print('extra gaps', extra, 'channel conflicts', nb, 'iterations', it)
    return r, nb


def write_mag(res, path):
    out = ['magic', 'tech sky130A', 'magscale 1 2', 'timestamp 0', '<< checkpaint >>', 'rect -2000 -2000 2000 2000']
    by = {}
    for l, a, b, c, d, net in res['R']: by.setdefault(l, []).append((a, b, c, d))
    for l, rs in by.items(): out.append(f'<< {l} >>'); out += [f'rect {a} {b} {c} {d}' for a, b, c, d in rs]
    out.append('<< labels >>')
    for i, (l, x, y, t) in enumerate(res['LAB']):
        out.append(f'flabel {l} {x} {y} {x} {y} 0 FreeSans 120 0 0 0 {t}'); out.append(f'port {i+1} nsew')
    out.append('<< end >>')
    head, rest = ('\n'.join(out) + '\n').split('<< checkpaint >>', 1)
    open(path, 'w').write(head + res['uses'] + '<< checkpaint >>' + rest)
