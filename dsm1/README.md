# First-order switched-capacitor delta-sigma modulator on the v2 inverter amplifier (Sky130, ngspice)

**Status: pre-layout, schematic-level transistor simulation at one PVT point (TT, 27 C, 3.3 V). Not an entry-ready
design:** there is no layout, GDS, DRC or LVS, no PVT sweep, no noise simulation, and parts of the loop are still ideal
(see "What is transistor-level and what is ideal").

This directory sits next to `v2/` in the Chipalooza 4 repository and **imports `v2/sim/v2.py`, `simlib.py` and `mylib.py`**,
so it must stay in that place (`dsm1/sim/` and `v2/sim/` side by side).

## What was simulated

A single-ended, first-order, 1-bit SC delta-sigma modulator. The integrator's OTA is the **v2 self-biased inverter core**
(L = 2 um, WN = 32 um, WP = 128 um thick-oxide 5 V devices, with v2's enable header 300 um / footer 100 um, all taken from
`v2.py`). The switches are the **v2 transmission gate** (NMOS 8 um / PMOS 24 um, L = 0.5 um) unless a size knob says otherwise.

Discrete-time behaviour (non-delaying integrator, one-cycle decision delay):

    Vout[n+1] = Vout[n] + (Cs/Ci) * (Vin - Vdac[n]),     Vdac = vcm +/- Vref chosen by the previous bit

| Parameter | Value |
|---|---|
| Supply | 3.3 V |
| Clock fclk | 1.024 MHz |
| OSR / signal band | 128 / fclk/(2*OSR) = 4 kHz |
| Cs / Ci (ideal capacitors) | 2 pF / 4 pF |
| Vref | +/-0.8 V around vcm (full scale = +/-0.8 V) |
| Input | sine, 0.4 V peak = -6 dBFS |
| vcm | about 1.624 V at TT (from a self-biased replica of the core at 1/8 width) |
| Integrator DC bias path | 10 Gohm resistor from out to g (ideal) |

Switched-capacitor schematic (as in `dsm1.py`): input sampled on the bottom plate of Cs during phi1 (`sin`), top plate to
vcm (`st1`, opens first = bottom-plate sampling); in phi2 the top plate goes to the inverter input g (`st2`) and the bottom
plate to the DAC level (`sb2`), which a 2-switch mux (`dp`, `dn`) selects as vcm+Vref or vcm-Vref from the bit `q`. The bit is
latched by a transmission gate onto a 50 fF hold capacitor and buffered by two inverters.
Timing (fractions of the clock period T): phi1a 0.02-0.44, phi1 0.02-0.47, phi2 0.52-0.97, latch window 0.10-0.20.

### What is transistor-level and what is ideal

