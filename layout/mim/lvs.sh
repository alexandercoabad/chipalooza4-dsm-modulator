#!/usr/bin/env bash
# LVS (Netgen, official sky130A setup) of the extracted array against cap_array_sch.spice, plus four negative tests that must FAIL:
# Cs with 3 units / Ci with 3, one unit with plates swapped, one unit with a wrong size, one Cs top plate on g.  usage: lvs.sh   (run build.sh first)
cd "$(dirname "$0")"; : ${PDK_ROOT:=$HOME/openeda/pdk/share/pdk}
S=$PDK_ROOT/sky130A/libs.tech/netgen/sky130A_setup.tcl
run() { netgen-lvs -batch lvs "cap_array_ext.spice cap_array" "$1 cap_array" $S $2 > /dev/null 2>&1
        if grep -qiE "mismatch|property error|do not match|Netlists do not" $2 || ! grep -q "Circuits match uniquely" $2; then return 1; else return 0; fi; }
rc=0
if run cap_array_sch.spice lvs.out; then echo "lvs.out: MATCH"; else echo "lvs.out: FAIL"; rc=1; fi
for n in neg_cs3_ci3 neg_plate_swap neg_wrong_size neg_cs_top_on_g; do
  if run ref/$n.spice lvs_$n.out; then echo "negative test $n NOT detected"; rc=1; else echo "negative test $n detected"; fi
done
exit $rc
