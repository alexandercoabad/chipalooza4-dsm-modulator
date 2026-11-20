#!/usr/bin/env bash
# Build Magic and the Sky130A PDK (primitive devices only) from source, without Docker or the volare/GitHub-release downloads.
# Worked on Ubuntu 24.04 (cloud sandbox, 18 Nov 2026). Pinned: Magic 8.3.704 @ 4205ad2, open_pdks @ 0c1f823, sky130_fd_pr @ f62031a.
# apt: tcl-dev tk-dev libx11-dev libcairo2-dev libgl1-mesa-dev libglu1-mesa-dev m4 klayout netgen-lvs   (netgen binary: /usr/bin/netgen-lvs)
# Fixed 18 Nov 2026: Magic must be on PATH before open_pdks configure (else "You need magic"). Whole build about 6 min on 2 cores.
set -euo pipefail
W=${1:-$HOME/openeda}; mkdir -p $W/swpdk/libraries; cd $W
git clone -q https://github.com/google/skywater-pdk-libs-sky130_fd_pr; git -C skywater-pdk-libs-sky130_fd_pr checkout -q f62031a1be9aefe902d6d54cddd6f59b57627436
ln -sfn $W/skywater-pdk-libs-sky130_fd_pr swpdk/libraries/sky130_fd_pr
git clone -q https://github.com/RTimothyEdwards/magic; git -C magic checkout -q 4205ad2
(cd magic && ./configure --prefix=$W/magicinst && make -j4 && make install)
export PATH=$W/magicinst/bin:$PATH   # open_pdks configure needs magic on PATH
[ -d open_pdks ] || git clone -q https://github.com/RTimothyEdwards/open_pdks; git -C open_pdks checkout -q 0c1f823
(cd open_pdks && ./configure --prefix=$W/pdk --enable-sky130-pdk=$W/swpdk --enable-primitive-sky130 --disable-io-sky130 \
  --disable-sc-hd-sky130 --disable-sc-hvl-sky130 --disable-sc-hs-sky130 --disable-sc-ms-sky130 --disable-sc-ls-sky130 --disable-sc-lp-sky130 \
  --disable-sc-hdll-sky130 --disable-alpha-sky130 --disable-sram-sky130 --disable-sram-space-sky130 && make -j4 && make install)
echo "export PATH=$W/magicinst/bin:\$PATH PDK_ROOT=$W/pdk/share/pdk PDK=sky130A"
