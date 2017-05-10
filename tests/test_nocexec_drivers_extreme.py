"""
Tests for module nocexec.drivers.extreme
"""

import unittest
try:
    from unittest import mock
except ImportError:  # pragma: no cover
    import mock
from nocexec.drivers.extreme import XOS, XOSError, XOSCommandError
from nocexec.exception import SSHClientError, SSHClientExecuteCmdError

# pylint: disable=invalid-name,missing-docstring,protected-access
invalid_input = [' asdasdasd', '', '\x07        ^',
                 '', "%% Invalid input detected at '^' marker.", '']
error_input = [' create vlan Test tag 11', '',
               'Error: 802.1Q Tag 11 is assigned to VLAN test.']
normal = [' show vlan', '', 'test']


class TestXOS(unittest.TestCase):

    def setUp(self):
        self.c = XOS(device="d")
        self.c.cli = mock.MagicMock()

    def test_init(self):
        with self.assertRaises(XOSError):
            XOS(device="d", protocol="bad_proto")

    @mock.patch('nocexec.drivers.base.NOCExecDriver.init_client')
    def test_connect(self, mock_init_client):
        mock_sendline = self.c.cli.connection.sendline
        mock_expect = self.c.cli.connection.expect
        self.c.cli.connection.before.splitlines.return_value = ["", "hostname"]
        self.c.connect()
        mock_init_client.assert_called_with()
        self.c.cli.connect.assert_called_with()
        mock_sendline.assert_called_with("disable clipaging")
        mock_expect.assert_called_with('.2 #')
        self.assertEqual(self.c._hostname, "hostname")

    # Test connection error
    @mock.patch('nocexec.drivers.base.NOCExecDriver.init_client')
    def test_error_connect(self, mock_init_client):
        self.c.cli.connect.side_effect = SSHClientError("error")
        with self.assertRaises(XOSError):
            self.c.connect()
        mock_init_client.assert_called_with()

    def test_is_error(self):
        self.assertTrue(self.c._is_error(invalid_input))
        self.assertTrue(self.c._is_error(error_input))
        self.assertFalse(self.c._is_error(normal))

    def _command_function_test(self, funct):
        self.c.cli.execute.return_value = ["l1", "l2"]
        # If the command is repeated then the counter self._cmd_num does
        # not increase
        for _ in range(3):
            self.assertEqual(funct("test"), ["l1", "l2"])
            self.c.cli.execute.assert_called_with(
                command='test', wait=['d.3 #'])
        # but if run new command, counter self._cmd_num does increase
        self.assertEqual(funct("test2"), ["l1", "l2"])
        self.c.cli.execute.assert_called_with(command='test2', wait=['d.4 #'])
        # check errors in result
        for err in [invalid_input, error_input]:
            self.c.cli.execute.return_value = err
            with self.assertRaises(XOSCommandError):
                funct("test2")
            self.c.cli.execute.assert_called_with(
                command='test2', wait=['d.4 #'])
        # execute error
        self.c.cli.execute.side_effect = SSHClientExecuteCmdError("error")
        with self.assertRaises(XOSCommandError):
            self.assertFalse(funct("test"))
        # client not initilized
        self.c.cli = None
        with self.assertRaises(XOSError):
            self.assertFalse(funct("test"))

    def test_view(self):
        self._command_function_test(self.c.view)

    def test_edit(self):
        self._command_function_test(self.c.edit)

    def test_save(self):
        call1 = mock.call(command="save configuration primary",
                          wait=["Do you want to save configuration to primary."
                                "cfg and overwrite it?"])
        call2 = mock.call(command='Yes',
                          wait=["Configuration saved to primary.cfg "
                                "successfully."])
        self.assertTrue(self.c.save())
        self.assertEqual(self.c.cli.execute.mock_calls, [call1, call2])
        # error command
        self.c.cli.execute.side_effect = SSHClientExecuteCmdError("error")
        self.assertFalse(self.c.save())
        # client is None
        self.c.cli = None
        self.assertFalse(self.c.save())
