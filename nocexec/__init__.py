#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
.. note::
    Why not use paramiko/escript/other non-interactive SSH client?

    Non-interactive SSH clients usually work only with Unix like SSH server.
    Example run exscript on Cisco switch with old version ISO:

    ```
    DEBUG:paramiko.transport:starting thread (client mode): 0xe12399d0L
    DEBUG:paramiko.transport:Local version/idstring: SSH-2.0-paramiko_2.1.2
    DEBUG:paramiko.transport:Remote version/idstring: SSH-1.99-Cisco-1.25
    INFO:paramiko.transport:Connected (version 1.99, client Cisco-1.25)
    DEBUG:paramiko.transport:kex algos:[u'diffie-hellman-group-exchange-sha1',
    u'diffie-hellman-group14-sha1', u'diffie-hellman-group1-sha1'] server key:
    [u'ssh-rsa'] client encrypt:[u'aes128-cbc', u'3des-cbc', u'aes192-cbc',
    u'aes256-cbc'] server encrypt:[u'aes128-cbc', u'3des-cbc', u'aes192-cbc',
    u'aes256-cbc'] client mac:[u'hmac-sha1', u'hmac-sha1-96', u'hmac-md5',
    u'hmac-md5-96'] server mac:[u'hmac-sha1', u'hmac-sha1-96', u'hmac-md5',
    u'hmac-md5-96'] client compress:[u'none'] server compress:[u'none']
    client lang:[u''] server lang:[u''] kex follows?False
    DEBUG:paramiko.transport:Kex agreed: diffie-hellman-group1-sha1
    DEBUG:paramiko.transport:Cipher agreed: aes128-cbc
    DEBUG:paramiko.transport:MAC agreed: hmac-md5
    DEBUG:paramiko.transport:Compression agreed: none
    DEBUG:paramiko.transport:kex engine KexGroup1 specified hash_algo <built-in
        function openssl_sha1>
    DEBUG:paramiko.transport:Switch to new keys ...
    DEBUG:paramiko.transport:userauth is OK
    INFO:paramiko.transport:Authentication (password) successful!
    DEBUG:paramiko.transport:[chan 0] Max packet in: 32768 bytes
    DEBUG:paramiko.transport:[chan 0] Max packet out: 4096 bytes
    DEBUG:paramiko.transport:Secsh channel 0 opened.
    DEBUG:paramiko.transport:[chan 0] Sesch channel 0 request ok
    DEBUG:paramiko.transport:[chan 0] Sesch channel 0 request ok
    ('RESPONSE:', 'show clock\r\n13:48:46.774 MSK Fri Mar 31 2017\r')
    DEBUG:paramiko.transport:EOF in transport thread
    ```

    The developers of the paramiko directly report that there is no support:
    http://www.paramiko.org/faq.html#paramiko-doesn-t-work-with-my-cisco-windows-or-other-non-unix-system

