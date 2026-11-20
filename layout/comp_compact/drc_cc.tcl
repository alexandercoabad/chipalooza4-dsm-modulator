load comp_compact
select top cell
drc euclidean on
drc style drc(full)
drc check
drc catchup
puts "DRC_COUNT: [drc listall count]"
set why [drc listall why]
foreach {rule boxes} $why { puts "RULE: $rule  ([llength $boxes] boxes)" }
quit -noprompt
