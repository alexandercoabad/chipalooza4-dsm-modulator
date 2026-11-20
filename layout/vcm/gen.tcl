# vcm replica = the v2 core at 1/8 width (dsm1/sim/dsm1.py, k = 8): header PMOS 37.5/0.5, core PMOS 16/2 (5 x 3.2), core NMOS 4/2 (1 finger), footer NMOS 12.5/0.5 (g5v0d10v5), as multifinger PDK cells
proc mk {tag args} {
    cellname create top_$tag; load top_$tag; box 0 0 0 0
    eval magic::gencell sky130::$args
    save top_$tag
    set child [lindex [cellname list children top_$tag] 0]
    if {$child ne ""} { load $child; save $child }
    puts "PCELL $tag $child"
}
# warm-up: the first generator call in a fresh Magic has no box tool yet, so its device cell comes out empty
mk warm sky130_fd_pr__nfet_g5v0d10v5 inst_warm w 4.0 l 2.0 nf 1 guard 1
mk mp sky130_fd_pr__pfet_g5v0d10v5 inst_mp w 3.2 l 2.0 nf 5 conn_gates 1 guard 1
mk mn sky130_fd_pr__nfet_g5v0d10v5 inst_mn w 4.0 l 2.0 nf 1 conn_gates 1 guard 1
mk hp sky130_fd_pr__pfet_g5v0d10v5 inst_hp w 3.75 l 0.5 nf 10 conn_gates 1 guard 1
mk hn sky130_fd_pr__nfet_g5v0d10v5 inst_hn w 3.125 l 0.5 nf 4 conn_gates 1 guard 1
quit -noprompt
