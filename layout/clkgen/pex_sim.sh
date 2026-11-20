#!/usr/bin/env bash
# Extract wiring capacitance (to substrate, plus coupling; no wire resistance) from clkgen.mag and run the clock-generator test bench on it.
# Same method as layout/comp_compact/pex_sim.sh.  Results append to ../../results/analog/clk_postlayout.jsonl.
# usage: pex_sim.sh   (run build.sh first; needs SKY130PR pointing at the PDK model clone)
set -e; cd "$(dirname "$0")"; : ${PDK_ROOT:=$HOME/openeda/pdk/share/pdk}; export PDK_ROOT
rm -rf pex; mkdir pex; cp clkgen.mag build/sky130_fd_pr__*.mag pex/; cp pex.tcl pex/
(cd pex && magic -dnull -noconsole -rcfile $PDK_ROOT/sky130A/libs.tech/magic/sky130A.magicrc pex.tcl < /dev/null > pex.log 2>&1)
cd ../../analog
for c in "tt 27" "ss 27" "ff 27"; do set -- $c
  python3 tb_clk_pex.py sch_ideal $1 $2; python3 tb_clk_pex.py sch_mim $1 $2; python3 tb_clk_pex.py pex $1 $2
done
