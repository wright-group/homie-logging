from homie.node.node_base import Node_Base
from homie.node.property.property_float import Property_Float
# from homie.node.property.property_boolean import Property_Boolean
from scipy.optimize import curve_fit

import yaqc
import time


def gauss(x, mu, std, amp):
    z = (x - mu) / (np.sqrt(2) * std)
    out = np.exp(-z**2)
    return amp * out


class YaqcNode(Node_Base):
    def __init__(self, dev, config):
        super().__init__(dev, *[config[k] for k in ["id", "name", "type"]])
        self.client = yaqc.Client(config["yaqc_port"])
        self.units = self.get_units()

        measured = self.get_measured()

        for k in self.units.keys():
            self.add_property(
                Property_Float(
                    self,
                    k.replace("_", "-"),
                    k,
                    settable=False,
                    unit=self.units[k], 
                    value=measured[k]
                )
            )

    def update(self):
        measured = self.get_measured()
        if len(measured) > 0:
            for k in self.units.keys():
                self.set_property_value(k.replace("_", "-"), measured[k])

    def get_units(self):
        ...

    def get_measured(self):
        ...


class Millennia(YaqcNode):

    def get_units(self):
        return self.client.get_channel_units()

    def get_measured(self):
        self.client.measure()
        while True:
            time.sleep(0.1)
            if not self.client.busy():
                break
        return self.client.get_measured()


class Tsunami(YaqcNode):
    units = {
        "amp": "# MHz",
        "mu": "cm-1",
        "area": "# cm-1 MHz",
        "fwhm": "cm-1",
        "ier": None,
        "rms": None,
        "relative-amp": None,
        "relative-mu": None,
        "relative-area": None,
        "relative-fwhm": None,
        "relative-rms": None,
    }

    def __init__(self, dev, config):
        self.create_reference(config["reference_path"])
        # self.client.measure(True)  # ensure looping is on
        super().__init__(self, dev, config)

    def get_units(self):
        return self.units

    def get_measured(self) -> dict:
        nm = self.client.get_mappings()["wavelengths"]
        y = self.client.get_measured()["intensities"]

        self.time_us = self.client.get_integration_time_micros()

        p_out = self._fit_gauss(nm, y / self.time_us)
        p_out |= {
            f"relative-{k}": p_abs[k] / self.reference[k] \
                for k in p_abs.keys() if k not in ["ier"]
        }
        return p_out

    def _fit_gauss(self, nm, y):
        p0 = [x[np.argmax(y)], 350., y.max()]
        inds = [np.argmin(np.abs(nm-725)), np.argmin(np.abs(nm-875))]
        sl = slice(min(inds), max(inds), None)
        x = 1e7 / nm[sl]
        try:
            p, cov, infodict, mesg, ier = curve_fit(gauss, x, y[sl], *p0, full_output=True)
        except Exception as e:
            logging.getLogger(__name__).error(e)
            return {}
        rms = ((gauss(x, p) - y[sl])**2).sum()
        rms /= x.size
        rms **= 0.5

        return dict(
            mu = p[0],
            fwhm = p[1] * 2.35,
            amp = p[2] / time,
            area = np.sum(y) / time,
            rms = rms / time,
            ier = ier,
        )

    def create_reference(self, path):
        x, y = np.loadtxt(config["reference_path"], unpack=True)
        self.reference = self._fit_gauss(self, 1e7 / x, y / config["reference_time"])
        logging.getLogger(__name__).info(self.reference)

