"""ocean optics script from fs table"""


import numpy as np
import yaqc
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider, CheckButtons
import tomllib as toml
import pathlib


# plt.style.use("dark_background")
config_filepath = pathlib.Path().expanduser() / "homie-logging" / "show-spectrum.toml"


def main():
    config = toml.load(config_filepath.open("rb"))

    fig, (ax, opt1, opt2, opt3) = plt.subplots(nrows=4, height_ratios=[10, 1, 1, 1], layout="tight")
    fig.canvas.manager.set_window_title("Tsunami")

    slice_args = [config["slice"].pop(k, None) for k in ["start", "stop", "step"]]
    sl = slice(*slice_args)

    spec = yaqc.Client(config["yaq"]["spec_port"])

    state = {
        "current" : 0,
        "next" : 0
    }

    wl = spec.get_mappings()["wavelengths"]
    wl = 1e7 / wl
    init = spec.get_measured()
    if "mean" in init.keys():
        y0 = init["mean"]
        ymin = init["min"]
        ymax = init["max"]
    else:
        y0 = [0] * wl.size
        ymin = [-1] * wl.size
        ymax = [1] * wl.size

    l, = ax.plot(wl[sl], spec.get_measured()["mean"][sl], lw=2)
    ref_path = config["reference"].get("path", None)
    if ref_path:
        ref_x, ref_y = np.genfromtxt(
            ref_path,
            unpack=True,
            skip_header=14,
            skip_footer=1
        )
        ref_y *= config["reference"]["scalar"] / ref_y.max()
        ax.plot(1e7/ref_x, ref_y, ls='--', linewidth=2)

    ax.grid()
    ax.set_ylim(-100, 4096)

    integration = Slider(opt1, "integration time", 3000, 1e6, valinit=spec.get_integration_time_micros())
    acquisition = Slider(opt2, "acquisitions (2^x)", 0, 8, valinit=int(np.log2(spec.get_acquisitions())), valstep=1)
    measure_button = CheckButtons(opt3, labels=["call measure"], label_props=dict(fontsize=[20]))

    def update_line(ydata:dict):
        l.set_ydata(ydata["mean"][sl])
        if ax.collections:
            ax.collections[0].remove()
        if int(acquisition.val) > 0:
            ax.fill_between(wl[sl], ydata["min"][sl], ydata["max"][sl], alpha=0.5, color="cyan")
        ax.relim()
        ax.autoscale_view()
        fig.canvas.draw_idle()

    def submit(measure=False, button=measure_button):
        try:
            if "call measure" in button.get_checked_labels() \
                or measure:
                    if state["current"] >= state["next"]:
                        state["next"] = spec.measure()
            measured = spec.get_measured()
            state["current"] = measured["measurement_id"]
            update_line(measured)
        except ConnectionError:
            pass

    submit(measure=True)
    timer = fig.canvas.new_timer(interval=100)

    @timer.add_callback
    def update():
        submit()

    def update_integration_time(arg):
        spec.set_integration_time_micros(arg)

    def update_acquisition(arg):
        spec.set_acquisitions(2**arg)


    integration.on_changed(update_integration_time)
    acquisition.on_changed(update_acquisition)

    timer.start()
    plt.show()


if __name__ == "__main__":
    main()