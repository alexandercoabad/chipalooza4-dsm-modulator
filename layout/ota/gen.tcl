proc mk {tag fet args} {
    cellname create top_$tag
    load top_$tag
    eval magic::gencell sky130::$fet inst_$tag $args
    save top_$tag
    set child [lindex [cellname list children top_$tag] 0]
    if {$child eq ""} { select top cell; set child [lindex [cellname list children top_$tag] 0] }
    load $child
    save $child
    puts "PCELL $tag $child"
}
# warm-up: the first generator call in a fresh Magic has no box tool yet, so its device cell comes out empty
mk warm sky130_fd_pr__nfet_g5v0d10v5 w 4.0 l 2.0 nf 1 guard 1
mk mp sky130_fd_pr__pfet_g5v0d10v5 w 4.0 l 2.0 nf 32 conn_gates 1 guard 1
mk mn sky130_fd_pr__nfet_g5v0d10v5 w 4.0 l 2.0 nf 8 conn_gates 1 guard 1
mk hp sky130_fd_pr__pfet_g5v0d10v5 w 5.0 l 0.5 nf 60 conn_gates 1 guard 1
mk hn sky130_fd_pr__nfet_g5v0d10v5 w 5.0 l 0.5 nf 20 conn_gates 1 guard 1
quit -noprompt
