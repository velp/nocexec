import logging
import nocexec.drivers
from nocexec.exception import NOCExecError, NetConfClientError, \
    NetConfClientExecuteCmdError


LOG = logging.getLogger('nocexec.drivers.juniper')


class JunOSError(NOCExecError):
    pass


class JunOSCommandError(JunOSError):
    pass


class JunOS:

    def __init__(self, device, login="", password="", timeout=5):
        self.device = device
        self.login = login
        self.password = password
        self.timeout = timeout
        self.cli = None
        # now support only netconf for JunOS
        self.protocol = nocexec.drivers.protocols.get("netconf")

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.disconnect()

    def connect(self):
        self.cli = self.protocol(device=self.device,
                                 login=self.login,
                                 password=self.password,
                                 timeout=self.timeout,
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
        if self.cli is not None:
            self.cli.unlock()
            self.cli.disconnect()

    def edit(self, command, tostring=False):
        if self.cli is None:
            raise JunOSError("no connection to the device")
        try:
            result = self.cli.edit(command=command, tostring=tostring)
        except NetConfClientExecuteCmdError as err:
            raise JunOSCommandError(err)
        return result

    def view(self, command, tostring=False):
        if self.cli is None:
            raise JunOSError("no connection to the device")
        try:
            result = self.cli.view(command=command, tostring=tostring)
        except NetConfClientExecuteCmdError as err:
            raise JunOSCommandError(err)
        return result

    def save(self):
        if self.cli.validate():
            if self.cli.compare() is not None:
                if not self.cli.commit():
                    LOG.error("don't commit configuration on '%s'", self.device)
                    return False
            return True
        else:
            LOG.error("error in device configuration")
            return False
