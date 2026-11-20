#!/usr/bin/env bash
# Clock generator layout from scratch: PDK multifinger pcells (Magic) -> placement and routing (gen_cg.py + autolay3.py) -> DRC -> GDS -> extraction.
set -e; cd "$(dirname "$0")"
export PDK=sky130A; : ${PDK_ROOT:=$HOME/openeda/pdk/share/pdk}; export PDK_ROOT
MAGIC="magic -dnull -noconsole -rcfile $PDK_ROOT/sky130A/libs.tech/magic/sky130A.magicrc"
rm -rf build; mkdir build
python3 gen_cg.py > gen_cg.log; tail -4 gen_cg.log
for s in drc_cg ext_cg gds_cg; do cp $s.tcl build/; (cd build && timeout 900 $MAGIC $s.tcl < /dev/null > $s.log 2>&1); done
cp build/clkgen.mag build/clkgen.gds ./; cp build/clkgen_layout.spice clkgen_ext.spice
grep -h "DRC_COUNT\|RULE" build/drc_cg.log
