#!/usr/bin/env bash
# LVS (Netgen, official sky130A setup) of the extracted clock generator against clkgen_sch.spice, plus six negative tests that must FAIL
# (see make_neg.py).  Verdict looks for property errors and pin mismatches explicitly, as layout/tg_mf/lvs_mf.sh does.  usage: lvs.sh   (run build.sh first)
cd "$(dirname "$0")"; : ${PDK_ROOT:=$HOME/openeda/pdk/share/pdk}
S=$PDK_ROOT/sky130A/libs.tech/netgen/sky130A_setup.tcl
run() { netgen-lvs -batch lvs "clkgen_ext.spice clkgen" "$1 clkgen" $S $2 > /dev/null 2>&1
        if grep -qiE "mismatch|property error|do not match|Netlists do not|no matching" $2 || ! grep -q "Circuits match uniquely" $2; then return 1; else return 0; fi; }
python3 make_neg.py
rc=0
if run clkgen_sch.spice lvs.out; then echo "lvs.out: MATCH"; else echo "lvs.out: FAIL"; rc=1; fi
for n in delay_gate cap_node cap_size driver_w nand_input nor_rail; do
  if run ref/neg_$n.spice lvs_neg_$n.out; then echo "negative test $n NOT detected"; rc=1; else echo "negative test $n detected"; fi
done
exit $rc
