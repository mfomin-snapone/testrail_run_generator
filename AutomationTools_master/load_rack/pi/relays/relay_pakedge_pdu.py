
# Copyright 2017 Control4 Corporation. All Rights Reserved.

import logging
import time

from c4common.hw_tools.relay import Relay
from c4common.networking.pakedge_p8_pdu import PakedgeP8

logger = logging.getLogger(__name__)

class RelayPakedgePDU(Relay):
    """
    Creates an ioserver relay object.
    """
    def __init__(self, outlet, ipaddress='192.168.1.210', username='pakedge', password='pakedgep'):
        """
        Creates a relay object controlled by ioserver
        :param ipaddress:  IP address of the ioserver
        :param outlet: Outlet to control (1 - 8)
        :param username: username to user
        :param password: password to the user account
        """
        super().__init__(on=1, r_type='iosrv')
        self.ipaddr = ipaddress
        self.outlet = outlet
        self.username = username
        self.password = password

        pdu = PakedgeP8(ipaddress=self.ipaddr, user=self.username, password=self.password)
        status = pdu.outlet_status(outlet=outlet)
        logger.debug(status)
        if status['status'] == 'ON':
            self._curr_state = self.ON
            logger.debug('Setting initial state of p8 relay to ON')
        elif status['status'] == 'OFF':
            self._curr_state = self.OFF
            logger.debug('Setting initial state of p8 relay to OFF')
        else:
            logger.error('Could not determine the state of the outlet')


    def _write_state(self, state):

        pdu = PakedgeP8(ipaddress=self.ipaddr, user=self.username, password=self.password)

        if state == self.ON:
            pdu.enable(self.outlet)
        else:
            pdu.disable(self.outlet)
        time.sleep(0.1)  # We have to keep the connection open for a little bit for the command to complete


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    r = RelayPakedgePDU(1)

    for _ in range(4):
        time.sleep(1)
        r.toggle()
