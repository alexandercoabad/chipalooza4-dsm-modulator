#!/usr/bin/env bash
# Build, DRC (Magic drc(full) + official KLayout deck), LVS and fault-injection tests for every TG size.  About 1 minute.
# usage: PATH=$HOME/openeda/magicinst/bin:$PATH PDK_ROOT=$HOME/openeda/pdk/share/pdk ./check_mf.sh      Exit code 0 only if everything is as expected.
cd "$(dirname "$0")"; : ${PDK_ROOT:=$HOME/openeda/pdk/share/pdk}; export PDK_ROOT; rc=0
mkdir -p ref
klayout_items() { klayout -b -r $PDK_ROOT/sky130A/libs.tech/klayout/drc/sky130A_mr.drc -rd input=$1.gds -rd topcell=$1 -rd report=klayout_$1.lyrdb -rd feol=true -rd beol=true -rd offgrid=true -rd thr=2 >/dev/null 2>&1; grep -c '<item>' klayout_$1.lyrdb; }
expect_fail() { "$@" >/dev/null 2>&1 && { echo "  NOT DETECTED: $*"; rc=1; } || echo "  detected (LVS fails as it must): $LABEL"; }
# name  WN NFN WP NFP
for spec in "tg_x0p5_mf 4 1 12 3" "tg_x0p25_mf 2 1 6 3"; do
  set -- $spec; N=$1
  echo "=== $N: nfet $2/0.5 as $3 finger(s), pfet $4/0.5 as $5 fingers"
  export NAME=$N WN=$2 NFN=$3 WP=$4 NFP=$5
  ./build_mf.sh | grep -E "DRC_RULES|SIZE" | sed 's/^/  Magic /'
  k=$(klayout_items $N); echo "  KLayout official deck items: $k"
  [ "$(grep -c '^DRC_RULES_VIOLATED: 0' ${N}_run.log)" = 1 ] && [ "$k" = 0 ] || { echo "  DRC NOT CLEAN"; rc=1; }
  ./lvs_mf.sh || rc=1
  # fault injection: each of these must make LVS fail
  sed '/XMN/ s/ en / enb /; /XMP/ s/ enb / en /' ${N}_sch.spice > ref/${N}_neg_swap_gates.spice
  sed '/pfet/ s/w=[0-9.]*/w=10/' ${N}_sch.spice > ref/${N}_neg_pfet_w10.spice
  sed '/nfet/ s/w=[0-9.]*/w=1.5/' ${N}_sch.spice > ref/${N}_neg_nfet_w1p5.spice
  for t in swap_gates pfet_w10 nfet_w1p5; do LABEL="schematic $t"; SCH=ref/${N}_neg_$t.spice OUT=ref/${N}_lvs_neg_$t.out expect_fail ./lvs_mf.sh; done
  DEFECT=openstrip NAME=${N}_defect ./build_mf.sh >/dev/null; kd=$(klayout_items ${N}_defect)
  mc=$([ "$(grep -c '^DRC_RULES_VIOLATED: 0' ${N}_defect_run.log)" = 1 ] && echo clean || echo "NOT clean"); LABEL="layout with one S/D strip unwired (it is DRC-clean: Magic $mc, KLayout items $kd)"
  NAME=${N}_defect SCH=${N}_sch.spice SCHCELL=$N OUT=ref/${N}_lvs_neg_openstrip.out expect_fail ./lvs_mf.sh
  rm -f ${N}_defect* klayout_${N}_defect.lyrdb
done
[ $rc = 0 ] && echo "ALL CHECKS AS EXPECTED" || echo "SOMETHING FAILED"; exit $rc
