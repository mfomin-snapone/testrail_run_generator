#!/usr/bin/env python3

# Author: Michael Kredt <mkredt@control4.com>

# Import Statements
import logging
import os
import re
from configparser import ConfigParser

logger = logging.getLogger('relaytemp')


class RelayTemperatureCfg(ConfigParser):
    base_filename = 'relaytemp'
    """:type: str
    Base filename of all relay and temperature control board configuration files, if not provided
    """

    relay_info_pattern = re.compile('r_[a-zA-Z0-9_]+', re.IGNORECASE)
    temp_sens_info_pattern = re.compile('ts_[a-zA-Z0-9_]+', re.IGNORECASE)

    @property
    def file_path(self):
        return self._file_path

    @file_path.setter
    def file_path(self, value: str):
        self._file_path = self.make_file_name(value, self.base_filename)

    def __init__(self, file_path: str, instance_num: int = 0):
        """
        :param file_path: Path to file, if file name itself is omitted then the default name will be used
        :param instance_num: This integer value denotes which configuration file will be read to setup the relay and
        temperature board object and its accompanying objects
        """
        logger.debug('Loading config file: {}, inst: {}'.format(file_path, instance_num))
        super().__init__()
        self._file_path = self.make_file_name(file_path)
        self.instance_num = instance_num

    @classmethod
    def make_file_name(cls, path: str, file_name: str = '', iteration: int = 0):
        file_path = ''
        if not file_name:
            file_name = 'relaytempboard.cfg'
        if os.path.isdir(path):
            file_path = os.path.join(path, file_name)
        elif os.path.isfile(path):
            file_path = path
        if file_path.endswith('.cfg'):
            file_path = file_path[:-4]
        return '{}{}.cfg'.format(file_path, iteration if iteration else '')

    def load_devices(self):
        """
        Performs a load of information for the relay and temperature board

        :return:
        """
        logger.debug('Loading devices')
        if not os.path.exists(self.file_path):
            raise FileNotFoundError('"{}" does not exist'.format(self.file_path))

        relay_info = {}
        temp_sens_info = {}

        # Setup the configuration object from which we will pull configuration data
        self.read_file(open(self.file_path))

        for section in self.sections():
            # Assign boolean values which determine if the pattern matches the section header
            rp = self.relay_info_pattern.match(section)
            tsp = self.temp_sens_info_pattern.match(section)

            # If section name matches the linkbone information pattern, add to associated list
            if rp:
                alias = str(section)
                bus_id = int(self.get(section, 'bus_id'), 16)
                pin_id = int(self.get(section, 'pin_id'))
                relay_info[alias] = {'bus_id': bus_id, 'pin_id': pin_id}
            if tsp:
                alias = str(section)
                sens_id = str(self.get(section, 'sensor_id'))
                temp_sens_info[alias] = {'sensor_id': sens_id}
        return relay_info, temp_sens_info


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    rtb = RelayTemperatureCfg('/home/c4/')
