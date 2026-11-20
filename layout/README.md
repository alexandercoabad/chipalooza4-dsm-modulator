# Layout

Sky130A layouts of the blocks of the modulator `dsm_top`. Each block directory has its own build, DRC (Magic and KLayout) and LVS scripts; `top/` is the floorplan with extraction results, `top_compact/` a 17 % smaller floorplan of the same blocks (see its README).
The sections below are copied from the project log and may mention `comp/`, `tg/` and `adc_top/`, which belong to the full-ADC project and are not in this repository.

## tg_mf/ : multifinger transmission gate, TG scale 0.5 (and 0.25), `tg_x0p5_mf`, `tg_x0p25_mf`

Same electrical TG as `tg/` (same sizes as `common/amp_core.py tg()`; schematic nfet 4/0.5 and pfet 12/0.5, nf=1 as simulated), drawn as **nfet 1 finger, pfet 3 fingers of 4 um**.
`make_tg_mf.tcl` (parameters in environment variables, `build_mf.sh` runs it) takes the PDK's multifinger cells (guard rings, gates strapped with
`conn_gates 1`), and ties the source/drain strips, which the generator leaves as separate nets: strips alternate a, b, a, b on both devices, metal2 bars join all
"a" strips and all "b" strips. Scale 0.25 (nfet 2/0.5, pfet 6/0.5 as 3 x 2 um) is the size of the sampling switches in the earlier SNDR runs. It lives in its own folder because the
generated PDK cells of both flows are cleaned by their build scripts. One command, about 1 minute: `make layout-tg-mf` (or `layout/tg_mf/check_mf.sh`; output in `tg_mf/check_mf.txt`).

| Check | x0.5 (`tg_x0p5_mf`) | x0.25 (`tg_x0p25_mf`) |
|---|---|---|
| Size from Magic (single-finger `tg/` x0.5: 133.9 um2) | 7.985 x 6.970 um = **55.7 um2** (58 % smaller) | 7.985 x 4.970 um = 39.7 um2 |
| Magic DRC `drc(full)` | 0 rules violated | 0 rules violated |
| KLayout official `sky130A_mr.drc` (FEOL, BEOL, offgrid) | 0 items | 0 items |
| Netgen LVS vs schematic (`*_lvs.out`; verdict from `lvs_mf.sh`) | match (Netgen merges the 3 fingers: 2 devices, 6 nets) | match |
| Fault injection, each must make LVS fail (`ref/`) | en/enb swapped: detected; pfet w=10: detected; nfet w=1.5: detected; one S/D strip left unwired: detected | same four detected |

`lvs_mf.sh` returns an explicit PASS/FAIL because Netgen prints "Circuits match uniquely" and "Cell pin lists are equivalent" even when the pin table shows **Mismatch**
or when device properties differ (property errors); the verdict looks for those. The unwired-strip layout is **DRC-clean in both tools** (0 items): only LVS catches it,
so DRC alone would not have.

**Spacing between the nfet and pfet cells (`gap_sweep.sh`, `gap_sweep.txt`).** The chosen gap is 1.0 um; the layout is clean in Magic from 0.8 um up:

| gap (um) | size (um) | Magic rules violated | KLayout items |
|---|---|---|---|
| 0.0 | 6.985 x 6.970 | 6 | 33 |
| 0.2 | 7.185 x 6.970 | 4 | 2 |
| 0.4 | 7.385 x 6.970 | 3 | 0 |
| 0.6 | 7.585 x 6.970 | 2 | 0 |
| 0.8 | 7.785 x 6.970 | 0 | 0 |
| 1.0 | 7.985 x 6.970 | 0 | 0 |
| 1.2 | 8.185 x 6.970 | 0 | 0 |

At 0.4 and 0.6 um Magic reports the medium-voltage well rules (N-diffusion or P-tap to MV nwell < 0.43 um, MV diffusion in nwell to P-tap < 0.76 um) while the official KLayout deck
reports nothing. **A clean KLayout run is therefore not sufficient for this kind of spacing; Magic `drc(full)` is the stricter check here.** (We have not determined whether the KLayout deck omits these rules or measures them differently.)

**Electrical check against the schematic (`ron_check.py`, `ron_check.txt`; `make tg-mf-ron`).** Ron = 10 mV / I over a 0.2-3.1 V common mode, one ngspice run per netlist; the extracted netlist has no parasitic R/C:

