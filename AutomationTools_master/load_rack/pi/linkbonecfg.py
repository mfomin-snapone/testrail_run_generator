#!/usr/bin/env python3

# Author: Michael Kredt <mkredt@control4.com>

# Import Statements
import logging
import os
import re
from configparser import ConfigParser

logger = logging.getLogger('pqa_logger')


class LinkboneCfg(ConfigParser):
    base_filename = 'linkbone'
    """:type: str
    Base filename of all linkbone configuration files, if not provided
    """
    linkbone_info_pattern = re.compile('linkbone(/d?)', re.IGNORECASE)

    @property
    def file_path(self):
        return self._file_path

    @file_path.setter
    def file_path(self, value: str):
        self._file_path = self.make_file_name(value, self.base_filename)

    def __init__(self, file_path: str, instance_num: int = 0):
        """
        :param file_path: Path to file, if file name itself is omitted then the default name will be used
        :param instance_num: This integer value denotes which configuration file will be read to setup the linkbone
        object and its accompanying objects
        """
        logger.debug('Loading config file: {}/{}, inst: {}'.format(file_path, self.base_filename, instance_num))
        super().__init__()
        self._file_path = self.make_file_name(file_path)
        self.instance_num = instance_num

    @classmethod
    def make_file_name(cls, path: str, file_name: str = '', iteration: int = 0):
        file_path = ''
        if not file_name:
            file_name = 'linkbone.cfg'
        if os.path.isdir(path):
            file_path = os.path.join(path, file_name)
        elif os.path.isfile(path):
            file_path = path
        if file_path.endswith('.cfg'):
            file_path = file_path[:-4]
        return '{}{}.cfg'.format(file_path, iteration if iteration else '')

    def load_devices(self):
        """
        Performs a load of information for the linkbone device(s) -- despite one per system is generally the use case

        :return:
        """
        logger.debug('Loading devices')
        if not os.path.exists(self.file_path):
            raise FileNotFoundError('"{}" does not exist'.format(self.file_path))

        ip_address = None
        ip_port = None
        comm_type = None

        # Setup the configuration object from which we will pull configuration data
        self.read_file(open(self.file_path))

        for section in self.sections():
            logger.debug("Section: {}".format(section))
            # Assign boolean values which determine if the pattern matches the section header
            # If section name matches the linkbone information pattern, add to associated list

            ip_address = str(self.get(section, 'ip'))
            ip_port = str(self.get(section, 'port'))
            comm_type = str(self.get(section, 'type'))
        return ip_address, ip_port, comm_type


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    lb = LinkboneCfg('/home/c4/')
