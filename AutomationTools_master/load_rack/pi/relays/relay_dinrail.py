#!/usr/bin/env python3

import logging
import pexpect
import random
from c4common.hw_tools.relay import Relay
from c4common.utils.retry import retry

logger = logging.getLogger(__name__)

class RelayDinrail(Relay):
    """
    Creates an dinrail relay object.
    """
    def __init__(self, ipaddress, channel):
        """
        Creates a relay object controlled by Dinrail 8-Channel relay
        :param ipaddress:  IP address of the Dinrail device
        :param relayid: ID of the relay
        """
        super().__init__(on=0, r_type='dinrail')
        self.ipaddr = ipaddress
        self.channel = channel
        self.next_mib = random.randint(1, 32000)

        self.turn_off()

    def __next_mib(self):
        """
        Generate an incrementing MIB id.
        :return:
        """

        self.next_mib += 1
        if self.next_mib > 32000:
            self.next_mib = 1
        return '%0.4x' % self.next_mib

    @retry(tries=10, timeout=0, raises=False, sleep=.25, logger=logger)
    def _write_state(self, state):
        """
        Write the state of a relay.
        Decorator causes it to try up to 10 times.
        :param state:
        :return: Boolean
        """

        cmd = 'netcat -u {} {}'.format(self.ipaddr, 8750)
        tel = pexpect.spawnu(cmd)
        mib = self.__next_mib()
        cmd = '0i{} c4.dm.bp {} {} 2'.format(mib, self.channel, state)
        res = '0r{} 000'.format(mib)
        tel.sendline(cmd)
        idx = tel.expect([res, pexpect.TIMEOUT], timeout=3)
        if idx == 1:
            return False
        else:
            return True
