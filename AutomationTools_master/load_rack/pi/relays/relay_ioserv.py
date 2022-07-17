import telnetlib
import random
from .relay import Relay


class RelayIOServ(Relay):
    """
    Creates an ioserver relay object.
    """

    def __init__(self, ipaddress, relayid):
        """
        Creates a relay object controlled by ioserver
        :param ipaddress:  IP address of the ioserver
        :param relayid: ID of the relay
        """
        super().__init__(on=1, r_type='iosrv')
        self.ipaddr = ipaddress
        self.relayid = relayid
        self.next_mib = random.randint(1, 32000)

        self.turn_off()

    def __next_mib(self):
        self.next_mib += 1
        if self.next_mib > 32000:
            self.next_mib = 1
        return '%0.4x' % self.next_mib

    def _write_state(self, state):

        tel = telnetlib.Telnet(self.ipaddr, port=5100)
        mib = self.__next_mib()
        tel.write('0s{} c4.hc.rc {:02d} {}\n'.format(mib, self.relayid, state))
        idx, _, _ = tel.expect(['0r{} c4.hc.rc {:02d}'.format(mib, self.relayid)], timeout=3)
        tel.close()

        if idx == -1:
            raise Exception("Error talking to IOServer relay")
