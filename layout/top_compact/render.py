import pya, os
lyp = os.path.join(os.environ.get("PDK_ROOT", os.path.expanduser("~/openeda/pdk/share/pdk")), "sky130A/libs.tech/klayout/tech/sky130A.lyp")
lv = pya.LayoutView(); lv.load_layout("dsm_top.gds", True)
try: lv.load_layer_props(lyp)
except Exception as e: print("lyp:", e)
lv.max_hier(); lv.zoom_fit(); lv.set_config("background-color", "#ffffff"); lv.save_image("dsm_top_layout.png", 2400, 1200)
