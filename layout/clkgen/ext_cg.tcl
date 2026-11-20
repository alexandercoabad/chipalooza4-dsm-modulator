load clkgen
select top cell
extract no all
extract do local
extract all
ext2spice lvs
ext2spice -o clkgen_layout.spice clkgen
quit -noprompt
