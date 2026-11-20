# Pseudo-resistor for the integrator DC bias path (out -> g): what was tried, 19 Nov 2026

The simulated modulator has no self-bias switch: the DC bias path is an ideal 10 Gohm resistor `Rleak` from the OTA output to its input (`dsm1/sim/dsm1.py`, "stand-in for pseudo-resistor").
`pseudo_res.py` tests a pseudo-resistor made of anti-parallel diode-connected PMOS (`pfet_g5v0d10v5`), DC operating points at +/-25 mV .. +/-0.4 V around vcm = 1.624 V, one ngspice run per condition.
Reference for comparison: the ideal resistor carries 40 pA at 0.4 V (about 10 uV of integrator-output error per clock cycle with Ci = 4 pF).

**Single pair, each bulk at its own source** (the only variant whose DC solution is stable; `W/L` is the width of each device):

| Condition | W/L | R at +/-25 mV | I at 0.1 V | I at 0.3 V | I at 0.4 V | error per cycle at 0.4 V |
|---|---|---|---|---|---|---|
| TT / 27 C | 0.25 | 1.6 Tohm | 0.17 pA | 50 pA | 846 pA | 206 uV |
| TT / 27 C | 40 | 160 Gohm | 1.7 pA | 496 pA | 8.5 nA | 2.1 mV |
| SS / 125 C | 0.25 | 500 Gohm | 0.26 pA | 9.9 pA | 70 pA | 17 uV |
| SS / 125 C | 40 | 11.6 Gohm | 10 pA | 252 pA | 1.4 nA | 350 uV |
| FF / -40 C | 0.25 | 1.2 Tohm | 0.39 pA | 572 pA | 22 nA | 5.4 mV |
| FF / -40 C | 40 | 119 Gohm | 3.9 pA | 5.7 nA | 220 nA | 54 mV |

Findings: (1) the I-V is exponential, so it is nowhere near the linear 10 Gohm: reaching about 10 Gohm at small signal (SS/125 C, W/L = 40) already leaks 1.4 nA at 0.4 V, 35 times the ideal resistor, and the leak at 0.4 V moves by a factor of about 300 between SS/125 C and FF/-40 C;
(2) at TT the small-signal resistance is 160 Gohm to 1.6 Tohm, so the g node would take many seconds to bias up and its DC level would then be set by junction and gate leakage that this model does not contain;
(3) the current did not scale simply with W (W/L 0.25 and 2.5 gave the same current to 0.02 %), which I did not explain; treat the absolute numbers as indicative of the model's bin behaviour, not as a design.
**Stacks of two or more pairs were not usable:** the middle node floats, and the result depended on the solver options (N = 2, W = 1: 3.4 Tohm / 2.9 pA with gmin 1e-18, 6.5 Mohm / 66 nA with gmin 1e-15). A real stack's middle node would be set by junction leakage, which the model has none of. Bulk on vdda leaves the devices cut off (about 0.05 pA, a numerical floor).
Not simulated at all: well-to-substrate and source/drain junction leakage of the bulk-at-source wells (it loads whichever node they hang on), startup, and the effect on the modulator loop (no `dsm1.py` run with this element).
Conclusion: no layout was made. A pseudo-resistor as drawn here cannot stand in for the ideal 10 Gohm over the integrator swing.
