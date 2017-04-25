"""
Driver classes for cisco devices.

  - IOS - driver for cisco IOS operating system
"""

import logging
from nocexec.drivers.base import NOCExecDriver
from nocexec.exception import SSHClientError, TelnetClientError, \
    NOCExecError, SSHClientExecuteCmdError, TelnetClientExecuteCmdError


LOG = logging.getLogger('nocexec.drivers.cisco')

__all__ = ['IOSError', 'IOSCommandError', 'IOS']


class IOSError(NOCExecError):
    """
    The base exception class for Cisco IOS driver
    """
    pass


class IOSCommandError(IOSError):
    """
    The exception class for command errors
    """
    pass


class IOS(NOCExecDriver):  # pylint: disable=too-many-instance-attributes
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

    >>> from nocexec.drivers.cisco import IOS
    >>> with IOS("192.168.0.1", "user", "password") as cli:
    ...     for l in cli.view("show system mtu"):
    ...         print(l)
    ['', 'System MTU size is 1500 bytes', 'System Jumbo MTU size is 1500
    bytes', 'System Alternate MTU size is 1500 bytes', 'Routing MTU size is
    1500 bytes']

    .. seealso:: :class:`nocexec.drivers.juniper.JunOS` and
                 :class:`nocexec.drivers.extreme.XOS`
    .. note::
        raises exceptions inherited from IOSError exception
    """

    def __init__(self, *args, **kwargs):
        super(IOS, self).__init__(*args, **kwargs)
        self._shell_prompt = "#"
        self._config_prompt = r"\(config.*?\)#"
        self._priv_mode = False
        self._config_mode = False

    def _prepare_shell(self):
        # disable clipaging, check permission level nad fill hostname
        shell_ends = ['>', '#']
        self.cli.connection.sendline("terminal length 0")
        answ = self.cli.connection.expect(shell_ends)
        self._hostname = self.cli.connection.before.splitlines()[-1]
        self._shell_prompt = self._hostname + "#"
        self._config_prompt = self._hostname + self._config_prompt
        self._priv_mode = bool(answ)

    def _enable_privileged(self):
        try:
            self.cli.execute("enable", wait=[self._hostname + "#"])
            self._shell_prompt = self._hostname + "#"
            self._priv_mode = True
            return True
        except (SSHClientExecuteCmdError, TelnetClientExecuteCmdError):
            return False

    def _disable_privileged(self):
        try:
            self.cli.execute("disable", wait=[self._hostname + ">"])
            self._shell_prompt = self._hostname + ">"
            self._priv_mode = False
            return True
        except (SSHClientExecuteCmdError, TelnetClientExecuteCmdError):
            return False

    def _enter_config(self):
        if not self._priv_mode and not self._enable_privileged():
            LOG.error("unregistered mode is used")
            return False
        if self._config_mode:
            return True
        try:
            self.cli.execute("configure terminal",
                             wait=[self._config_prompt])
            self._config_mode = True
            return True
        except (SSHClientExecuteCmdError, TelnetClientExecuteCmdError) as err:
            LOG.error("enter config mode error: %s", str(err))
            return False

    def _exit_config(self):
        if not self._config_mode:
            return True
        try:
            self.cli.execute("end", wait=[self._shell_prompt])
            self._config_mode = False
            return True
        except (SSHClientExecuteCmdError, TelnetClientExecuteCmdError) as err:
            LOG.error("enter config mode error: %s", str(err))
            return False

    def connect(self):
        """
        Connection to the device via the specified protocol.

        .. note::
            raises an exception IOSError if a connection error occurs.
        """
        super(IOS, self).init_client()
        try:
            self.cli.connect()
        except (SSHClientError, TelnetClientError) as err:
            raise IOSError(err)
        self._prepare_shell()

    def edit(self, command):
        """
        Running a command on the Cisco IOS device in configuration mode with
        the expected result and error handling. Before executing the command,
        the access level is checked and the configuration mode is enabled.

            :param command: sent command
            :type command: string
            :returns: list of lines with the result of the command execution
            :rtype: list of lines

        .. warning:: command is required argument
        .. note::
            raises an exception IOSError if connection not established.
            raises an exception IOSCommandError if an error occurs.
        """
        if self.cli is None:
            raise IOSError("no connection to the device")
        if not self._enter_config():
            raise IOSCommandError("can not enter configuration mode")
        try:
            result = self.cli.execute(
                command=command, wait=[self._config_prompt])
        except (SSHClientExecuteCmdError, TelnetClientExecuteCmdError) as err:
            raise IOSCommandError(err)
        return result

    def view(self, command):
        """
        Running a command on the Cisco IOS device in view mode with
        the expected result and error handling. Before executing the command,
        the configuration mode is disabled.

            :param command: sent command
            :type command: string
            :returns: list of lines with the result of the command execution
            :rtype: list of lines

        .. warning:: command is required argument
        .. note::
            raises an exception IOSError if connection not established.
            raises an exception IOSCommandError if an error occurs.
        """
        if self.cli is None:
            raise IOSError("no connection to the device")
        if not self._exit_config():
            raise IOSCommandError("can not exit the configuration mode")
        try:
            result = self.cli.execute(
                command=command, wait=[self._shell_prompt])
        except (SSHClientExecuteCmdError, TelnetClientExecuteCmdError) as err:
            raise IOSCommandError(err)
        return result

    def save(self):
        """
        Saving the configuration on the device

            :returns: True if configuration saved, False if not
            :rtype: bool

        .. note::
            not raises exceptions.
        """
        if self.cli is None:
            return False
        if not self._exit_config():
            return False
        try:
            self.cli.execute(command="write memory", wait=[r"\[OK\]"])
            return True
        except (SSHClientExecuteCmdError, TelnetClientExecuteCmdError) as err:
            LOG.error("CiscoIOS save configuration on device '%s' error: %s",
                      self._device, str(err))
            return False
