import time

from zpyclient.clients.c4node import C4Node
from zpyclient.clients.c4mib import C4MIB, MIBType
from zpyclient.fw_api.mibs.pqa.mtx.path import MtxPathMib
from zpyclient.fw_api.mibs.pqa.rtb.rel import RtbRelMib
from zpyclient.fw_api.mibs.pqa.lkb.path import LkbPathMib
from zpyclient.fw_api.mibs.pqa.lkb.rst import LkbRstMib
from zpyclient.protocol.ip.ip_connection import IPConnection


class LoadRackError(StandardError):
    """ Inappropriate argument value (of correct type). """
    def __init__(self, *args, **kwargs): # real signature unknown
        pass


class LoadRack():
    def __init__(self, ip_of_control_pi):
        self.ip_of_control_pi = ip_of_control_pi
        self.comms = IPConnection(self.ip_of_control_pi)
        self.node = self.comms.nodes[self.ip_of_control_pi]
        """:type: C4Node"""
        assert isinstance(self.node, C4Node), 'Node not found for ip: {}.  Exiting'.format(self.ip_of_control_pi)

    def disconnect(self):
        self.comms.disconnect()

    def set_load_path(self, device_index, load_bank, load_mask):
        packet_number = self.comms.get_next_sequence_number()
        mib = MtxPathMib(MIBType.SET, packet_number, device_index, load_bank, load_mask)
        return self.comms.send_mib(mib, wait_for_reply=True)

    def get_load_path(self):
        packet_number = self.comms.get_next_sequence_number()
        mib = MtxPathMib(MIBType.GET, packet_number)
        return self.comms.send_mib(mib, wait_for_reply=True)

    def get_device_power(self, device_index):
        packet_number = self.comms.get_next_sequence_number()
        mib = RtbRelMib(MIBType.GET, packet_number, device_index)
        return self.comms.send_mib(mib, wait_for_reply=True)

    def turn_on_device(self, device_index):
        packet_number = self.comms.get_next_sequence_number()
        mib = RtbRelMib(MIBType.SET, packet_number, device_index, RtbRelMib.PowerState.ON)
        return self.comms.send_mib(mib, wait_for_reply=True)

    def turn_off_device(self, device_index):
        packet_number = self.comms.get_next_sequence_number()
        mib = RtbRelMib(MIBType.SET, packet_number, device_index, RtbRelMib.PowerState.OFF)
        return self.comms.send_mib(mib, wait_for_reply=True)

    def set_linkBone_path(self, enable_disable, src_port, dest_port):
        packet_number = self.comms.get_next_sequence_number()
        mib = LkbPathMib(MIBType.SET, packet_number, enable_disable, src_port, dest_port)
        return self.comms.send_mib(mib, wait_for_reply=True)

    def reset_linkBone_paths(self):
        packet_number = self.comms.get_next_sequence_number()
        mib = LkbRstMib(MIBType.INVOKE, packet_number)
        return self.comms.send_mib(mib, wait_for_reply=True)

    def reset_load_paths(self):
        existing_paths = self.get_load_path()

        pass

if __name__ == '__main__':
    lr = LoadRack('192.168.1.139')

    # time.sleep(10)
    # print(lr.set_linkBone_path(1, 'C', 'L'))
    # time.sleep(3)
    # print(lr.reset_linkBone_paths())

    print(lr.turn_on_device(0x01))

    # print(lr.set_load_path(0x00, 0x02, 0x19))
    # print(lr.get_load_path())

    # print(lr.get_load_path())
    # print(lr.set_load_path(0x00, 0x02, 0x00))
    # time.sleep(5)
    # print(lr.get_load_path())
    # print(lr.set_load_path(0x00, 0x02, 0x00))
    # time.sleep(5)
    # print(lr.get_load_path())

    # print(lr.get_device_power(0x03))

    # print(lr.set_load_path(0x00, 0x01, 0x03))
    # print(lr.set_load_path(0x00, 0x02, 0x01))

    # time.sleep(10)
    # print(lr.mtx_path('00', '02', '03'))
    # time.sleep(5)
    # print(lr.reset_paths())

    time.sleep(1)
    lr.disconnect()
