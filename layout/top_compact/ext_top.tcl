gds read dsm_top.gds
load dsm_top
select top cell
extract unique
extract all
ext2spice lvs
ext2spice hierarchy off
ext2spice -o dsm_top_ext.spice dsm_top
quit -noprompt
