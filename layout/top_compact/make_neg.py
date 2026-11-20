"""Fault-injected copies of dsm_top_sch.spice (each must fail LVS): sample switch on the wrong phase, DAC switch polarity swapped, Cs plates swapped, vcm replica footer off."""
s = open('dsm_top_sch.spice').read()
def put(n, new): assert new != s, n; open(f'ref/{n}.spice', 'w').write(new)
put('neg_phase_swap', s.replace('Xxst1 vcm t p1a p1ab', 'Xxst1 vcm t p2 p2b'))
put('neg_dac_swap', s.replace('Xxdp vrp dac q qb', 'Xxdp vrp dac qb q'))
put('neg_cap_nodes', s.replace('Xxcap g t b out', 'Xxcap g b t out'))
put('neg_vcm_en', s.replace('Xxvcm vcm vdda gnd vdda gnd', 'Xxvcm vcm vdda gnd gnd gnd'))
