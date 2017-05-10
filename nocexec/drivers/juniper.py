"""
Driver classes for Juniper devices.

  - JunOS - driver for Juniper JunOS operating system
"""
import logging
from nocexec.drivers.base import NOCExecDriver, NOCExecDriverError
from nocexec.exception import NOCExecError, NetConfClientError, \
    NetConfClientExecuteCmdError


LOG = logging.getLogger('nocexec.drivers.juniper')

__all__ = ['JunOSError', 'JunOSCommandError', 'JunOS']


class JunOSError(NOCExecError):
    """
    The base exception class for Juniper JunOS driver
    """
    pass


class JunOSCommandError(JunOSError):
    """
    The exception class for command errors
    """
    pass


class JunOS(NOCExecDriver):
    """
    A driver class for connecting to Juniper JunOS devices using the NetConf
    protocol and executing commands.

        :param device: domain or ip address of device (default: "")
        :param login: username for authorization on device (default: "")
        :param password: password for authorization on device (default: "")
        :param port: port number for connection (default: 22)
        :param timeout: timeout waiting for connection (default: 5)
        :type device: string
        :type login: string
        :type password: string
        :type port: int
        :type timeout: int

    :Example:

    >>> from nocexec.drivers.juniper import JunOS
    >>> with JunOS("192.168.0.1", "user", "password") as cli:
    ...     for l in cli.view("show system uptime", tostring=True):
    ...         print(l)
    ['Current time: 2017-04-24 14:54:04 MSK', 'System booted: 2017-03-27
    11:34:59 MSK (4w0d 03:19 ago)'...............

    .. seealso:: :class:`nocexec.drivers.juniper.JunOS` and
                 :class:`nocexec.drivers.extreme.XOS`
    .. note::
        raises exceptions inherited from IOSError exception
    """

    def __init__(self, *args, **kwargs):  # pylint: disable=too-many-arguments
        try:
            super(JunOS, self).__init__(driver_protocols=["netconf"],
                                        *args, **kwargs)
        except NOCExecDriverError as err:
            raise JunOSError(err)

    def connect(self):
        """
        Connection to the device via the specified protocol.

        .. note::
            raises an exception JunOSError if a connection error occurs.
        """
        self.cli = self._protocol(device=self._device,
                                  login=self._login,
                                  password=self._password,
                                  timeout=self._timeout,
                                  exclusive=False,
                                  device_params={'name': 'junos'})
        try:
            self.cli.connect()
        except NetConfClientError as err:
            raise JunOSError(err)
        # only exclusive mode
        if not self.cli.lock():
            raise JunOSError("configuration lock error")

    def disconnect(self):
        """
        Unlock configuration and close connection.

        .. note::
            not raises exceptions.
        """
        if self.cli is not None:
            self.cli.unlock()
            self.cli.disconnect()

    def edit(self, command, tostring=False):
        """
        Running a command on the Juniper JunOS device in configuration mode
        with the expected result and error handling.

            :param command: sent command
            :param tostring: enable or disable converting to
                             string (default: False)
            :type command: string
            :type tostring: bool
            :returns: result of the command execution
            :rtype: list of lines or etree Element (if tostring == False)

        .. warning:: command is required argument
        .. note::
            raises an exception JunOSError if connection not established.
            raises an exception JunOSCommandError if an error occurs.
        """
        if self.cli is None:
            raise JunOSError("no connection to the device")
        try:
            result = self.cli.edit(command=command, tostring=tostring)
        except NetConfClientExecuteCmdError as err:
            raise JunOSCommandError(err)
        return result

    def view(self, command, tostring=False):
        """
        Running a command on the Juniper JunOS device in view mode
        with the expected result and error handling.

            :param command: sent command
            :param tostring: enable or disable converting to
                             string (default: False)
            :type command: string
            :type tostring: bool
            :returns: result of the command execution
            :rtype: list of lines or etree Element (if tostring == False)

        .. warning:: command is required argument
        .. note::
            raises an exception JunOSError if connection not established.
            raises an exception JunOSCommandError if an error occurs.
        """
        if self.cli is None:
            raise JunOSError("no connection to the device")
        try:
            result = self.cli.view(command=command, tostring=tostring)
        except NetConfClientExecuteCmdError as err:
            raise JunOSCommandError(err)
        return result

    def save(self):
        """
        Saving the configuration on the device. Before saving, the
        configuration is checked for errors, and if any changes were made. If
        no changes were made, the save command is not called on the device,
        but the function returns true.

            :returns: True if configuration saved, False if not
            :rtype: bool

        .. note::
            not raises exceptions.
        """
        if self.cli.validate():
            if self.cli.compare() is not None:
                if not self.cli.commit():
                    LOG.error("don't commit configuration on '%s'",
                              self._device)
                    return False
            return True
        else:
            LOG.error("error in device configuration")
            return False
