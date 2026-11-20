# Chipalooza Challenge #4: one-bit first-order switched-capacitor delta-sigma modulator (Sky130)

A 3.3 V, single-ended, first-order, one-bit switched-capacitor delta-sigma modulator: sampling capacitor Cs 2 pF, integrator capacitor Ci 4 pF,
self-biased inverter amplifier (thick-oxide `g5v0d10v5`), StrongARM comparator with NOR SR latch, six transmission-gate switches, a vcm replica and its own
two-phase clock generator. 1.024 MHz clock, oversampling ratio 128, 4 kHz band. The proposal is in `docs/`.
Status: proposal stage. All results are schematic or extracted-capacitance simulation at the typical corner unless stated; there is no silicon.
This repository holds only the modulator; the decimator, level shifter and full-ADC work are in a separate project.

## Layout of this repository

| Path | Contents |
|---|---|
| `dsm1/` | System-level modulator simulations (`dsm1/sim/`), results and plots (`dsm1/results/`), and `dsm1/README.md` with the method, numbers and limitations |
| `analog/` | Comparator and clock-generator test benches (schematic and post-layout), cell generators, pseudo-resistor notes |
| `layout/` | Block layouts with build, DRC (Magic and KLayout) and LVS (Netgen) scripts: `tg_mf`, `ota`, `mim`, `comp_compact`, `clkgen`, `vcm`; `top/` is `dsm_top` with extraction (`top/pex/`); `top_compact/` is a 17 % smaller floorplan of the same blocks. `layout/README.md` has the per-block log |
| `v2/sim/` | Device and netlist helpers (`v2.py`, `simlib.py`, `mylib.py`) shared with the inverter-amplifier repository; the modulator scripts import them |
| `results/analog/` | Comparator and clock-generator corner results (JSON lines) |
| `docs/` | Chipalooza #4 proposal for this block (Word and PDF), the test equipment list (sent separately, rule 6) and the block diagram. The proposal quotes the `layout/top/` floorplan (390 x 158 um, 0.061 mm2) |

## Requirements

- ngspice 42 (tested), Python 3 with `numpy`, `scipy` and `matplotlib` (`pip install -r requirements.txt`)
- Sky130 device models: `make pdk` clones `skywater-pdk-libs-sky130_fd_pr` at a pinned commit; `SKY130PR` points to it; `SIMTMP` is an optional scratch directory
- Layout targets: Magic 8.3.x, KLayout, Netgen and the Sky130A PDK (`tools/setup_open_pdks.sh` installs Magic and the PDK under `~/openeda`)
- Run each script from its own directory: each directory has a `.spiceinit` that ngspice picks up from the working directory
- Multi-job ngspice runs on a 2-core machine thrash; run the simulations one at a time

## Quick start

```
make reproduce                 # pdk + smoke test (about 25.5 dB) + ideal-model reference (57.3 / 55.2 dB)
make stepcheck                 # per-step accuracy of the modulator, about 4 minutes
make analog-corners            # comparator and clock generator, 5 corners
make layout-top                # dsm_top: route, DRC, LVS with fault injection (needs the layout tools)
```

## Results so far (TT, 27 C, 3.3 V unless stated)

| Item | Value | Where |
|---|---|---|
| SNDR, -6 dBFS, 4 kHz band, real comparator and clock generator, half-size switches | 56.9 dB (SFDR 61.0 dB), one run | `dsm1/README.md` |
| SNDR, extracted layout capacitance | 59.3 dB, one run, no wire resistance | `layout/top/pex/README.md` |
| Ideal first-order reference, same method | 55.2 dB (57.3 dB at N = 8192) | `make ideal` |
| DC transfer | gain error -0.66 %, offset +0.97 LSB10, INL within a +-1.1 LSB10 measurement floor | `dsm1/results/` |
| `dsm_top` layout, extracted floorplan | 390 x 158 um; Magic DRC 0, KLayout 0, LVS match, 4 fault injections detected | `layout/top/` |
| `dsm_top` layout, compact floorplan | 360.5 x 142.2 um (0.051 mm2); DRC 0, LVS match, 4 fault injections detected | `layout/top_compact/` |

## Limitations

- No noise, mismatch or jitter simulation. Reference voltages, input and clock are ideal sources, and the 10 GOhm bias resistor is ideal and not laid out.
- SNDR numbers are single runs at the typical corner and vary by a few dB with input amplitude and frequency.
- Parasitic extraction, the closed-loop check and the SNDR runs were done on the `layout/top/` floorplan. They have not been repeated on `layout/top_compact/`.
- The extracted-netlist runs include wiring capacitance but no wire resistance. Magic extraction double-counts the MIM plate overlap; the scripts subtract it.
- Details, and the remaining open items, are in `dsm1/README.md`, `layout/README.md` and the proposal.

## Use of AI

AI tools assisted drafting and scripting. Every result is reproducible with the scripts in this repository, and no AI is needed to use, verify or modify the block.

## License

Apache License 2.0 (`LICENSE`).
