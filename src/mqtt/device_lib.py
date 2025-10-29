from homie.device_base import Device_Base
from . import node_lib as node


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
            node.Millennia(
                self,
                config["millennia"]
            )
        )

        self.add_node(
            node.Tsunami(
                self,
                config["tsunami"]
            )
        )

        self.start()

    def update(self):
        for node in self.nodes.values():
            node.update()
