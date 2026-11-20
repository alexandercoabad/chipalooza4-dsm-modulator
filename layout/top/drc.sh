#!/usr/bin/env bash
# Magic DRC (drc(full)) and the official sky130A KLayout deck on dsm_top.gds.  usage: drc.sh   (run top_route.py first)
cd "$(dirname "$0")"; : ${PDK_ROOT:=$HOME/openeda/pdk/share/pdk}; export PDK_ROOT PDK=sky130A
export PATH=$HOME/openeda/magicinst/bin:$PATH
magic -dnull -noconsole -rcfile $PDK_ROOT/sky130A/libs.tech/magic/sky130A.magicrc drc_top.tcl < /dev/null > drc_magic.log 2>&1
grep -E "DRC_COUNT|RULE" drc_magic.log
klayout -b -r $PDK_ROOT/sky130A/libs.tech/klayout/drc/sky130A_mr.drc -rd input=dsm_top.gds -rd topcell=dsm_top -rd report=klayout_top.lyrdb -rd feol=true -rd beol=true -rd offgrid=true -rd thr=4 > klayout.log 2>&1
echo "KLayout items: $(grep -c '<item>' klayout_top.lyrdb)"
