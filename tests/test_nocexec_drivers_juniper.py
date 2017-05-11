"""
Tests for module nocexec.drivers.juniper
"""

import unittest
try:
    from unittest import mock
except ImportError:  # pragma: no cover
    import mock
from nocexec.drivers.juniper import JunOS, JunOSError, JunOSCommandError
from nocexec.exception import NetConfClientError, NetConfClientExecuteCmdError

# pylint: disable=invalid-name,missing-docstring,protected-access


class TestJunOS(unittest.TestCase):

    def setUp(self):
        self.c = JunOS(device="d", protocol="netconf")
        self.c.cli = mock.MagicMock()

    def test_init(self):
        with self.assertRaises(JunOSError):
            JunOS(device="d", protocol="bad_proto")

    @mock.patch('nocexec.NetConfClient.__init__', return_value=None)
    @mock.patch('nocexec.NetConfClient.connect')
    @mock.patch('nocexec.NetConfClient.lock')
    def test_connect(self, mock_lock, mock_connect, mock_init):
        self.c.connect()
        mock_init.assert_called_with(device='d',
                                     device_params={'name': 'junos'},
                                     exclusive=False, login='',
                                     password='', timeout=5)
        # not lock
        mock_lock.return_value = False
        with self.assertRaises(JunOSError):
            self.c.connect()
        # connect error
        mock_connect.side_effect = NetConfClientError("error")
        with self.assertRaises(JunOSError):
            self.c.connect()

    def test_disconnect(self):
        # client initilized
        self.c.disconnect()
        self.c.cli.unlock.assert_called_with()
        self.c.cli.disconnect.assert_called_with()

    def _command_functions_test(self, funct_name):
        # get ftesting functions
        funct = getattr(self.c, funct_name)
        cli_funct = getattr(self.c.cli, funct_name)
        # mocking result from client
        result = cli_funct.return_value = mock.Mock()
        # test base call
        self.assertEqual(funct("test"), result)
        cli_funct.assert_called_with(command="test")
        # test tostring
        self.assertEqual(funct("test", tostring=True), result)
        cli_funct.assert_called_with(command="test", tostring=True)
        # test command error
        cli_funct.side_effect = NetConfClientExecuteCmdError("error")
        with self.assertRaises(JunOSCommandError):
            funct("test")
        # test client not initilized
        self.c.cli = None
        with self.assertRaises(JunOSError) as err:
            funct("test")
        self.assertEqual("no connection to the device", str(err.exception))

    def test_edit(self):
        self._command_functions_test("edit")

    def test_view(self):
        self._command_functions_test("view")

    def test_save(self):
        self.assertTrue(self.c.save())
        # not commit
        self.c.cli.reset_mock()
        self.c.cli.commit.return_value = False
        self.assertFalse(self.c.save())
        # compare is None (not found changes)
        self.c.cli.reset_mock()
        self.c.cli.compare.return_value = None
        self.assertTrue(self.c.save())
        # errors in config
        self.c.cli.reset_mock()
        self.c.cli.validate.return_value = False
        self.assertFalse(self.c.save())
