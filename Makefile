# Checks for the one-bit delta-sigma modulator. Requirements: ngspice 42, Python 3 (numpy, scipy, matplotlib), git;
# the layout targets also need Magic, KLayout and Netgen (tools/setup_open_pdks.sh installs Magic and the PDK).
PDK_PR_COMMIT := f62031a1be9aefe902d6d54cddd6f59b57627436
PDK_DIR       ?= $(CURDIR)/pdk/skywater-pdk-libs-sky130_fd_pr
export SKY130PR ?= $(PDK_DIR)
export SIMTMP   ?= $(CURDIR)/.simtmp
OPENEDA       ?= $(HOME)/openeda
LAYOUT_ENV = PATH=$(OPENEDA)/magicinst/bin:$$PATH PDK_ROOT=$(OPENEDA)/pdk/share/pdk

.PHONY: reproduce pdk smoke ideal stepcheck comparator analog-corners layout-tg-mf tg-mf-ron layout-ota layout-mim layout-comp-compact layout-vcm layout-top layout-top-compact clean
reproduce: pdk smoke ideal            ## quick checks (a few minutes)
	@echo "reproduce: OK"

pdk:                                  ## fetch the pinned Sky130 device models
	@test -d $(PDK_DIR)/.git || (mkdir -p $(dir $(PDK_DIR)) && git clone -q https://github.com/google/skywater-pdk-libs-sky130_fd_pr $(PDK_DIR))
	@git -C $(PDK_DIR) checkout -q $(PDK_PR_COMMIT)
	@mkdir -p $(SIMTMP)

smoke: pdk                            ## checks ngspice + PDK setup, expects 25.50 dB (inverter amplifier helper)
	cd v2/sim && python3 smoke_test.py

ideal:                                ## ideal first-order model (57.3 / 55.2 dB)
	cd dsm1/sim && python3 ideal_model.py | tee ../results/ideal_model.txt

stepcheck: pdk                        ## per-step accuracy table of the modulator, about 4 minutes
	cd dsm1/sim && python3 run_step_checks.py

comparator: pdk                       ## StrongARM comparator at TT (about 15 s)
	cd analog && python3 tb_comp.py tt 27 3.3

analog-corners: pdk                   ## comparator + clock generator, 5 corners (about 4 min)
	cd analog && for c in "tt 27 3.3" "ss 125 3.0" "ff -40 3.6" "sf 27 3.3" "fs 27 3.3"; do python3 tb_comp.py $$c; python3 tb_clk.py $$c; done | tee ../results/analog/corners_rerun.jsonl

layout-tg-mf:                         ## transmission gate: build, DRC, LVS, fault injection
	$(LAYOUT_ENV) layout/tg_mf/check_mf.sh

tg-mf-ron: pdk                        ## TG on-resistance, schematic vs layout
	cd layout/tg_mf && python3 ron_check.py tg_x0p5_mf 3 && python3 ron_check.py tg_x0p25_mf 3

layout-ota:                           ## OTA core
	$(LAYOUT_ENV) sh -c 'layout/ota/build.sh && layout/ota/lvs.sh && layout/ota/drc.sh'

layout-mim:                           ## Cs/Ci capacitor array
	$(LAYOUT_ENV) sh -c 'layout/mim/build.sh && layout/mim/lvs.sh && layout/mim/drc.sh && cd layout/mim && python3 cap_values.py'

layout-comp-compact:                  ## comparator
	$(LAYOUT_ENV) sh -c 'layout/comp_compact/build.sh && cd layout/comp_compact && python3 make_neg.py && ./lvs.sh && ./drc.sh && klayout -b -r size.py comp_compact.gds'

layout-vcm:                           ## vcm replica
	$(LAYOUT_ENV) sh -c 'layout/vcm/build.sh && layout/vcm/lvs.sh && layout/vcm/drc.sh && python3 layout/vcm/bias_check.py'

layout-top:                           ## dsm_top (extracted floorplan): route, DRC, LVS with fault injection
	$(LAYOUT_ENV) sh -c 'cd layout/top && python3 gen_top_sch.py && klayout -b -r top_route.py && ./drc.sh && python3 make_neg.py && ./lvs.sh'

layout-top-compact:                   ## dsm_top, compact floorplan
	$(LAYOUT_ENV) sh -c 'cd layout/top_compact && python3 gen_top_sch.py && klayout -b -r top_route.py && ./drc.sh && python3 make_neg.py && ./lvs.sh'

clean:
	rm -rf .simtmp
