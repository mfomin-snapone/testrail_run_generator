"""
DinRail Matrix

Created By: Michael Kredt
Created On: 29 November 2017

This code is being developed in conjunction with other modules to assist in the automation of load testing for different
lighting products. The devices this code controls are DinRail Relay (C4-DIN-8REL-E or -E2 if you've got the $$$ in the
future) modules which control the matrix and handle the load banks. This device and the code associated do not represent
a true matrix device. The reason we cannot do this is because we are testing 8 different load types. Were we to mix
these load types in a true matrix, we would likely experience issues and probably blow out equipment.

The device is therefore a limited matrix, with a 1:1 assignment from DUT channel to matrix bus as opposed to a 1:N
(1:8 in reality, unless future models of the DinRail Relay, C4-DIN-8REL-E or E2 or later, have more than 8 outputs).
This code is developed with the intent of having a full 8x8 device setup (8 DinRail Relays for switching, 8 DinRail
Relays for load banks) but is capable of handling more or less than 8 channels per DinRail Relay. Should product
specifications change, this code will hopefully not need modification.
"""

# Import Statements
import logging
import re
from enum import IntEnum
from c4common.hw_tools import relay
from c4common.utils.c4_loggers.csv_logger import CsvLogger
from c4common.utils.c4_loggers.csv_logger import HeaderItem
from .din_load_bank import DinLoadBank
from .din_bus import DinBus
from .din_module import DinModule, MatrixEnum

logger = logging.getLogger(__name__)


# Module Defined Variables


