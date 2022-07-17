import piplates.RELAYplate as RELAY
import logging

from c4common.hw_tools.relay import Relay


logger = logging.getLogger(__name__)


class RelayPiPlate(Relay):
    def __init__(self, address=0, channel=1):
        super().__init__(on=1, r_type='piplate')
        self.address = address
        self.channel = channel
        self.turn_off()

    def _write_state(self, state):
        if state == self.ON:
            RELAY.relayON(self.address, self.channel)
        else:
            RELAY.relayOFF(self.address, self.channel)
