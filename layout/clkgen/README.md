# clkgen/ : two-phase clock generator layout (Magic), 19 Nov 2026

Circuit = `analog/cells.py clockgen('g','clk')` with its default delay settings (as in `dsm1/`): 60 transistor fingers (`g5v0d10v5`, 3.3 V) and 10 delay capacitors.
`clkgen_sch.spice` is generated from `cells.py` by `gen_sch.py`, so connectivity and sizes cannot drift from the simulated circuit.

**One change from the simulated circuit:** the ideal delay capacitors (6 x 20 fF, 4 x 60 fF to ground) are real MIM capacitors (`cap_mim_m3_1`),
3.00 x 3.00 um (19.96 fF) and 5.32 x 5.32 um (60.10 fF) at TT (`cap_size.py`, PDK ngspice model). MIM capacitance moves with the process corner
(ll / hh: -17 % / +16 %), which the ideal capacitors did not; the corner effect on the dead times is **not yet simulated**.

| Check | Result |
|---|---|
| Magic DRC `drc(full)` | 0 errors |
| KLayout official `sky130A_mr.drc` (FEOL, BEOL, offgrid) | 0 items |
| Netgen LVS vs `clkgen_sch.spice` (`lvs.out`) | **match**: 27 nfet + 27 pfet + 10 MIM, 30 nets, pins `clk p1a p1ab p1 p1b p2 p2b cc vdda gnd` |
| Negative tests (`ref/`, `make_neg.py`), each must fail LVS | delay-chain gate on wrong node, capacitor on wrong node, 60 fF drawn as 20 fF, driver width 8 -> 4, NAND input wrong, NOR pfet on wrong rail: all detected |
| Size | about 226 x 46 um (about 10 400 um2); long because the six delay stages and ten capacitors are laid in rows |

Reproduce (about 20 s): `PATH=$HOME/openeda/magicinst/bin:$PATH PDK_ROOT=$HOME/openeda/pdk/share/pdk layout/clkgen/build.sh && layout/clkgen/drc.sh && layout/clkgen/lvs.sh`.
Files: `gen_cg.py` (specs from the schematic, placement), `autolay3.py` (engine of `comp_compact/autolay2.py` plus MIM cells), `build.sh`, `drc.sh`, `lvs.sh`, `clkgen.mag`, `clkgen.gds`, `clkgen_ext.spice`, `clkgen_layout.png`.

**Found while building.** The first routing left an undetected short between `p1a` and `gdc_d0` (both metal3, so Magic and KLayout DRC saw nothing); only LVS caught it. The router's
spacing pre-check had flagged it, and a different optimiser seed (`SEED=2`, now the default) removed it. DRC alone is not a sign-off for this generator.

**What this does not show.** Post-layout simulation is capacitance only (section below; no wire resistance, no coupling study), no matching or symmetry work,
guard rings are the PDK generator's defaults, no pin placement for top-level integration, no `make` target or CI step yet.
Also: a fresh `python3 tb_clk.py tt 27 3.3` with the current `cells.py` gives `cc_rise_after_p2_fall_ns` 30.11 and 49.64 uA, while `results/analog/clk_corners.jsonl` and `analog/README.md` record 12.83 ns and 48.88 uA
(the other timings agree exactly). The recorded `cc`/current numbers appear to come from an earlier version of the comparator-clock delay; which version the 56.9 dB SNDR run used is not established here.

## Post-layout simulation (19 Nov 2026, second session)

`pex_sim.sh` extracts wiring capacitance with Magic (`pex.tcl`: `extract do capacitance`, `ext2spice cthresh 0`, **`rthresh infinite`: no wire resistance**) and runs the edge-timing test bench of `analog/tb_clk.py` through `analog/tb_clk_pex.py` on three versions of the circuit:
`sch_ideal` (`cells.py`, ideal delay capacitors as in `dsm1/`), `sch_mim` (`clkgen_sch.spice`, real MIM capacitors, no wiring) and `pex` (the extracted layout). Same switch loads and 1.024 MHz clock as `tb_clk.py`. Results: `results/analog/clk_postlayout.jsonl`.
Extracted wiring capacitance: 386 fF in total, 13-25 fF on each delay-chain and phase node (the delay nodes carry 20 fF or 60 fF MIM capacitors on top), because the cell is 226 um wide.

All times in ns. `dt1` = p2 fall to p1a rise, `dt2` = p1 fall to p2 rise (both must stay > 0), `early` = p1a fall to p1 fall (> 0), `cc` = comparator clock rise after p2 fall.
Condition column: process corner / temperature / supply / MIM capacitor corner (`res_*__cap_*` file of the PDK models).

| Condition | schematic with MIM: dt1 / dt2 / early / cc | **extracted layout**: dt1 / dt2 / early / cc |
|---|---|---|
| tt / 27 C / 3.3 V / typical | 7.05 / 7.03 / 7.23 / 30.13 | 9.34 / 9.15 / 9.66 / 38.39 |
| ss / 125 C / 3.3 V / cap high | 10.60 / 10.57 / 10.92 / 47.53 | 13.87 / 13.60 / 14.40 / 59.62 |
| ss / 125 C / 3.3 V / cap low | 9.33 / 9.30 / 9.64 / 39.54 | 12.61 / 12.34 / 13.13 / 51.66 |
| ff / -40 C / 3.3 V / cap low | 4.62 / 4.60 / 4.74 / 19.29 | 6.36 / 6.22 / 6.57 / 25.15 |
| ff / -40 C / 3.3 V / cap high | 5.36 / 5.34 / 5.48 / 23.25 | 7.01 / 6.88 / 7.23 / 29.02 |
| ss / 125 C / 3.0 V / cap high | 12.13 / 12.11 / 12.48 / 54.57 | 15.92 / 15.62 / 16.51 / 68.58 |
| ff / -40 C / 3.6 V / cap low | 4.07 / 4.05 / 4.18 / 17.04 | 5.63 / 5.50 / 5.82 / 22.21 |

(`sch_ideal` at TT: 7.05 / 7.03 / 7.23 / 30.11, so the real MIM capacitors change nothing at TT.)

What this says: (1) every non-overlap and early-open margin stays positive in all seven conditions, the smallest being 5.5 ns (extracted, FF / -40 C / 3.6 V / cap low); (2) the wiring adds 30-38 % to every delay (TT dead time 7.05 -> 9.34 ns),
so the wiring capacitance is comparable to the 20 fF delay capacitors and is not negligible; (3) the MIM capacitor corner alone moves the delays by about 16 % at the same device corner (FF: 4.62 vs 5.36 ns); (4) the longest `cc` delay, 68.6 ns, is still far below the half period (488 ns) and the comparator's 2-4 ns decision delay.
**Not covered:** wire resistance, coupling between nets, mismatch, noise or jitter, the 4 other process-corner combinations, and the modulator loop with this netlist (the 56.9 dB SNDR run used the ideal-capacitor clock generator).
The extracted numbers should not be read as a prediction of silicon timing; they show the layout is not worse than the schematic by more than about a third in delay, and in the safe direction for non-overlap.
**The `cc` discrepancy flagged above is unchanged:** a fresh `tb_clk.py tt 27 3.3` in this session again gave `cc_rise_after_p2_fall_ns` 30.11 and 49.64 uA (recorded earlier: 12.83 ns and 48.88 uA); the other timings match the recorded ones.
