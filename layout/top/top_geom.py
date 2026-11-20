"""Geometry for dsm_top: place the block GDS files per topdef.FLOORPLAN, find the metal shape behind every pin label, report overlaps.
Run with klayout -b -r top_geom.py.  Units: dbu = 1 nm."""
import pya, os, sys, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import topdef as T

LABEL_LAYER = {67: 'li1', 68: 'met1', 69: 'met2', 70: 'met3', 71: 'met4', 72: 'met5'}
LAYERNUM = {'li1': 67, 'met1': 68, 'met2': 69, 'met3': 70, 'met4': 71, 'met5': 72}
NM = lambda um: int(round(um * 1000))


def load_top():
    """returns (layout, top cell, {inst: (cell, dx, dy)}, {cell: block bbox in block coordinates})"""
    ly = pya.Layout(); ly.dbu = 0.001
    top = ly.create_cell('dsm_top'); cells = {}; bbox = {}
    for name, (gds, sch) in T.BLOCKS.items():
        sub = pya.Layout(); sub.read(os.path.join(T.BASE, gds))
        sc = sub.top_cell(); c = ly.create_cell(name); c.copy_tree(sc); cells[name] = c; bbox[name] = sc.bbox()
    inst = {}
    for i, (cell, x, y) in T.FLOORPLAN.items():
        top.insert(pya.CellInstArray(cells[cell].cell_index(), pya.Trans(NM(x), NM(y)))); inst[i] = (cell, NM(x), NM(y))
    return ly, top, inst, bbox


def pin_shapes(ly, top, inst, bbox):
    """{(inst, pin): [(layername, polygon in top coordinates), ...]}: for every label of the block the merged drawing-layer polygon it sits on"""
    out = collections.defaultdict(list)
    done = {}
    for i, (cell, dx, dy) in inst.items():
        c = ly.cell(ly.cell_by_name(cell)); shift = pya.Trans(dx, dy)
        if cell not in done:
            labs = []
            for li in ly.layer_indexes():
                info = ly.get_info(li)
                if info.datatype != 5 or info.layer not in LABEL_LAYER: continue
                it = c.begin_shapes_rec(li)
                while not it.at_end():
                    sh = it.shape()
                    if sh.is_text(): p = it.trans() * sh.text.trans.disp; labs.append((sh.text.string, info.layer, pya.Point(p.x, p.y)))
                    it.next()
            regs = {}
            for L in set(l for _, l, _ in labs):
                dl = ly.find_layer(L, 20); regs[L] = pya.Region(c.begin_shapes_rec(dl)).merged() if dl is not None else pya.Region()
            done[cell] = (labs, regs)
        labs, regs = done[cell]
        for name, L, pt in labs:
            if name not in {p for (j, p) in T_pins(i)}: continue
            for poly in regs[L].each():
                b = poly.bbox()
                if b.left <= pt.x <= b.right and b.bottom <= pt.y <= b.top and poly.inside(pt):
                    out[(i, name)].append((LABEL_LAYER[L], poly.transformed(shift)))
    return out


def T_pins(i):
    return {(j, p) for pins in T.NETS.values() for (j, p) in pins if j == i}


if __name__ == '__main__':
    ly, top, inst, bbox = load_top()
    ps = pin_shapes(ly, top, inst, bbox)
    boxes = {}
    for i, (cell, dx, dy) in inst.items():
        b = bbox[cell]; boxes[i] = pya.Box(b.left + dx, b.bottom + dy, b.right + dx, b.top + dy)
        print('%-5s %-13s x %.2f..%.2f  y %.2f..%.2f' % (i, cell, boxes[i].left/1e3, boxes[i].right/1e3, boxes[i].bottom/1e3, boxes[i].top/1e3))
    names = list(boxes)
    for a in range(len(names)):
        for b in range(a + 1, len(names)):
            if boxes[names[a]].overlaps(boxes[names[b]]): print('OVERLAP', names[a], names[b])
    allb = pya.Box()
    for b in boxes.values(): allb += b
    print('chip bbox um', allb.left/1e3, allb.bottom/1e3, allb.right/1e3, allb.top/1e3)
    missing = [(i, p) for pins in T.NETS.values() for (i, p) in pins if i != 'TOP' and (i, p) not in ps]
    print('pins without a shape:', missing)
    for k, v in sorted(ps.items()):
        print(k, [(l, round(pl.bbox().width()/1e3, 2), round(pl.bbox().height()/1e3, 2)) for l, pl in v][:3])