```
tg_x0p5_mf tt: Ron schematic 537..1147 ohm over 0.2..3.1 V | extracted layout vs schematic: max diff 3.19 % | nf=3 form vs schematic: max diff 5.41 %
tg_x0p5_mf ss: Ron schematic 610..1676 ohm over 0.2..3.1 V | extracted layout vs schematic: max diff 2.45 % | nf=3 form vs schematic: max diff 6.53 %
tg_x0p5_mf ff: Ron schematic 478..847 ohm over 0.2..3.1 V | extracted layout vs schematic: max diff 5.05 % | nf=3 form vs schematic: max diff 12.75 %
tg_x0p25_mf tt: Ron schematic 1094..2332 ohm over 0.2..3.1 V | extracted layout vs schematic: max diff 5.17 % | nf=3 form vs schematic: max diff n/a (ngspice aborts)
tg_x0p25_mf ss: Ron schematic 1272..3392 ohm over 0.2..3.1 V | extracted layout vs schematic: max diff 6.02 % | nf=3 form vs schematic: max diff n/a (ngspice aborts)
tg_x0p25_mf ff: Ron schematic 956..1752 ohm over 0.2..3.1 V | extracted layout vs schematic: max diff 4.56 % | nf=3 form vs schematic: max diff n/a (ngspice aborts)
```

LVS equality does not mean SPICE equality: the extracted layout (three 4 um devices) and the schematic (one 12 um device) pick different BSIM bins of the PDK models, so Ron differs by
2.5-6 % over this range. That is a model-binning difference, not a layout parasitic. The `nf=3` form is a third way to write the same pfet and differs more (up to 12.8 % at FF for x0.5).
**Simulator quirk found on the way:** with ngspice 42 and these models, a `pfet_g5v0d10v5` with nf > 1 and 2 um fingers (`w=6 nf=3`, `w=4 nf=2`) aborts a DC sweep, while nf=1 devices
(which is what the extracted netlist contains), 4 um fingers (`w=12 nf=3`) and nfets with 2 um fingers work (TT only; not scanned further). In the sky130 wrapper `w` is the total width and `nf` splits it,
so `w=4 nf=3` is a 4 um device, not three 4 um fingers. The extracted netlist's port order is `a b en enb vss vdd`, the schematic's is `a b en enb vdd vss`; instantiate by the right order.

**What this does not show.** No parasitic extraction (cthresh/rthresh are infinite, so metal2 bar resistance and wiring capacitance are not in any number above), no post-layout simulation of the modulator with these cells, no matching or symmetry analysis
(the TG is one of six switches; charge-injection symmetry between a and b was not examined), each device keeps its own guard ring and the 1.0 um gap is 0.2 um above the clean minimum, so the cell can still be made smaller (shared well or tap, gap 0.8 um).
Only the two sizes above are built and checked; other sizes are possible through the environment variables (`WN WP NFN NFP GAP`) but untested. `render_mf.py` draws the pictures (`tg_x0p5_mf_layout.png`, `tg_x0p25_mf_layout.png`).

## ota/ : inverter OTA core (amplifier core, resized), `ota_core`

Same devices and sizes as `common/amp_core.py`: header PMOS 300/0.5, core PMOS 128/2, core NMOS 32/2, footer NMOS 100/0.5 (`g5v0d10v5`), each split into fingers
from the PDK generators (guard rings on), stacked hp / mp / mn / hn and wired with metal2 bars over the source/drain strips. Pins `vdda gnd g out en enb`.
The core only: the integrator capacitors (`mim/`), the vcm replica (`vcm/`) and the DC bias path are separate. The simulated modulator has no self-bias switch: its DC bias path is an ideal 10 Gohm resistor `Rleak`, not laid out (see `analog/PSEUDO_RES_NOTES.md`).

| Check | Result |
|---|---|
| Magic DRC (`drc(full)`) | 0 errors |
| KLayout official deck (FEOL, BEOL, offgrid) on `ota_core.gds` | 0 items (`drc.sh`) |
| Netgen LVS vs `ota_core_sch.spice` | **match**: 4 devices, 8 nets, 6 pins equivalent (`lvs.out`); parallel fingers are merged by Netgen |
| Negative tests (`ref/`): en/enb swapped, core PMOS width halved | both detected (pin mismatch, property error) |

