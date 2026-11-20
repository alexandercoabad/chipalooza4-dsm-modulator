#!/usr/bin/env bash
# LVS (Netgen, official sky130A setup) of the extracted layout against ota_core_sch.spice, plus two negative tests
# (en/enb swapped, wrong width) that must FAIL. usage: lvs.sh   (run build.sh first)
cd "$(dirname "$0")"; : ${PDK_ROOT:=$HOME/openeda/pdk/share/pdk}
S=$PDK_ROOT/sky130A/libs.tech/netgen/sky130A_setup.tcl
run() { netgen-lvs -batch lvs "ota_core_ext.spice ota_core" "$1 ota_core" $S $2 > /dev/null 2>&1
        if grep -qiE "mismatch|property error|do not match|Netlists do not|Pin lists.*differ" $2 || ! grep -q "Circuits match uniquely" $2; then echo "$2: FAIL"; return 1; else echo "$2: MATCH"; fi; }
run ota_core_sch.spice lvs.out; rc=$?
run ref/neg_en_enb_swap.spice lvs_neg_swap.out >/dev/null && { echo "negative test (swap) NOT detected"; rc=1; } || echo "negative test (swap) detected"
run ref/neg_wrong_width.spice lvs_neg_w.out >/dev/null && { echo "negative test (width) NOT detected"; rc=1; } || echo "negative test (width) detected"
exit $rc
