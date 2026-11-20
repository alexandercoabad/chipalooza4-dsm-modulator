#!/usr/bin/env bash
# LVS of the extracted TG against a schematic (Netgen, official sky130A setup) with an explicit verdict.
# usage: [NAME=..] [SCH=..] [SCHCELL=..] [OUT=..] lvs_mf.sh   (run build_mf.sh first).  Exit code 0 = PASS, 1 = FAIL.
# Netgen prints "Circuits match uniquely" and "Cell pin lists are equivalent" even when a pin-table row says **Mismatch** or when
# device properties (w, l) differ ("property errors"), so the verdict looks for those explicitly (as layout/ota/lvs.sh does).
cd "$(dirname "$0")"; : ${PDK_ROOT:=$HOME/openeda/pdk/share/pdk}; NAME=${NAME:-tg_x0p5_mf}; SCH=${SCH:-${NAME}_sch.spice}
SCHCELL=${SCHCELL:-$NAME}; OUT=${OUT:-${NAME}_lvs.out}
netgen-lvs -batch lvs "${NAME}_ext.spice $NAME" "$SCH $SCHCELL" $PDK_ROOT/sky130A/libs.tech/netgen/sky130A_setup.tcl $OUT > /dev/null 2>&1
v=PASS
grep -q "Circuits match uniquely" $OUT || v=FAIL
grep -qiE "mismatch|property errors|do not match|Netlists do not|no matching" $OUT && v=FAIL
echo "LVS_VERDICT: $v ($NAME vs $SCH)"; [ $v = PASS ]
