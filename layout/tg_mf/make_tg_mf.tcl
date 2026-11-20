# Multifinger transmission gate (sky130 g5v0d10v5): scripted layout, DRC, extraction.  Run via build_mf.sh.
# Parameters come from the environment (defaults = TG scale 0.5 of the modulator: nfet 4/0.5 as 1 finger, pfet 12/0.5 as 3 fingers of 4):
#   NAME  cell name                 WN, WP  total widths (um)          NFN, NFP  number of fingers (width per finger = W/NF)
#   L     gate length (um)          GAP     clear distance between the nfet and pfet cell outlines (um)
# Device cells come from the PDK's Magic generators (guard ring, gates strapped with conn_gates 1).  The generator leaves the
# source/drain strips of a multifinger device as separate nets (it extracts as NF devices in a chain), so this script ties them:
# strips alternate a, b, a, b ... on both devices; every "a" strip gets a metal2 via at height ya and every "b" strip one at yb,
# and two metal2 bars join them.  A transmission gate is symmetric in a/b, so the assignment of the nets to the strips is free.
proc env_or {n d} { global env; if {[info exists env($n)]} { return $env($n) } else { return $d } }
set NAME [env_or NAME tg_x0p5_mf]
set WN [env_or WN 4.0]; set WP [env_or WP 12.0]; set NFN [env_or NFN 1]; set NFP [env_or NFP 3]
set L [env_or L 0.5]; set GAP [env_or GAP 1.0]
set DEFECT [env_or DEFECT none]   ;# test hook only: openstrip = leave one pfet 'a' strip unwired (LVS must fail)
set wfn [expr {$WN/double($NFN)}]; set wfp [expr {$WP/double($NFP)}]
set PITCH 0.79        ;# finger pitch at L = 0.5 um (poly 0.5 + contacted S/D 0.29); strips are centred on the cell, verified in the GDS
proc rect {x1 y1 x2 y2} { box [format %.3fum $x1] [format %.3fum $y1] [format %.3fum $x2] [format %.3fum $y2] }
proc bbox_um {inst} { select cell $inst; set v [box values]
  return [list [expr {[lindex $v 0]*0.005}] [expr {[lindex $v 1]*0.005}] [expr {[lindex $v 2]*0.005}] [expr {[lindex $v 3]*0.005}]] }

load $NAME -quiet
rect 0 0 0 0
magic::gencell sky130::sky130_fd_pr__nfet_g5v0d10v5 mn w $wfn l $L nf $NFN guard 1 conn_gates 1
lassign [bbox_um mn] nx1 ny1 nx2 ny2
set hxn [expr {($nx2-$nx1)/2.0}]; set hyn [expr {($ny2-$ny1)/2.0}]
set xn [expr {($nx1+$nx2)/2.0}]; set yn [expr {($ny1+$ny2)/2.0}]
# pfet: lower-left corner placed so that the outlines are GAP apart and the diffusion centres are at the same height
# (hyp is only known after generation: generate once at the corner, measure, then move the instance)
rect [expr {$nx2+$GAP}] $ny1 [expr {$nx2+$GAP}] $ny1
magic::gencell sky130::sky130_fd_pr__pfet_g5v0d10v5 mp w $wfp l $L nf $NFP guard 1 conn_gates 1
lassign [bbox_um mp] px1 py1 px2 py2
set hxp [expr {($px2-$px1)/2.0}]; set hyp [expr {($py2-$py1)/2.0}]
set xp [expr {($px1+$px2)/2.0}]; set yp [expr {($py1+$py2)/2.0}]
set dy [expr {$yn-$yp}]
if {$dy > 0.001} { select cell mp; move north [format %.3fum $dy]; set yp $yn } elseif {$dy < -0.001} { select cell mp; move south [format %.3fum [expr {-$dy}]]; set yp $yn }
puts [format "ORIGINS nfet (%.3f,%.3f) half-size (%.3f,%.3f) | pfet (%.3f,%.3f) half-size (%.3f,%.3f)" $xn $yn $hxn $hyn $xp $yp $hxp $hyp]