| Transistor-level (Sky130 `g5v0d10v5` models) | Ideal / behavioural (declared) |
|---|---|
| Inverter OTA with header/footer (v2 core) | Clock phases in the default runs (ideal PULSE sources); `real_clk=1` uses the transistor-level generator |
| vcm replica | Comparator decision in the default runs: smooth tanh of (out - vcm); `real_comp=1` uses the StrongARM from `analog/` |
| All six switches and the latch switch | Vin and +/-Vref sources (referenced to the replica vcm) |
| Hold node and the two bit-buffer inverters | Cs, Ci, hold capacitor (ideal capacitors, no parasitics except the devices' own) |
| | 10 Gohm integrator bias resistor |

ngspice transient runs contain **no thermal or kT/C noise**, so the SNDR below is quantisation noise plus circuit error only.

## Test method

`run_sndr.py` runs a transient of N + 258 clock cycles, discards the first 256, samples the latched bit `q` at 0.4 T of every
cycle (+/-1), and takes a coherent FFT (N points, tone at bin M, Hann window). Signal = bins M +/- 3; noise + distortion = all
other bins from 1 to N/(2*OSR) (DC excluded), so **harmonics that fall inside the 4 kHz band count against SNDR**.
Ideal-model reference (`ideal_model.py`, same Cs/Ci, Vref, input level and FFT method, no circuit effects):
**57.3 dB at N = 8192, M = 17** and **55.2 dB at N = 4096, M = 5** (`results/ideal_model.txt`).

## Results (TT, 27 C, 3.3 V, all at OSR 128, input -6 dBFS)

| Configuration | N / M | Tone | SNDR | ENOB | SFDR | Data |
|---|---|---|---|---|---|---|
| v2 switch sizes (tone placed so H2, H3 are out of band) | 8192 / 17 | 2.12 kHz | 50.2 dB | 8.04 | 60.8 dB | `results/sndr_N8192_tone2p1kHz_v2switches.json` |
| v2 switch sizes (H2, H3 in band) **baseline** | 4096 / 5 | 1.25 kHz | 45.9 dB | 7.34 | 48.0 dB | `results/sndr_N4096_v2switches.json` |
| all transmission gates x0.5 | 4096 / 5 | 1.25 kHz | 54.7 dB | 8.80 | 59.7 dB | `results/sndr_N4096_allTGx0p5.json` |
| input-sampling, `st1`, `st2` switches x0.25 | 4096 / 5 | 1.25 kHz | 52.3 dB | 8.39 | 55.4 dB | `results/sndr_N4096_sampling_switches_x0p25.json` |
| Vref = 0.5 V, input 0.25 V peak (smaller swing) | 4096 / 5 | 1.25 kHz | 58.9 dB | 9.50 | 64.3 dB | `results/sndr_N4096_vref0p5.json` |

* The first row looks better than the second only because its 2.1 kHz tone puts the 2nd and 3rd harmonics (4.2 and 6.4 kHz)
  outside the 4 kHz band. The N = 4096, M = 5 tone (1.25 kHz) keeps them in band and is the fair baseline: **45.9 dB**.
* A single FFT run with only 16-32 in-band bins has a few dB of run-to-run pattern variation (first-order modulators are
  sensitive to input amplitude and frequency), so **do not rank results that differ by 2-3 dB** (for example the x0.5 and x0.25
  switch rows). The per-step error table below is the cleaner metric.
* The reduced-swing row is not comparable with the others (different Vref and input); its ideal reference is the same 55.2 dB.
* Spectra: `results/*_spectrum.png`.

## Where the error comes from: per-step accuracy

`step_check.py` (about 35 s per case; 900 cycles = one full period of the 1.25 kHz tone) compares every simulated integrator step with the ideal `(Cs/Ci)(Vin - Vdac)` and fits
`step = gain*e + cubic*e^3 + offset`. `resid` is the rms residual in mV; "+level terms" also fits terms in the output level
before the step (to separate step-size dependence from output-level dependence); `step-cubic` is the remaining step-size
cubic coefficient in that fit. Output of `run_step_checks.py` (`results/step_check.txt`):

```
TT, 27 C, 3.3 V, 1.024 MHz unless stated; ~840 cycles analysed per case (one full tone period); step = out(end of phi2) difference per cycle
case                                        gain    cubic  resid mV  resid mV (+level terms)  step-cubic
baseline (v2 switch sizes)                1.0022  -0.0771      3.55                     2.14     -0.0256
fclk = 512 kHz (half clock)               1.0018  -0.0777      3.64                     2.05     -0.0214
p2_early=1 (DAC switch opens early)       1.0120  -0.0921      3.90                     2.30     -0.0326
all TGs x0.5                              0.9868  -0.0270      1.29                     0.55     -0.0054
Vref 0.5 V, Vin 0.25 V peak               0.9883  -0.0902      1.06                     0.60     -0.0293
sin x0.5                                  0.9933  -0.0510      2.54                     1.28     -0.0121
st1 x0.5                                  0.9996  -0.0704      3.30                     1.81     -0.0197
sb2 x0.5                                  1.0026  -0.0777      3.71                     2.16     -0.0191
st2 x0.5                                  0.9923  -0.0440      1.85                     1.03     -0.0131
dac mux x0.5                              1.0022  -0.0783      3.48                     2.01     -0.0224
sin+st2 x0.5                              0.9881  -0.0317      1.40                     0.61     -0.0073
sin+st1+st2 x0.5                          0.9869  -0.0275      1.28                     0.57     -0.0064
sin+st1+st2 x0.25                         0.9829  -0.0131      0.42                     0.14     -0.0036
```

**Caveat on the cubic coefficient.** The `cubic` and `step-cubic` columns depend on how much of the tone period the run covers (for the baseline, a 300-cycle run gave -0.013 and a 500-cycle run -0.073; the table uses a full period). The rms residual is stable across run lengths, so the conclusions below rest mainly on the residual column. Treat the coefficients as indicative only.

What the data supports:

1. **Not settling-limited.** Halving the clock does not reduce the error.
2. **Early opening of the DAC switch does not help** (it is slightly worse), so this is not a bottom-plate-switch ordering problem.
3. **The input-sampling switch (`sin`) and the top-plate switches (`st1`, `st2`) drive the step-dependent error;** `sb2` and the DAC mux
   do not (3.71 and 3.48 mV against 3.55 mV at baseline). Shrinking all three to 1/4 of the v2 size takes the residual from 3.55 mV to 0.42 mV. A plausible mechanism (charge
   injection from `sin`, converted to an error by the top-plate switch parasitics) is consistent with this but **was not proven**.
4. A smaller error that depends on the output level remains with small switches; it is consistent with inverter gain
   nonlinearity at large output swing, also **not isolated**. Reducing the swing (Vref 0.5 V) lowers the residual to 1.06 mV (the cubic coefficient itself does not shrink, but the error scales with e^3 and the steps are smaller).
5. Smaller switches raise Ron; with these sizes and a 440 ns integrate phase this did not hurt, but it must be rechecked at
   corners and higher clock rates.

## Not done yet

* PVT corners (SS/FF/SF/FS, supply, temperature). Each N = 4096 FFT run takes ~3.5 min on one core, so use `step_check.py` as a
  quick screen and FFTs for the extremes.
* Noise (thermal, kT/C), clock jitter, comparator mismatch/noise, real pseudo-resistor
  for the DC bias path (the 10 Gohm ideal resistor makes the integrator leak negligible at about 0.0025 %/cycle; a real device will not),
  signal-dependent reference loading, input-source impedance.
* Layout, GDS, DRC and LVS (Magic/Netgen or KLayout), post-layout (RC-extracted) simulation. Without these the design does
  not meet the SMACD Open-Source Design Challenge entry minimum.
* Decimation filter (the bitstream is analysed directly with an FFT).

## Reproduce

Requirements: ngspice 42, Python 3 with `numpy` (and `matplotlib` for `plot_spectrum.py`), and the Sky130 models.
Versions used: ngspice-42, numpy 2.5.4, matplotlib 3.11.2, `skywater-pdk-libs-sky130_fd_pr` commit
`f62031a1be9aefe902d6d54cddd6f59b57627436`.

```
git clone https://github.com/google/skywater-pdk-libs-sky130_fd_pr
cd skywater-pdk-libs-sky130_fd_pr && git checkout f62031a1be9aefe902d6d54cddd6f59b57627436 && cd ..
export SKY130PR=$PWD/skywater-pdk-libs-sky130_fd_pr
export SIMTMP=/tmp                      # optional scratch dir
cd chipalooza4-inverter-amplifier/v2/sim && python3 smoke_test.py      # expects 25.50 dB (checks the setup)
cd ../../dsm1/sim                                                        # run everything from here (needs .spiceinit)
python3 run_dsm.py 40                   # 40-cycle sanity run (a few seconds)
python3 ideal_model.py                  # ideal reference
python3 run_step_checks.py              # per-step accuracy table, ~4 min
# FFT SNDR runs: run_sndr.py <corner> <temp C> <vdd> <N> <out.json> [key=value ...]
python3 run_sndr.py tt 27 3.3 4096 ../results/mine_base.json M=5
python3 run_sndr.py tt 27 3.3 4096 ../results/mine_sw025.json M=5 sc_sin=0.25 sc_st1=0.25 sc_st2=0.25
python3 plot_spectrum.py ../results/mine_base_P.npy 4096 5
python3 plot_bitstream.py 128 0.7 sc_sin=0.25 sc_st1=0.25 sc_st2=0.25   # input sine + output bitstream over one period, ~15 s
```

**Real clock generator and comparator** (`real_clk=1 real_comp=1`, blocks in `../analog/cells.py`). Use tight tolerances and note the cost:

```
python3 run_sndr.py tt 27 3.3 4096 ../results/mine_real.json M=5 real_clk=1 real_comp=1 pts_per_cycle=200 reltol=1e-4 vntol=1e-7 tg_scale=0.5
```

* About 35 min per N = 4096 run on one core; run one at a time (two in parallel on 2 cores exceeded the 3000 s limit of an earlier revision).
* `run_dsm.py` saves only `q, out, vcm, g` (ngspice otherwise kept every node and ran out of memory at about 8 GB) and stops with an error if ngspice ends early (at tight tolerances one run aborted at cycle 40 with `vcm` above the supply; the output file simply ended, so undetected it would have been analysed as data).
* At ngspice default tolerances these runs gave wrong results (32 of 75 comparator decisions disagreed with the sign of `out - vcm`; with `reltol=1e-4` 4 of 74). The remaining disagreements are 13-25 mV from the threshold: the comparator evaluates 30-60 ns after the phase change, while `out` and `vcm` are still settling. This acts as a comparator error inside the loop (shaped like quantisation error) and is included in the SNDR below.

| Configuration (TT, 27 C, 3.3 V, N = 4096, M = 5) | SNDR | ENOB | SFDR | Data |
|---|---|---|---|---|
| Real comparator + clock generator, all TGs x0.5 | 56.9 dB | 9.17 | 61.0 dB | `results/sndr_N4096_realclk_realcomp_allTGx0p5.json` |
| Real comparator + clock generator, v2 switch sizes | **no result**: ngspice aborted at cycle 988 of 4354 (`reltol=1e-4`) | | | none |

The v2-switch run with the real blocks was not completed: ngspice ended at cycle 988 and `run_dsm.py` refused to analyse it. Cause not investigated (ngspice's message was not kept); the earlier 40-cycle aborts at tighter tolerances (`reltol=1e-5`) had the same signature. Treat convergence of the real-block runs as fragile.

The ideal-block reference is 55.2 dB at this N and M, and single runs vary by a few dB, so 56.9 dB means "no measurable loss from the real comparator and clock generator at this point", not an improvement.

**Raw waveform data** (`results/wave_*.npz`, 14 and 50 MB) is not in the zip because of the upload size limit; regenerate with `wave_run.py` (about 15 min) and `wave_run_overlay.py` (about 5 min), or use the separate data zip.

**Waveforms** (`wave_run.py`, about 15 min): `results/waveforms_realblocks_allTGx0p5.png` (input, integrator output, bitstream, the 10 output bits b9..b0 of the bit-exact CIC2 model and the 128-clock strobe), `results/decimated_code_realblocks.png`, `results/vcm_node_kicks.png`. Three periods of a 2 kHz input give only 12 output words (8 kHz output rate), so this is a visual check, not a measurement; the first word is start-up.

**Overlay figure** (`wave_run_overlay.py`, about 5 min, then `plot_overlay.py`): `results/sine_and_bitstream_overlay.png`, an 8 kHz tone (128 clocks per period, 70 % of full scale; outside the 4 kHz band, for visualisation only), real comparator and clock generator, all TGs x0.5, TT.

**Finding from the waveforms: the `vcm` replica node is kicked by the switches by up to about -0.3 V / +3.9 V for a few ns each cycle** (it is a weakly driven self-biased node that also serves as comparator reference and top-plate reference; the integrator output itself stays within 0.96-2.17 V). It settles before the end of each phase, but the comparator evaluates while it is still settling, which is the likely origin of the 13-25 mV decision errors above. A buffered or heavily decoupled reference would be the fix; not done, and not simulated.

Run-time knobs (`key=value`): `M` (tone bin), `osr`, `fclk`, `cs`, `ci`, `vref`, `vin_amp`, `rleak`, `tg_scale` (all switches),
`real_clk`, `real_comp` (0/1), `pts_per_cycle`, `reltol`, `vntol`, `sc_sin` / `sc_st1` / `sc_sb2` / `sc_st2` / `sc_dac` (per-switch size factor, default = `tg_scale`), `p2_early` (0/1).
The result files in `results/` were produced by earlier revisions of `dsm1.py` whose default netlist is identical to the
current one (the current `baseline` row of `step_check.txt` reproduces the earlier baseline).

## Files

| File | Purpose |
|---|---|
| `sim/dsm1.py` | Netlist generator (imports `v2.py`) |
| `sim/run_dsm.py` | One transient run, returns waveforms |
| `sim/run_sndr.py`, `sim/analyze.py` | Coherent-FFT SNDR / ENOB / SFDR |
| `sim/step_check.py`, `sim/run_step_checks.py` | Per-step accuracy analysis and the table above |
| `sim/ideal_model.py` | Ideal discrete-time reference |
| `sim/plot_spectrum.py` | Spectrum plot from a saved `*_P.npy` |
| `sim/plot_bitstream.py` | Input sine and output bitstream over one period (`results/bitstream_vs_sine.png`: 128 cycles per period, input 70 % of full scale, quarter-size sampling switches) |
| `results/` | JSON results, power spectra (`*_P.npy`), plots, `step_check.txt`, `ideal_model.txt` |

Licence: Apache-2.0, inherited from the repository (`../LICENSE`).

## INL / DNL (pre-layout, DC sweep)

`sim/inl_run.py` then `sim/inl_analyze.py` (about 22 min, **run one instance at a time**: two parallel ngspice runs on 2 cores were about 7x slower each).
Transistor-level modulator, all TGs x0.5, **ideal comparator and clock**, TT, 27 C, 3.3 V. 33 DC inputs from -0.78 V to +0.78 V (97.5 % of the 0.8 V reference) relative to `vcm`,
each simulated separately: 256 clocks to settle, then the density of ones over 1024 clocks, scaled to a 10-bit code (LSB = 1.6 V / 1024 = 1.5625 mV).
Results: `results/inl_level_*.json`, `results/inl_dnl_summary.json`, `results/inl_dnl.png`.

| Quantity | Value |
|---|---|
| Gain error (slope 635.8 vs ideal 640 codes/V) | -0.66 % |
| Offset | +0.97 LSB10 |
| INL vs least-squares line | max 1.12 LSB, peak-to-peak 2.17 LSB |
| INL vs end-point line | max 1.69 LSB |
| Step DNL (adjacent levels, 31-LSB steps) | max 0.034 LSB |
| Integrator output range | 0.86 - 2.39 V (no overload) |

**Read these as "at the measurement floor", not as measured sub-LSB linearity.** A first-order loop averaged over 1024 clocks resolves the density only to 1/1024, i.e. 1 LSB10, and the INL values
are indeed all 0, +/-1 codes (they step in whole counts). So INL is bounded by about +/-1.1 LSB, with no evidence of a larger error; any structure below 1 LSB is not resolved.
The step DNL is a slope check over 31-LSB steps; **a 1-LSB code-width DNL is not obtainable this way** (it would need a much longer average per code, or a histogram test on the decimated output).
The full-scale ends (+/-0.78 V) show the same size of error as the middle, so there is no sign of compression near the reference within the measurable range.
Not covered: the real comparator and clock generator (the sweep used the ideal ones; a real-block run costs about 10x more time per clock), other corners, temperature, mismatch, noise.

### INL / DNL with the extracted capacitor-array parasitics (`sim/inl_run.py par`, `sim/inl_analyze.py inl_par`)

Same sweep, same conditions, plus the substrate capacitances extracted from `layout/mim/cap_array_para.spice`: 19.4 fF on `g`, 10.0 fF on the Cs top plate, 26.1 fF on the Cs bottom plate, 51.0 fF on the Ci bottom plate (OTA output).
Results: `results/inl_par_level_*.json`, `results/inl_par_dnl_summary.json`, `results/inl_par_dnl.png`. About 17 minutes.

| Quantity | ideal capacitors | with array parasitics |
|---|---|---|
| Gain error | -0.66 % | -0.64 % |
| Offset | +0.97 LSB10 | +0.94 LSB10 |
| INL vs least-squares line, max / peak-to-peak | 1.12 / 2.17 LSB | 1.06 / 2.00 LSB |
| INL vs end-point line, max | 1.69 LSB | 1.69 LSB |
| Step DNL, max | 0.034 LSB | 0.034 LSB |
| Integrator output range | 0.86-2.39 V | 0.86-2.39 V |

**No change within the measurement floor** (1 LSB10); the differences above are below that resolution and should not be read as an improvement. Only the capacitor array's substrate parasitics are included: no
wiring, switch or OTA-layout parasitics, no metal3-metal4 overlap capacitance (see `layout/README.md`, mim), still the ideal comparator and clock, TT only.