"""

import logging
import pexpect
from ncclient import manager
from ncclient.transport.errors import TransportError, AuthenticationError
from ncclient.operations.rpc import RPCError
from nocexec.exception import SSHClientError, TelnetClientError, \
    NetConfClientError, SSHClientExecuteCmdError, NetConfClientExecuteCmdError

LOG = logging.getLogger('nocexec')

__all__ = ['TelnetClient', 'SSHClient', 'NetConfClient']


class ContextClient(object):  # pylint: disable=too-few-public-methods
    """Context manager class for all clients and drivers"""

    def __enter__(self):
        self.connect()  # pylint: disable=no-member
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.disconnect()  # pylint: disable=no-member


class TelnetClient(ContextClient):  # pylint: disable=too-few-public-methods
    """
    A client class for connecting to devices using the telnet protocol and
    executing commands.
    """
    pass


class SSHClient(ContextClient):
    """
    A client class for connecting to devices using the SSH protocol and
    executing commands.

        :param device: domain or ip address of device (default: "")
        :param login: username for authorization on device (default: "")
        :param password: password for authorization on device (default: "")
        :param port: SSH port for connection
        :param timeout: timeout waiting for connection (default: 5)
        :type device: string
        :type login: string
        :type password: string
        :type port: int
        :type timeout: int

    :Example:

    >>> from nocexec import SSHClient
    >>> with SSHClient("192.168.0.1", "user", "password") as cli:
    ...     cli.execute("terminal length 0", wait=["#"])
    ...     cli.send("exit")
    ...
    ['terminal length 0', 'cisco-router']

    .. seealso:: :class:`TelnetClient` and :class:`NetConfClient`
    .. note::
        raises exceptions inherited from SSHClientError exception
    """

    # pylint: disable=too-many-arguments
    def __init__(self, device="", login="", password="", port=22, timeout=5):
        self.ssh_options = {"UserKnownHostsFile": "/dev/null",
                            "StrictHostKeyChecking": "no",
                            "PubkeyAuthentication": "no"}
        self.device = device
        self.port = port
        self.login = login
        self.password = password
        self.timeout = timeout
        self.connection = None

    def disconnect(self):
        """
        Close SSH connection.

        .. note::
            not raises exceptions.
        """
        self.connection.close()

    def connect(self):
        """
        Connection to the device via SSH protocol.

        .. note::
            raises an exception SSHClientError if a connection error occurs.
        """
        opts = " ".join(["-o%s=%s" % (k, v)
                         for k, v in self.ssh_options.items()])
        conn_cmd = 'ssh {0} -p {1} {2}@{3}'.format(
            opts, self.port, self.login, self.device)
        self.connection = pexpect.spawn(conn_cmd, timeout=self.timeout)
        LOG.debug("SSH client command: %s", conn_cmd)
        if self.connection is None:
            LOG.error("SSH spawn error to host %s", self.device)
            raise SSHClientError(
                "SSH spawn error to host {0}".format(self.device))
        answ = self.connection.expect(['.?assword.*:',
                                       pexpect.EOF, pexpect.TIMEOUT])
        # Catch password request
        if answ == 0:
            self.connection.sendline(self.password)
            answ = self.connection.expect(['>', '#', 'Permission denied',
                                           pexpect.EOF, pexpect.TIMEOUT])
            # Check promt
            if not answ > 1:
                LOG.debug("Connect and login successful on %s", self.device)
                return
            elif answ in [2, 3]:
                LOG.error("permission denied on %s", self.device)
                raise SSHClientError(
                    "Permission denied on {0}".format(self.device))
            elif answ == 4:
                LOG.error("timeout welcome shell %s", self.device)
                raise SSHClientError(
                    "Timeout wait welcome shell on {0}".format(self.device))
        # if EOF or Timeout
        elif answ == 1 or answ == 2:

            LOG.debug("timeout or EOF error wait password request on %s",
                      self.device)
            raise SSHClientError("Timeout or EOF error wait password request "
                                 "on {0}".format(self.device))

    def execute(self, command, wait=None, timeout=10):
        """
        Running a command on the device with the expected result and error
        handling.

            :param command: sent command
            :param wait: list of patterns expected from the
                         execution (default: None)
            :param timeout: timeout waiting patterns (default: 10)
            :type command: string
            :type wait: list
            :type timeout: int
            :returns: list of lines with the result of the command execution
            :rtype: list of lines

        .. warning:: command is required argument
        .. note::
            raises an exception SSHClientExecuteCmdError if an error occurs.
        """
        ex = [pexpect.TIMEOUT, pexpect.EOF]
        if isinstance(wait, list):
            ex = wait + ex
        LOG.debug("execute command '%s'", command)
        self.connection.sendline(command)
        answ = self.connection.expect(ex, timeout=timeout)
        LOG.debug("expect (regex): %s", ex)
        before = self.connection.before.splitlines()
        LOG.debug("lines before expect: %s", before)
        # Catch EOF
        if answ == len(ex) - 1:
            LOG.error("execute command '%s' EOF error", command)
            raise SSHClientExecuteCmdError(
                "Execute command '{0}' EOF error".format(command))
        # Catch timeout
        elif answ == len(ex) - 2:
            LOG.error("execute command '%s' timeout", command)
            raise SSHClientExecuteCmdError(
                "Execute command '{0}' timeout".format(command))
        return before

    def send(self, command):
        """
        NOT guaranteed sending a command to the device without waiting for
        the result.

            :param command: sent command
            :type command: string

        .. note::
            not raises exceptions.
        """
        LOG.debug("send command '%s'", command)
        self.connection.sendline(command)


# pylint: disable=too-many-instance-attributes
class NetConfClient(ContextClient):
    """
    A client class for connecting to devices using the NetConf protocol
    (RFC6241) and executing commands.

        :param device: domain or ip address of device (default: "")
        :param login: username for authorization on device (default: "")
        :param password: password for authorization on device (default: "")
        :param timeout: timeout waiting for connection (default: 5)
        :param exclusive: enable or disable using exclusive configuration
                          mode (default: True)
        :param ignore_rpc_errors: a list of the RPC error patterns that will be
                                  ignored (default: ["statement not found", "no
                                  entry for"])
        :type device: string
        :type login: string
        :type password: string
        :type timeout: int
        :type exclusive: bool
        :type ignore_rpc_errors: list

    :Example:

    >>> from nocexec import NetConfClient
    >>> with NetConfClient("192.168.0.1", "user", "password") as cli:
    ...     cli.view("show system uptime", tostring=True)
    ...     cli.validate()
    ...     if cli.compare() is not None:
    ...         cli.commit()
    ...
    '<rpc-reply message-id="urn:uuid:a89b27fb-209c-4e61-9a38-993b51b54eae">\n
    <system-uptime-information>\n
    <current-time>\n
    .....
    </current-time>\n
    </system-uptime-information>\n
    </rpc-reply>\n'

    .. seealso:: :class:`TelnetClient` and :class:`SSHClient`
    .. note::
        * Raises exceptions inherited from NetConfClientError exception.
        * Use an ignore_rpc_errors argument to set special rules for handling
          the RPC errors.
    """

    # pylint: disable=too-many-arguments
    def __init__(self, device="", login="", password="", timeout=5,
                 device_params=None, exclusive=True, ignore_rpc_errors=None):
        self.device = device
        self.login = login
        self.password = password
        self.timeout = timeout
        self.connection = None
        self.exclusive = exclusive
        self._configuration_lock = False
        self.device_params = device_params or {'name': 'junos'}
        if ignore_rpc_errors is None:
            self.ignore_rpc_errors = [
                # delete not existing configuration
                "statement not found",
                # clear not exist entry
                "no entry for"]

    def _ignored_rpc_error(self, error):
        """
        Check error ignored or not.

        :parapm error: RPC exception error
        :type error: ncclient.operations.rpc.RPCError

        :returns: True if text of error found in ignore_rpc_errors
                  False if text of error not found in ignore_rpc_errors
        :rtype: bool
        """
        error_str = str(error).strip()
        for pattern in self.ignore_rpc_errors:
            if pattern in error_str:
                return True
        return False

    def disconnect(self):
        """
        Close NetConf connection.

        .. note::
            not raises exceptions.
        """
        if self.exclusive:
            self.unlock()
        self.connection.close_session()

    def connect(self):
        """
        Connection to the device via NetConf protocol.

        .. note::
            raises an exception NetConfClientError if a connection error
            occurs.
        """
        try:
            self.connection = manager.connect(host=self.device,
                                              port=22,
                                              username=self.login,
                                              password=self.password,
                                              timeout=self.timeout,
                                              device_params=self.device_params,
                                              hostkey_verify=False)
        except AuthenticationError:
            LOG.error("authentication failed on '%s'", self.device)
            raise NetConfClientError(
                "Authentication failed on '{0}'".format(self.device))
        except TransportError as err:
            LOG.error("connection to '%s' error: %s", self.device, err)
            raise NetConfClientError(
                "Connection to '{0}' error: {1}".format(self.device, err))
        if self.connection is None:
            LOG.error("connection to '%s' error: manager return "
                      "None object", self.device)
            raise NetConfClientError("Connection to '{0}' error: manager "
                                     "return None object".format(self.device))
        if self.exclusive:
            LOG.debug("netconf use exclusive mode")
            self.lock()

    def _locking(self, action):
        """
        Lock (https://tools.ietf.org/html/rfc6241#section-7.5) and unlock
        (https://tools.ietf.org/html/rfc6241#section-7.6) configuration on
        device.

        :param action: name of action (must be "lock" and "unlock")
        :type action: string

        :returns: True, if the action is committed without errors
                  False, if errors occur
        :rtype: bool
        """
        try:
            if action == "unlock":
                lock_res = self.connection.unlock()
            else:
                lock_res = self.connection.lock()
            if lock_res.xpath('//ok'):
                self._configuration_lock = not self._configuration_lock
                LOG.debug("%s configuration on '%s'", action, self.device)
                return True
            else:
                LOG.error("configuration %s on '%s' error: unexpected "
                          "rpc-reply: %s", action, self.device,
                          lock_res.tostring)
        except RPCError as err:
            LOG.error("configuration %s on '%s' error: %s",
                      action, self.device, str(err))
        return False

    def lock(self):
        """
        Lock (https://tools.ietf.org/html/rfc6241#section-7.5) configuration on
        device.

        :returns: True, if the action is committed without errors
                  False, if errors occur
        :rtype: bool

        .. note::
            If the configuration has already been locked, then the lock is not
            retried
        """
        # config already locked
        if self._configuration_lock:
            return True
        return self._locking(action="lock")

    def unlock(self):
        """
        Unlock (https://tools.ietf.org/html/rfc6241#section-7.6) configuration
        on device.

        :returns: True, if the action is committed without errors
                  False, if errors occur
        :rtype: bool

        .. note::
            If the configuration has already been unlocked, then the unlock
            is not retried
        """
        # config not locked
        if not self._configuration_lock:
            return True
        return self._locking(action="unlock")

    def edit(self, command, tostring=False):
        """
        Run the command on the device with the configuration change (edit
        command).

        :param command: sent command
        :param tostring: result convert to string or not
        :type command: string
        :type bool: bool
        :returns: result of execute command
        :rtype: if tostring == True: string
                if tostring == False: xml.etree.ElementTree
        """
        LOG.debug("execute edit command '%s'", command)
        try:
            result = self.connection.load_configuration(
                action='set', config=[command])
            if tostring:
                return result.tostring
            return result
        except RPCError as err:
            if self._ignored_rpc_error(err):
                LOG.info("catch skiped RCP error: %s", str(err))
                return
            LOG.error("execute the editing command '%s' error: %s",
                      command, str(err))
            raise NetConfClientExecuteCmdError("Executing the editing command "
                                               "'{0}' error: "
                                               "{1}".format(command, err))

    def view(self, command, tostring=False):
        """
        Run the command on the device without the configuration change (view
        command).

        :param command: sent command
        :param tostring: result convert to string or not
        :type command: string
        :type bool: bool
        :returns: result of execute command
        :rtype: if tostring == True: string
                if tostring == False: xml.etree.ElementTree
        """
        LOG.debug("execute view command '%s'", command)
        try:
            if tostring:
                return self.connection.command(command).tostring
            return self.connection.command(command)
        except RPCError as err:
            if self._ignored_rpc_error(err):
                LOG.info("catch skiped RCP error: %s", str(err))
                return
            LOG.error("execute the view command '%s' error: %s",
                      command, str(err))
            raise NetConfClientExecuteCmdError("Execute the view command '{0}'"
                                               " error: "
                                               "{1}".format(command, err))

    def compare(self, version=0):
        """
        Compare configuration versions.

        :returns: differences between versions in unix diff format
        :rtype: string or None (if no differences)
        """
        result = self.connection.compare_configuration(version).xpath(
            '//configuration-information/configuration-output')
        if result[0].text and result[0].text.rstrip() != '':
            return result[0].text
        LOG.debug("running configuration and the candidate did not differ")
        return None

    def commit(self):
        """
        Commit (https://tools.ietf.org/html/rfc6241#section-8.4) configuration
        changes on device.

        :returns: boolean result of the commit
        :rtype: True, if commit without errors
                False, if errors occur
        """
        try:
            commit_res = self.connection.commit()
            if commit_res.xpath('//ok'):
                return True
        except RPCError as err:
            LOG.error("commit configuration on '%s' error: %s",
                      self.device, str(err))
        return False

    def validate(self):
        """
        Validate (https://tools.ietf.org/html/rfc6241#section-8.6)
        configuration on device.

        :returns: boolean result of the validate
        :rtype: True, if validate without errors
                False, if errors occur
        """
        try:
            self.connection.validate()
            return True
        except RPCError as err:
            LOG.error("configuration check on '%s' error: %s",
                      self.device, str(err))
            return False

# pylint: disable=invalid-name
protocols = {
    "ssh": SSHClient,
    "telnet": TelnetClient,
    "netconf": NetConfClient
}
