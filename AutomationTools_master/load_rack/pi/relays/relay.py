import Adafruit_GPIO as Gpio                 # For Raspberry Pi GPIO relays.
from Adafruit_GPIO.MCP230xx import MCP23017  # For i2c relays using the MCP32017 chip
import logging
logger = logging.getLogger(__name__)


class Relay:
    """
    Base class for all relays.
    Inherent from this class when implementing a new type of relay.
    You must implement _write_state() in your derived relay class.
    """

    r_types = ['rp', 'lj', 'ncd', 'mcp', 'iosrv', 'sr', 'dinrail', '3gstore', 'piplate']

    def __init__(self, on=1, r_type=None):
        """
        :param on: What value is "on" for this relay?
        :type on: int
        :param r_type: Type of relay. See self.r_types
        :type r_type: str
        """

        if r_type is None or r_type not in self.r_types:
            raise ValueError('Missing or bad relay type: r_type = %s' % r_type)
        self._r_type = r_type
        if on == 1:
            self.ON = 1
            self.OFF = 0
        elif on == 0:
            self.ON = 0
            self.OFF = 1
        else:
            raise ValueError('Value for no, not valid: on = %s' % on)
        self._curr_state = None

    def _write_state(self, state):
        """
        Implement this method in your derived class.
        :param state:
        :return:
        """
        # >>> Code to actually write state goes here <<<
        # Keep track of what we wrote.
        # if state == self.ON:
        #     self._curr_state = self.ON
        # else:
        #     self._curr_state = self.OFF
        raise NotImplementedError("Overwrite this method")

    def toggle(self):
        """
        Toggle's the relay state
        """
        if self._curr_state == self.ON:
            self.set_state(self.OFF)
        else:
            self.set_state(self.ON)

    def get_state(self):
        """
        Get the current state of the relay
        """
        return self._curr_state

    def turn_on(self):
        """
        Turn the relay on
        """
        self.set_state(self.ON)

    def turn_off(self):
        """
        Turn the relay off
        """
        self.set_state(self.OFF)

    def set_state(self, val):
        """
        Set the relay's state

        :param val: The new value to set the relay to
        :type val:  self.ON / self.OFF
        """
        if val == self.ON:
            logger.debug('*********************************')
            logger.debug("set_state(): Setting Relay to ON")
            self._write_state(self.ON)
            self._curr_state = self.ON
        else:
            logger.debug('*********************************')
            logger.debug("set_state(): Setting Relay to OFF")
            self._write_state(self.OFF)
            self._curr_state = self.OFF


class RelayRp(Relay):
    """
    Creates a Raspberry Pi relay object.
    """

    platform_gpio = None

    def __init__(self, on=1, gpio_pin=None):
        """
        :param on: Specifies if a relay's 'on' state is a high or low signal
        :type on:  integer (1/0)
        """
        super().__init__(on=on, r_type='rp')
        self._pin = gpio_pin
        if self._pin is None:
            raise ValueError("GPIO pin number missing")
        if self.platform_gpio is None:
            self.gpio = Gpio.get_platform_gpio()
        self.gpio.setup(self._pin, Gpio.OUT)

    def _write_state(self, value):
        if value == self.ON:
            self.gpio.output(self._pin, self.ON)
            self._curr_state = self.ON
        else:
            self.gpio.output(self._pin, self.OFF)
            self._curr_state = self.OFF


class RelaySr(Relay):
    """
    Creates a Raspberry shift_register relay object.
    """
    def __init__(self, on=0, sr_channel=0):
        super().__init__(on=1, r_type='sr')
        """
        :param on: Specifies if a relay's 'on' state is a high or low signal
        :type on:  integer (1/0)
        :param r_type: The type of relay
        :type r_type" string:
        """
        _ = on
        _ = sr_channel
        # relay.__init__(self, on=0, r_type='sr')
        # SR support requires sr.py to be ported to new apscheduler
        raise Exception('Shift register relay type not implemented yet')


class RelayLj(Relay):
    """
    Creates a relay controlled by a LabJack
    """
    def __init__(self, serial_number=None, ip_address=None, fio=None):
        super().__init__(on=1, r_type='lj')
        _ = serial_number
        _ = ip_address
        _ = fio
        raise Exception('LabJack relay type not implemented yet')


class RelayNcd(Relay):
    """
    Creates an NCD networked relay board relay
    """
    def __init__(self, ipaddress, relayid):
        """
        Creates a relay object controlled by an NCD relay board
        :param ipaddress:
        :param relayid:
        """
        super().__init__(on=1, r_type='ncd')
        _ = ipaddress
        _ = relayid
        raise Exception('NCD relay type not implemented yet')


class RelayMcp(Relay):
    """
    Creates a mcp GPIO extender relay object.
    We can support up to 8 mcp23017 chips.
    As we create them, we put them in a static dictionary.
    If the mcp object exists in the array, we use it, 
    if not, we create it first.
    """

    chip_d = {}  # The GPIO chip objects, indexed by I2C bus ID. {ID: <object>, ID: <object>, etc.}

    def __init__(self, on=0, mcp_bus_id=None, mcp_pin=None):
        logger.debug(">>>>>>> Running __init__() for relay {}".format(mcp_pin))
        logger.debug("on = %s" % on)
        super().__init__(on=on, r_type='mcp')
        logger.debug("on = %s" % on)
        self._id = mcp_bus_id
        self._pin = mcp_pin
        if self._id not in self.chip_d:
            self.chip_d[self._id] = MCP23017(address=self._id)
        logger.debug(self.chip_d)
        logger.debug('PIN = {}'.format(self._pin))
        self._relay = self.chip_d[self._id]
        self._relay.setup(self._pin, Gpio.OUT)
        self._relay.output(self._pin, Gpio.HIGH)
        logger.debug("self.ON = %d" % self.ON)
        logger.debug("self.OFF = %d" % self.OFF)
        logger.debug('Gpio.HIGH = {}'.format(Gpio.HIGH))
        logger.debug('Gpio.LOW = {}'.format(Gpio.LOW))
        logger.debug(self.chip_d)

    def _write_state(self, value):
        logger.debug('================Write State===============')
        logger.debug('>>>>>> self.ON = {}'.format(self.ON))
        logger.debug('>>>>>> self.OFF = {}'.format(self.OFF))
        if value == self.ON:
            logger.debug('Turning relay ON')
            on_value = Gpio.LOW if self.ON == 0 else Gpio.HIGH
            logger.debug('on_value = {}'.format(on_value))
            self._relay.output(self._pin, on_value)
            self._curr_state = self.ON
        else:
            logger.debug('Turning relay OFF')
            off_value = Gpio.HIGH if self.ON == 0 else Gpio.LOW
            logger.debug('off_value = {}'.format(off_value))
            self._relay.output(self._pin, off_value)
            self._curr_state = self.OFF


if __name__ == '__main__':
    logging.basicConfig(filename='relay_control.log', level=logging.DEBUG)
    logger = logging.getLogger('RelayControl')
    import time
    relays = {}
    for i in range(16):
        relays[i] = RelayMcp(mcp_bus_id=0x21, mcp_pin=i)

    for relay in relays:
        print('Turning on relay: {}'.format(relay))
        time.sleep(1)
        relays[relay].set_state(relays[relay].ON)

    for relay in relays:
        print('Turning off relay: {}'.format(relay))
        time.sleep(1)
        relays[relay].set_state(relays[relay].OFF)
