#!/usr/bin/env bash
# flat extraction of dsm_top.gds (Magic) and Netgen LVS against dsm_top_sch.spice.  usage: lvs.sh   (run top_route.py first)
cd "$(dirname "$0")"; : ${PDK_ROOT:=$HOME/openeda/pdk/share/pdk}; export PDK_ROOT PDK=sky130A
export PATH=$HOME/openeda/magicinst/bin:$PATH
mkdir -p build; cp ext_top.tcl dsm_top.gds build/
(cd build && magic -dnull -noconsole -rcfile $PDK_ROOT/sky130A/libs.tech/magic/sky130A.magicrc ext_top.tcl < /dev/null > ext.log 2>&1)
# the extracted top has no ports (pads are labels only): add the subckt header in the order of topdef.TOP_PORTS
PORTS=$(PYTHONPATH=. python3 -c "import topdef;print(' '.join(topdef.TOP_PORTS))")
{ echo "* extracted dsm_top, flat"; echo ".subckt dsm_top $PORTS"; grep -v -E '^\*|^\.end|^\.subckt' build/dsm_top_ext.spice; echo ".ends"; } > build/dsm_top_flat.spice
netgen-lvs -batch lvs "build/dsm_top_flat.spice dsm_top" "dsm_top_sch.spice dsm_top" $PDK_ROOT/sky130A/libs.tech/netgen/sky130A_setup.tcl lvs.out > /dev/null 2>&1
grep -i -E "mismatch|property error|Circuits match|do not match|Final result" lvs.out | sort | uniq -c | head
# negative tests (ref/*.spice, made by make_neg.py): each must FAIL
for n in neg_phase_swap neg_dac_swap neg_cap_nodes neg_vcm_en; do
  netgen-lvs -batch lvs "build/dsm_top_flat.spice dsm_top" "ref/$n.spice dsm_top" $PDK_ROOT/sky130A/libs.tech/netgen/sky130A_setup.tcl lvs_$n.out > /dev/null 2>&1
  if grep -qi "do not match" lvs_$n.out; then echo "negative test $n detected"; else echo "negative test $n NOT detected"; fi
done
