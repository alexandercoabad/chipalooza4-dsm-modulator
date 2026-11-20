# usage: klayout -zz -rd gds=tg_x0p5_mf.gds -rd png=tg_x0p5_mf_layout.png -r render_mf.py
import pya
lv = pya.LayoutView(); lv.load_layout(gds, True); lv.max_hier(); lv.zoom_fit()
lv.set_config("background-color", "#ffffff"); lv.save_image(png, 1400, 900)
