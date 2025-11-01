# homie-logging

Package to be deployed on monitor computer for upstream ps/fs laser components (Millennia, Tsunami).

Millennia is a `scpi-sensor` daemon.
Tsunami is a `yaqd-ocean-optics` daemon.

Publishes laser vitals to mqtt network.
Includes simple gui for monitoring Tsunami spectrum.
 
## setup
from local folder:
```
pip install -e .
```
Put config files `show-spectrum.toml` and `mqtt-publish.toml` in directory `~/homie-logging`.
Config templates are provided  (`.\config-templates`).

## usage (cli)
* Run logging: `mqtt-publish`
* Run spec gui: `show-spectrum`
