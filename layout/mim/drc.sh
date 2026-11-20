#!/usr/bin/env bash
# Official sky130A KLayout deck on the generated GDS. usage: drc.sh
cd "$(dirname "$0")"; : ${PDK_ROOT:=$HOME/openeda/pdk/share/pdk}
klayout -b -r $PDK_ROOT/sky130A/libs.tech/klayout/drc/sky130A_mr.drc -rd input=cap_array.gds -rd topcell=cap_array -rd report=klayout_cap.lyrdb -rd feol=true -rd beol=true -rd offgrid=true -rd thr=2 > klayout.log 2>&1
echo "KLayout items: $(grep -c '<item>' klayout_cap.lyrdb)"
