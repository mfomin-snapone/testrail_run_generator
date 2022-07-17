# File has been converted to Python3 from Python2 using 2to3 tool

import logging
import socket
import threading
from enum import IntEnum, Enum, EnumMeta
import RPi.GPIO as GPIO

from c4common.hw_tools.linkbone import Linkbone8x8Matrix, LinkboneMatrixEnum
from c4common.hw_tools.relaytempboard import RelayTemperatureBoard
from .relaytempcfg import RelayTemperatureCfg
from .linkbonecfg import LinkboneCfg
from .din_matrix.dinmatrix import DinMatrix
from .mib import Mib

logger = logging.getLogger('pqa_logger')
logger.setLevel(logging.DEBUG)

CFG_FILE_PATH = '/etc/default'


class RelayCmd(IntEnum):
    ON = 0
    OFF = 1


class MibManager:
    class BaseCommands(Enum):
        PQA_PI_GPIO = ('pqa.pi.gpio', 'Get status of RPi GPIO pin')
        LIST_MIBS = ('pqa.mibs.list',
                     'List all known MIBS including plugins')
        SWITCHLEG_MIB = ('pqa.dut.sl',
                         'Set the DUT into switchleg using relay')
        PWR_MIB = ('pqa.dut.pwr',
                   'Turn on or off DUT power using relay')
        MTX_PATH_MIB = ('pqa.mtx.path',
                        'Enable/Disable Matrix paths')
        MTX_LOAD_MIB = ('pqa.mtx.ld',
                        'Choose which load on the LOAD bus (not matrix)')
        SET_LKB_MODE = ('pqa.lkb.md',
                        'Set multi-mode or single mode')
        SET_LKB_PATH = ('pqa.lkb.path',
                        'Sets the linkbone path from a single node (A-H) to any/all of dest (I-P)')
        RESET_LKB = ('pqa.lkb.rst',
                     'Opens all connections (all paths removed)')
        GET_LKB_STATUS = ('pqa.lkb.stat',
                          'TBD')
        SEND_LKB_PING = ('pqa.lkb.ping',
                         'Network ping to linkbone to check if it is alive')
        RTB_REL_MIB = ('pqa.rtb.rel',
                       'Sets state or gets information about a relay from the Relay and Temperature Board')
        RTB_TEMP_MIB = ('pqa.rtb.temp',
                        'Gets the temperature (in F or C) from a sensor aliased with the Relay and Temperature Board')
        GPIO_MIB = ('pqa.pi.gpio',
                    'Handle a Raspberry Pi GPIO action')
        SUB_MIB = ('c4.sy.sub',
                   'Subscribe to mib handler')

    def add_plugin(self, sender: object, plg_enum: EnumMeta):
        for plg_item in plg_enum:
            assert isinstance(plg_item, Enum)
            func_name = str(plg_item.value[0]).replace('.', '_')
            if plg_item.value in self.MIBS:
                logger.critical('MIB handler "{}" already exists, skipping duplicate item')
            else:
                logger.debug('Adding plugin MIB: {} - {}'.format(plg_item.value[0], plg_item.value[1]))
                self.MIBS[plg_item.value[0]] = [getattr(sender, func_name), plg_item.value[1]]

    def _set_gpio(self, mib, gpio_port, enable, host, port):
        logger.debug(str(mib.type))
        try:
            if mib.is_set:
                if len(mib.param) == 1:
                    GPIO.output(gpio_port, RelayCmd.ON if enable else RelayCmd.OFF)
                    self.send_reply(None, mib.packet_number, host, port)
                else:
                    self.send_reply("E01", mib.packet_number, host, port)
            elif mib.is_get:
                gpio_state = GPIO.input(gpio_port)
                self.send_reply('{} {}'.format(mib.command, gpio_state), mib.packet_number, host, port)
            else:
                self.send_reply("N01", mib.packet_number, host, port)
        except Exception as e:
            # traceback.print_exc()
            logger.error(e, exc_info=True)
            self.send_reply("E03", mib.packet_number, host, port)

    def __init__(self, server: socket.socket, switchleg_gpio: int, power_gpio: int, instance_number=0):
        self.gpio_switchleg = switchleg_gpio
        self.gpio_dut_power = power_gpio

        # GPIO.setwarnings(False)
        # GPIO.setmode(GPIO.BOARD)
        # GPIO.setup(self.gpio_switchleg, GPIO.OUT)
        # GPIO.setup(self.gpio_dut_power, GPIO.OUT)

        lcfg = LinkboneCfg(CFG_FILE_PATH)
        rtcfg = RelayTemperatureCfg(CFG_FILE_PATH)

        self.E_PLUGINS = []
        self.MIBS = {}
        self.instance_number = instance_number
        self.packet_number = 1000
        self.lock = threading.Lock()
        self.server = server
        self.sub_address = None
        self.sub_port = None
        self.din_matrix = DinMatrix()  # Do not forget to include the instance value (integer)
        # self.linkbone_matrix = None if not linkbone_ip else Linkbone8x8Matrix(linkbone_ip, linkbone_port)
        ip_addr, ip_port, comm_type = lcfg.load_devices()
        self.linkbone_matrix = Linkbone8x8Matrix(ip_addr, ip_port, comm_type)
        # self.relay_temp_control = RelayTemperatureBoard({'r0': {'bus_id': 0x20, 'pin_id': 0},
        #                                                  'r1': {'bus_id': 0x20, 'pin_id': 7}})
        relays, sensors = rtcfg.load_devices()
        self.relay_temp_control = RelayTemperatureBoard(relays, sensors)
        self.add_plugin(self, self.BaseCommands)

    def set_devices(self, matrix_devices: list, bus_devices: list):
        """
        Sets both matrix and bus devices to supplied lists.  These will remove all old items and replace them with the
        new ones.
        :param matrix_devices: list of parameters for new devices
        :param bus_devices: list of parameters for new bus devices
        """
        self.din_matrix.matrix_din_devices.clear()
        self.din_matrix.bus_din_devices.clear()
        for alias, ip_addr, mac_addr in matrix_devices:
            self.din_matrix.add_matrix_device(alias, ip_addr, mac_addr)
        for alias, ip_addr, mac_addr, load_type, num_loads in bus_devices:
            self.din_matrix.add_bus_device(alias, ip_addr, mac_addr, load_type, num_loads)

    def incoming_mib(self, mib_string, host, port):
        logger.debug(mib_string)
        mib = Mib(mib_string)
        logger.debug(str(mib))

        if not mib.error:
            logger.debug('Incoming MIB: "{}"'.format(str(mib).strip()))

            if mib.command in self.MIBS:
                logger.debug("Processing known MIB '{}'".format(str(mib).strip()))
                # cmd = getattr(self, self.MIBS[mib.command])
                cmd = self.MIBS[mib.command][0]
                cmd(mib, host, port)
            else:
                self.send_reply("V01", mib.packet_number, host, port)
        else:
            self.send_reply("E01 - INCOMING MIB", None, host, port)

    def send_mib(self, mib_type="r", mib="000", packet_number=None, address=None, port=None):
        self.lock.acquire()

        if packet_number is None:
            self.packet_number += 1
            number = self.int_to_hex_str_packet(self.packet_number)
        else:
            number = "%x" % packet_number
            number = number.zfill(4)

        mib = "0" + str(mib_type) + number + " " + mib + "\r\n"
        if self.server is not None:
            self.server.sendto(bytes(mib, 'UTF-8'), address)
        else:
            logger.debug("Server is None")

        self.lock.release()

    def send_reply(self, msg, number=None, host=None, port=None):
        if msg:
            self.send_mib("r", "000 " + msg, number, host, port)
        else:
            self.send_mib("r", "000", number, host, port)

    def send_trap(self, msg):
        self.send_mib("t", msg, None, self.sub_address, self.sub_port)

    def pqa_mibs_list(self, mib, host, port):
        self.send_reply('=' * 40, mib.packet_number, host, port)
        self.send_reply('== MIBS LIST', mib.packet_number, host, port)
        self.send_reply('=' * 40, mib.packet_number, host, port)
        for key, value in self.MIBS.items():
            self.send_reply('{0: <20}:{1}'.format(key, value[1]), mib.packet_number, host, port)
        self.send_reply('-' * 40, mib.packet_number, host, port)

    @staticmethod
    def int_to_hex_str_packet(packet):
        hex_packet = "%x" % packet
        hex_packet = hex_packet.zfill(4)
        return hex_packet

    # region Raspberry Pi MIB Functionality
    def pqa_pi_gpio(self, mib: Mib, host: str, port: int):
        """
        Sets/Gets GPIO pin to High or Low

        MIB parameters:
            1. (int) GPIO port number
            2. (0,1) True to bring high, False to set low

        :param mib: Received MIB
        :param host: Host that sent this MIB
        :param port: Network port
        """
        enable = False
        pi_pin = int(mib.param[0])
        if len(mib.param) > 1:
            enable = int(mib.param[1])
        self._set_gpio(mib, gpio_port=pi_pin, enable=enable, host=host, port=port)

    def c4_sy_sub(self, mib, host, port):
        self.sub_address = host
        self.sub_port = port
        self.send_reply(mib.command, mib.packet_number, host, port)

    def pi_status(self, mib, host, port):
        self.send_reply("E03, RPi Status not implemented", mib.packet_number, host, port)
        # try:
        #     if "s" in mib.type:
        #         # print(str(mib.param))
        #         # print(str(len(mib.param)))
        #         self.send_reply("E01", mib.packet_number, host, port)
        #     elif "g" in mib.type:
        #         self.db.get_device()
        #         pins_value = self.ad_reader.get_channel_status(int(mib.param[0]))
        #         pins = "{0}".format(int(pins_value))
        #         self.send_reply(mib.command + " " + pins, mib.packet_number, host, port)
        #     else:
        #         self.send_reply("N01", mib.packet_number, host, port)
        # except Exception as e:
        #     # traceback.print_exc()
        #     logger.error(e, exc_info=True)
        #     self.send_reply("E03", mib.packet_number, host, port)

    def pqa_mtx_path(self, mib, host, port):
        """
        Set matrix path.
        MIB Parameters:
        0s1234 pqa.mtx.path

        *    SET

             *    enable: int  [0: false, 1, true]
             *    DUT channel: int [0-8]
             *    Matrix bus: int
             *    Load flag: int

             GET

             * Matrix bus: int
        """
        try:
            if "s" in mib.type:
                if len(mib.param) == 4:
                    enable = int(mib.param[0], 16)
                    dut_channel = int(mib.param[1], 16)
                    matrix_bus = int(mib.param[2], 16)
                    load_flag = int(mib.param[3], 16)

                    logger.debug('Setting Matrix, enable: {}, dut_channel: {}, matrix_bus: {}, load_flag: {}'.format(
                        enable, dut_channel, matrix_bus, load_flag))

                    if enable:
                        self.din_matrix.set_matrix_path(dut_channel, matrix_bus, load_flag)
                    else:
                        self.din_matrix.set_matrix_path(dut_channel, matrix_bus, 0x00)
                if len(mib.param) == 3:
                    input_channel = int(mib.param[0], 16)
                    load_bank = int(mib.param[1], 16)
                    load_flag = int(mib.param[2], 16)

                    self.din_matrix.set_matrix_path(input_channel, load_bank, load_flag)
                    self.send_reply(None, mib.packet_number, host, port)
                elif len(mib.param) == 2:
                    input_channel = int(mib.param[0], 16)
                    load_bank = int(mib.param[1], 16)

                    self.din_matrix.set_matrix_path(input_channel, load_bank)
                    self.send_reply(None, mib.packet_number, host, port)
                else:
                    self.send_reply("E01", mib.packet_number, host, port)
            elif "g" in mib.type:
                def get_path(input_channel):
                    return str(self.din_matrix.get_matrix_path(input_channel=input_channel))
                if (len(mib.param) < 1):
                    channels = [ x[-1:] for x in self.din_matrix.matrix_din_devices.keys() ];
                    reply = " ".join(filter(None, [ get_path(x) for x in channels ]))
                    self.send_reply(reply, mib.packet_number, host, port)
                else:
                    reply = get_path(mib.param[0])
                    self.send_reply(reply, mib.packet_number, host, port)
                    return
            else:
                logger.debug(str(mib.type))
                self.send_reply("N01", mib.packet_number, host, port)
        except Exception as e:
            # traceback.print_exc()
            logger.error(e, exc_info=True)
            self.send_reply("E03", mib.packet_number, host, port)

    def pqa_mtx_ld(self, mib, host, port):
        '''
        SET
        Sets the load state for the specified channel
        0s1234 pqa.mtx.ld [CHANNEL] [LOAD_BITMASK]
        0r1234 000

        Set channels 0, 1, and 7 on load bank 4:
        0s1235 pqa.mtx.ld 04 83
        0r1235 000

        GET
        Gets the load state of a paticular load bank or all load banks
        if no channel is specified
        0g1236 pqa.mtx.ld [CHANNEL]
        0r1236 000 [CHANNELS_THAT_EXIST_BITMASK] [CHANNEL_STATE_BITMASK]
        0g1237 pqa.mtx.ld
        0r1237 000 [CH0_BITMASK] [CH0_STATE] [CH1_BITMASK] ..... [CH7_STATE]

        Get load state of load bank 3 (All channels off)
        0g1238 pqa.mtx.ld 0
        0r1238 000 FF 00

        Get load state of all load banks (Load bank 1: channel 7 on, Load bank 7: channels 0 and 1 on)
        0g1239 pqa.mtx.ld
        0r1239 000 FF 00 FF 80 FF 00 FF 00 FF 00 FF 00 FF 00 FF 03
        '''
        try:
            if "s" in mib.type:
                if len(mib.param) == 2:
                    load_bank = int(mib.param[0], 16)
                    load_mask = int(mib.param[1], 16)

                    self.din_matrix.set_bus_loads(load_bank, load_mask)
                    self.send_reply(None, mib.packet_number, host, port)
                else:
                    self.send_reply("E01", mib.packet_number, host, port)
            elif "g" in mib.type:
                def get_load(channel):
                    relay = "dinbus{}".format(channel)
                    load_bank = self.din_matrix.bus_din_devices[relay].get_load_bank_din()
                    channels = [ x[1:] for x in load_bank._relay_list.keys() ];
                    channels_that_exist = 0
                    channel_status = 0
                    #Create a bitmask of channels that exists and the loads that are on
                    for channel in channels:
                        channels_that_exist |= 1<<int(channel)
                        if load_bank.get_load_state(channel) == RelayCmd.ON:
                            channel_status |= 1<<int(channel)
                    return "{:02X} {:02X}".format(channels_that_exist, channel_status);
                if len(mib.param) > 0:
                    self.send_reply(get_load(mib.param[0]), mib.packet_number, host, port)
                else:
                    reply = " ".join(get_load(x) for x in range(len(self.din_matrix.bus_din_devices)))
                    self.send_reply(reply, mib.packet_number, host, port)
            else:
                logger.debug(str(mib.type))
                self.send_reply("N01", mib.packet_number, host, port)
        except Exception as e:
            logger.error(e, exc_info=True)
            self.send_reply("E03", mib.packet_number, host, port)

    def pqa_dut_pwr(self, mib, host, port):
        """
        Turn on/off power on the DUT
        1=on, 0=off
        :param mib:
        :param host:
        :param port:
        :return:
        """
        enable = 0 if len(mib.param) <= 0 else int(mib.param[0])
        self._set_gpio(mib, gpio_port=self.gpio_dut_power, enable=enable, host=host, port=port)

    def pqa_dut_sl(self, mib, host, port):
        enable = 0 if len(mib.param) <= 0 else int(mib.param[0])
        self._set_gpio(mib, gpio_port=self.gpio_switchleg, enable=enable, host=host, port=port)

    # endregion Raspberry Pi MIB Functionality

    # region Linkbone MIB Functionality
    def pqa_lkb_md(self, mib, host, port):
        try:
            if "s" in mib.type:
                if len(mib.param) is 1:
                    mode = int(mib.param[0], 16)

                    if mode == 0:
                        self.linkbone_matrix.set_mode(LinkboneMatrixEnum.SINGLE)
                        self.send_reply(None, mib.packet_number, host, port)
                    elif mode == 1:
                        self.linkbone_matrix.set_mode(LinkboneMatrixEnum.MULTI)
                        self.send_reply(None, mib.packet_number, host, port)
                    else:
                        self.send_reply("V01", mib.packet_number, host, port)
                else:
                    self.send_reply("E01", mib.packet_number, host, port)
            elif "g" in mib.type:
                self.send_reply("N01", mib.packet_number, host, port)
            elif "i" in mib.type:
                self.send_reply("N01", mib.packet_number, host, port)
            else:
                logger.debug(str(mib.type))
                self.send_reply("N01", mib.packet_number, host, port)
        except Exception as e:
            logger.debug(e, exc_info=True)
            self.send_reply("E03", mib.packet_number, host, port)

    def pqa_lkb_path(self, mib, host, port):
        try:
            if "s" in mib.type:
                if len(mib.param) >= 2:
                    enable = int(mib.param[0])
                    src_prt = mib.param[1]
                    dst_prts = None if len(mib.param) <= 2 else mib.param[2:]

                    self.linkbone_matrix.set_path(enable, src_prt, dst_prts)
                    self.send_reply(None, mib.packet_number, host, port)
                else:
                    self.send_reply("E01", mib.packet_number, host, port)
            elif "g" in mib.type:
                self.send_reply("N01", mib.packet_number, host, port)
            elif "i" in mib.type:
                self.send_reply("N01", mib.packet_number, host, port)
            else:
                logger.debug(str(mib.type))
                self.send_reply("N01", mib.packet_number, host, port)
        except Exception as e:
            logger.debug(e, exc_info=True)
            self.send_reply("E03", mib.packet_number, host, port)

    def pqa_lkb_rst(self, mib, host, port):
        try:
            if "s" in mib.type:
                self.send_reply("N01", mib.packet_number, host, port)
            elif "g" in mib.type:
                self.send_reply("N01", mib.packet_number, host, port)
            elif "i" in mib.type:
                if len(mib.param) == 0:
                    self.linkbone_matrix.send_reset()
                    self.send_reply(None, mib.packet_number, host, port)
                else:
                    self.send_reply("E01", mib.packet_number, host, port)
            else:
                logger.debug(str(mib.type))
                self.send_reply("N01", mib.packet_number, host, port)
        except Exception as e:
            logger.debug(e, exc_info=True)
            self.send_reply("E03", mib.packet_number, host, port)

    def pqa_lkb_stat(self, mib, host, port):
        try:
            if "s" in mib.type:
                self.send_reply("N01", mib.packet_number, host, port)
            elif "g" in mib.type:
                if len(mib.param) == 0:
                    self.linkbone_matrix.get_status()
                    self.send_reply(None, mib.packet_number, host, port)
                else:
                    self.send_reply("E01", mib.packet_number, host, port)
            elif "i" in mib.type:
                self.send_reply("N01", mib.packet_number, host, port)
            else:
                logger.debug(str(mib.type))
                self.send_reply("N01", mib.packet_number, host, port)
        except Exception as e:
            logger.debug(e, exc_info=True)
            self.send_reply("E03", mib.packet_number, host, port)

    def pqa_lkb_ping(self, mib, host, port):
        try:
            if "s" in mib.type:
                self.send_reply("N01", mib.packet_number, host, port)
            elif "g" in mib.type:
                self.send_reply("N01", mib.packet_number, host, port)
            elif "i" in mib.type:
                if len(mib.param) == 0:
                    self.linkbone_matrix.send_ping()
                    self.send_reply(None, mib.packet_number, host, port)
                else:
                    self.send_reply("E01", mib.packet_number, host, port)
            else:
                logger.debug(str(mib.type))
                self.send_reply("N01", mib.packet_number, host, port)
        except Exception as e:
            logger.debug(e, exc_info=True)
            self.send_reply("E03", mib.packet_number, host, port)

    def pqa_lkb_disc(self, mib, host, port):
        try:
            if "s" in mib.type:
                self.send_reply("N01", mib.packet_number, host, port)
            elif "g" in mib.type:
                self.send_reply("N01", mib.packet_number, host, port)
            elif "i" in mib.type:
                if len(mib.param) == 0:
                    self.linkbone_matrix.disconnect()
                    self.send_reply(None, mib.packet_number, host, port)
                else:
                    self.send_reply("E01", mib.packet_number, host, port)
            else:
                logger.debug(str(mib.type))
                self.send_reply("N01", mib.packet_number, host, port)
        except Exception as e:
            logger.debug(e, exc_info=True)
            self.send_reply("E03", mib.packet_number, host, port)
    # endregion Linkbone MIB Functionality

    # region Relay and Temperature Board MIB Functionality
    def pqa_rtb_rel(self, mib, host, port):
        try:
            if "s" in mib.type:
                alias = mib.param[0]
                state = mib.param[1]
                self.relay_temp_control.set_relay_state(alias, state)
                self.send_reply(None, mib.packet_number, host, port)
            elif "g" in mib.type:
                alias = mib.param[0]
                res = str(self.relay_temp_control.get_relay_state(alias))
                self.send_reply(mib.command + ' ' + res, mib.packet_number, host, port)
            elif "i" in mib.type:
                self.send_reply("N01", mib.packet_number, host, port)
            else:
                logger.debug(str(mib.type))
                self.send_reply("N01", mib.packet_number, host, port)
        except Exception as e:
            logger.debug(e, exc_info=True)
            self.send_reply("E03", mib.packet_number, host, port)

    def pqa_rtb_temp(self, mib, host, port):
        try:
            if "s" in mib.type:
                self.send_reply("N01", mib.packet_number, host, port)
            elif "g" in mib.type:
                alias = mib.param[0]
                fahrenheit = mib.param[1]
                res = self.relay_temp_control.read_temp_sensor(alias, fahrenheit)
                self.send_reply(res, mib.packet_number, host, port)
            elif "i" in mib.type:
                self.send_reply("N01", mib.packet_number, host, port)
            else:
                logger.debug(str(mib.type))
                self.send_reply("N01", mib.packet_number, host, port)
        except Exception as e:
            logger.debug(e, exc_info=True)
            self.send_reply("E03", mib.packet_number, host, port)
    # endregion Relay and Temperature Board MIB Functionality
