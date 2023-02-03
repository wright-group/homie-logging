
import time
import logging
import pathlib
import toml
import device_lib as lib


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

here = pathlib.Path(__file__).resolve().parent
config = toml.load(here / "wright-upstream-0.toml")
wait = config["device"].pop("wait", 15)

khz_system = lib.Upstream_Device(config)


def main():
    while True:
        khz_system.update()
        time.sleep(wait)


if __name__ == '__main__':
    try:
        main()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Quitting.")