gds read dsm_top.gds
load dsm_top
select top cell
extract unique
extract do capacitance
extract do coupling
extract all
ext2spice lvs off
ext2spice hierarchy off
ext2spice cthresh 0
ext2spice rthresh infinite
ext2spice format ngspice
ext2spice -o dsm_top_pex.spice dsm_top
quit -noprompt
