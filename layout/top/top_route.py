"""Router for dsm_top.  Blocks are placed by top_geom/topdef; every net of topdef.NETS is wired on met3/met4 with a grid maze router (pitch 0.35 um, wire width 0.35 um,
adjacent grid lines are never used by different nets, so the spacing is 0.35 um >= the 0.30 um rule).  Pins are reached by via stacks that are checked against the
flattened metal of the blocks.  Output: dsm_top.gds (blocks as instances + routing + pads + labels).   run: klayout -b -r top_route.py
Not a general router: no rip-up, one net at a time (shortest first, power last); the checks are the DRC and LVS that follow."""
import pya, os, sys, heapq, itertools, collections, json, time
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import topdef as T, top_geom as G

P = 350                                   # grid pitch, nm
HW = 175                                  # half wire width (wire = one pitch wide)
SP = 300                                  # met3/met4 spacing
PAD = 190                                 # landing pad half size on met2/met3/met4 at a via2/via3: 0.09 um enclosure (via3.5 = 0.09, via2.5 = 0.085 on two adjacent edges)
M1PAD = 160                               # met1 pad half size at a via1 (via.5a = 0.085 on two adjacent edges)
BL = HW + SP                              # static bloat: a node is blocked if within BL of a foreign shape; a landing pad that would come closer than 0.30 um is turned away from it (pad_box)
CUTSP = {'mcon': 190, 'via1': 170, 'via2': 200, 'via3': 200, 'via4': 800}     # cut spacing rules (ct.2, via.2, via2.2, via3.2)
MIM_KEEP = 1400                           # capm.11 / capm.2b_a: met3 wires stay 1.4 um away from every MIM plate
NX, NY = 1143, 486                        # nodes: x 0..400 um, y 0..170 um
LAY = {'met3': 0, 'met4': 1}              # routing layers
GL = {'li1': (67, 20), 'mcon': (67, 44), 'met1': (68, 20), 'via1': (68, 44), 'met2': (69, 20), 'via2': (69, 44), 'met3': (70, 20), 'via3': (70, 44), 'met4': (71, 20), 'via4': (71, 44), 'met5': (72, 20), 'capm': (89, 44)}
TEXT = {'met4': (71, 5), 'met2': (69, 5)}
SPACE = {'li1': 170, 'met1': 140, 'met2': 140, 'met3': 300, 'met4': 300, 'met5': 400}   # spacing rules used by the stack legaliser
POWER = ('vdda', 'gnd')


def box(cx, cy, hx, hy=None): hy = hx if hy is None else hy; return pya.Box(cx - hx, cy - hy, cx + hx, cy + hy)
def node_xy(i, j): return i * P, j * P


class Grid:
    def __init__(self):
        self.bl = [np.zeros((NX, NY), dtype=np.int16) for _ in range(2)]        # 0 free, net id>0 owned region, -1 blocked
        self.netid = {}
    def nid(self, net): return self.netid.setdefault(net, len(self.netid) + 1)
    def mark(self, l, r, net, bloat=BL):
        """mark every node closer than `bloat` to rectangle r as belonging to `net` (net=None: blocked for everyone)"""
        i0 = int(np.floor((r.left - bloat) / P)) + 1; i1 = int(np.ceil((r.right + bloat) / P)) - 1
        j0 = int(np.floor((r.bottom - bloat) / P)) + 1; j1 = int(np.ceil((r.top + bloat) / P)) - 1
        i0, j0 = max(i0, 0), max(j0, 0); i1, j1 = min(i1, NX - 1), min(j1, NY - 1)
        if i0 > i1 or j0 > j1: return
        a = self.bl[l][i0:i1 + 1, j0:j1 + 1]
        if net is None: a[:] = -1; return
        k = self.nid(net); a[(a != 0) & (a != k)] = -1; a[a == 0] = k
    def ok(self, l, i, j, k): v = self.bl[l][i, j]; return v == 0 or v == k


