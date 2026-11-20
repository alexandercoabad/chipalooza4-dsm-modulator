import os
R=os.environ.get("SKY130PR","/path/to/skywater-pdk-libs-sky130_fd_pr")  # git clone github.com/google/skywater-pdk-libs-sky130_fd_pr
RC={c:'r+c/res_typical__cap_typical.spice' for c in ['tt','ss','ff','sf','fs']}
def lib(corner, rc=None):
    c=corner
    return f"""
.include "{R}/cells/nfet_01v8/sky130_fd_pr__nfet_01v8__{c}.corner.spice"
.include "{R}/cells/pfet_01v8/sky130_fd_pr__pfet_01v8__{c}.corner.spice"
.include "{R}/cells/nfet_g5v0d10v5/sky130_fd_pr__nfet_g5v0d10v5__{c}.corner.spice"
.include "{R}/cells/pfet_g5v0d10v5/sky130_fd_pr__pfet_g5v0d10v5__{c}.corner.spice"
.include "{R}/models/corners/{c}/nonfet.spice"
.include "{R}/models/{rc or RC[c]}"
.include "{R}/models/{(rc or RC[c]).replace('.spice','__lin.spice')}"
.include "{R}/models/all.spice"
.include "{R}/cells/nfet_01v8/sky130_fd_pr__nfet_01v8__mismatch.corner.spice"
.include "{R}/cells/pfet_01v8/sky130_fd_pr__pfet_01v8__mismatch.corner.spice"
.include "{R}/cells/nfet_g5v0d10v5/sky130_fd_pr__nfet_g5v0d10v5__mismatch.corner.spice"
.include "{R}/cells/pfet_g5v0d10v5/sky130_fd_pr__pfet_g5v0d10v5__mismatch.corner.spice"
"""
