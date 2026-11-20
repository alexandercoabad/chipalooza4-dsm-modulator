#!/usr/bin/env bash
# Compact comparator layout from scratch: PDK multifinger pcells (Magic) -> placement and routing (gen_cc.py + autolay2.py) -> DRC -> GDS -> extraction.
set -e; cd "$(dirname "$0")"
export PDK=sky130A; : ${PDK_ROOT:=$HOME/openeda/pdk/share/pdk}; export PDK_ROOT
MAGIC="magic -dnull -noconsole -rcfile $PDK_ROOT/sky130A/libs.tech/magic/sky130A.magicrc"
rm -rf build; mkdir build
python3 gen_cc.py > gen_cc.log; tail -4 gen_cc.log
for s in drc_cc ext_cc gds_cc; do cp $s.tcl build/; (cd build && timeout 900 $MAGIC $s.tcl < /dev/null > $s.log 2>&1); done
cp build/comp_compact.mag build/comp_compact.gds ./; cp build/comp_compact_layout.spice comp_compact_ext.spice
grep -h "DRC_COUNT\|RULE" build/drc_cc.log
