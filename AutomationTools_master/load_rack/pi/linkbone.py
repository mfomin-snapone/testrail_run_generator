# !/usr/bin/env python3

# Author: Michael Kredt: <mkredt@control4.com>

# Import Statements
import string
import warnings
from enum import IntEnum
from enum import Enum
import pexpect
import time
import re
import logging

from c4common.pexpect_connections.pexpect_serial import SerialConnection
from c4common.utils.usbtty import usbtty

logger = logging.getLogger('pqa_logger')
logger.setLevel(logging.DEBUG)


class CommEnum(IntEnum):
    SERIAL = 0
    TELNET = 1


class LinkboneMatrixEnum(Enum):
    SINGLE = 'single'
    MULTI = 'multi'


class Linkbone8x8Matrix:
    """
    Works with Linkbone BNC 8x8 BNC Matrix (Single or Dual Matrix) Device via Telent or Serial communication
    """

    LINKBONE_DONE = re.compile('Done.')
    LINKBONE_PING = re.compile('Pong.')
    LINKBONE_DISCONNECT = re.compile('Connection closed by foreign host.')
    LINKBONE_SPECIFY_MASTER_PORT = re.compile('For master ports A to H you can only specify ports I to P')
    LINKBONE_SPECIFY_SLAVE_PORT = re.compile('For master ports I to P you can only specify ports I to P')
    LINKBONE_INVALID_PORT = re.compile('Invalid arguments. Please specify master port A to P and a set of slave ports '
                                       'separated by comma.')
    LINKBONE_MODE = re.compile('Mode: (single|multi)')
    LINKBONE_SLAVE_PORT_HEADER = re.compile('( {5}I {3}J {3}K {3}L {3}M {3}N {3}O {3}P {2})')
    LINKBONE_MASTER_PORT_ROW = re.compile('([A-H]) - ((On|Off) +){8}')
    LINKBONE_MASTER_PORT_STATUS = re.compile('(On|Off)')

    master_ports = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']
    slave_ports = ['I', 'J', 'K', 'L', 'M', 'N', 'O', 'P']

    def __init__(self, comm_addr: str=None, comm_port: str=None, comm_type=CommEnum.TELNET, baud_rate: int=None):
        """
        Initialize the Linkbone8x8Matrix object

        :param comm_addr: String representing the IP address of the Linkbone device
        :param comm_port: String representing the IP address port or serial port being used
        :param comm_type: String or CommEnum representing communication type used
        :param baud_rate: Integer represeting baud rate of serial connection
        """

        # Perform a test to ensure valid types for parameters received. Pending the comm_type value, certain values
        # will not be useful, as such a conditional is used to ensure the necessary value exists per comm_type
        assert (type(comm_addr) is str or type(comm_addr) is int or comm_addr is None)
        assert (type(comm_port) is str or type(comm_port) is int)
        assert (type(comm_type) is CommEnum or type(comm_type) is str)
        assert (type(baud_rate) is int or baud_rate is None)

        if comm_type is CommEnum.TELNET:
            assert comm_addr
        elif comm_type is CommEnum.SERIAL:
            assert baud_rate

        logger.debug("linkbone address {} Port {} type {}".format(comm_addr, comm_port, comm_type))

        self.linkbone_connection = None
        self.comm_addr = None
        self.comm_port = None
        self.comm_type = None
        self.baud_rate = None
        self.matrix_mode = None
        self.current_connections = None

        self.comm_addr = comm_addr
        self.comm_port = comm_port
        self.comm_type = comm_type if type(comm_type) is CommEnum else CommEnum.TELNET if comm_type is 'TELNET' \
            else CommEnum.SERIAL
        self.baud_rate = baud_rate

        if comm_type == CommEnum.SERIAL or 'SERIAL' in comm_type:
            # Pending information provided, raise an exception or initiate connection to serial port
            logger.debug("Connecting Telnet.....")

            if comm_addr is None or comm_port is None:
                raise ValueError('Missing Serial Number or Port')
            if comm_addr is not None:
                self.linkbone_connection = usbtty.normalize_serial_port(comm_addr)
            if comm_port is not None:
                self.linkbone_connection = usbtty.normalize_serial_port(comm_port)

        elif comm_type == CommEnum.TELNET or 'TELNET' in comm_type:
            # Construct and issue telnet command, begin _keep_alive loop
            logger.debug("Connecting Telnet.....")
            comm_port = comm_port if comm_port is not None else 23
            cmd = 'telnet %s %s' % (comm_addr, comm_port)

            connected = None
            while connected is None:
                self.linkbone_connection = pexpect.spawnu(cmd)
                connected = self.linkbone_connection.expect([re.compile('Hello. Please enter your command:\r\n'),
                                                             pexpect.TIMEOUT, pexpect.EOF], timeout=10)
                logger.debug("Connection Status {}".format(str(connected)))
        else:
            logger.error("Failed to connect {}".format(str(comm_addr)))


    def __del__(self):
        """
        Delete the Linkbone8x8Matrix object
    
        :return:
        """
        if self.comm_type is CommEnum.TELNET:
            self.linkbone_connection.close()
        elif self.comm_type is CommEnum.SERIAL:
            pass
        else:
            print('COMM_TYPE NOT VALID TYPE ON DEL')
    
    
    def _check_connection(self):
        """
        Checks the telnet connection is still alive by pinging the device. If it is not alive it will re-establish
        the connection
    
        :return:
        """
    
        self.linkbone_connection.sendline('ping')
        result = self.linkbone_connection.expect(['Pong.', pexpect.TIMEOUT, pexpect.EOF], timeout=1)
    
        if result == 2 or result == 1:
            cmd = 'telnet %s %s' % (self.comm_addr, self.comm_port)
            connected = None
    
            while connected is None:
                self.linkbone_connection = pexpect.spawnu(cmd)
                connected = self.linkbone_connection.expect([re.compile('Hello. Please enter your command:\r\n'),
                                                             pexpect.TIMEOUT, pexpect.EOF], timeout=10)
        else:
            pass

    def _get_device_status(self)->list:
        """
        Functions obtains status information about the matrix from the device

        :return:
        """

        self._check_connection()

        # If the firmware for the device is updated, check these patterns against the output from a manual command test
        status_patterns = [Linkbone8x8Matrix.LINKBONE_MODE, Linkbone8x8Matrix.LINKBONE_SLAVE_PORT_HEADER,
                           Linkbone8x8Matrix.LINKBONE_MASTER_PORT_ROW, pexpect.TIMEOUT, pexpect.EOF]
        status_timeout = 1

        status_text = []
        self.linkbone_connection.sendline('status')

        for line_count in range(0, 10):
            self.linkbone_connection.expect(status_patterns, timeout=status_timeout)

            status_text.append(self.linkbone_connection.match.group(0))

        return status_text

    def set_mode(self, matrix_mode: LinkboneMatrixEnum=LinkboneMatrixEnum.SINGLE):
        """
        Set the mode of the Linkbone 8x8 BNC device.
    
        :param matrix_mode: Receives a LinkboneMatrixEnum which determines single (one-to-one) or multi (one-to-many)
        operation.
        :return:
        """
    
        self.linkbone_connection.sendline('mode %s' % matrix_mode.value)
        self.linkbone_connection.expect([Linkbone8x8Matrix.LINKBONE_DONE, pexpect.TIMEOUT, pexpect.EOF], timeout=1)
    
    
    def set_path(self, enable: int, src_port: str, dst_ports: [list, tuple] = None):
        """
        Enable connection between source and destination ports provided
    
        :param enable: An integer representing whether to enable or disable port connections
        :param src_port: A string representing a single source port
        :param dst_ports: A list or tuple of string(s) representing destination port(s)
        :return:
        """
    
        assert (isinstance(enable, int))
        assert (isinstance(src_port, str))
        if dst_ports:
            assert (isinstance(dst_ports, (list, tuple)))
        self._check_connection()
    
        on_patterns = [Linkbone8x8Matrix.LINKBONE_DONE, Linkbone8x8Matrix.LINKBONE_SPECIFY_MASTER_PORT,
                       Linkbone8x8Matrix.LINKBONE_SPECIFY_SLAVE_PORT, Linkbone8x8Matrix.LINKBONE_INVALID_PORT,
                       pexpect.TIMEOUT, pexpect.EOF]
    
        if enable:
            if dst_ports:
                self.linkbone_connection.sendline('on %s, %s' % (src_port, ' '.join(dst_ports)))
            else:
                self.linkbone_connection.sendline('on %s, %s' % (src_port, ' '.join(Linkbone8x8Matrix.slave_ports)))
        else:
            if dst_ports:
                self.linkbone_connection.sendline('off %s, %s' % (src_port, ' '.join(dst_ports)))
            else:
                self.linkbone_connection.sendline('off %s, %s' % (src_port, ' '.join(Linkbone8x8Matrix.slave_ports)))
    
        self.linkbone_connection.expect(on_patterns, timeout=1)
        time.sleep(1)    
    
    def send_reset(self):
        """
        Resets all source-destination port connections
    
        :return:
        """
    
        self._check_connection()
    
        self.linkbone_connection.sendline('reset')
        self.linkbone_connection.expect([Linkbone8x8Matrix.LINKBONE_DONE, pexpect.TIMEOUT, pexpect.EOF], timeout=1)
    
    
    def get_status(self):
        """
        WARNING: Function will be deprecated as the usefulness is being replaced with get_mode() and get_path()

        Prints all information about the status of the matrix
    
        IMPORTANT NOTE: This function is being implemented with the current supposition that it will be built upon
        when time becomes more available. For now this function exists mostly for more convenient debugging.
    
        :return:
        """
        warnings.warn('get_status() has been deprecated, use get_mode() and get_path() instead', DeprecationWarning)

        self._check_connection()
    
        # If the firmware for the device is updated, check these patterns against the output from a manual command test
        status_patterns = [Linkbone8x8Matrix.LINKBONE_MODE, Linkbone8x8Matrix.LINKBONE_SLAVE_PORT_HEADER,
                           Linkbone8x8Matrix.LINKBONE_MASTER_PORT_ROW, pexpect.TIMEOUT, pexpect.EOF]
        status_timeout = 1
    
        status_text = []
        self.linkbone_connection.sendline('status')
    
        for line_count in range(0, 10):
            self.linkbone_connection.expect(status_patterns, timeout=status_timeout)
    
            status_text.append(self.linkbone_connection.match.group(0))
            # print(self.linkbone_connection.match.groups())
    
        # print(status_text)

    def get_mode(self)->LinkboneMatrixEnum:
        """
        Returns the current operating mode of the Linkbone matrix, being SINGLE or MULTI

        :return: an enumerated value describing the mode of the server
        """

        # Obtain status information and prune to necessary text
        connection_info = self._get_device_status()
        connection_info = connection_info[0]

        if str(LinkboneMatrixEnum.SINGLE.value) in connection_info:
            matrix_mode = LinkboneMatrixEnum.SINGLE
        elif str(LinkboneMatrixEnum.MULTI.value) in connection_info:
            matrix_mode = LinkboneMatrixEnum.MULTI
        else:
            raise ValueError('Linkbone 8x8 BNC Matrix returned corrupt status information')

        return matrix_mode

    def get_path(self, input_port=None)->dict:
        """
        Returns the current path(s) for the input designated, if none is given all paths will be returned

        :param input_port:
        :return: an dictionary describing the path(s) specified by input
        """

        # Ensure proper data type for provided input port
        if input_port:
            if type(input_port) is str:
                if string.ascii_uppercase.index(input_port) in range(0, 8):
                    port = string.ascii_uppercase.index(input_port)
                else:
                    raise ValueError('Input port {} is not in range of input ports'.format(input_port))
            elif type(input_port) is int:
                if input_port in range(0, 8):
                    port = input_port
                else:
                    raise ValueError('Input port at index {} is not in tange of input ports'.format(input_port))
            else:
                raise ValueError('Input port {} given for Linkbone is not valid value type'.format(input_port))

        # Obtain status information and prune to necessary text
        connection_info = self._get_device_status()
        connection_info = connection_info[2:]
        port_status = {}

        if input_port:
            input_status = re.findall(self.LINKBONE_MASTER_PORT_STATUS, connection_info[port])

            output_status = []
            for status in range(0, 8):
                if input_status[status] == 'On':
                    output_status.append(string.ascii_uppercase[status + 8])

            if output_status:
                port_status[string.ascii_uppercase[port]] = output_status

        else:
            # Run through rows of statys returned by the device, determine if the input port is connected to output port
            for master_port in range(0, 8):
                input_status = re.findall(self.LINKBONE_MASTER_PORT_STATUS, connection_info[master_port])

                # With matches found for status, run through statuses and add ASCII character of connected ports to list
                output_status = []
                for status in range(0, 8):
                    if input_status[status] == 'On':
                        output_status.append(string.ascii_uppercase[status+8])

                # If the input port was connected to an output, add to returning dictionary, else ignore
                if output_status:
                    port_status[string.ascii_uppercase[master_port]] = output_status

        # print(port_status)
        return port_status

    def send_reset(self):
        """
        Resets all source-destination port connections

        :return:
        """

        self._check_connection()

        self.linkbone_connection.sendline('reset')
        self.linkbone_connection.expect([Linkbone8x8Matrix.LINKBONE_DONE, pexpect.TIMEOUT, pexpect.EOF], timeout=1)

    def send_ping(self):
        """
        Checks network or serial connection to the matrix
    
        :return:
        """
    
        self._check_connection()
    
        self.linkbone_connection.sendline('ping')
        self.linkbone_connection.expect([Linkbone8x8Matrix.LINKBONE_PING, pexpect.TIMEOUT, pexpect.EOF], timeout=1)
    
    
    def disconnect(self):
        """
        Terminates current session, Telent or Serial
    
        :return:
        """
    
        self.linkbone_connection.sendline('quit')
        self.linkbone_connection.expect([Linkbone8x8Matrix.LINKBONE_DISCONNECT,
                                         pexpect.TIMEOUT, pexpect.EOF], timeout=1)