class DinMatrix:
    """
    A matrix (limited operation) device which is constructed from DinRail RelayCmd modules.

    Creates buses and relay objects which will allow for control of the NxN matrix device.
    """

    @property
    def matrix_din_devices(self) -> dict:
        return self._matrix_din_devices

    @matrix_din_devices.setter
    def matrix_din_devices(self, value: list):
        if self._matrix_din_devices:
            self._matrix_din_devices.clear()

        self._matrix_din_devices = value
        for dev in self._matrix_din_devices:
            assert isinstance(dev, DinModule)
            dev.setup_relays()

    @property
    def bus_din_devices(self) -> dict:
        return self._bus_din_devices

    @bus_din_devices.setter
    def bus_din_devices(self, value: list):
        self._bus_din_devices = value
        for dev in self._bus_din_devices:
            assert isinstance(dev, DinModule)
            dev.setup_relays()

    def __init__(self, matrix_instance: int = 0):
        """
        Init for DinMatrix object

        :param matrix_instance:
        """
        self.active_matrix_paths = []
        self._matrix_din_devices = {}
        self._bus_din_devices = {}

        self.logger = log_setup(matrix_instance)
        # load_devices(matrix_instance)

        self.matrix_instance = matrix_instance
        logger.debug('Created DinMatrix')
    
    def get_matrix_path(self, input_channel):
        for x in self.active_matrix_paths:
            if x.startswith("path_{}".format(input_channel)):
                dummy, matrix, load = x.split("_")
                return "{:02X} {:02X}".format(int(matrix), int(load))
        return ""

    def set_matrix_path(self, input_channel: int, load_bank: int, load_mask: int = 0) -> IntEnum:
        """
        Given input information, determines how to setup a path between a lighting input channel and load bank

        :param input_channel: The channel of (or the) DUT which will be tested
        :param load_bank: The bank of loads which will be tested
        :param load_mask: The loads on the load bank which will be tested
        :return: An IntEnum representing the ON or OFF state of the path being modified; for unittest purposes only, is
        not used for other reasons
        """

        assert isinstance(input_channel, int)
        assert isinstance(load_bank, int)
        assert isinstance(load_mask, int)

        path_pattern = 'path_%s_%s'

        # Determine what change needs to be made to the matrix
        change_code = self._check_channels(input_channel, load_bank)
        if change_code[0] is MatrixEnum.NO_PATH_CHANGE:
            if load_mask:
                # Change which loads are active on the loadbank
                self.set_bus_loads(load_bank, load_mask)
                log_state(bus_name=str(load_bank), bus_state='on', dut_ch_name=str(input_channel),
                          dut_ch_state='on', message='Enabling loadbank with mask')
                print(self.active_matrix_paths)
                return MatrixEnum.ON
            else:
                # Disable and stop tracking the path since no loads are active on the load bank
                self.active_matrix_paths.remove(path_pattern % (input_channel, load_bank))
                self.bus_din_devices['dinbus{}'.format(load_bank)].disable_bus()
                self.set_bus_loads(load_bank, 0)
                log_state(bus_name=str(load_bank), bus_state='off', dut_ch_name=str(input_channel),
                          dut_ch_state='off', message='Disabling matrix bus channel and DUT channel')
                print(self.active_matrix_paths)
                return MatrixEnum.OFF
        elif change_code[0] is MatrixEnum.BOTH_CHANNEL_CHANGE:
            # Disable and stop tracking the path of the original input and output channel
            remove_input = change_code[1][0][1] if change_code[1][0][0] is MatrixEnum.INPUT_CHANNEL_CHANGE else\
                change_code[1][1][1]
            remove_loadbank = change_code[1][0][1] if change_code[1][0][0] is MatrixEnum.LOADBANK_CHANNEL_CHANGE else\
                change_code[1][1][1]
            self.active_matrix_paths.remove(path_pattern % (remove_input, load_bank))
            self.active_matrix_paths.remove(path_pattern % (input_channel, remove_loadbank))
            self.bus_din_devices['dinbus{}'.format(load_bank)].disable_bus()
            self.bus_din_devices['dinbus{}'.format(remove_loadbank)].disable_bus()

            # Enable and being tracking a new path
            self.active_matrix_paths.append(path_pattern % (input_channel, load_bank))
            self.bus_din_devices['dinbus{}'.format(load_bank)].enable_bus(input_channel)
            self.set_bus_loads(load_bank, load_mask)
            log_state(bus_name=str(load_bank), bus_state='on', dut_ch_name=str(input_channel),
                      dut_ch_state='on', message='Enabling input path to output channel')
            print(self.active_matrix_paths)
            return MatrixEnum.ON
        elif change_code[0] is MatrixEnum.INPUT_CHANNEL_CHANGE:
            # Disable and stop tracking the path of the original input channel
            self.active_matrix_paths.remove(path_pattern % (change_code[1], load_bank))
            self.bus_din_devices['dinbus{}'.format(load_bank)].disable_bus()

            # Enable and begin tracking the path of the new input channel
            self.active_matrix_paths.append(path_pattern % (input_channel, load_bank))
            self.bus_din_devices['dinbus{}'.format(load_bank)].enable_bus(input_channel)
            log_state(bus_name=str(load_bank), bus_state='on', dut_ch_name=str(input_channel),
                      dut_ch_state='on', message='Enabling loadbank with mask')
            print(self.active_matrix_paths)
            return MatrixEnum.ON
        elif change_code[0] is MatrixEnum.LOADBANK_CHANNEL_CHANGE:
            # Disable and stop tracking the path of the original load bank
            self.active_matrix_paths.remove(path_pattern % (input_channel, change_code[1]))
            self.bus_din_devices['dinbus{}'.format(change_code[1])].disable_bus()



            # Enable and begin tracking the path of the new load bank
            self.active_matrix_paths.append(path_pattern % (input_channel, load_bank))
            self.bus_din_devices['dinbus{}'.format(load_bank)].enable_bus(input_channel)
            self.set_bus_loads(load_bank, load_mask)
            log_state(bus_name=str(load_bank), bus_state='on', dut_ch_name=str(input_channel),
                      dut_ch_state='on', message='Enabling loadbank with mask')
            print(self.active_matrix_paths)
            return MatrixEnum.ON

        elif change_code[0] is MatrixEnum.NEW_PATH_CHANGE:
            # Enable and being tracking the path of a new input and load bank
            self.active_matrix_paths.append(path_pattern % (input_channel, load_bank))
            self.bus_din_devices['dinbus{}'.format(load_bank)].enable_bus(input_channel)
            self.set_bus_loads(load_bank, load_mask)
            log_state(bus_name=str(load_bank), bus_state='on', dut_ch_name=str(input_channel),
                      dut_ch_state='on', message='Enabling loadbank with mask')
            print(self.active_matrix_paths)
            return MatrixEnum.ON
        else:
            print(self.active_matrix_paths)
            raise Exception('Error, no valid change code found for matrix.')

    def add_matrix_device(self, alias, ip_addr, mac_addr):
        new_mod = DinModule(alias, ip_addr, mac_addr)
        self.matrix_din_devices[alias] = new_mod
        return new_mod

    def add_bus_device(self, alias, ip_addr, mac_addr, load_type, num_loads):
        new_bus = DinBus(alias, ip_addr, mac_addr, load_type, num_loads)
        self.bus_din_devices[alias] = new_bus
        self._set_matrix_din_relays(new_bus)
        return new_bus

    def set_bus_loads(self, matrix_bus: int, load_flag: int) -> bool:
        """
        Enables the loads of a particular bus in the DinMatrix. The function will be able to accept a single index, a
        list of indices, a bit mask as a bytes object, or a string representing a wattage value, to engage loads.

        :param matrix_bus: The bus (load type) we desire to enable or disable load banks
        :param load_flag: This parameter can take a value which will specify which relays on a specific matrix_bus
        (load type) will be enabled or disabled. Integers, a list of integers, bytes, or a string objects accepted.
        :return:
        """

        assert isinstance(matrix_bus, int)
        assert isinstance(load_flag, int)

        bus_str = 'dinbus{}'.format(matrix_bus)
        temp_bus_din = self.bus_din_devices[bus_str]
        temp_load_din = temp_bus_din.get_load_bank_din()
        temp_rel_list = temp_bus_din.get_bus_relay_list()

        for i in range(0, len(temp_rel_list)):
            if ((load_flag >> i) & 0x01) is 1:
                temp_load_din.set_load_state(i, MatrixEnum.ON)
            else:
                temp_load_din.set_load_state(i, MatrixEnum.OFF)

        return True

    def _check_channels(self, input_channel: int, loadbank_channel: int) -> tuple:
        """

        :param input_channel:
        :param loadbank_channel:
        :return: A tuple of the format (change_type, channel_num) which tells the matrix what change to make and
        what channel is being modified.
        """

        assert isinstance(input_channel, int)
        assert isinstance(loadbank_channel, int)

        # WORKING CODE
        # if enable:
        #     for path in self.active_matrix_paths:
        #         # Check first integer of bus path to ensure dut_channel is not already active
        #         if dut_channel is path[0]:
        #             raise ConflictingDUTChannelException('ERROR: DUT CHANNEL {} ALREADY ACTIVE'.format(dut_channel))
        #         # Check second integer of bus path to ensure matrix_bus is not already active
        #         elif matrix_bus is path[1]:
        #             raise ConflictingBusException('ERROR: LOAD BUS {} ALREADY ACTIVE'.format(matrix_bus))
        #
        #     # Neither the dut_channel or matrix_bus are in use, we can proceed
        #     return True
        # else:
        #     # If we are disabling a path, we want to ensure that the path we are seeking exists
        #     if (dut_channel, matrix_bus) in self.active_matrix_paths:
        #         return True
        #     else:
        #         return False

        path_patterns = [re.compile('path_%s_%s' % (input_channel, loadbank_channel)),
                         re.compile('path_([0-7])_%s' % loadbank_channel),
                         re.compile('path_%s_([0-7])' % input_channel)]

        # Determine which change code needs to be issued, by default we assume a new path is being created
        change_type = MatrixEnum.NEW_PATH_CHANGE
        change_code = []
        print("EXISTING PATHS BEFORE CHANGE: %s" % str(len(self.active_matrix_paths)))
        for key in self.active_matrix_paths:
            # Path exists, want to change loads active on the load bank
            if path_patterns[0].search(key):
                change_type = MatrixEnum.NO_PATH_CHANGE
                change_code = None
                break
            # Load bank is in use but another input channel is desired
            elif path_patterns[1].search(key):
                if self._check_full_matrix():
                    change_type = MatrixEnum.BOTH_CHANNEL_CHANGE
                    channel_change = (MatrixEnum.INPUT_CHANNEL_CHANGE, int(path_patterns[1].search(key).group(1)))
                    change_code.append(channel_change)
                    continue
                else:
                    change_type = MatrixEnum.INPUT_CHANNEL_CHANGE
                    channel_change = int(path_patterns[1].search(key).group(1))
                    change_code = channel_change
                    break
            # Input channel is in use but another load bank is desired
            elif path_patterns[2].search(key):
                if self._check_full_matrix():
                    change_type = MatrixEnum.BOTH_CHANNEL_CHANGE
                    channel_change = (MatrixEnum.LOADBANK_CHANNEL_CHANGE, int(path_patterns[2].search(key).group(1)))
                    change_code.append(channel_change)
                    continue
                else:
                    change_type = MatrixEnum.LOADBANK_CHANNEL_CHANGE
                    channel_change = int(path_patterns[2].search(key).group(1))
                    change_code = channel_change
                    break

        change_info = (change_type, change_code)
        print(change_info)
        return change_info

    def _check_full_matrix(self) -> bool:
        """
        Return boolean value signifying whether or not all inputs and outputs are occupied

        *WARNING: This function has been written with the idea that each input will match 1:1 with an output, it does
        not provision for less inputs than outputs or more outputs than inputs; this will change the logic immensely
        :return:
        """

        return True if len(self.active_matrix_paths) == len(self.matrix_din_devices) else False

    def _set_matrix_din_relays(self, relay_dev: DinBus):
        """
        Creates the relays which correlate to those attached to the matrix bus. Because the it is a bus output, the
        relays will all correlate to the index of an output channel but from each DinRail device. Thus, for BUS0, CH0
        from each DinRail associated with the matrix will be added to the dictionary.
        """

        # Add relays of the bus_index from each din_matrix device to this bus (CH4 of each matrix Din device to BUS4)
        for alias_base in range(0, len(self.matrix_din_devices)):
            alias = 'r{}'.format(alias_base)
            relay_dev.relay_list[alias] = relay.relay_factory(r_type='dinrail',
                                                              ipaddr=self.matrix_din_devices[
                                                                  'dinmatrix{}'.format(alias_base)].ip_addr,
                                                              relayid=relay_dev.alias[-1])
            relay_dev.relay_list[alias].set_state(relay_dev.relay_list[alias].OFF)


