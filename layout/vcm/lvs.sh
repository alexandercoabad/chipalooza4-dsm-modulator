#!/usr/bin/env bash
# LVS (Netgen, official sky130A setup) of the extracted layout against vcm_replica_sch.spice, plus four negative tests that must FAIL
# (header gate on vdda, core gate not tied to the output, core PMOS width halved, footer gate on gnd).  usage: lvs.sh   (run build.sh first)
cd "$(dirname "$0")"; : ${PDK_ROOT:=$HOME/openeda/pdk/share/pdk}
S=$PDK_ROOT/sky130A/libs.tech/netgen/sky130A_setup.tcl
run() { netgen-lvs -batch lvs "vcm_replica_ext.spice vcm_replica" "$1 vcm_replica" $S $2 > /dev/null 2>&1
        if grep -qiE "mismatch|property error|do not match|Netlists do not|Pin lists.*differ" $2 || ! grep -q "Circuits match uniquely" $2; then return 1; else return 0; fi; }
rc=0
if run vcm_replica_sch.spice lvs.out; then echo "lvs.out: MATCH"; else echo "lvs.out: FAIL"; rc=1; fi
for n in neg_header_off neg_gate_untied neg_wrong_width neg_footer_off; do
  if run ref/$n.spice lvs_$n.out; then echo "negative test $n NOT detected"; rc=1; else echo "negative test $n detected"; fi
done
exit $rc