Size 87.6 x 39.6 um (about 3460 um2, from the Magic bounding box). Picture: `ota_core_layout.png`.
Reproduce: `PATH=$HOME/openeda/magicinst/bin:$PATH PDK_ROOT=$HOME/openeda/pdk/share/pdk layout/ota/build.sh && layout/ota/lvs.sh && layout/ota/drc.sh` (`render.py` via `klayout -b -r`).

**Limits.** Geometry and connectivity only: no parasitic extraction, no post-layout simulation, no matching/symmetry work, the two core devices are not interdigitated and the
guard rings are the generator defaults. Whether the finger split changes the OTA gain/bandwidth versus the unsplit schematic is not yet simulated.

## mim/ : integrator capacitors Cs and Ci, `cap_array`

Six identical unit capacitors from the PDK generator (`cap_mim_m3_1`, metal3 bottom plate, metal4 top plate, 22.2 x 22.2 um = 1.00 pF at the typical corner) in 3 columns x 2 rows,
columns **Ci | Cs | Ci**: Cs = the 2 middle units (2 pF), Ci = the 4 outer units (4 pF). Both share the array centre, and the ratio is a unit count, so the 0.5 does not depend on the process.
All top plates are `g` (the OTA input, virtual ground); bottom plates are `cs_b` (sampling/DAC side) and `ci_b` (OTA output). Pins `g`, `cs_b`, `ci_b`.
The `cs_b` pin is a metal5 stripe (via4 from the middle column), because that column sits between the two Ci columns.

| Check | Result |
|---|---|
| Magic DRC (`drc(full)`) | 0 errors |
| KLayout official deck (FEOL, BEOL, offgrid) on `cap_array.gds` | 0 items (`drc.sh`) |
| Netgen LVS vs `cap_array_sch.spice` | **match** (`lvs.out`; Netgen merges the parallel units: 2 devices, 3 nets) |
| Negative tests (`ref/`): Cs with 3 units and Ci with 3, one unit with plates swapped, one unit with a wrong size | all three detected |

Two DRC findings from the first run, both fixed: the PDK generator's cell needs 1.34 um between a capacitor's capm and a neighbour's metal3 (rule `capm.11`), which sets the 26 um column pitch; and a via4 drawn in Magic must be 1.18 um (it includes the metal4 enclosure).

**Capacitance from the extracted netlist (`cap_values.py`, ngspice AC at 1 kHz, `cap_values.txt`):** typical Cs = 2.0006 pF, Ci = 4.0013 pF; the cap-corner models give -12 % (ll) to +13 % (hh) on the absolute values (Cs 1.74-2.27 pF), Cs/Ci = 0.5000 in every corner because the model has no mismatch term in these runs. Absolute capacitance spread does not matter for the loop gain, only the ratio, but it changes kT/C noise and the OTA load.

**Parasitics (Magic `extract do capacitance`, `cap_array_para.spice`):** bottom plate to substrate 26 fF (cs_b) and 51 fF (ci_b), about 1.3 % of each capacitor; `g` to substrate 27 fF. Magic also reports 96 fF (cs_b-g) and 192 fF (ci_b-g) of metal3-metal4 overlap; **I think this is an extractor artefact, not extra capacitance**, since the foundry MIM model already includes the plate structure, but I have not confirmed it. The ratio is not affected either way (4.8 % on both).

Size 76.4 x 59.5 um (about 4545 um2; the six units alone are 2960 um2). Picture: `cap_array_layout.png`.
Reproduce: `PATH=$HOME/openeda/magicinst/bin:$PATH PDK_ROOT=$HOME/openeda/pdk/share/pdk layout/mim/build.sh && layout/mim/lvs.sh && layout/mim/drc.sh && python3 layout/mim/cap_values.py` (`render.py` via `klayout -b -r`).

**Limits.** No mismatch or gradient analysis (no dummy units around the array, the edge columns see a different neighbourhood than the middle one); no post-layout simulation of the modulator with the 1.3 % substrate parasitics; the 50 fF hold capacitor of the comparator output is not laid out.

## comp_compact/ : compact comparator, `comp_compact` (same circuit and sizes as `comp/`)