# ---- source/drain strips: x of strip i = centre + (i - NF/2)*PITCH; strip i even -> net a, odd -> net b
proc strip_x {xc nf i} { global PITCH; return [expr {$xc + ($i - $nf/2.0)*$PITCH}] }
set wmin [expr {min($wfn,$wfp)}]
set dyv [expr {min(1.2, $wmin/2.0 - 0.5)}]
set ya [expr {$yn+$dyv}]; set yb [expr {$yn-$dyv}]
proc via {x y} { rect [expr {$x-0.25}] [expr {$y-0.25}] [expr {$x+0.25}] [expr {$y+0.25}]; paint metal1
                 rect [expr {$x-0.13}] [expr {$y-0.13}] [expr {$x+0.13}] [expr {$y+0.13}]; paint m2contact }
set ax {}; set bx {}
foreach {xc nf} [list $xn $NFN $xp $NFP] {
  for {set i 0} {$i <= $nf} {incr i} {
    set x [strip_x $xc $nf $i]
    if {$DEFECT eq "openstrip" && $xc == $xp && $i == 2} { continue }
    if {$i % 2 == 0} { via $x $ya; lappend ax $x } else { via $x $yb; lappend bx $x }
  }
}
set ax [lsort -real $ax]; set bx [lsort -real $bx]
rect [expr {[lindex $ax 0]-0.25}] [expr {$ya-0.25}] [expr {[lindex $ax end]+0.25}] [expr {$ya+0.25}]; paint metal2
rect [expr {[lindex $bx 0]-0.25}] [expr {$yb-0.25}] [expr {[lindex $bx end]+0.25}] [expr {$yb+0.25}]; paint metal2

# ---- small patches so that the labels sit on real layers of this cell (they overlap the child cells' paint)
set gyn [expr {$yn+$wfn/2.0+0.32}]; set gyp [expr {$yp+$wfp/2.0+0.32}]      ;# centre of the top gate bar (metal1)
rect [expr {$xn-0.1}] [expr {$gyn-0.115}] [expr {$xn+0.1}] [expr {$gyn+0.115}]; paint metal1
rect [expr {$xp-0.1}] [expr {$gyp-0.115}] [expr {$xp+0.1}] [expr {$gyp+0.115}]; paint metal1
# right side of the guard rings (li1 centre line): 0.325 um inside the nfet cell outline, 0.475 um inside the pfet outline (nwell overhang)
set rn [expr {$xn+$hxn-0.325}]; set rp [expr {$xp+$hxp-0.475}]
rect [expr {$rn-0.075}] [expr {$yn-0.2}] [expr {$rn+0.075}] [expr {$yn+0.2}]; paint locali      ;# p+ ring (vss)
rect [expr {$rp-0.075}] [expr {$yp-0.2}] [expr {$rp+0.075}] [expr {$yp+0.2}]; paint locali      ;# n+ ring in the nwell (vdd)
proc pin {name x y layer} { rect $x $y $x $y; label $name c $layer }
pin a   [lindex $ax 0] $ya metal2
pin b   [lindex $bx end] $yb metal2
pin en  $xn $gyn metal1
pin enb $xp $gyp metal1
pin vss $rn $yn locali
pin vdd $rp $yp locali
foreach n {a b en enb vss vdd} { findlabel $n; port make }
puts "built"
save $NAME
drc euclidean on
drc style drc(full)
select top cell
drc check
drc catchup
puts "DRC_RULES_VIOLATED: [expr {[llength [drc listall why]]/2}]"      ;# drc listall why = {rule rects rule rects ...}
puts "DRC_COUNT: [drc listall count]"
puts [drc listall why]
select top cell
set v [box values]
puts [format "SIZE_UM: %.3f x %.3f" [expr {([lindex $v 2]-[lindex $v 0])*0.005}] [expr {([lindex $v 3]-[lindex $v 1])*0.005}]]
extract all
ext2spice lvs
ext2spice cthresh infinite
ext2spice rthresh infinite
ext2spice -o ${NAME}_ext.spice
gds write ${NAME}.gds
puts "EXTRACTED"
quit -noprompt