if __name__ == '__main__':
    t_linkbone = Linkbone8x8Matrix('192.168.1.8', '23', CommEnum.TELNET)
    # t_linkbone = Linkbone8x8Matrix(None, None, None)

    # Begin Sample Functionality Sequence for Telnet
    t_linkbone.send_ping()
    t_linkbone.set_mode(LinkboneMatrixEnum.MULTI)
    t_linkbone.get_mode()
    t_linkbone.set_mode(LinkboneMatrixEnum.SINGLE)
    t_linkbone.get_mode()
    t_linkbone.set_mode(LinkboneMatrixEnum.MULTI)
    t_linkbone.get_mode()

    #   Test List Acceptance Functionality
    t_linkbone.set_path(1, 'A', Linkbone8x8Matrix.slave_ports)
    t_linkbone.get_path()
    t_linkbone.get_path('A')
    t_linkbone.get_path(0)
    t_linkbone.send_reset()
    t_linkbone.get_path()

    #   Test Integer Acceptance Functionality
    t_linkbone.set_path(1, 'A', Linkbone8x8Matrix.slave_ports)
    t_linkbone.get_path('A')
    t_linkbone.get_path(0)
    t_linkbone.send_reset()

    #   Test Sample Sequence
    t_linkbone.get_status()
    t_linkbone.set_path(1, 'A', ('I', 'J'))
    t_linkbone.set_path(1, 'H', ('M', 'N'))
    t_linkbone.get_path()
    t_linkbone.get_path('A')
    t_linkbone.get_path(0)
    t_linkbone.get_path('H')
    t_linkbone.get_path(7)
    t_linkbone.set_path(1, 'A', ('K', 'L'))
    t_linkbone.set_path(1, 'H', ('O', 'P'))
    t_linkbone.get_path()
    t_linkbone.get_path('A')
    t_linkbone.get_path(0)
    t_linkbone.get_path('H')
    t_linkbone.get_path(7)

    t_linkbone.set_path(0, 'A', ('I', 'J'))
    t_linkbone.set_path(0, 'H', ('M', 'N'))
    t_linkbone.get_path()
    t_linkbone.get_path('A')
    t_linkbone.get_path(0)
    t_linkbone.get_path('H')
    t_linkbone.get_path(7)

    t_linkbone.set_path(0, 'A', ('K', 'L'))
    t_linkbone.set_path(0, 'H', ('O', 'P'))
    t_linkbone.get_path()
    t_linkbone.get_path('A')
    t_linkbone.get_path(0)
    t_linkbone.get_path('H')
    t_linkbone.get_path(7)

    t_linkbone.set_path(1, 'A', ['M', 'N', 'O', 'P'])
    t_linkbone.set_path(1, 'H', ['I', 'J', 'K', 'L'])
    t_linkbone.get_path()
    t_linkbone.get_path('A')
    t_linkbone.get_path(0)
    t_linkbone.get_path('H')
    t_linkbone.get_path(7)
    t_linkbone.send_reset()
    t_linkbone.get_path()
    t_linkbone.get_path('A')
    t_linkbone.get_path(0)
    t_linkbone.get_path('H')
    t_linkbone.get_path(7)

    t_linkbone.set_path(1, 'A')
    t_linkbone.get_path()
    t_linkbone.get_path('A')
    t_linkbone.get_path(0)
    t_linkbone.get_path('H')
    t_linkbone.get_path(7)
    t_linkbone.set_path(0, 'A')
    t_linkbone.get_path()
    t_linkbone.get_path('A')
    t_linkbone.get_path(0)
    t_linkbone.get_path('H')
    t_linkbone.get_path(7)

    # #   Begin Master-Master Sequence Test
    # for master_port_0 in range(0, 8):
    #     for master_port_1 in range(0, 8):
    #         slv_lst = []
    #         for p in range(0, master_port_1 + 1):
    #             slv_lst.append(master_ports[p])
    #
    #         t_linkbone.set_on(master_ports[master_port_0], master_ports[master_port_1])
    #         t_linkbone.send_reset()
    #         t_linkbone.set_on(master_ports[master_port_0], dst_list=tuple(slv_lst))
    #         t_linkbone.send_reset()
    #
    # #   Begin Master-Slave Sequence Test
    # for master_port_0 in range(0, 8):
    #     for slave_port_0 in range(0, 8):
    #         slv_lst = []
    #         for p in range(0, slave_port_0 + 1):
    #             slv_lst.append(slave_ports[p])
    #
    #         t_linkbone.set_on(master_ports[master_port_0], slave_ports[slave_port_0])
    #         t_linkbone.send_reset()
    #         t_linkbone.set_on(master_ports[master_port_0], dst_list=tuple(slv_lst))
    #         t_linkbone.send_reset()
    #
    # #   Begin Slave-Master Sequence Test
    # for slave_port_0 in range(0, 8):
    #     for master_port_0 in range(0, 8):
    #         slv_lst = []
    #         for p in range(0, master_port_0 + 1):
    #             slv_lst.append(master_ports[p])
    #
    #         t_linkbone.set_on(slave_ports[slave_port_0], master_ports[master_port_0])
    #         t_linkbone.send_reset()
    #         t_linkbone.set_on(slave_ports[slave_port_0], dst_list=tuple(slv_lst))
    #         t_linkbone.send_reset()
    #
    # #   Begin Slave-Slave Sequence Test
    # for slave_port_0 in range(0, 8):
    #     for slave_port_1 in range(0, 8):
    #         slv_lst = []
    #         for p in range(0, slave_port_1 + 1):
    #             slv_lst.append(slave_ports[p])
    #
    #         t_linkbone.set_on(slave_ports[slave_port_0], slave_ports[slave_port_1])
    #         t_linkbone.send_reset()
    #         t_linkbone.set_on(slave_ports[slave_port_0], dst_list=tuple(slv_lst))
    #         t_linkbone.send_reset()

    # End Sample Tests, Disconnect and Delete Testing Object
    t_linkbone.disconnect()
    del t_linkbone
