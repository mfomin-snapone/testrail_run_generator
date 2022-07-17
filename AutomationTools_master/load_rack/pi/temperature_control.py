#!/usr/bin/env python3
import logging
from ast import literal_eval
from time import sleep
from numpy import array
from threading import Thread, Lock
from typing import Dict, List

from c4common.hw_tools.relay import RelayRp, relay_factory
from c4common.hw_tools.temp_sensor import TempSensorDS18B20 as TempSensor, TemperatureUnits

logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)

rack_id = 0


class Rack:
    def __init__(self, unit: TemperatureUnits, fan: RelayRp, temperature_sensors: Dict[str, TempSensor], name: str = None):
        """
        A Rack contains a fan that is triggered by any one of it's temperature sensors
        :param fan: An object returned from relay_factory() to control the rack fan
        :param name: A unique Identifier for this rack
        :param temperature_sensors: A list of temperature sensors in the rack
        """
        self._lock = Lock()
        self.temperature_sensors = temperature_sensors
        self.fan = fan
        self.name = name
        self.unit = unit
        # Assign a unique name to this rack if none was provided
        if name is None:
            global rack_id
            self.name = "Rack {}".format(rack_id)
            rack_id += 1
        logger.debug("Initialized Rack: {}".format(self.name))

    def poll_temperature(self) -> array:
        """
        :return: A numpy array of all the temperature sensor values in the rack
        """
        with self._lock:
            raw_data = array([t.get_temp(scale=self.unit.name.lower()) for t in self.temperature_sensors.values()])
            logger.debug("{}: Temperature Sensor: {}".format(self.name, raw_data))
            return raw_data

    def set_fan(self, state: str):
        """
        Set the power state of the fan
        :param state: on, off, or toggle
        """

        with self._lock:
            if state.lower() == "on":
                if not self.fan.get_state() == self.fan.ON:
                    logger.debug("{} Fan on".format(self.name))
                    self.fan.turn_on()
            elif state.lower() == "off":
                if not self.fan.get_state() == self.fan.OFF:
                    logger.debug("{} Fan off".format(self.name))
                    self.fan.turn_off()
            elif state.lower() == "toggle":
                self.fan.toggle()
                logger.debug("{} Fan {}".format(
                    self.name, 'toggled' + ('on' if self.fan.get_state() is self.fan.ON else 'off'))
                )
            else:
                logger.error("Unknown fan power state {}".format(state))


class TemperatureControl(Thread):
    """
    Monitors all of the racks and activates/deactivates fans based on their temperatures
    """

    def __init__(self, racks: List[Rack], max_temp: int = 120, average_temp: int = 100, check_rate: int = 20):
        """
        :param racks: A list of rack objects
        :param max_temp:  the temperature trigger for the max value of sensors
        :param average_temp: The temperature trigger for the average values of sensors
        :param check_rate: The number of seconds between polling of the sensors
        """
        Thread.__init__(self)
        self.rack_lock = Lock()
        self.racks = racks
        self.max_temperature = max_temp
        self.average_temperature = average_temp
        self.check_rate = check_rate

    def run(self):
        logger.info("Started Temperature Control Thread")
        while True:
            for rack in self.racks:
                temperature = rack.poll_temperature()
                if temperature.max() >= self.max_temperature:
                    logger.debug("A single fan has reached a high temperature of {} degrees".format(temperature.max()))
                    rack.set_fan('on')
                elif temperature.mean() >= self.average_temperature:
                    logger.debug("The average temperature of the rack {} is too high".format(temperature.mean()))
                    rack.set_fan('on')
                else:
                    rack.set_fan('off')
                sleep(self.check_rate)


if __name__ == "__main__":
    from c4common.configuration import Parameter, DebugLevel, Parser

    options = [
        # Debugging
        Parameter("-d", "--debug", type=DebugLevel, default=DebugLevel.INFO, group="Debugging",
                  help="Logging debug level: {}. Default is 'INFO'".format(", ".join([d.name for d in DebugLevel]))),
        # Temperature Control
        Parameter("-u", "--temperature-unit", type=TemperatureUnits, default=TemperatureUnits.F, group="Temperature",
                  help="The unit to use for temperature.  {}".join(t.name for t in TemperatureUnits)),
        Parameter("-M", "--max-temperature", type=int, default=120, group="Temperature",
                  help="The maximum temperature a single sensor must reach to turn on a rack fan"),
        Parameter("-A", "--average-temperature", type=int, default=100, group="Temperature",
                  help="The temperature the average of all sensors much reach to turn on a rack fan"),
        Parameter("-R", "--check-rate", type=int, default=10, group="Temperature",
                  help="The number of seconds between sensor polls")
    ]

    # Parse config file
    cfg = Parser(options, config_file="temperature_control.cfg", default_section="main", save_cfg_parser=True)
    logger.setLevel(cfg.debug.value)
    logger.debug(cfg)

    # Generate rack objects from config file
    rack_cfg = cfg.cfg
    main_racks = list()
    # Create Racks based on section names
    for section in cfg.cfg.sections():

        # Look at only sections that have "rack" in the name
        if 'rack' not in section.lower():
            logger.debug("Ignoring section '{}'".format(section))
            continue

        logger.debug("Creating Rack from section '{}'".format(section))
        sensors = dict()
        cfg_sensors = literal_eval(rack_cfg.get(section, 'temperature_sensors'))
        assert isinstance(cfg_sensors, dict)
        for sensor_name, parameters in cfg_sensors.items():
            logger.debug("Creating Sensor: {}".format(sensor_name))
            logger.debug("Sensor Parameters: {}".format(parameters))
            sensors[sensor_name] = TempSensor(**parameters)

        # Add the rack to the list
        main_racks.append(Rack(
            unit=cfg.temperature_unit,
            name=section,
            fan=relay_factory(**literal_eval(rack_cfg.get(section, 'fan'))),
            temperature_sensors=sensors
        ))

    # Create the controller class and run it until CTRL-C
    controller = TemperatureControl(
        main_racks, max_temp=cfg.max_temperature, average_temp=cfg.average_temperature, check_rate=cfg.check_rate
    )
    controller.run()
    controller.join()
