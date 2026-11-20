#!/usr/bin/env bash
# Generate the OTA core layout from scratch: PDK pcells (Magic) -> scripted wiring (gen_ota.py) -> DRC -> GDS -> extraction.
set -e; cd "$(dirname "$0")"
export PDK=sky130A; : ${PDK_ROOT:=$HOME/openeda/pdk/share/pdk}; export PDK_ROOT
MAGIC="magic -dnull -noconsole -rcfile $PDK_ROOT/sky130A/libs.tech/magic/sky130A.magicrc"
rm -rf build; mkdir build
cp gen.tcl drc_ota.tcl ext_ota.tcl gds_ota.tcl build/
(cd build && $MAGIC gen.tcl < /dev/null > gen.log 2>&1)
python3 -I gen_ota.py > build/gen_ota.log
for s in drc_ota ext_ota gds_ota; do (cd build && $MAGIC $s.tcl < /dev/null > $s.log 2>&1); done
cp build/ota_core.mag build/ota_core.gds ./
cp build/ota_core_layout.spice ota_core_ext.spice
grep -h "DRC_COUNT" build/drc_ota.log
