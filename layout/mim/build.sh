#!/usr/bin/env bash
# Generate the Cs/Ci capacitor array from scratch: PDK MIM pcell (Magic) -> placement and wiring (gen_mim.py) -> DRC -> GDS -> extraction.
set -e; cd "$(dirname "$0")"
export PDK=sky130A; : ${PDK_ROOT:=$HOME/openeda/pdk/share/pdk}; export PDK_ROOT
MAGIC="magic -dnull -noconsole -rcfile $PDK_ROOT/sky130A/libs.tech/magic/sky130A.magicrc"
rm -rf build; mkdir build
cp gen.tcl drc_cap.tcl ext_cap.tcl gds_cap.tcl ext_para.tcl build/
(cd build && timeout 120 $MAGIC gen.tcl < /dev/null > gen.log 2>&1)
python3 -I gen_mim.py > build/gen_mim.log
for s in drc_cap ext_cap gds_cap ext_para; do (cd build && timeout 300 $MAGIC $s.tcl < /dev/null > $s.log 2>&1); done
cp build/cap_array.mag build/cap_array.gds ./
cp build/cap_array_layout.spice cap_array_ext.spice; cp build/cap_array_para.spice ./
grep -h "DRC_COUNT\|RULE" build/drc_cap.log
