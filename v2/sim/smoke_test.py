"""Quick check that ngspice, the Sky130 models and the scripts are wired up correctly.
Expected: code 7 midband gain about 25.5 dB at tt, 27 C, 3.3 V."""
import json, simlib, v2
RIN = json.load(open('rin_design.json'))
b = v2.netlist(RIN, 7) + ".control\nop\nac lin 1 1e5 1e5\nlet g=db(v(out)/v(in))\nwrdata OUT g\n.endc\n"
a, _ = simlib.run(b, 'tt', 27)
g = float(a[1]) if a.ndim == 1 else float(a[0, 1])
print(f"code 7 gain at 100 kHz: {g:.2f} dB")
assert abs(g - 25.5) < 0.3, "unexpected gain: check SKY130PR and .spiceinit"
print("OK")
