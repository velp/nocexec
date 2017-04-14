import nocexec.drivers
from nocexec.exception import SSHClientError, TelnetClientError, \
    NOCExecError, SSHClientExecuteCmdError, TelnetClientExecuteCmdError


class IOSError(NOCExecError):
    pass


class IOSCommandError(IOSError):
    pass


class IOS:

    def __init__(self, device, login="", password="", timeout=5, protocol="ssh"):
        self.device = device
        self.login = login
        self.password = password
        self.timeout = timeout
        self.cli = None
        self.protocol = nocexec.drivers.protocols.get(protocol)
        self.hostname = device
        self.shell_prompt = "#"
        self.config_prompt = "(config)#"
        self.priv_mode = False
        self.config_mode = False

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.disconnect()

    def _prepare(self):
        # disable clipaging, check permission level nad fill hostname
        shell_ends = ['>', '#']
        self.cli.cli.sendline("terminal length 0")
        answ = self.cli.cli.expect(shell_ends)
        self.hostname = self.cli.cli.before.splitlines()[1]
        self.shell_prompt = self.hostname + "#"
        self.config_prompt = self.hostname + "(config)#"
        self.priv_mode = bool(answ)

    def _enable_privileged(self):
        try:
            self.cli.edit("enable", wait=[self.hostname + "#"])
            self.shell_prompt = self.hostname + "#"
            self.priv_mode = True
            return True
        except (SSHClientExecuteCmdError, TelnetClientExecuteCmdError):
            return False

    def _disable_privileged(self):
        try:
            self.cli.edit("disable", wait=[self.hostname + ">"])
            self.shell_prompt = self.hostname + ">"
            self.priv_mode = False
            return True
        except (SSHClientExecuteCmdError, TelnetClientExecuteCmdError):
            return False

    def _enter_config(self):
        if not self.priv_mode and not self._enable_privileged():
            LOG.error("unregistered mode is used")
            return False
        if self.config_mode:
            return True
        try:
            self.cli.edit("configure terminal", wait=[self.config_prompt])
            self.config_mode = True
            return True
        except (SSHClientExecuteCmdError, TelnetClientExecuteCmdError) as err:
            LOG.error("enter config mode error: %s", str(err))
            return False

    def _exit_config(self):
        if not self.config_mode:
            return True
        try:
            self.cli.edit("end", wait=[self.shell_prompt])
            self.config_mode = False
            return True
        except (SSHClientExecuteCmdError, TelnetClientExecuteCmdError) as err:
            LOG.error("enter config mode error: %s", str(err))
            return False

    def connect(self):
        self.cli = self.protocol(device=self.device,
                                 login=self.login,
                                 password=self.password,
                                 timeout=self.timeout)
        try:
            self.cli.connect()
        except (SSHClientError, TelnetClientError) as err:
            raise IOSError(err)
        self._prepare()

    def disconnect(self):
        if self.cli is not None:
            self.cli.disconnect()

    def edit(self, command):
        if self.cli is None:
            raise IOSError("no connection to the device")
        try:
            result = self.cli.execute(
                command=command, wait=[self.shell_prompt])
        except (SSHClientExecuteCmdError, TelnetClientExecuteCmdError) as err:
            raise IOSCommandError(err)
        return result

    def view(self, command):
        pass

    def save(self):
        pass
