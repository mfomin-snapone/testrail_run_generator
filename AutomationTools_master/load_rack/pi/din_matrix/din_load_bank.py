import logging
from enum import IntEnum

from c4common.hw_tools import relay
from .din_module import DinModule, MatrixEnum

logger = logging.getLogger(__name__)


class DinLoadBank(DinModule):
    """
    An object which describes a DinLoadBank

    Creates a din module which interfaces relays associated with the load type
    """

    @property
    def load_relay_list(self) -> dict:
        """
        Return relay_list
        """

        return self._relay_list

    def __init__(self, alias: str, ip_addr: str, mac_addr: str, num_loads: int):
        """
        Init for DinBus

        :param alias:
        :param ip_addr:
        :param mac_addr:
        """

        super(DinLoadBank, self).__init__(alias, ip_addr, mac_addr)

        self.num_loads = num_loads
        self._relay_list = {}

        self.setup_relays()

        logger.debug('DinLoadBus Device Created')

    @staticmethod
    def relay_counter():
        """
        A generator which will produce alias strings for relays being generated. Counting is arbitrary and based upon
        the current model of the C4-DIN-8REL-E device.

        :return:
        """

        while True:
            for i in range(0, 8):
                yield ('r{}'.format(i))

    def setup_relays(self):
        # Assign values from the relay generator object to this variable
        relay_gen = self.relay_counter()

        # Add all relays of this Din device to a dictionary
        for i in range(0, self.num_loads):
            alias = next(relay_gen)
            self._relay_list[alias] = relay.relay_factory(r_type='dinrail', ipaddr=self.ip_addr, relayid=i)
            self._relay_list[alias].set_state(self._relay_list[alias].OFF)

    def set_load_state(self, load_channel: int, on_off: IntEnum) -> IntEnum:
        """
        Enables or disables the load specified by parameter

        :param load_channel:
        :param on_off:
        :return:
        """

        assert isinstance(load_channel, int)
        assert isinstance(on_off, MatrixEnum)

        with self.din_lock:
            if on_off is MatrixEnum.ON:
                self._relay_list['r{}'.format(load_channel)].set_state(self._relay_list['r{}'.format(load_channel)].ON)
                return MatrixEnum.ON
            else:
                self._relay_list['r{}'.format(load_channel)].set_state(self._relay_list['r{}'.format(load_channel)].OFF)
                return MatrixEnum.OFF

    def get_load_state(self, load_channel: int):
        """
        Return the state of the relay of the channel provided

        :param load_channel: The load bank for which we desire to obtain state
        :return relay_state: The status of the relay (load bank), whether on or off
        """
        return self._relay_list['r{}'.format(load_channel)].get_state()