class Plan:
    def __init__(self):
        self.ly, self.top, self.inst, self.bbox = G.load_top()
        self.pins = G.pin_shapes(self.ly, self.top, self.inst, self.bbox)
        self.reg = {}; self.li = {}; self.committed = []
        for name, (L, D) in GL.items():
            li = self.ly.find_layer(L, D); self.li[name] = li
            self.reg[name] = pya.Region(self.top.begin_shapes_rec(li)).merged() if li is not None else pya.Region()
        self.shapes = collections.defaultdict(list)       # (layername) -> [(Box, net)] routing and access shapes added by the router
        self.stackreg = {n: pya.Region() for n in ('li1', 'met1', 'met2', 'met3', 'met4', 'met5')}   # committed non-routing shapes per layer (for spacing checks)
        self.stacknet = {}                                 # (layer, Box tuple) -> net, for foreign tests
        self.grid = Grid(); self.cutlist = []; self.why = {}
        self.pad_poly = {}                                 # TOP pins -> polygon
        for pin, (x, y) in T.TOP_PINS.items(): self.pad_poly[pin] = pya.Polygon(box(int(round(x * 1000)), int(round(y * 1000)), 1750))
        self.make_static()
        self.reserve()

    def reserve(self):
        """pins with few access nodes (TG gate pads) reserve them: other nets pay a penalty for passing there, so their only way in is not taken by an earlier net"""
        self.pen_net = {}; self.pen = np.zeros((2, NX, NY), dtype=np.float32)
        for net, plist in T.NETS.items():
            for inst, pin in plist:
                cs = self.candidates(net, inst, pin, limit=10**6)
                if len(cs) > 40: continue
                a = np.zeros((2, NX, NY), dtype=np.float32)
                for (l, i, j, _) in cs: a[:, max(i - 1, 0):i + 2, max(j - 1, 0):j + 2] = 40.0
                self.pen_net[(net, inst, pin)] = a; self.pen = np.maximum(self.pen, a)
        print('reserved pins:', len(self.pen_net))

    # ---- electrical ownership of block metal: shapes connected to a pin through mcon/via1..via4 (no traversal of devices) ----
    CUT = [('li1', 'mcon', 'met1'), ('met1', 'via1', 'met2'), ('met2', 'via2', 'met3'), ('met3', 'via3', 'met4'), ('met4', 'via4', 'met5')]
    def local(self, layer, win):
        return pya.Region(self.top.begin_shapes_rec_touching(self.li[layer], win)).merged()
    def flood(self, inst, pin):
        """{layer: Region} of block metal electrically tied to the pin (within the instance window)"""
        cell, dx, dy = self.inst[inst]; b = self.bbox[cell]; win = pya.Box(b.left + dx - 100, b.bottom + dy - 100, b.right + dx + 100, b.top + dy + 100)
        loc = {n: self.local(n, win) for n in ('li1', 'met1', 'met2', 'met3', 'met4', 'met5', 'mcon', 'via1', 'via2', 'via3', 'via4', 'capm')}
        loc['via3'] = loc['via3'] - loc['via3'].interacting(loc['capm'])      # via3 on a MIM top plate does not connect to the metal3 plate below
        own = {n: pya.Region() for n in ('li1', 'met1', 'met2', 'met3', 'met4', 'met5')}
        for ln, poly in self.pins[(inst, pin)]: own[ln] = own[ln] + pya.Region(poly)
        changed = True
        while changed:
            changed = False
            for a, c, bb in self.CUT:
                cuts = loc[c]
                for src, dst in ((a, bb), (bb, a)):
                    if own[src].is_empty(): continue
                    hit = cuts.interacting(own[src])
                    if hit.is_empty(): continue
                    add = loc[dst].interacting(hit)
                    new = (own[dst] + add).merged()
                    if new.area() != own[dst].area(): own[dst] = new; changed = True
        return own

    # ---- static obstacles: block metal on the routing layers (pin shapes on a routing layer belong to their net) ----
    def make_static(self):
        own = collections.defaultdict(list)                # layer -> [(poly, net)] metal tied to a pin, on the routing layers
        self.own = {}
        for net, plist in T.NETS.items():
            for inst, pin in plist:
                if inst == 'TOP': own['met4'].append((self.pad_poly[pin], net)); self.own[(inst, pin)] = {'met4': pya.Region(self.pad_poly[pin])}
                else:
                    fl = self.flood(inst, pin); self.own[(inst, pin)] = fl
                    for ln in LAY:
                        for poly in fl[ln].each(): own[ln].append((poly, net))
        # layer changes (via3) must not touch or crowd a block via3; the MIM plates keep met3 wires 1.4 um away
        self.netown = {ln: collections.defaultdict(pya.Region) for ln in ('met3', 'met4')}
        for net, plist in T.NETS.items():
            for inst, pin in plist:
                for ln in ('met3', 'met4'):
                    if inst == 'TOP': continue
                    self.netown[ln][net] = self.netown[ln][net] + self.own[(inst, pin)][ln]
        self.via3ok = np.ones((NX, NY), dtype=bool)
        for poly in self.reg['via3'].each():
            b = poly.bbox().enlarged(100 + CUTSP['via3'] - 1, 100 + CUTSP['via3'] - 1)
            i0, i1 = int(np.floor(b.left / P)) + 1, int(np.ceil(b.right / P)) - 1; j0, j1 = int(np.floor(b.bottom / P)) + 1, int(np.ceil(b.top / P)) - 1
            self.via3ok[max(i0, 0):max(i1 + 1, 0), max(j0, 0):max(j1 + 1, 0)] = False
        for poly in self.reg['met3'].each():                  # wide met3 (MIM plates): no layer change (met3 landing pad) closer than 0.4 um + pad (met3.3d)
            if min(poly.bbox().width(), poly.bbox().height()) <= 3000: continue
            b = poly.bbox().enlarged(400 + PAD + 20, 400 + PAD + 20)
            i0, i1 = int(np.floor(b.left / P)) + 1, int(np.ceil(b.right / P)) - 1; j0, j1 = int(np.floor(b.bottom / P)) + 1, int(np.ceil(b.top / P)) - 1
            self.via3ok[max(i0, 0):max(i1 + 1, 0), max(j0, 0):max(j1 + 1, 0)] = False
        for poly in self.reg['capm'].each():
            self.grid.mark(0, poly.bbox(), None, bloat=MIM_KEEP + PAD)
        for ln, l in LAY.items():
            R = self.reg[ln].dup()
            for poly, net in own[ln]: R = R - pya.Region(poly)
            for poly in R.merged().each():
                for t in poly.decompose_trapezoids(0): self.grid.mark(l, t.bbox(), None)
            for poly, net in own[ln]:
                for t in poly.decompose_trapezoids(0): self.grid.mark(l, t.bbox(), net)
        # chip border: keep nodes 2 pitches inside the grid
        for l in (0, 1):
            self.grid.bl[l][:2, :] = -1; self.grid.bl[l][-2:, :] = -1; self.grid.bl[l][:, :2] = -1; self.grid.bl[l][:, -2:] = -1

    # ---- pin access candidates ----
    def foreign(self, layer, b, net, own=None):
        """True if rectangle b on `layer` is closer than the spacing rule to block metal that is not electrically tied to this pin, or to a committed stack of another net"""
        sp = SPACE[layer]; win = b.enlarged(sp, sp); probe = pya.Region(b.enlarged(sp - 1, sp - 1))
        loc = pya.Region(self.top.begin_shapes_rec_touching(self.li[layer], win)).merged()
        if own is not None and layer in own and not own[layer].is_empty(): loc = loc - own[layer]
        if not (loc & probe).is_empty(): return True
        for (lay, bt, n) in self.committed:
            if lay == layer and n != net and b.enlarged(sp - 1, sp - 1).overlaps(pya.Box(*bt)): return True
        return False

    def stack_m1(self, net, ln, x, y, rects, reg, own):
        """via stack from li1/met1 metal up to met3 at grid node (x, y): an anchor on the nearest strip rectangle (mcon for li1), met1 jog to the node, via1, met2 pad, via2"""
        best = None
        for r in rects:
            mx = min(max(x, r.left + (85 if ln == 'li1' else 0)), r.right - (85 if ln == 'li1' else 0)); my = min(max(y, r.bottom + (85 if ln == 'li1' else 0)), r.top - (85 if ln == 'li1' else 0))
            d = abs(mx - x) + abs(my - y)
            if d <= 1400 and (best is None or d < best[0]): best = (d, mx, my)
        if best is None: return self._no('nobest')
        d, mx, my = best
        m2 = self.m2_pad(net, x, y, own)
        if m2 is None: return self._no('m2foreign')
        shapes = []
        if ln == 'li1':
            mc = box(mx, my, 85)
            if not self.inside(mc, reg): return self._no('mcon_notin')
            st = self.cut_state('mcon', mc)
            if st is None: return self._no('mcon_state')
            if st == 'new': shapes.append(('mcon', mc))
            shapes.append(('met1', box(mx, my, 145)))
        if d > 0 or ln == 'li1':
            shapes.append(('met1', pya.Box(min(mx, x) - 145, my - 145, max(mx, x) + 145, my + 145)))
            shapes.append(('met1', pya.Box(x - 145, min(my, y) - 145, x + 145, max(my, y) + 145)))
        shapes.append(('met1', box(x, y, M1PAD)))
        for l2, b2 in shapes:
            if l2 == 'met1' and self.foreign('met1', b2, net, own): return self._no('met1foreign')
        if self.own_gap('met1', [b2 for l2, b2 in shapes if l2 == 'met1'], own): return self._no('met1owngap')
        v1, v2 = box(x, y, 75), box(x, y, 100)
        s1, s2 = self.cut_state('via1', v1), self.cut_state('via2', v2)
        if s1 is None or s2 is None: return self._no('cut_state')
        if s1 == 'new': shapes.append(('via1', v1))
        shapes.append(('met2', m2))
        if s2 == 'new': shapes.append(('via2', v2))
        return shapes

    def _no(self, tag):
        self.why[tag] = self.why.get(tag, 0) + 1; return None

    def m2_pad(self, net, x, y, own):
        """met2 pad under via1 (75) and via2 (100): 0.085 beyond via1 on two adjacent sides (m2.5), >= 0.045 beyond via2 on all sides; try the symmetric pad, then the four oriented ones"""
        for hl, hr, hb, ht in ((PAD, PAD, PAD, PAD), (185, 185, 145, 145), (145, 145, 185, 185)):   # 0.085 beyond the via2 on both sides in one direction (via2.4a; also gives the via1 its 0.085 in one direction, met2.5), 0.045 the other way
            b = pya.Box(x - hl, y - hb, x + hr, y + ht)
            if not self.foreign('met2', b, net, own) and not self.own_gap('met2', [b], own) and self.neck_ok(b, own): return b
        return None

    def neck_ok(self, b, own):
        """a met2 pad may overlap the pin's own met2 only by a piece at least 0.14 um wide each way (a smaller overlap is a neck: met2.1)"""
        R = own.get('met2') if own else None
        if R is None or R.is_empty(): return True
        inter = pya.Region(b) & R
        if inter.is_empty(): return True
        if (pya.Region(b) - R).is_empty(): return True                          # pad entirely inside own metal
        return all(p.bbox().width() >= 140 and p.bbox().height() >= 140 for p in inter.each())

    def own_gap(self, layer, boxes, own):
        """True if the new metal `boxes` comes closer than the spacing rule to a polygon of the pin's own metal that it does not touch (touching = merged, fine)"""
        R = own.get(layer) if own else None
        if R is None or R.is_empty(): return False
        S = pya.Region(); [S.insert(b) for b in boxes]; S = S.merged(); sp = SPACE[layer]
        others = R.not_interacting(S)
        return not (others & S.sized(sp - 1)).is_empty()

    def inside(self, b, R): return (pya.Region(b) - R).is_empty()

    def pad_legal(self, layer, b, net):
        sp = SPACE[layer]; probe = b.enlarged(sp - 1, sp - 1)
        loc = pya.Region(self.top.begin_shapes_rec_touching(self.li[layer], b.enlarged(sp + 100, sp + 100))).merged()
        own = self.netown[layer].get(net) if layer in self.netown else None
        if own is not None and not own.is_empty(): loc = loc - own
        if not (loc & pya.Region(probe)).is_empty(): return False
        if layer == 'met3':                                                       # met3.3d: wide (> 3 um) met3 wants 0.4 um to unrelated met3 (MIM plates)
            wide = pya.Region(); [wide.insert(p) for p in loc.each() if min(p.bbox().width(), p.bbox().height()) > 3000]
            if not (wide & pya.Region(b.enlarged(399, 399))).is_empty(): return False
        return not any(n != net and bb.overlaps(probe) for bb, n in self.shapes[layer])

    def pad_box(self, layer, x, y, net):
        """landing pad for via2/via3 on met3/met4: 0.09 um beyond the cut on two adjacent sides (via3.5), 0.065 on the others; the corner that keeps 0.3 um to foreign metal wins"""
        for hl, hr, hb, ht in ((PAD, PAD, PAD, PAD), (PAD, 165, PAD, 165), (165, PAD, PAD, 165), (PAD, 165, 165, PAD), (165, PAD, 165, PAD)):
            b = pya.Box(x - hl, y - hb, x + hr, y + ht)
            if self.pad_legal(layer, b, net): return b
        print('  no legal pad on', layer, 'at', x / 1000, y / 1000, 'net', net); return box(x, y, PAD)

    def cut_state(self, layer, b):
        """'new' if a cut at b is legal and does not exist yet, 'exists' if the block already has that cut there, None if it would overlap a block cut partially or violate the cut spacing"""
        sp = CUTSP[layer]; R = pya.Region(self.top.begin_shapes_rec_touching(self.li[layer], b.enlarged(sp + 10, sp + 10))).merged(); rb = pya.Region(b)
        if not (R & rb).is_empty():
            return 'exists' if (rb - R).is_empty() else None
        if not (R & pya.Region(b.enlarged(CUTSP[layer] - 1, CUTSP[layer] - 1))).is_empty(): return None
        for (lay, bt) in self.cutlist:
            if lay == layer and pya.Box(*bt).enlarged(CUTSP[layer] - 1, CUTSP[layer] - 1).overlaps(b) and pya.Box(*bt) != b: return None
        return 'new'

    def candidates(self, net, inst, pin, limit=60):
        """list of (route layer index, i, j, [(layername, Box)] shapes of the via stack) for this pin"""
        own = self.own[(inst, pin)]; k = self.grid.nid(net); out = []
        def free(l, i, j): return 0 <= i < NX and 0 <= j < NY and self.grid.ok(l, i, j, k)
        for ln in ('met5', 'met4', 'met3', 'met2', 'met1', 'li1'):
            R = own.get(ln)
            if R is None or R.is_empty(): continue
            strips = {}
            for poly in R.each():
                strips[id(poly)] = [t.bbox() for t in poly.decompose_trapezoids(0)]
                bb = poly.bbox(); reg = pya.Region(poly)
                if ln == 'met5':                                           # strip: via4 centred in the strip, M4 pad 1.2 um
                    cx = (bb.left + bb.right) // 2
                    for y in range(bb.bottom + 1000, bb.top - 600, 700):
                        pad = box(cx, y, 600); v4 = box(cx, y, 400); i = int(round(cx / P)); j = int(round(y / P))
                        st = self.cut_state('via4', v4)
                        if st is not None and free(1, i, j) and not self.foreign('met4', pad, net, own): out.append((1, i, j, [('met4', pad)] + ([('via4', v4)] if st == 'new' else [])))
                    continue
                ext = 1400 if ln in ('met1', 'li1') else 0                         # nodes up to 0.7 um outside the shape are reached by a met1 jog
                i0, i1 = int(np.ceil((bb.left - ext) / P)), int(np.floor((bb.right + ext) / P)); j0, j1 = int(np.ceil((bb.bottom - ext) / P)), int(np.floor((bb.top + ext) / P))
                stride = max(1, int(np.sqrt(max(1, (i1 - i0 + 1) * (j1 - j0 + 1)) / 120.0)))
                for i in range(i0, i1 + 1, stride):
                    for j in range(j0, j1 + 1, 1 if (j1 - j0) <= 12 else stride):          # every row for narrow strips (thin pins at a block edge have few legal rows)
                        x, y = node_xy(i, j)
                        if ln in ('met3', 'met4'):
                            l = LAY[ln]
                            if free(l, i, j) and self.inside(box(x, y, HW), reg): out.append((l, i, j, []))
                            continue
                        if not free(0, i, j): continue
                        v2 = box(x, y, 100)
                        if ln == 'met2':
                            if self.inside(box(x, y, 140), reg):
                                st = self.cut_state('via2', v2)
                                if st is None: continue
                                sh = [('via2', v2)] if st == 'new' else []
                                if not self.inside(box(x, y, PAD), reg):
                                    pad = self.m2_pad(net, x, y, own)
                                    if pad is None: continue
                                    sh.append(('met2', pad))
                                out.append((0, i, j, sh))
                        elif ln in ('met1', 'li1'):
                            c = self.stack_m1(net, ln, x, y, strips[id(poly)], reg, own)
                            if c: out.append((0, i, j, c))
        if len(out) > limit:
            step = len(out) / limit; out = [out[int(q * step)] for q in range(limit)]
        return out

    # ---- maze search ----
    def search(self, net, starts, tree):
        """Dijkstra/A* from `starts` [(l,i,j)] to any node of `tree` (set of (l,i,j)); returns path list"""
        k = self.grid.nid(net); bl = self.grid.bl
        others = [a for (n2, _, _), a in self.pen_net.items() if n2 != net]
        pen = np.maximum.reduce(others) if others else np.zeros((2, NX, NY), dtype=np.float32)
        ti = np.array([n[1] for n in tree]); tj = np.array([n[2] for n in tree])
        ix0, ix1, jy0, jy1 = ti.min(), ti.max(), tj.min(), tj.max()
        def h(i, j): return max(ix0 - i, 0, i - ix1) + max(jy0 - j, 0, j - jy1)
        pq = []; dist = {}; prev = {}; cnt = itertools.count()
        for s in starts:
            dist[s] = 0; heapq.heappush(pq, (h(s[1], s[2]), next(cnt), 0, s))
        VIA = 10
        while pq:
            f, _, g, u = heapq.heappop(pq)
            if g > dist.get(u, 1e18): continue
            if u in tree: break
            l, i, j = u
            for dl, di, dj in ((0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1), (1, 0, 0)):
                if dl:
                    if not self.via3ok[i, j]: continue
                    nl = 1 - l; ni, nj = i, j; c = VIA
                else:
                    nl, ni, nj = l, i + di, j + dj
                    if not (0 <= ni < NX and 0 <= nj < NY): continue
                    horiz = di != 0; c = 1 if (horiz == (l == 0)) else 3          # met3 horizontal, met4 vertical preferred
                v = bl[nl][ni, nj]
                if v != 0 and v != k: continue
                ng = g + c + float(pen[nl, ni, nj]); w = (nl, ni, nj)
                if ng < dist.get(w, 1e18):
                    dist[w] = ng; prev[w] = u; heapq.heappush(pq, (ng + h(ni, nj), next(cnt), ng, w))
        else:
            return None
        path = [u]
        while path[-1] in prev and path[-1] not in starts: path.append(prev[path[-1]])
        return path[::-1]

    def commit_nodes(self, net, path, tree):
        """draw the path: squares at nodes, rectangles between neighbours, via3 at layer changes; mark the grid"""
        for a, b in zip(path, path[1:] + [None]):
            tree.add(a)
            l, i, j = a; x, y = node_xy(i, j)
            r = box(x, y, HW); self.add_shape('met3' if l == 0 else 'met4', r, net)
            if b is None: continue
            if b[0] != l:
                self.add_shape('via3', box(x, y, 100), net)
                for ln2 in ('met3', 'met4'): self.add_shape(ln2, self.pad_box(ln2, x, y, net), net)
            else:
                x2, y2 = node_xy(b[1], b[2]); self.add_shape('met3' if l == 0 else 'met4', pya.Box(min(x, x2) - HW, min(y, y2) - HW, max(x, x2) + HW, max(y, y2) + HW), net)
        if len(path) == 1:
            pass

    def add_shape(self, layer, b, net):
        self.shapes[layer].append((b, net))
        if layer in ('mcon', 'via1', 'via2', 'via3', 'via4'): self.cutlist.append((layer, (b.left, b.bottom, b.right, b.top)))
        if layer in LAY: self.grid.mark(LAY[layer], b, net)

    def route_all(self, order):
        report = {}
        for net in order:
            pins = T.NETS[net]; t0 = time.time()
            tree = set(); cand = {}
            ordered = list(pins)
            first = True
            for (inst, pin) in ordered:
                self.why = {}; cs = self.candidates(net, inst, pin)
                cand[(inst, pin)] = cs
                if not cs:
                    pb = pya.Region([poly for l, poly in self.pins[(inst, pin)]]).bbox().enlarged(2500, 2500)
                    print('  committed near', inst, pin, [(l, (round(bt[0]/1000, 2), round(bt[1]/1000, 2), round(bt[2]/1000, 2), round(bt[3]/1000, 2)), n) for l, bt, n in self.committed if pya.Box(*bt).overlaps(pb)][:12])
                if not cs: print('  NO ACCESS', net, inst, pin, 'rejections:', dict(self.why)); report.setdefault(net, []).append(('noaccess', inst, pin)); continue
                if first:
                    # seed the tree with the access nodes closest to the other pins' centroid
                    c0 = cs[len(cs) // 2]; self.apply_access(net, c0, tree); first = False; continue
                starts = [(c[0], c[1], c[2]) for c in cs]
                path = self.search(net, starts, tree)
                if path is None: print('  NO PATH', net, inst, pin); report.setdefault(net, []).append(('nopath', inst, pin)); continue
                chosen = [c for c in cs if (c[0], c[1], c[2]) == path[0]][0]
                self.apply_access(net, chosen, tree); self.commit_nodes(net, path, tree)
            print('net %-5s %2d pins  %.1fs' % (net, len(pins), time.time() - t0)); sys.stdout.flush()
        return report

    def apply_access(self, net, c, tree):
        l, i, j, shapes = c
        for ln, b in shapes:
            self.add_shape(ln, b, net)
            if ln == 'via2': self.add_shape('met3', self.pad_box('met3', b.center().x, b.center().y, net), net)
            if ln in ('li1', 'met1', 'met2', 'met3', 'met4', 'met5'): self.committed.append((ln, (b.left, b.bottom, b.right, b.top), net))
        x, y = node_xy(i, j)
        self.add_shape('met3' if l == 0 else 'met4', box(x, y, HW), net); tree.add((l, i, j))

    # ---- output ----
    def fix_min_area(self, layer, amin=240000):
        """met3/met4 minimum area 0.24 um2: a router shape (access pad, short stub) that stays smaller is lengthened into free space (>= 0.3 um from foreign metal, outside the MIM keep-out)"""
        li = self.li[layer]; routed = pya.Region(); [routed.insert(b) for b, n in self.shapes[layer]]
        allr = (self.reg[layer] + routed).merged(); fixed = 0; stuck = 0
        capk = self.reg['capm'].sized(MIM_KEEP - 1) if layer == 'met3' else pya.Region()
        for poly in allr.each():
            a = poly.area()
            if a >= amin or (pya.Region(poly) & routed).is_empty(): continue
            bb = poly.bbox(); w, h = bb.width(), bb.height()
            foreign = allr - pya.Region(poly)
            cands = []
            for horiz in (True, False):
                short = h if horiz else w; e = int(np.ceil((amin - a) / short / 10.0)) * 10 + 10
                if horiz: cands += [pya.Box(bb.right - 1, bb.bottom, bb.right + e, bb.top), pya.Box(bb.left - e, bb.bottom, bb.left + 1, bb.top)]
                else: cands += [pya.Box(bb.left, bb.top - 1, bb.right, bb.top + e), pya.Box(bb.left, bb.bottom - e, bb.right, bb.bottom + 1)]
            for c in cands:
                if (foreign & pya.Region(c.enlarged(SP - 1, SP - 1))).is_empty() and (capk & pya.Region(c)).is_empty():
                    # the extension may be a wire of the same net next to a via2 pad etc.: draw it as router metal of that net
                    net = next((n for b, n in self.shapes[layer] if b.overlaps(bb) or b.touches(bb)), None)
                    self.shapes[layer].append((c, net)); fixed += 1; break
            else: stuck += 1; print('  min-area stub not fixable on', layer, 'at', bb.center().x / 1000, bb.center().y / 1000)
        print('min-area', layer, 'lengthened', fixed, 'stuck', stuck)

    def close_notches(self, layer, g=None):
        """slits narrower than the spacing rule between router metal and the block metal it touches (edge offsets of 20-30 nm) are filled, net by net:
        the metal of one net (its routed shapes plus the block metal they touch) is closed on its own, and fill that would touch any metal outside that net is skipped.
        (Closing all touched metal together also filled the 0.14 um slit between two different nets and shorted q to dac in the first version.)"""
        g = g or {'met1': 70, 'met2': 70, 'met3': 160, 'met4': 160}[layer]          # slits up to 2g wide between metal of ONE net are filled (0.14 um on met1/met2, 0.32 um on met3/met4)
        li = self.li[layer]; snap = list(self.shapes[layer])
        allr = (pya.Region(self.top.begin_shapes_rec(li)) + (lambda r: ([r.insert(b) for b, n in snap], r)[1])(pya.Region())).merged()
        n = 0; skipped = 0
        for net in sorted({nn for b, nn in snap if nn is not None}):
            routed = pya.Region(); [routed.insert(b) for b, nn in snap if nn == net]
            touched = allr.interacting(routed); foreign = allr - touched
            fill = touched.sized(g).sized(-g) - touched
            for poly in fill.each():
                if not (foreign & pya.Region(poly).sized(SPACE[layer] - 1)).is_empty(): skipped += 1; continue          # the fill must keep the spacing rule to every other net
                self.shapes[layer].append((poly.bbox(), None)) if poly.is_box() else [self.shapes[layer].append((t.bbox(), None)) for t in poly.decompose_trapezoids(0)]; n += 1
        print('notch fill', layer, n, 'skipped', skipped)

    def write(self, path):
        for lay in ('met3', 'met4'): self.fix_min_area(lay)
        for lay in ('met1', 'met2', 'met3', 'met4'): self.close_notches(lay)
        for ln, lst in self.shapes.items():
            li = self.ly.layer(*GL[ln])
            for b, net in lst: self.top.shapes(li).insert(b)
        for pin, (x, y) in T.TOP_PINS.items():
            li = self.ly.layer(*TEXT['met4']); self.top.shapes(li).insert(pya.Text(pin, pya.Trans(int(round(x * 1000)), int(round(y * 1000)))))
            li = self.ly.layer(*GL['met4']); self.top.shapes(li).insert(self.pad_poly[pin])
        self.ly.write(path)


if __name__ == '__main__':
    pl = Plan()
    gate = ('p2', 'p2b', 'q', 'qb', 'p1a', 'p1ab', 'p1', 'p1b')                 # nets whose TG gate pins have the least room come first, power last
    sizes = sorted(T.NETS, key=lambda n: (n in POWER, n not in gate, len(T.NETS[n])))
    rep = pl.route_all(sizes)
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dsm_top.gds'); pl.write(out)
    print('failures:', json.dumps(rep)); print('wrote', out)
