"""
Handle and configure the DIN Matrix config file
"""
import logging
import os
import re
from configparser import ConfigParser

logger = logging.getLogger('dinmatrix')


class DinCfg(ConfigParser):
    base_filename = 'dinmatrix'
    """ :type: str
    Base filename of all matrix configuration files, if not provided
    """
    # Use cfg file and name patterns to populate DUT channel and load bus (DinBus) dictionaries
    matrix_din_pattern = re.compile('dinmatrix(\d+)', re.IGNORECASE)
    load_bus_din_pattern = re.compile('dinbus(\d+)', re.IGNORECASE)

    @property
    def file_path(self):
        return self._file_path

    @file_path.setter
    def file_path(self, value: str):
        self._file_path = self.make_file_name(value, self.base_filename, self.instance_num)

    def __init__(self, file_path: str, instance_num: int = 0):
        """
        :param file_path: Path to file, if file name itself is omitted then the default name will be used
        :param instance_num: This integer value denotes which configuration file will be read to setup the DinMatrix
        object and its accompanying objects
        """
        logger.debug('Loading config file: {}, inst: {}'.format(file_path, instance_num))
        super().__init__()
        self._file_path = self.make_file_name(file_path)
        self.instance_num = instance_num

    @classmethod
    def make_file_name(cls, path: str, file_name: str='', iteration: int=0):
        file_path = ''
        if not file_name:
            file_name = 'dinmatrix.cfg'
        if os.path.isdir(path):
            file_path = os.path.join(path, file_name)
        elif os.path.isfile(path):
            file_path = path
        if file_path.endswith('.cfg'):
            file_path = file_path[:-4]
        return '{}{}.cfg'.format(file_path, iteration if iteration else '')

    def load_devices(self):
        """
        Performs a setup of initial DIN objects for the DinMatrix. The number of entries which will be inserted into the
        matrix and load bus dictionaries is dynamic as per the section entries provided in the configuration file.

        :return:
        """
        logger.debug('Loading devices')
        if not os.path.exists(self.file_path):
            raise FileNotFoundError('"{}" does not exist'.format(self.file_path))

        matrix_din_devices = []
        bus_din_devices = []

        # Setup the configuration object from which we will pull configuration data
        self.read_file(open(self.file_path))

        for section in self.sections():
            # Assign boolean values which determine if the pattern matches the section header
            mdp = self.matrix_din_pattern.match(section)
            lbdp = self.load_bus_din_pattern.match(section)

            # If section name matches either matrix or bus pattern (from above), add to associated dictionary
            if mdp:
                alias = str(section)
                ip_addr = self.get(section, 'ip')
                mac_addr = self.get(section, 'mac')
                matrix_din_devices.append([alias, ip_addr, mac_addr])
            elif lbdp:
                alias = str(section)
                ip_addr = self.get(section, 'ip')
                mac_addr = self.get(section, 'mac')
                load_type = self.get(section, 'loadtype')
                num_loads = self.getint(section, 'numloads')
                bus_din_devices.append([alias, ip_addr, mac_addr, load_type, num_loads])
        return matrix_din_devices, bus_din_devices


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    d = DinCfg('/home/c4/')
