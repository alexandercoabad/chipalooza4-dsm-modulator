import re, collections
def parse(path):
    layers = collections.defaultdict(list); labels = []; uses = []; cur = None; scale = (1, 1)
    for ln in open(path):
        ln = ln.rstrip('\n')
        if ln.startswith('magscale'): scale = tuple(int(x) for x in ln.split()[1:3])
        elif ln.startswith('<<'): cur = ln.split()[1]
        elif ln.startswith('rect') and cur: layers[cur].append(tuple(int(x) for x in ln.split()[1:5]))
        elif ln.startswith('rlabel'):
            p = ln.split(); labels.append((p[1], tuple(int(x) for x in p[2:6]), p[7] if len(p) > 7 else p[-1]))
    return dict(layers=layers, labels=labels, scale=scale)
def union_x(rects, tol=0):
    xs = sorted(set((r[0], r[2]) for r in rects)); out = []
    for a, b in xs:
        if out and a <= out[-1][1] + tol: out[-1][1] = max(out[-1][1], b)
        else: out.append([a, b])
    return out
def bbox(layers):
    allr = [r for k, v in layers.items() if k not in ('checkpaint', 'end') for r in v]
    return (min(r[0] for r in allr), min(r[1] for r in allr), max(r[2] for r in allr), max(r[3] for r in allr))
