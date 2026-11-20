load cap_array
select top cell
extract no all
extract do capacitance
extract do coupling
extract all
ext2spice cthresh 0
ext2spice rthresh infinite
ext2spice -o cap_array_para.spice cap_array
quit -noprompt
