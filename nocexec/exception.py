"""
Main exceptions module for nocexec
"""


class NOCExecError(Exception):
    """
    The base exception class for the nocexec module. All other exceptions are
    inherited from this class.
    """
    pass


class SSHClientError(NOCExecError):
    """
    The base exception class for SSH client
    """
    pass


class TelnetClientError(NOCExecError):
    """
    The base exception class for Telnet client
    """
    pass


class NetConfClientError(NOCExecError):
    """
    The base exception class for NetConf client
    """
    pass


class SSHClientExecuteCmdError(SSHClientError):
    """
    The exception class for errors that occurred during the execution of
    commands
    """
    pass


class TelnetClientExecuteCmdError(TelnetClientError):
    """
    The exception class for errors that occurred during the execution of
    commands
    """
    pass


class NetConfClientExecuteCmdError(SSHClientError):
    """
    The exception class for errors that occurred during the execution of
    commands
    """
    pass
