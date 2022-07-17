#!/usr/bin/env python3

import requests
from .relay import Relay

class Relay3GStore(Relay):
    """
    Creates an 3GStore relay object.
    """
    def __init__(self, ipaddress, outlet, user='admin', password=''):
        """
        Creates a relay object for a 3GStore IP controlled power switch
        http://3gstore.com/product/6081_2_outlet_ip_switch.html

        :param ipaddress:  IP address of the 3GStore device
        :param outlet: Power outlet to control. 1,2
        :param user:
        :param password:
        """
        super().__init__(on=1, r_type='3gstore')
        self.ipaddr = ipaddress
        self.user = user
        self.password = password
        self.outlet = int(outlet)
        assert self.outlet in [1, 2]

        self._curr_state = self._get_init_state()

    def _get_init_state(self):
        r = requests.get('http://{}/xml/outlet_status.xml'.format(self.ipaddr),
                         auth=(self.user, self.password))

        # Look for <outlet_status>1,1</outlet_status> in the response
        idx = r.text.find('<outlet_status>')
        idx += 15
        s = r.text[idx:idx+3]
        state = int(s.split(',')[self.outlet - 1])
        return state

    def _write_state(self, state):
        requests.get('http://{}/cgi-bin/control.cgi?outlet={}&control={}'.format(
            self.ipaddr, self.outlet, state),
            auth=(self.user, self.password))


