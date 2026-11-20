#!/usr/bin/env bash
# Extract wiring capacitance (to substrate; no wire resistance) from comp_compact.mag and run the comparator test bench on the extracted netlist.
# Also runs the schematic with and without the 50 fF placeholder loads for reference. Results append to ../../results/analog/comp_postlayout.jsonl.
# usage: pex_sim.sh   (run build.sh first; needs SKY130PR pointing at the PDK model clone)
set -e; cd "$(dirname "$0")"; : ${PDK_ROOT:=$HOME/openeda/pdk/share/pdk}; export PDK_ROOT
rm -rf pex; mkdir pex; cp comp_compact.mag build/sky130_fd_pr__*.mag pex/; cp pex.tcl pex/
(cd pex && magic -dnull -noconsole -rcfile $PDK_ROOT/sky130A/libs.tech/magic/sky130A.magicrc pex.tcl < /dev/null > pex.log 2>&1)
cd ../../analog
python3 tb_comp_pex.py schematic_50fF sch50; python3 tb_comp_pex.py schematic_0fF sch0
python3 tb_comp_pex.py compact_layout_cap pex ../layout/comp_compact/pex/comp_compact_pex.spice comp_compact
