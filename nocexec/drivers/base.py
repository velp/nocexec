"""
Parent driver class from which other drivers are inherited
"""

import nocexec

__all__ = ['NOCExecDriver']


class NOCExecDriver(nocexec.ContextClient):  # pylint: disable=too-many-instance-attributes
    """
    Parent driver class from which other drivers are inherited
    """

    def __init__(self, device, login="", password="", port=22, timeout=5,  # pylint: disable=too-many-arguments
                 protocol="ssh"):
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