class PathAddressNotFoundException(Exception):
    """
    Exception is raised when the address being enabled or disabled does not exist.
    """
    pass


class ConflictingDUTChannelException(Exception):
    """
    Exception is raised when the DUT channel seeking to be activated is found to be already active
    """
    pass


class ConflictingBusException(Exception):
    """
    Exception is raised when the bus seeking to be activated is found to be already active with another DUT channel
    """
    pass


def log_setup(instance_num: int):
    """
    Setup the logger

    :param instance_num: Integer representing which configuration instance of this device is operating
    :return:  CSV Logger for logging values
    :rtype csv_logger
    """
    # Base filename for all log files
    base_filename = 'dinmatrix'

    # Prepare headers for the log
    log_headers = (
        HeaderItem(name='RELAY_NAME', header_type=str, doc='Name of RelayCmd', required=False),
        HeaderItem(name='RELAY_STATE', header_type=str, doc='State of RelayCmd', required=False),
        HeaderItem(name='BUS_NAME', header_type=str, doc='Name of Matrix Bus', required=False),
        HeaderItem(name='BUS_STATE', header_type=str, doc='State of Bus', required=False),
        HeaderItem(name='DUT_CH_NAME', header_type=str, doc='Name of DUT Channel', required=False),
        HeaderItem(name='DUT_CH_STATE', header_type=str, doc='State of DUT channel', required=False)
    )

    # Create logger
    csv_logger = CsvLogger(headers=log_headers, log_file_name='{0}{1}_log.csv'.format(base_filename, instance_num))
    return csv_logger


def log_state(bus_name: str = '', bus_state: str = '', dut_ch_name: str = '', dut_ch_state: str = '', message: str = '',
              level=logging.DEBUG):
    logger.log(level, 'bus_name={}, bus_state={}, dut_ch_name={}, dut_ch_state={}, message={}'.format(
        bus_name, bus_state, dut_ch_name, dut_ch_state, message))


if __name__ == '__main__':
    print('CAUTION: NO TEST STATEMENTS, INSERT TEST STATEMENTS')
    pass
