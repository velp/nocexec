"""
Driver classes for Extreme networks devices.

  - XOS - driver for extreme XOS operating system
"""


import logging
import re
from nocexec.drivers.base import NOCExecDriver, NOCExecDriverError
from nocexec.exception import SSHClientError, TelnetClientError, \
    NOCExecError, SSHClientExecuteCmdError, TelnetClientExecuteCmdError


LOG = logging.getLogger('nocexec.drivers.extreme')

__all__ = ['XOSError', 'XOSCommandError', 'XOS']


class XOSError(NOCExecError):
    """
    The base exception class for Extreme XOS driver
    """
    pass


class XOSCommandError(XOSError):
    """
    The exception class for command errors
    """
    pass


class XOS(NOCExecDriver):  # pylint: disable=too-many-instance-attributes
    """
    A driver class for connecting to Cisco IOS devices using the SSH or Telnet
    protocol and executing commands.

        :param device: domain or ip address of device (default: "")
        :param login: username for authorization on device (default: "")
        :param password: password for authorization on device (default: "")
        :param port: port number for connection (default: 22)
        :param timeout: timeout waiting for connection (default: 5)
        :param protocol: use protocol ('ssh' or 'telnet') for
                         connection (default: "ssh")
        :type device: string
        :type login: string
        :type password: string
        :type port: int
        :type timeout: int
        :type protocol: string

    :Example:

    >>> from nocexec.drivers.extreme import XOS
    >>> with XOS("192.168.0.1", "user", "password") as cli:
    ...     for l in cli.view("show system mtu"):
    ...         print(l)
    ['', 'SysName:          extreme-switch', ............

    .. seealso:: :class:`nocexec.drivers.juniper.JunOS` and
                 :class:`nocexec.drivers.cisco.IOS`
    .. note::
        raises exceptions inherited from XOSError exception
    """

    def __init__(self, *args, **kwargs):
        try:
            super(XOS, self).__init__(driver_protocols=["ssh"],
                                      *args, **kwargs)
        except NOCExecDriverError as err:
            raise XOSError(err)
        self._cmd_num = 2
        self._last_cmd = ""

    def _prepare_shell(self):
        # disable clipaging, check permission level nad fill hostname
        self.cli.connection.sendline("disable clipaging")
        self.cli.connection.expect('.{0} #'.format(self._cmd_num))
        self._hostname = self.cli.connection.before.splitlines()[-1]

    @staticmethod
    def _is_error(cmd_result_lines):
        text = '|'.join(cmd_result_lines)
        errors = [r'Invalid .* detected.*[.]',
                  r'Error:.*[.]']
        for error in errors:
            if re.findall(error, text):
                return True
        return False

    def connect(self):
        """
        Connection to the device via the specified protocol.

        .. note::
            raises an exception XOSError if a connection error occurs.
        """
        super(XOS, self).init_client()
        try:
            self.cli.connect()
        except (SSHClientError, TelnetClientError) as err:
            raise XOSError(err)
        self._prepare_shell()

    def edit(self, command, **kwargs):
        """
        Since there is no configuration mode in the Extreme networks devices,
        this function is a wrapper over the view() function for driver
        compatibility.
        """
        return self.view(command, **kwargs)

    def view(self, command, **kwargs):
        """
        Running a command on the extreme XOS device with the expected result
        and error handling.

            :param command: sent command
            :param kwargs: arguments for client.execute() function
            :type command: string
            :type kwargs: dict
            :returns: list of lines with the result of the command execution
            :rtype: list of lines

        .. warning:: command is required argument
        .. note::
            raises an exception XOSError if connection not established.
            raises an exception XOSCommandError if an error occurs.
        """
        if self.cli is None:
            raise XOSError("no connection to the device")
        shell_prompt = self._hostname + ".{0} #"
        if command != self._last_cmd:
            self._cmd_num += 1
            self._last_cmd = command
        try:
            result = self.cli.execute(
                command=command, wait=[shell_prompt.format(self._cmd_num)],
                **kwargs)
            if self._is_error(result):
                raise XOSCommandError('\n'.join(result))
        except (SSHClientExecuteCmdError, TelnetClientExecuteCmdError) as err:
            raise XOSCommandError(err)
        return result

    def save(self):
        """
        Saving the primary configuration on the device

            :returns: True if configuration saved, False if not
            :rtype: bool

        .. note::
            not raises exceptions.
        """
        if self.cli is None:
            return False
        try:
            self.cli.execute(command="save configuration primary",
                             wait=["Do you want to save configuration to "
                                   "primary.cfg and overwrite it?"])
            self.cli.execute(command="Yes", wait=["Configuration saved to "
                                                  "primary.cfg successfully."])
            return True
        except (SSHClientExecuteCmdError, TelnetClientExecuteCmdError) as err:
            LOG.error("ExtremeXOS save configuration on device '%s' error: %s",
                      self._device, str(err))
            return False
