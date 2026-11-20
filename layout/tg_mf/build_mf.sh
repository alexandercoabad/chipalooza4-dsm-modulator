#!/usr/bin/env bash
# Multifinger TG: generate, DRC (Magic drc(full)), extract, GDS.  usage: [NAME=.. WN=.. WP=.. NFN=.. NFP=.. GAP=..] build_mf.sh
# needs magic on PATH and PDK_ROOT (see ../../tools/setup_open_pdks.sh).  Only this cell's generated files are cleaned.
set -e; cd "$(dirname "$0")"; export PDK=sky130A; : ${PDK_ROOT:=$HOME/openeda/pdk/share/pdk}; export PDK_ROOT
export NAME=${NAME:-tg_x0p5_mf}
rm -f ${NAME}.mag ${NAME}.ext ${NAME}.gds ${NAME}_ext.spice ${NAME}_run.log sky130_fd_pr__*_*.mag sky130_fd_pr__*_*.ext
magic -dnull -noconsole -rcfile $PDK_ROOT/sky130A/libs.tech/magic/sky130A.magicrc make_tg_mf.tcl < /dev/null > ${NAME}_run.log 2>&1
grep -E "^(ORIGINS|built|DRC_|SIZE_UM|EXTRACTED)" ${NAME}_run.log
