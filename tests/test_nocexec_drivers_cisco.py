"""
Tests for module nocexec.drivers.base
"""

import unittest
try:
    from unittest import mock
except ImportError:  # pragma: no cover
    import mock
from nocexec import SSHClient
from nocexec.drivers.cisco import IOS, IOSError, IOSCommandError
from nocexec.exception import SSHClientError, TelnetClientError, \
    SSHClientExecuteCmdError, TelnetClientExecuteCmdError


class TestIOS(unittest.TestCase):

    def setUp(self):
        self.c = IOS(device="d")
        self.c.cli = mock.MagicMock()

    @mock.patch('nocexec.drivers.base.NOCExecDriver.init_client')
    def test_connect(self, mock_init_client):
        mock_sendline = self.c.cli.connection.sendline
        mock_expect = self.c.cli.connection.expect
        self.c.cli.connection.before.splitlines.return_value = ["", "hostname"]
        self.c.connect()
        mock_init_client.assert_called_with()
        self.c.cli.connect.assert_called_with()
        mock_sendline.assert_called_with("terminal length 0")
        mock_expect.assert_called_with(['>', '#'])
        self.assertEqual(self.c._hostname, "hostname")
        self.assertEqual(self.c._shell_prompt, "hostname#")
        self.assertEqual(self.c._config_prompt, "hostname\(config.*?\)#")
        self.assertEqual(self.c._priv_mode, bool(mock_expect.return_value))

    # Test connection error
    @mock.patch('nocexec.drivers.base.NOCExecDriver.init_client')
    def test_error_connect(self, mock_init_client):
        self.c.cli.connect.side_effect = SSHClientError("error")
        with self.assertRaises(IOSError):
            self.c.connect()
        mock_init_client.assert_called_with()

    def test_enable_privileged(self):
        self.assertTrue(self.c._enable_privileged())
        self.c.cli.execute.assert_called_with("enable", wait=["d#"])
        self.assertEqual(self.c._shell_prompt, "d#")
        self.assertEqual(self.c._priv_mode, True)
        # error
        self.c.cli.execute.side_effect = SSHClientExecuteCmdError("error")
        self.assertFalse(self.c._enable_privileged())

    def test_disable_privileged(self):
        self.assertTrue(self.c._disable_privileged())
        self.c.cli.execute.assert_called_with("disable", wait=["d>"])
        self.assertEqual(self.c._shell_prompt, "d>")
        self.assertEqual(self.c._priv_mode, False)
        # error
        self.c.cli.execute.side_effect = SSHClientExecuteCmdError("error")
        self.assertFalse(self.c._disable_privileged())

    @mock.patch('nocexec.drivers.cisco.IOS._enable_privileged')
    def test_enter_config(self, mock_priv):
        self.assertTrue(self.c._enter_config())
        self.c.cli.execute.assert_called_with(
            'configure terminal', wait=['\\(config.*?\\)#'])
        # error execute
        self.c._priv_mode = True
        self.c._config_mode = False
        self.c.cli.execute.side_effect = SSHClientExecuteCmdError("error")
        self.assertFalse(self.c._enter_config())
        # already config mode
        self.c.cli.reset_mock()
        self.c._config_mode = True
        self.assertTrue(self.c._enter_config())
        self.c.cli.execute.assert_not_called()
        # not privilaged mode
        self.c._priv_mode = False
        mock_priv.return_value = False
        self.assertFalse(self.c._enter_config())

    def test_exit_config(self):
        self.assertTrue(self.c._exit_config())
        # exit from config mode
        self.c._config_mode = True
        self.assertTrue(self.c._exit_config())
        self.c.cli.execute.assert_called_with("end", wait=["#"])
        self.assertFalse(self.c._config_mode)
        # command error
        self.c._config_mode = True
        self.c.cli.execute.side_effect = SSHClientExecuteCmdError("error")
        self.assertFalse(self.c._exit_config())

    @mock.patch('nocexec.drivers.cisco.IOS._enter_config')
    def test_edit(self, mock_config):
        self.c.cli.execute.return_value = ["l1", "l2"]
        self.assertEqual(self.c.edit("test"), ["l1", "l2"])
        self.c.cli.execute.assert_called_with(
            command='test', wait=['\\(config.*?\\)#'])
        # command error
        self.c.cli.execute.side_effect = SSHClientExecuteCmdError("error")
        with self.assertRaises(IOSCommandError):
            self.assertFalse(self.c.edit("test"))
        # not configuration mode
        mock_config.return_value = False
        with self.assertRaises(IOSCommandError) as err:
            self.assertFalse(self.c.edit("test"))
        self.assertEqual("can not enter configuration mode",
                         str(err.exception))
        # client not initilized
        self.c.cli = None
        with self.assertRaises(IOSError):
            self.assertFalse(self.c.edit("test"))

    @mock.patch('nocexec.drivers.cisco.IOS._exit_config')
    def test_view(self, mock_config):
        self.c.cli.execute.return_value = ["l1", "l2"]
        self.assertEqual(self.c.view("test"), ["l1", "l2"])
        self.c.cli.execute.assert_called_with(command='test', wait=['#'])
        # command error
        self.c.cli.execute.side_effect = SSHClientExecuteCmdError("error")
        with self.assertRaises(IOSCommandError):
            self.assertFalse(self.c.view("test"))
        # not configuration mode
        mock_config.return_value = False
        with self.assertRaises(IOSCommandError) as err:
            self.assertFalse(self.c.view("test"))
        self.assertEqual("can not exit the configuration mode",
                         str(err.exception))
        # client not initilized
        self.c.cli = None
        with self.assertRaises(IOSError):
            self.assertFalse(self.c.view("test"))

    @mock.patch('nocexec.drivers.cisco.IOS._exit_config')
    def test_save(self, mock_exit):
        self.assertTrue(self.c.save())
        self.c.cli.execute.assert_called_with(command="write memory",
                                              wait=[r"\[OK\]"])
        # error command
        self.c.cli.execute.side_effect = SSHClientExecuteCmdError("error")
        self.assertFalse(self.c.save())
        # error exit config mode
        mock_exit.return_value = False
        self.assertFalse(self.c.save())
        # client is None
        self.c.cli = None
        self.assertFalse(self.c.save())
