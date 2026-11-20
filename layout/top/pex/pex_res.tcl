gds read dsm_top.gds
load dsm_top
select top cell
flatten dsm_top_flat
load dsm_top_flat
select top cell
extract unique
extract do resistance
extract all
ext2sim labels on
ext2sim -o dsm_top_flat.sim dsm_top_flat
extresist tolerance 10
extresist all
quit -noprompt
