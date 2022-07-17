from enum import IntEnum
from threading import Lock
import logging

logger = logging.getLogger(__name__)


def log_state(bus_name: str = '', bus_state: str = '', dut_ch_name: str = '', dut_ch_state: str = '', message: str = '',
              level=logging.DEBUG):
    logger.log(level, 'bus_name={}, bus_state={}, dut_ch_name={}, dut_ch_state={}, message={}'.format(
        bus_name, bus_state, dut_ch_name, dut_ch_state, message))


class MatrixEnum(IntEnum):
    # On Off Status
    OFF = 0
    ON = 1

    # Load Types
    LOAD_TYPE_TEN_VOLT = 10
    LOAD_TYPE_INCANDESCENT = 11
    LOAD_TYPE_LED = 12
    LOAD_TYPE_ELV = 13
    LOAD_TYPE_FAN = 14
    LOAD_TYPE_MLV = 15
    LOAD_TYPE_CFL = 16
    LOAD_TYPE_FLUORESCENT = 17

    # Matrix Path Status Codes
    NO_PATH_CHANGE = 20
    BOTH_CHANNEL_CHANGE = 21
    INPUT_CHANNEL_CHANGE = 22
    LOADBANK_CHANNEL_CHANGE = 23
    NEW_PATH_CHANGE = 24


class DinModule:
    """
    An object which describes a DinRail.

    Creates a bus object which will be used by the matrix to enable and disable operable buses
    """

    @property
    def alias(self) -> str:
        """
        Return alias of the bus object
        """
        return self._alias

    @property
    def ip_addr(self) -> str:
        """
        Return IP address of the bus object
        """

        return self._ip_addr

    @property
    def mac_addr(self) -> str:
        """
        Return MAC address of the bus object

        :return:
        """

        return self._ip_addr

    def __init__(self, alias: str, ip_addr: str, mac_addr: str):
        """
        Init for DinModule

        :param alias:
        :param ip_addr:
        :param mac_addr:
        """

        self._alias = alias
        self._ip_addr = ip_addr
        self._mac_addr = mac_addr

        self.din_lock = Lock()

    def setup_relays(self):
        """
        Used to set up the relays, MUST be used in
        overridden class
        """
        raise NotImplementedError()

