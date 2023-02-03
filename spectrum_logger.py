import numpy as np
import yaqc
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import matplotlib.gridspec as gridspec
from matplotlib.widgets import Slider
from scipy.optimize import curve_fit

import time
import pathlib
import toml


here = pathlib.Path(__file__).resolve().parent
config = toml.load(here / "spectrum_logger.toml")

spec = yaqc.Client(config["yaq_port"])
sl =slice(20, None, None)

wl = spec.get_mappings()["wavelengths"][sl]
wl = 1e7 / wl

fig = plt.figure()
gs = gridspec.GridSpec(2, 1, height_ratios=[10, 1])

ax = plt.subplot(gs[0])
hl, = plt.plot(wl, spec.get_measured()["intensities"][sl])

plt.ylim(-100, 4096)


def update_line(y):
    hl.set_ydata(y)
    plt.draw()


def data_gen():
    index = 0
    while True:
        new_index = spec.get_measurement_id()
        if index < new_index:
            index = new_index
            measured = spec.get_measured()["intensities"][sl]
            yield measured
        else:
            time.sleep(0.1)


ax = plt.subplot(gs[1])
slider = Slider(ax, "integration time", 3000, 1e6, valinit=spec.get_integration_time_micros())
slider.on_changed(spec.set_integration_time_micros)

# run animation
ani = animation.FuncAnimation(fig, update_line, data_gen, interval=100, )
plt.show()