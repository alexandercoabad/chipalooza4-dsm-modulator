import pya, sys
for f in sys.argv[1:] if len(sys.argv)>1 else ["comp_compact.gds","../comp/comp.gds"]:
    l=pya.Layout(); l.read(f); c=l.top_cell(); b=c.bbox(); print(f, "bbox um %.2f x %.2f = %.0f um2"%(b.width()*l.dbu, b.height()*l.dbu, b.width()*b.height()*l.dbu**2))
