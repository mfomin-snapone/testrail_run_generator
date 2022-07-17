from enum import IntEnum

from .din_load_bank import DinLoadBank
from .din_module import DinModule, MatrixEnum, log_state


class DinBus(DinModule):
    """
    An object which describes a DinBus

    Creates a bus object which will be used by the matrix to enable and disable operable buses
    """

    def setup_relays(self):
        pass

    def __init__(self, alias: str, ip_addr: str, mac_addr: str, load_type: str, num_loads: int):
        """
        Init for DinBus

        :param alias:
        :param ip_addr:
        :param mac_addr:
        """

        super(DinBus, self).__init__(alias, ip_addr, mac_addr)

        self.load_type = load_type
        self.relay_list = {}

        bus_index = int(self.alias[-1])
        self.load_bank_din = DinLoadBank('dinloadbank{}'.format(bus_index), ip_addr, mac_addr, num_loads)

        # self.setup_relays()

        self.bus_status = MatrixEnum.OFF

        log_state(bus_name=alias, bus_state=str(self.get_bus_state()), message='DinBus Device Created')

    def enable_bus(self, loadbank_channel: int) -> IntEnum:
        """
        Enables the bus and forwards the channel specified in the parameters

        :param loadbank_channel: The loadbank channel we wish to forward through the bus
        :return:
        """

        # Check for valid parameter data types
        assert isinstance(loadbank_channel, int)

        # Disable all relays before enabling the desired relay
        with self.din_lock:
            for rel in self.relay_list:
                self.relay_list[rel].set_state(self.relay_list[rel].OFF)

            # Enable the desired relay and set the bus status as ON
            rel_str = 'r{}'.format(loadbank_channel)
            self.relay_list[rel_str].set_state(self.relay_list[rel_str].ON)
            self.bus_status = MatrixEnum.ON

            return MatrixEnum.ON

    def disable_bus(self) -> IntEnum:
        """
        Disables all relays associated with the bus

        :return:
        """

        # Disable all relays
        with self.din_lock:
            for rel in self.relay_list:
                self.relay_list[rel].set_state(self.relay_list[rel].OFF)

            # Set bus status as OFF
            self.bus_status = MatrixEnum.OFF

            return MatrixEnum.OFF

    def get_bus_state(self):
        """
        Returns the state of the bus

        :return bus_status:
        """
        return self.bus_status

    def get_bus_relay_list(self):
        """
        Return relay_list

        :return:
        """

        return self.relay_list

    def get_load_bank_din(self):
        """
        Returns load_bank_din

        :return:
        """

        return self.load_bank_din


