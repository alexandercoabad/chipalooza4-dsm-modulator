"""dsm_top definition: blocks, floorplan, pin map (which block pin belongs to which top-level net).  Units: um in this file, nm in the geometry code.
Everything here is data; the geometry (top_geom.py), the router (top_route.py) and the schematic generator (gen_top_sch.py) read it, so the three cannot drift apart."""
import os
BASE = os.environ.get('LAYOUT_DIR', os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

# cell name -> (gds path relative to layout/, schematic file relative to layout/, subckt name in the schematic)
BLOCKS = {
    'ota_core':     ('ota/ota_core.gds',               'ota/ota_core_sch.spice'),
    'cap_array':    ('mim/cap_array.gds',              'mim/cap_array_sch.spice'),
    'comp_compact': ('comp_compact/comp_compact.gds',  'comp_compact/comp_sch.spice'),
    'clkgen':       ('clkgen/clkgen.gds',              'clkgen/clkgen_sch.spice'),
    'vcm_replica':  ('vcm/vcm_replica.gds',            'vcm/vcm_replica_sch.spice'),
    'tg_x0p5_mf':   ('tg_mf/tg_x0p5_mf.gds',           'tg_mf/tg_x0p5_mf_sch.spice'),
}

# instance -> (cell, x um, y um), orientation R0.  All multiples of the 0.35 um routing grid.
FLOORPLAN = {
    'xclk':  ('clkgen',       29.75, 104.65),
    'xvcm':  ('vcm_replica',  20.30,  40.25),
    'xsin':  ('tg_x0p5_mf',   44.45,  40.25),
    'xst1':  ('tg_x0p5_mf',   58.45,  40.25),
    'xst2':  ('tg_x0p5_mf',   72.45,  40.25),
    'xsb2':  ('tg_x0p5_mf',   44.45,  60.20),
    'xdp':   ('tg_x0p5_mf',   58.45,  60.20),
    'xdn':   ('tg_x0p5_mf',   72.45,  60.20),
    'xcap':  ('cap_array',   110.25,  40.25),
    'xota':  ('ota_core',    228.20,  40.25),
    'xcmp':  ('comp_compact', 290.50, 40.25),
}

# top-level nets: net -> list of (instance, pin) ; instance 'TOP' = a top-level pad.  Pin names are the labels in the block GDS.
# TG pins: a, b (metal2 bars), en, enb (gate pads, metal1), vdd, vss (guard-ring li1).   en = nfet gate, enb = pfet gate.
NETS = {
    'vdda': [('xclk', 'vdda'), ('xcmp', 'vdda'), ('xota', 'vdda'), ('xota', 'en'), ('xvcm', 'vdda'), ('xvcm', 'en'),
             ('xsin', 'vdd'), ('xst1', 'vdd'), ('xst2', 'vdd'), ('xsb2', 'vdd'), ('xdp', 'vdd'), ('xdn', 'vdd'), ('TOP', 'vdda')],
    'gnd':  [('xclk', 'gnd'), ('xcmp', 'gnd'), ('xota', 'gnd'), ('xota', 'enb'), ('xvcm', 'gnd'), ('xvcm', 'enb'),
             ('xsin', 'vss'), ('xst1', 'vss'), ('xst2', 'vss'), ('xsb2', 'vss'), ('xdp', 'vss'), ('xdn', 'vss'), ('TOP', 'gnd')],
    'clk':  [('xclk', 'clk'), ('TOP', 'clk')],
    'p1a':  [('xclk', 'p1a'),  ('xst1', 'en')],
    'p1ab': [('xclk', 'p1ab'), ('xst1', 'enb')],
    'p1':   [('xclk', 'p1'),   ('xsin', 'en')],
    'p1b':  [('xclk', 'p1b'),  ('xsin', 'enb')],
    'p2':   [('xclk', 'p2'),   ('xst2', 'en'),  ('xsb2', 'en')],
    'p2b':  [('xclk', 'p2b'),  ('xst2', 'enb'), ('xsb2', 'enb')],
    'cc':   [('xclk', 'cc'), ('xcmp', 'clk')],
    'q':    [('xcmp', 'q'),  ('xdp', 'en'),  ('xdn', 'enb'), ('TOP', 'q')],
    'qb':   [('xcmp', 'qb'), ('xdp', 'enb'), ('xdn', 'en'),  ('TOP', 'qb')],
    'vcm':  [('xvcm', 'vcm'), ('xst1', 'a'), ('xcmp', 'inn'), ('TOP', 'vcm')],
    't':    [('xst1', 'b'), ('xst2', 'a'), ('xcap', 'cs_t')],
    'g':    [('xst2', 'b'), ('xcap', 'g'), ('xota', 'g'), ('TOP', 'g')],
    'out':  [('xota', 'out'), ('xcap', 'ci_b'), ('xcmp', 'inp'), ('TOP', 'out')],
    'b':    [('xsin', 'b'), ('xsb2', 'b'), ('xcap', 'cs_b')],
    'dac':  [('xsb2', 'a'), ('xdp', 'b'), ('xdn', 'b')],
    'vin':  [('xsin', 'a'), ('TOP', 'vin')],
    'vrp':  [('xdp', 'a'), ('TOP', 'vrp')],
    'vrn':  [('xdn', 'a'), ('TOP', 'vrn')],
}
# top-level pads (centre, um): M4 pads with a label
TOP_PINS = {
    'vin': (5.25, 70.00), 'vrp': (5.25, 60.20), 'vrn': (5.25, 50.40), 'vcm': (5.25, 40.25),
    'clk': (5.25, 141.05), 'vdda': (5.25, 100.10), 'gnd': (5.25, 90.30),
    'g': (160.30, 5.25), 'out': (200.20, 5.25), 'q': (362.25, 60.20), 'qb': (362.25, 50.40),
}
# the order of the top-level subckt ports
TOP_PORTS = ['vdda', 'gnd', 'clk', 'vin', 'vrp', 'vrn', 'vcm', 'q', 'qb', 'g', 'out']
