import time
import logging
import pathlib
import tomllib as toml

from . import device_lib as lib


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

here = pathlib.Path(__file__).resolve().parent
config_filepath = pathlib.Path.home() / "homie-logging" / "mqtt-publish.toml"
config = toml.load(config_filepath.open("rb"))
wait = config["device"].pop("wait", 15)


def main():
    while True:
        khz_system = lib.Upstream_Device(config)
        hour = time.localtime(time.time()).tm_hour
        # restart every hour
        while hour == time.localtime(time.time()).tm_hour:
            khz_system.update()
            time.sleep(wait)


if __name__ == '__main__':
    try:
        main()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Quitting.")