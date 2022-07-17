#!/usr/bin/python3
# File has been converted to Python3 from Python2 using 2to3 tool

import socket
import logging.handlers

from .din_matrix.dinmatrixcfg import DinCfg
from .din_matrix.din_module import DinModule
from .din_matrix.din_bus import DinBus
from .mibmanager import MibManager

log_name = '/tmp/pqa.log'
logger = logging.getLogger('pqa_logger')
logger_handler = logging.handlers.RotatingFileHandler(log_name, maxBytes=100000, backupCount=5)
formatter = logging.Formatter('%(asctime)s %(levelname)s %(module)s Line:%(lineno)d %(message)s')
logger_handler.setFormatter(formatter)
logger.addHandler(logger_handler)

logger.info("Start PI Logging")


CFG_FILE_PATH = '/etc/default'
SWITCHLEG_GPIO = 5
GPIO_DUT_PWR = 3
SERVER_PORT = 8750


def set_devices(self: MibManager, matrix_devices: list, bus_devices: list):
    """
    Sets both matrix and bus devices to supplied lists.  These will remove all old items and replace them with the
    new ones.
    :param matrix_devices: list of parameters for new devices
    :param bus_devices: list of parameters for new bus devices
    """
    self.matrix_din_devices.clear()
    self.bus_din_devices.clear()
    for alias, ip_addr, mac_addr in matrix_devices:
        self.matrix_din_devices[alias] = DinModule(alias, ip_addr, mac_addr)
    for alias, ip_addr, mac_addr, load_type, num_loads in bus_devices:
        self.bus_din_devices[alias] = DinBus(alias, ip_addr, mac_addr, load_type, num_loads)


def main():
    # Setup and receive information from server configuration files
    dcfg = DinCfg(CFG_FILE_PATH)
    matrix_dev, bus_dev = dcfg.load_devices()

    # A UDP server
    # Set up a UDP server
    logger.debug('Setting up UDP server')
    udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # Listen on port 21567
    # (to all IP addresses on this system)
    listen_address = ("", SERVER_PORT)
    udp_sock.bind(listen_address)

    # Report on all data packets received and
    # where they came from in each case (as this is
    # UDP, each may be from a different source and it's
    # up to the server to sort this out!)
    logger.debug('Loading MibManager')
    mib_pi = MibManager(udp_sock, SWITCHLEG_GPIO, GPIO_DUT_PWR)
    mib_pi.set_devices(matrix_dev, bus_dev)
    logger.debug('Waiting for input on port {}...'.format(SERVER_PORT))
    while True:
        data, address = udp_sock.recvfrom(1024)
        assert isinstance(data, bytes)
        mib_pi.incoming_mib(data.decode(), address, 8750)
    # print data.strip(),addr


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    main()
