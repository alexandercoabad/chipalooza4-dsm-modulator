#!/usr/bin/env bash
# How close can the pfet cell be to the nfet cell?  Rebuilds tg_x0p5_mf for several gaps and runs both DRC tools on each.  -> gap_sweep.txt
cd "$(dirname "$0")"; : ${PDK_ROOT:=$HOME/openeda/pdk/share/pdk}; export PDK_ROOT; mkdir -p /tmp/gs; out=gap_sweep.txt
echo "TG scale 0.5, nfet 4/0.5 x1 finger, pfet 12/0.5 x3 fingers; GAP = clear distance between the nfet and pfet cell outlines (um)" > $out
for g in 0.0 0.2 0.4 0.6 0.8 1.0 1.2; do
  n=tg_gap_${g/./p}; NAME=$n GAP=$g ./build_mf.sh > /tmp/gs/$n.txt 2>&1
  mg=$(grep DRC_RULES /tmp/gs/$n.txt | awk '{print $2}'); sz=$(grep SIZE /tmp/gs/$n.txt | sed 's/SIZE_UM: //')
  klayout -b -r $PDK_ROOT/sky130A/libs.tech/klayout/drc/sky130A_mr.drc -rd input=$n.gds -rd topcell=$n -rd report=/tmp/gs/k_$n.lyrdb -rd feol=true -rd beol=true -rd offgrid=true -rd thr=2 >/dev/null 2>&1
  k=$(grep -c '<item>' /tmp/gs/k_$n.lyrdb)
  rules=$(grep -o '{[A-Za-z][^}]*(diff/tap[^}]*)}' ${n}_run.log | sed 's/^{//; s/}$//' | sort -u | tr '\n' ';' | cut -c1-200)
  printf "gap %s um | size %s | Magic drc(full) rules violated: %s | KLayout official deck items: %s | %s\n" $g "$sz" "$mg" "$k" "$rules" | tee -a $out
  rm -f $n.* ${n}_* sky130_fd_pr__*_*.mag sky130_fd_pr__*_*.ext
done
