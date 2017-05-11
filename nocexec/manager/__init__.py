"""
Module with a class manager to manage various devices through the driver.

    - Manager - class for managing network devices
"""

import re
import nocexec.drivers
from nocexec.helpers import rpc_to_dict, unix_mac
from nocexec import ContextClient
from nocexec.exception import NOCExecError

__all__ = ['ManagerError', 'Manager']


class ManagerError(NOCExecError):
    """
    The base exception class for Juniper JunOS driver
    """
    pass

# pylint: disable=too-many-instance-attributes
class Manager(ContextClient):
    """
    Managing network devices through drivers.

        :param driver: driver for device management from module nocexec.drivers
        :param device: domain or ip address of device (default: "")
        :param login: username for authorization on device (default: "")
        :param password: password for authorization on device (default: "")
        :param port: port number for connection (default: from driver)
        :param timeout: timeout waiting for connection (default: from driver)
        :param protocol: protocol for connection (default: from driver)
        :type driver: string
        :type device: string
        :type login: string
        :type password: string
        :type port: int
        :type timeout: int
        :type protocol: string

    :Example:

    >>> from nocexec.manager import Manager
    >>> with Manager("CiscoIOS", "192.168.0.1", "user", "password") as cli:
    ...     for l in cli.get_fdb():
    ...         print(l)
    {'mac': 'e2:05:71:be:c2:40', 'vlan': '10', 'port': 'Gi1/0'}
    {'mac': 'e2:0d:cd:16:3a:1b', 'vlan': '12', 'port': 'Gi1/0'}
    {'mac': 'e2:36:6b:55:14:20', 'vlan': '10', 'port': 'Gi1/0'}
    {'mac': 'e2:63:2b:19:73:ad', 'vlan': '14', 'port': 'Gi1/0'}
    {'mac': 'e2:71:f8:7e:ae:11', 'vlan': '10', 'port': 'Gi1/0'}
    {'mac': 'e2:78:3e:c9:da:8a', 'vlan': '10', 'port': 'Gi1/0'}
    {'mac': 'e2:7b:39:2b:3b:66', 'vlan': '10', 'port': 'Gi1/0'}

    .. note::
        raises exceptions inherited from ManagerError exception
    """

    # pylint: disable=too-many-arguments
    def __init__(self, driver, device, login, password, port=None,
                 timeout=None, protocol=None):
        self._driver = nocexec.drivers.drivers.get(driver)
        if self._driver is None:
            raise ManagerError("driver '{0}' not found".format(driver))
        self._device = device
        self._login = login
        self._password = password
        self._port = port or self._driver.get('defaults').get('port')
        self._timeout = timeout or self._driver.get('defaults').get('timeout')
        self._protocol = protocol or self._driver.get(
            'defaults').get('protocol')
        self._commands = self._driver.get('commands')
        self.conn = None

    def connect(self):
        """Initialize client for protocol"""
        try:
            self.conn = self._driver.get('class')(device=self._device,
                                                  login=self._login,
                                                  password=self._password,
                                                  port=self._port,
                                                  timeout=self._timeout,
                                                  protocol=self._protocol)
            self.conn.connect()
        except NOCExecError as err:
            raise ManagerError(err)

    def disconnect(self):
        """Close the connection if the client is initialized."""
        if self.conn is not None:
            self.conn.disconnect()

    @staticmethod
    def _convert_statuses(elem):
        """Convert statuses strings from defferent device's format to
        boolean"""
        elem["admin_status"] = elem.get("admin_status") in ["up", "E", "A"]
        elem["oper_status"] = elem.get("oper_status") in ["up", "E", "A"]
        return elem

    def get_ports(self):
        """
        Get port list with statuses from device.

            :returns: dict of MAC ({'oper_status': True,
                                    'description': 'testPortName',
                                    'admin_status': True,
                                    'name': 'Gi0/0/1'})
            :rtype: dict
        """
        port_list = list()
        cmd_conf = self._commands.get("get_ports")
        result = self.conn.view(cmd_conf.get("cmd"), timeout=60)
        if cmd_conf.get("parser_type") == "regexp":
            for line in result:
                match = re.search(cmd_conf.get("parser"), line)
                if match is not None:
                    port_list.append(match.groupdict())
        elif cmd_conf.get("parser_type") == "etree":
            for line in rpc_to_dict(result, cmd_conf.get("parser")):
                port_list.append({"admin_status": line.get("admin-status"),
                                  "oper_status": line.get("oper-status"),
                                  "description": line.get("description"),
                                  "name": line.get("name")})
        # convert statuses to boolean
        return list(map(self._convert_statuses, port_list))

    def get_fdb(self):
        """
        Get mac address table from device.

            :returns: dict of MAC ({'mac': 'fe:84:e9:4c:91:37',
                                    'vlan': '110',
                                    'port': '17'})
            :rtype: dict
        """
        mac_table = list()
        cmd_conf = self._commands.get("get_fdb")
        result = self.conn.view(cmd_conf.get("cmd"), timeout=60)
        if cmd_conf.get("parser_type") == "regexp":
            for line in result:
                match = re.search(cmd_conf.get("parser"), line)
                if match is not None:
                    g_match = match.groupdict()
                    g_match['mac'] = unix_mac(g_match.get('mac'))
                    mac_table.append(g_match)
        elif cmd_conf.get("parser_type") == "etree":
            for line in rpc_to_dict(result, cmd_conf.get("parser")):
                mac = unix_mac(line.get("mac-address"))
                intf = line.get("mac-interfaces-list").get("mac-interfaces")
                if mac:
                    mac_table.append({"mac": mac,
                                      "port": intf,
                                      "vlan": line.get("mac-vlan")})
        # convert statuses to boolean
        return mac_table

    def get_vlans(self):
        """
        Get list of vlans from device.

            :returns: dict of vlans ({'tag': '1509', 'name': 'vlanName'})
            :rtype: dict
        """
        vlan_list = list()
        cmd_conf = self._commands.get("get_vlans")
        result = self.conn.view(cmd_conf.get("cmd"), timeout=60)
        if cmd_conf.get("parser_type") == "regexp":
            for line in result:
                match = re.search(cmd_conf.get("parser"), line)
                if match is not None:
                    vlan_list.append(match.groupdict())
        elif cmd_conf.get("parser_type") == "etree":
            for line in rpc_to_dict(result, cmd_conf.get("parser")):
                vlan_list.append({"name": line.get("vlan-name"),
                                  "tag": line.get("vlan-tag")})
        # convert statuses to boolean
        return vlan_list
