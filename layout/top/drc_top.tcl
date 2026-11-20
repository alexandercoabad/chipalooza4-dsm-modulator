gds read dsm_top.gds
load dsm_top
select top cell
drc euclidean on
drc style drc(full)
drc check
drc catchup
puts "DRC_COUNT: [drc listall count]"
set why [drc listall why]
foreach {rule boxes} $why { puts "RULE: $rule  ([llength $boxes] boxes)" }
# error boxes (internal units, 1 unit = 5 nm) for the analysis scripts
set f [open drc_boxes.txt w]
foreach {rule boxes} $why { foreach b $boxes { puts $f "$rule | $b" } }
close $f
quit -noprompt