Made by `gen_cc.py` with `autolay2.py`, which uses the PDK's **multifinger** cells so transistor pairs that share a terminal share diffusion and a well: the input pair (strips cx1 | ctail | cx2), the cross-coupled and reset PMOS pairs (shared vdda), the isolating inverters, the NOR latch halves (series PMOS stacks share the internal node), and the output buffers. 16 cells instead of 29 single-finger devices; the cell order comes from a wirelength annealer, and the router is the same row/channel scheme as `comp/` (one metal2 track per net, metal3 straps for NMOS, metal4 for PMOS), with the ring tie taken from the corner facing away from the channel. The schematic reference is the same `comp_sch.spice` (Netgen merges the fingers).

| Check | Result |
|---|---|
| Size | 69.9 x 38.6 um = **2701 um2** (first layout `comp/`: 125.7 x 40.0 = 5033 um2, 46 % smaller) |
| Magic DRC (`drc(full)`) | 0 errors |
| KLayout official deck (FEOL, BEOL, offgrid) | 0 items (`drc.sh`) |
| Netgen LVS vs `comp_sch.spice` | **match**: 27 devices, 18 nets, 7 pins equivalent (`lvs.out`) |
| Negative tests (`ref/`): inputs swapped, tail 8 -> 4 um, one reset PMOS gate on vdda | all three detected |

Reproduce (about 1 minute): `make layout-comp-compact`; post-layout run: `layout/comp_compact/pex_sim.sh` (needs `SKY130PR`). Picture: `comp_compact_layout.png`.

**Post-layout simulation (`analog/tb_comp_pex.py`, results in `results/analog/comp_postlayout.jsonl`).** The same test bench as the schematic (0.5 mV input steps, TT, 27 C, 3.3 V, 1.024 MHz), on the Magic-extracted netlist: devices with their diffusion areas plus **wiring capacitance to the substrate** (`ext2spice cthresh 0`); **no wire resistance** and no coupling-capacitance study.

| | Offset (up / down) | Single transition | Max decision delay | Supply current |
|---|---|---|---|---|
| Schematic, 50 fF placeholder loads | +0.25 / -0.25 mV | yes | 2.7 ns | 29.3 uA |
| Schematic, no placeholder loads | -0.25 / +0.25 mV | yes | 2.2 ns | 25.5 uA |
| First layout (`comp/`) with extracted capacitance | -3.25 / -3.25 mV | yes | 2.9 ns | 26.1 uA |
| **Compact layout** with extracted capacitance | **-1.25 / -1.25 mV** | yes | 2.8 ns | 27.4 uA |

Both layouts show no hysteresis and complementary outputs; the offset is a parasitic asymmetry (the same shift up and down), 1.25 mV for the compact layout against 3.25 mV for the first one, below one LSB10 (1.56 mV) in both cases. The test bench steps in 0.5 mV, so offsets are resolved to about 0.5 mV.

**Limits.** One corner (TT) and one temperature; capacitance only (a lumped model, no wire R, which would be expected to slow the long channel wires further); no mismatch or noise, so the offset above is systematic only (a real StrongARM offset is dominated by random mismatch, which this does not include); the comparator was not re-run inside the modulator loop with the extracted netlist. The placement is still a scripted row/channel layout, not a hand-matched common-centroid one: the input pair is a plain 2-finger cell (two gates sharing the tail strip, not interdigitated), there is no dummy device, no symmetric routing of the two sides, and the 16 channel tracks are not packed, so a hand layout would be smaller and better matched.

**Post-layout corners (19 Nov 2026, second session).** The same extracted-capacitance run of `comp_compact` at the other process corners (`analog/tb_comp_pex.py`; `COMP_TEMP` and `COMP_VDD` environment variables added, defaults unchanged), results in `results/analog/comp_postlayout.jsonl`:

| Corner / temp / supply | Offset (up / down) | Single transition | Max decision delay | Supply current | Schematic (50 fF loads, `comp_corners.jsonl`): offset / delay / current |
|---|---|---|---|---|---|
| tt / 27 C / 3.3 V | -1.25 / -1.25 mV | yes | 2.8 ns | 27.4 uA | +0.25 / -0.25 mV, 2.7 ns, 29.3 uA |
| ss / 27 C / 3.3 V | -1.25 / -1.25 mV | yes | 3.3 ns | 20.9 uA | not run at this temperature and supply |
| ff / 27 C / 3.3 V | -0.75 / -0.75 mV | yes | 2.4 ns | 30.9 uA | not run at this temperature and supply |
| sf / 27 C / 3.3 V | -1.25 / -1.25 mV | yes | 2.7 ns | 29.1 uA | +0.25 / -0.25 mV, 2.6 ns, 31.9 uA |
| fs / 27 C / 3.3 V | -0.75 / -0.75 mV | yes | 3.0 ns | 23.6 uA | -0.25 / +0.25 mV, 2.8 ns, 26.1 uA |
| ss / 125 C / 3.0 V | -1.25 / -1.25 mV | yes | 4.1 ns | 14.4 uA | +0.25 / -0.25 mV, 3.9 ns, 15.4 uA |
| ff / -40 C / 3.6 V | -0.75 / -0.75 mV | yes | 2.1 ns | 44.2 uA | +0.25 / +0.25 mV, 2.1 ns, 46.9 uA |

The systematic offset from the parasitic asymmetry stays between -0.75 and -1.25 mV in all seven conditions (below 1 LSB10 = 1.56 mV; resolution 0.5 mV), with a single transition, no hysteresis and complementary outputs everywhere, and the delay follows the schematic within about 0.2 ns at the temperature and supply extremes.
Same limits as above: capacitance only (no wire resistance), no mismatch or noise, not re-run in the modulator loop. A random-mismatch offset will add to this systematic term, and that has not been simulated.

## vcm/ : vcm replica, `vcm_replica`

The self-biased reference of the simulated modulator (`dsm1/sim/dsm1.py`): the inverter core at 1/8 width with its output tied to its input, header always on and footer always on (their gates are the pins `enb` and `en`, which the top level ties to gnd and vdda, as for the OTA core).
Devices (`g5v0d10v5`): header PMOS 37.5/0.5 (10 x 3.75), core PMOS 16/2 (5 x 3.2), core NMOS 4/2 (1 finger), footer NMOS 12.5/0.5 (4 x 3.125). Pins `vcm vdda gnd en enb`.
`vcm_replica_sch.spice` is generated by `gen_sch.py` from the constants in `common/amp_core.py` (so sizes cannot drift); `gen_vcm.py` adapts the OTA-core generator (stack hn / mn / mp / hp, metal2 bars and straps, the gate strap joined to the output bar by a via1 and a metal2 bar, the two enable gate pads brought out as the ports `en` and `enb`).

| Check | Result |
|---|---|
| Magic DRC (`drc(full)`) | 0 errors |
| KLayout official deck (FEOL, BEOL, offgrid) on `vcm_replica.gds` | 0 items (`drc.sh`) |
| Netgen LVS vs `vcm_replica_sch.spice` (extracted with `extract unique`, so labels alone cannot join nets) | **match**: 4 devices, 5 pins (`lvs.out`) |
| Negative tests (`ref/`, `make_neg.py`): header gate on vdda, core gate not tied to the output, core PMOS width halved, footer gate on gnd | all four detected |
| DC self-bias of the extracted netlist (`bias_check.py`) | vcm = 1.6314 / 1.6086 / 1.6509 V at TT / SS / FF (27 C, 3.3 V); the schematic gives 1.6242 V at TT (the 1.624 V in `dsm1/README.md`) |

**Correction (19 Nov 2026).** The first version of this block (wip16) matched its schematic only because Magic joins nets that carry the same label: the gate and the drain were both labelled `vcm`, the enable pads `vdda` and `gnd`, and none of them was drawn as connected. The top-level extraction (where the labels of a sub-cell do not join) showed the gate, the drain, the footer gate and the header gate as four separate nets. The layout now has the gate-to-drain connection drawn, and the enables are ports; `ext_vcm.tcl` uses `extract unique` so this cannot recur unseen. The same trick exists in `layout/ota_on/` (always-on OTA variant, enables labelled `vdda`/`gnd`), which is **not used** by the top level (it uses `ota_core` with `en`/`enb` routed) and should be treated as unverified.

Size 23.5 x 36.0 um (about 845 um2). Picture: `vcm_replica_layout.png`. Reproduce: `PATH=$HOME/openeda/magicinst/bin:$PATH PDK_ROOT=$HOME/openeda/pdk/share/pdk layout/vcm/build.sh && layout/vcm/lvs.sh && layout/vcm/drc.sh && python3 layout/vcm/bias_check.py` (`make layout-vcm`).

