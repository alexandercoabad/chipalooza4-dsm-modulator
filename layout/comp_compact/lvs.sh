#!/usr/bin/env bash
# LVS (Netgen, official sky130A setup) of the extracted array against comp_sch.spice, plus three negative tests that must FAIL:
# inputs swapped, tail width changed, one reset PMOS gate on vdda.  usage: lvs.sh   (run build.sh first)
cd "$(dirname "$0")"; : ${PDK_ROOT:=$HOME/openeda/pdk/share/pdk}
S=$PDK_ROOT/sky130A/libs.tech/netgen/sky130A_setup.tcl
run() { netgen-lvs -batch lvs "comp_compact_ext.spice comp_compact" "$1 comp" $S $2 > /dev/null 2>&1
        if grep -qiE "mismatch|property error|do not match|Netlists do not" $2 || ! grep -q "Circuits match uniquely" $2; then return 1; else return 0; fi; }
rc=0
if run comp_sch.spice lvs.out; then echo "lvs.out: MATCH"; else echo "lvs.out: FAIL"; rc=1; fi
for n in neg_inputs_swapped neg_tail_width neg_reset_gate; do
  if run ref/$n.spice lvs_$n.out; then echo "negative test $n NOT detected"; rc=1; else echo "negative test $n detected"; fi
done
exit $rc
