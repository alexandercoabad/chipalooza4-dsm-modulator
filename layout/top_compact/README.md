# dsm_top, compact floorplan (wip22, 20 Nov 2026)

Same blocks and netlist as `../top/` (wip21); only `topdef.py` changed (floorplan and the q/qb pad positions), then `top_route.py` re-run.
Bounding box 360.5 x 142.2 um = 51,256 um2, against 390.3 x 157.6 um = 61,496 um2 in `../top/` (-17 %).

| Change (um) | wip21 | compact |
|---|---|---|
| cap_array to ota_core gap | 22 | about 10 |
| ota_core to comp_compact gap | 33 | about 15 |
| clkgen origin | (30.10, 120.05) | (29.75, 104.65), vertical channel to the blocks below about 14 um |
| q / qb pads, x | 392.00 | 362.25 |

Checks (this directory, `drc.sh`, `lvs.sh`): router failures none; Magic DRC 0 errors; KLayout official deck 0 items; Netgen LVS matches uniquely; the four negative tests are detected.
The first two clkgen offsets tried (30.10, 103.95 and 30.10, 104.30) left one met4.2 spacing error (0.27 um) between a routed wire and an internal clkgen met4 stub; 29.75, 104.65 is clean.

**Not redone for this floorplan:** parasitic extraction, closed-loop test and SNDR (`../top/pex/` is for the wip21 floorplan), and `../adc_top/` still uses `../top/dsm_top.gds`. Wire lengths changed, so numbers must be re-run before quoting them for this version.
Reproduce: `cd layout/top_compact && python3 gen_top_sch.py && klayout -b -r top_route.py && ./drc.sh && ./lvs.sh` (same environment as `../top/`).
