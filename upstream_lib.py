from homie.device_base import Device_Base
from homie.node.node_base import Node_Base
from homie.node.property.property_float import Property_Float
import yaqc
import logging
import time
import numpy as np
from scipy.optimize import curve_fit


class Upstream_Device(Device_Base):
    def __init__(
        self,
        config,
    ):
        device_id = config["device"]["device_id"]
        device_name = config["device"]["device_name"]

        super().__init__(
            device_id,
            device_name,
            homie_settings = config["homie"],
            mqtt_settings = config["mqtt"])


        self.add_node(
            Millennia(
                self,
                config["millennia"]
            )
        )

        self.add_node(
            Tsunami(
                self,
                config["tsunami"]
            )
        )

        self.start()

    def update(self):
        for node in self.nodes.values():
            node.update()


class Millennia(Node_Base):
    def __init__(
        self,
        dev,
        config
    ):
        super().__init__(dev, *[config[k] for k in ["id", "name", "type"]])
        self.client = yaqc.Client(config["yaqc_port"])
        self.units = self.client.get_channel_units()

        measured = self._measure_and_get()

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
        measured = self._measure_and_get()
        for k in self.units.keys():
            self.set_property_value(k.replace("_", "-"), measured[k])
        self.publish_properties()

    def _measure_and_get(self):
        self.client.measure()
        while True:
            time.sleep(0.1)
            if not self.client.busy():
                break
        return self.client.get_measured()


def gauss(x, mu, std, amp):
    z = (x - mu) / (np.sqrt(2) * std)
    out = np.exp(-z**2)
    return amp * out


class Tsunami(Node_Base):
    def __init__(
        self,
        dev,
        config
    ):
        super().__init__(dev, *[config[k] for k in ["id", "name", "type"]])
        self.client = yaqc.Client(config["yaqc_port"])
        self.acquisition_time = None
        measured = self._get()
        if len(measured) == 0:
            raise ValueError
        self.units = dict(amp="#", mu="cm-1", fwhm="cm-1", ier=None)
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
        measured = self._get()
        if len(measured) > 0:
            for k in self.units.keys():
                self.set_property_value(k.replace("_", "-"), measured[k])
            self.publish_properties()

    def _get(self) -> dict:
        nm = self.client.get_mappings()["wavelengths"]
        y = self.client.get_measured()["intensities"]
        time_us = self.client.get_integration_time_micros()
        inds = [np.argmin(np.abs(nm-725)), np.argmin(np.abs(nm-875))]
        sl = slice(min(inds), max(inds), None)

        p0 = [x[np.argmax(y)], 200., y.max()]

        try:
            p, cov, infodict, mesg, ier = curve_fit(gauss, 1e7 / nm[sl], y[sl], *p0, full_output=True)
        except Exception as e:
            logging.getLogger(__name__).error(e)
            return {}

        return dict(
            mu = p[0],
            fwhm = p[1] * 2.35,
            amp = p[2] / time_us,
            ier = ier
        )
