load clkgen
select top cell
extract no all
extract do local
extract do capacitance
extract do resistance
extract all
ext2spice lvs off
ext2spice cthresh 0
ext2spice rthresh infinite
ext2spice format ngspice
ext2spice -o clkgen_pex.spice clkgen
quit -noprompt
