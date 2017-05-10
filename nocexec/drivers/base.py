"""
Parent driver class from which other drivers are inherited
"""

import nocexec
from nocexec.exception import NOCExecError

__all__ = ['NOCExecDriver', 'NOCExecDriverError']


class NOCExecDriverError(NOCExecError):
    """
    The base exception class for Juniper JunOS driver
    """
    pass

# pylint: disable=too-many-instance-attributes


class NOCExecDriver(nocexec.ContextClient):
    """
    Parent driver class from which other drivers are inherited
    """

    # pylint: disable=too-many-arguments
    def __init__(self, device, login="", password="",
                 port=22, timeout=5, protocol="ssh", driver_protocols=None):
        if driver_protocols is None or protocol not in driver_protocols:
            raise NOCExecDriverError("'{0}' protocol is not supported by "
                                     "the '{1}' driver. Supported "
                                     "protocols: {2}".format(
                                         protocol, self.__class__.__name__,
                                         driver_protocols))
        self._device = device
        self._login = login
        self._password = password
        self._port = port
        self._timeout = timeout
        self._protocol = nocexec.protocols.get(protocol)
        self._hostname = device
        self.cli = None

    def init_client(self):
        """Initialize client for protocol"""
        self.cli = self._protocol(device=self._device,
                                  login=self._login,
                                  password=self._password,
                                  port=self._port,
                                  timeout=self._timeout)

    def disconnect(self):
        """Close the connection if the client is initialized."""
        if self.cli is not None:
            self.cli.disconnect()
