import numpy as np
import yaqc
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import matplotlib.gridspec as gridspec
from matplotlib.widgets import Slider
import toml
import time
import pathlib

here = pathlib.Path(__file__).resolve().parent
plt.style.use("dark_background")
config = toml.load(here / "spectrum_logger.toml")

spec = yaqc.Client(config["yaq"]["spec_port"])
spec.measure(False)
while spec.busy():
    time.sleep(0.1)

slice_args = [config["slice"].pop(k, None) for k in ["start", "stop", "step"]]
sl = slice(*slice_args)

wl = spec.get_mappings()["wavelengths"][sl]
wl = 1e7 / wl

fig = plt.figure("Tsunami")
gs = gridspec.GridSpec(2, 1, height_ratios=[10, 1])

ax = plt.subplot(gs[0])
hl, = plt.plot(wl, spec.get_measured()["intensities"][sl], lw=2)
ref_x, ref_y = np.genfromtxt(
	config["reference"]["path"], 
	unpack=True,
	skip_header=14,
	skip_footer=1
)
ref_y *= config["reference"]["scalar"] / ref_y.max()
plt.plot(1e7/ref_x, ref_y, ls='--', linewidth=2)
ax.set_xlim(1e7/875, 1e7/725)
ax.grid()
plt.ylim(-100, 4096)

def update_line(y):
    hl.set_ydata(y)
    plt.draw()

def data_gen():
    index = 0
    start = time.time()
    while True:
        m_id = spec.get_measurement_id()
        i = 0
        if index < m_id:
            measured = spec.get_measured()
            index = measured["measurement_id"]
            t_measure = time.time()
            # print(f"get_measured: {t_measure-start}")
            ax.set_title(f"{index}")
            start = time.time()
            spec.measure(False)
            yield measured["intensities"][sl]
        elif i > 150:
            print("restarting")        
            spec.shutdown(True)
            time.sleep(3)
        else:
            time.sleep(0.1)

ax = plt.subplot(gs[1])
slider = Slider(ax, "integration time", 3000, 1e6, valinit=spec.get_integration_time_micros())
slider.on_changed(spec.set_integration_time_micros)

# run animation
ani = animation.FuncAnimation(fig, update_line, data_gen, interval=100)
plt.show()