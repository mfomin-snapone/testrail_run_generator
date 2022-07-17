#!/usr/bin/env python3

import sys
import signal
from time import sleep

from .relay import *
from .relay_piplate import RelayPiPlate
from .relay_dinrail import RelayDinrail
from .relay_ioserv import RelayIOServ
from .relay_3gstore import Relay3GStore


def relay_factory(**kwargs):
    """
    Relay factory.  Returns a relay class object base on the key word arguments.
    """
    args = kwargs
    if "r_type" not in args:
        raise Exception("Missing argument: r_type")
    if args['r_type'] == 'rp':
        if "on" in args:
            relay_on = args["on"]
        else:
            relay_on = 0
        return RelayRp(on=relay_on, gpio_pin=args['gpio_pin'])
    if args['r_type'] == 'sr':
        if "on" in args:
            relay_on = args["on"]
        else:
            relay_on = 1
        return RelaySr(on=relay_on, sr_channel=0)
    if args['r_type'] == 'mcp':
        if "on" in args:
            relay_on = args["on"]
        else:
            relay_on = 0
        return RelayMcp(on=relay_on, mcp_bus_id=args['mcp_bus_id'], mcp_pin=args['mcp_pin'])
    if args['r_type'] == 'iosrv':
        return RelayIOServ(ipaddress=args['ipaddr'], relayid=args['relayid'])
    if args['r_type'] == 'dinrail':
        return RelayDinrail(ipaddress=args['ipaddr'], channel=args['relayid'])
    if args['r_type'] == '3gstore':
        return Relay3GStore(ipaddress=args['ipaddr'], outlet=args['relayid'])
    if args['r_type'] == 'ncd':
        pass
    if args['r_type'] == 'piplate':
        """address=0, channel=0"""
        return RelayPiPlate(address=args['address'], channel=args['channel'])

    raise Exception("Unknown type of relay '{}'".format(args['r_type']))


if __name__ == '__main__':
    """
    Test the relay class methods.
    """
    logging.basicConfig()
    logger.setLevel(logging.DEBUG)


    def signal_handler(sig, f):
        """
        Handle Ctrl-C and clean up our scheduled jobs
        """
        _ = sig
        _ = f
        print('\nCtrl-C detected, cleaning up...')
        cleanup()

    signal.signal(signal.SIGINT, signal_handler)

    def cleanup():
        sys.exit(0)

    def r_test(my_relay):
        print("relay.ON = %d" % my_relay.ON)
        print("relay.OFF = %d" % my_relay.OFF)
        state = my_relay.get_state()
        if state == my_relay.ON:
            state_s = 'on'
        else:
            state_s = 'off'
        print("2: Current state of my_relay: %s" % state_s)
        sleep(.1)

        print("3: Setting relay to ON.")
        my_relay.set_state(my_relay.ON)
        state = my_relay.get_state()
        if state == my_relay.ON:
            state_s = 'on'
        else:
            state_s = 'off'
        print("4: Current state of relay: %s" % state_s)
        sleep(.1)

        print("5: Setting relay to OFF.")
        my_relay.set_state(my_relay.OFF)
        state = my_relay.get_state()
        if state == my_relay.ON:
            state_s = 'on'
        else:
            state_s = 'off'
        print("6: Current state of relay: %s" % state_s)
        sleep(.1)

        print("7: Setting relay to ON.")
        my_relay.set_state(my_relay.ON)
        state = my_relay.get_state()
        if state == my_relay.ON:
            state_s = 'on'
        else:
            state_s = 'off'
        print("8: Current state of relay: %s" % state_s)
        sleep(.1)

        print("9: Setting relay to OFF.")
        my_relay.set_state(my_relay.OFF)
        state = my_relay.get_state()
        if state == my_relay.ON:
            state_s = 'on'
        else:
            state_s = 'off'
        print("10: Current state of relay: %s" % state_s)
        sleep(.1)

        print("Toggling the relay:")
        for _ in range(9):
            my_relay.toggle()
            state = my_relay.get_state()
            if state == my_relay.ON:
                state_s = 'on'
            else:
                state_s = 'off'
            print("11: Current state of relay: %s" % state_s)
            sleep(.01)

        print("Turing off relay.")
        my_relay.set_state(my_relay.OFF)
        print("Done.\n")

    def r_test_simple(my_relay):
        print("Setting relay to ON.")
        my_relay.set_state(my_relay.ON)
        state = my_relay.get_state()
        if state == my_relay.ON:
            state_s = 'on'
        else:
            state_s = 'off'
        print("Current state of relay: %s" % state_s)
        sleep(4)
        print("Setting relay to OFF.")
        my_relay.set_state(my_relay.OFF)
        state = my_relay.get_state()
        if state == my_relay.ON:
            state_s = 'on'
        else:
            state_s = 'off'
        print("10: Current state of relay: %s" % state_s)
        sleep(.2)

    print("\n1: Starting test:")
    for i in range(16):
        print("Relay %s:" % i)
        r1 = relay_factory(r_type='mcp', mcp_bus_id=0x20, mcp_pin=i, on=0)
        r_test(r1)
        # r_test_simple(r1)
    cleanup()
