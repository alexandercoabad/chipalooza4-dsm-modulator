# Unit MIM capacitor from the PDK generator (cap_mim_m3_1: metal3 bottom plate, metal4 top plate), 22.2 x 22.2 um = 1.00 pF at the typical corner
proc mk {tag args} {
    cellname create top_$tag
    load top_$tag
    box 0 0 0 0
    eval magic::gencell sky130::sky130_fd_pr__cap_mim_m3_1 inst_$tag $args
    save top_$tag
    set child [lindex [cellname list children top_$tag] 0]
    if {$child ne ""} { load $child; save $child }
    puts "PCELL $tag $child"
}
# warm-up: the first generator call in a fresh Magic has no box tool yet and yields an empty cell
mk warm w 5.0 l 5.0
mk unit w 22.2 l 22.2
quit -noprompt
