"""Wire resistance from Magic extresist (pex_res.tcl, flat dsm_top, tolerance 10 ohm): per net, the largest shortest-path resistance between two of its terminal nodes (.tN) = worst driver-to-load wire resistance (series resistance of metal, vias, local interconnect, diffusion/contact stubs as Magic models them; device on-resistance excluded)."""
import re, heapq, collections, json, os
H = os.path.dirname(os.path.abspath(__file__))
nets = collections.defaultdict(lambda: collections.defaultdict(list)); terms = collections.defaultdict(set)
for ln in open(os.path.join(H, 'dsm_top_flat.res.ext')):
    t = re.findall(r'"([^"]+)"|(\S+)', ln); t = [a or b for a, b in t]
    if t[0] == 'rnode':
        net = re.sub(r'\.(t|n)\d+$', '', t[1])
        if re.search(r'\.t\d+$', t[1]): terms[net].add(t[1])
    elif t[0] == 'resist':
        net = re.sub(r'\.(t|n)\d+$', '', t[1]); nets[net][t[1]].append((t[2], float(t[3]))); nets[net][t[2]].append((t[1], float(t[3])))
def dij(g, s):
    d = {s: 0}; q = [(0, s)]
    while q:
        c, u = heapq.heappop(q)
        if c > d[u]: continue
        for v, r in g[u]:
            if c + r < d.get(v, 1e18): d[v] = c + r; heapq.heappush(q, (c + r, v))
    return d
out = {}
for net, g in nets.items():
    T = sorted(terms[net]); worst = (0, None, None); tot = sum(r for v in g.values() for _, r in v) / 2
    for a in T:
        d = dij(g, a)
        for b in T:
            if b in d and d[b] > worst[0]: worst = (d[b], a, b)
    out[net] = dict(terminals=len(T), worst_R_ohm=round(worst[0], 1), between=[worst[1], worst[2]], sum_of_all_resistors_ohm=round(tot, 0))
json.dump(out, open(os.path.join(H, 'net_res.json'), 'w'), indent=1)
for n, r in sorted(out.items(), key=lambda x: -x[1]['worst_R_ohm']): print(f"{n:28} terms {r['terminals']:3}  worst path {r['worst_R_ohm']:8.1f} ohm")