**Does it track the OTA?** `bias_check.py` also self-biases the extracted full-size OTA core (`layout/ota/`, same enables) and compares: the replica sits 2.8 / 1.6 / 2.1 mV above it at TT / SS / FF. The 7 mV difference between the
replica's layout (1.6314 V) and the schematic (1.6242 V) comes from the finger split: the PDK models are binned by width, and the layout fingers (3.2-4 um) differ from the 12.5 um pieces `v2.mos` uses. The schematic simulations (`dsm1/`) split both OTA and replica into pieces of at most 16 um; the layouts use different finger widths. A few millivolts between vcm and the OTA's trip point should appear as an
input offset of the integrator (about 3 mV is about 2 LSB10 on the 1.56 V peak-to-peak range); I have not simulated that in the loop.

**Limits.** Same finger-per-device plan as the OTA, so no interdigitation or common-centroid matching against the OTA core (matching is at the 1/8-ratio only through equal L and similar fingers); no parasitic extraction or simulation of the node;
the unbuffered, undecoupled `vcm` node and the switch-kick problem recorded in `dsm1/README.md` are not changed by this layout (a decoupling capacitor or a buffer would be a schematic change and has not been made); the 1 finger NMOS is narrow
(a single 4 um x 2 um finger) and its ring tie sits bottom-left because the D strip occupies the top-left.


## top/ : analog top level, `dsm_top` (blocks placed, routed on metal3/metal4, 19 Nov 2026)

Eleven block instances (`clkgen`, `vcm_replica`, 6 x `tg_x0p5_mf`, `cap_array`, `ota_core`, `comp_compact`) placed by `topdef.py` and wired by `top_route.py` (grid maze router, 0.35 um pitch, via stacks to every block pin, run in KLayout: `klayout -b -r top_route.py`, about 2 minutes).
`topdef.py` holds the floorplan and the net table; `gen_top_sch.py` writes `dsm_top_sch.spice` from the same table (the block schematics plus the top connection), so layout and schematic cannot drift apart. Top ports: `vdda gnd clk vin vrp vrn vcm q qb g out`.
The OTA and vcm replica enables are routed to the rails (`en` to vdda, `enb` to gnd). **The pseudo-resistor (Rleak) is not laid out**: `g` and `out` are pins, the bias path is an ideal element outside the layout.

| Check | Result |
|---|---|
| Magic DRC `drc(full)` on `dsm_top.gds` | 0 errors (`drc.sh`) |
| KLayout official `sky130A_mr.drc` | 0 items |
| Flat extraction (Magic, `extract unique`) vs `dsm_top_sch.spice`, Netgen | **match**: 113 devices, 11 pins (`lvs.sh`, `lvs.out`) |
| Negative tests (`ref/`, `make_neg.py`): sample switch on the wrong phase, DAC switch polarity swapped, Cs plates swapped, vcm replica footer off | all four detected |

**Found while checking (all fixed in this version).** (1) The router's notch fill closed the 0.14 um slit between two different nets and shorted `q` to `dac` at the DAC switch (no DRC error, only LVS showed it); the fill is now done net by net. (2) The vcm replica nets were only joined by labels (see its section). (3) Pad legalisation did not honour the via2.4a / met2.5 enclosure ("0.085 um on both sides in one direction"), the 0.4 um spacing of wide metal3 (MIM plates, met3.3d), the 0.14 um neck rule where a pad half-overlaps a block bar, and 0.285 um gaps between pieces of one net; all four are now handled in the router.
**Not done:** the extraction of the top (`top/pex/README.md`, 20 Nov: capacitance and closed-loop check at 3 corners, wire resistance only partly) has no wire resistance in the simulated netlists, no SNDR run on the extracted netlist, no power-grid or IR-drop study, no pad ring, no CIC (digital) place and route, no guard rings or shielding between the clock lines and the integrator nodes.
Reproduce: `PATH=$HOME/openeda/magicinst/bin:$PATH PDK_ROOT=$HOME/openeda/pdk/share/pdk sh -c "cd layout/top && python3 gen_top_sch.py && klayout -b -r top_route.py && ./drc.sh && python3 make_neg.py && ./lvs.sh"` (`make layout-top`).

