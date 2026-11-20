#!/usr/bin/env bash
# vcm replica layout from scratch: PDK cells (Magic) -> scripted wiring (gen_vcm.py) -> DRC -> GDS -> extraction.
set -e; cd "$(dirname "$0")"
export PDK=sky130A; : ${PDK_ROOT:=$HOME/openeda/pdk/share/pdk}; export PDK_ROOT
MAGIC="magic -dnull -noconsole -rcfile $PDK_ROOT/sky130A/libs.tech/magic/sky130A.magicrc"
rm -rf build; mkdir build
python3 -I gen_sch.py > /dev/null
cp gen.tcl drc_vcm.tcl ext_vcm.tcl gds_vcm.tcl build/
(cd build && timeout 120 $MAGIC gen.tcl < /dev/null > gen.log 2>&1)
python3 -I gen_vcm.py > build/gen_vcm.log
for s in drc_vcm ext_vcm gds_vcm; do (cd build && timeout 300 $MAGIC $s.tcl < /dev/null > $s.log 2>&1); done
cp build/vcm_replica.mag build/vcm_replica.gds ./
cp build/vcm_replica_layout.spice vcm_replica_ext.spice
grep -h "DRC_COUNT\|RULE" build/drc_vcm.log
