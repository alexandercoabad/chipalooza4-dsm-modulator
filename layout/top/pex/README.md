# dsm_top parasitic extraction (Magic, 20 Nov 2026)

Layout: `../dsm_top.gds`. Tool: Magic 8.3.704, flat extraction, `extract do capacitance/coupling`, no thresholds.

| File | Content |
|---|---|
| `pex_top.tcl` -> `dsm_top_pex.spice` | raw extraction: 113 devices, 571 capacitors, 1956 fF |
| `ca/cap_array_pex.spice` | `cap_array` extracted alone, to measure the extractor's plate-overlap capacitance |
| `make_pex_netlist.py` -> `dsm_top_pex_sim.spice`, `dsm_top_nopar_sim.spice` | corrected netlist (1657 fF) and control (devices only); subckt `dsm_top_pex` with the TOP_PORTS |
| `dsm_top_pex_pruned.spice` | 328 couplings < 1 fF (86 fF) lumped to ground; 208 couplings + 55 lumps |
| `net_caps.py`, `net_caps_corrected.json` | per-net C table (21 nets, all mapped to extracted nodes) |
| `pex_res.tcl`, `net_res.py`, `net_res.json` | `extresist` (10 ohm tolerance): worst terminal-to-terminal wire resistance |
| `../tb_top_loop.py`, `../loop_*.json` | closed-loop DC test (below) |

## Per-net capacitance, overlap removed (fF; total / to gnd)
out 151/58, g 110/24, p1a 78/17, p1 69/13, vcm 69/19, p2 55/11, cc 54/9, qb 53/15, p1b 51/9, q 50/8, b 45/27, p1ab 42/9, p2b 39/6, clk 28/6, t 21/6, dac 17/3, vrn 17/9, vrp 10/1, vin 10/2. Strongest couplings: g-out 21.7, out-vcm 15.8, out-qb 13.6, g-vcm 10.4. vdda-gnd 346 fF (supply decoupling).
The "total" includes capacitance to unnamed internal block nodes (g 43 fF, out 19 fF).

## Corrections made, and why
- Magic reports m3/m4 plate overlap inside `cap_array` (g-out 192.8 fF, t-b 96.8 fF, plus about 10 fF between the other plate pairs) **on top of** the `cap_mim_m3_1` devices, whose model already contains the plate capacitance. 299 fF removed pair by pair, measured on the standalone array. Raw numbers (g-out 214, t-b 97) are in `net_caps.json`.
- Plate-to-substrate capacitance (b 26.5 fF, out 57.9 fF) is kept; whether the PDK model for `cap_mim_m3_1` already includes a bottom-plate parasitic was not checked, so b and out may be slightly double-counted.

## Closed-loop check (`tb_top_loop.py`; vref 0.8 V, 1.024 MHz, 16 counted bits per level after 16 start-up cycles)
Bit density at vin = vcm + 0 / +0.3 / -0.4 V; ideal 0.500 / 0.688 / 0.250.

| Netlist | Corner | Density | out swing |
|---|---|---|---|
| devices only (control, 32 bits/level) | tt 27 C 3.3 V | 0.500 / 0.688 / 0.250 | 0.96-2.07 V |
| extracted, pruned | tt 27 C 3.3 V | 0.500 / 0.688 / 0.250 | 1.07-2.12 V |
| extracted, unpruned | tt 27 C 3.3 V | 0.500 / 0.688 / 0.250 | 1.00-2.11 V |
| extracted, pruned | ss 125 C 3.0 V | 0.500 / 0.688 / 0.250 | 0.84-1.98 V (vcm 1.512 V) |
| extracted, pruned | ff -40 C 3.6 V | 0.500 / 0.688 / 0.250 | 1.08-2.26 V (vcm 1.767 V) |

## Not covered
- Wire resistance is not in the simulated netlists. `extresist` covered 33 of 55 nets (not vin, vrp, t, b, the clock phases); worst paths found: out 756 ohm, g 386 ohm, q 853 ohm, vdda 6.1 kohm, so RC is well below 1 ns against a 488 ns half period; order of magnitude only (paths may run through diffusion/contact stubs).
- Only 16 bits per level at three DC inputs, so a density shift below about 0.06 would not show, and this is not an SNDR measurement. 
- Corners: tt, ss/125C/3.0 V, ff/-40C/3.6 V only; no sf/fs, no supply variation separately.
- `dsm_top_sch.spice` cannot be simulated in this ngspice (the OTA header is one 300 um device outside the model bins), so the control is the extracted layout devices, not the schematic. The `dsm1` schematic-level model gives the same densities.
- Magic extraction has no vertical/lateral fringe field solver accuracy claim; it is not a signoff RC extraction (no foundry PEX deck).
- Running two ngspice jobs at once on this 2-core machine made each 10x slower or not finish; the results above were run one at a time.

## Sine-input SNDR (20 Nov, `../tb_top_sndr.py`, `../results/`)
Extracted pruned netlist (wiring C, no wire R), tt/27 C/3.3 V, vin = vcm + 0.4 V sine at 1.75 kHz (bin 7 of 4096, coherent), vref 0.8 V, 1.024 MHz, Hann window, band 0..4 kHz (16 bins), 4096 samples after 64 start-up cycles: **SNDR 59.3 dB**, mean bit density 0.5005. For reference, a behavioural ideal first-order loop analysed the same way gives 52.6 dB, and the earlier `dsm1` run 56.9 dB; with only 16 in-band bins and one run, differences of several dB are within the spread of the estimate, so the result shows no degradation from the layout capacitance, not a measured improvement. One corner, no mismatch, no noise sources, no wire R, ideal 10 Gohm leak in place of the pseudo-resistor.
