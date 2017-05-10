"""
Tests for module nocexec.drivers.base
"""

import unittest
try:
    from unittest import mock
except ImportError:  # pragma: no cover
    import mock
from nocexec import SSHClient
from nocexec.drivers.base import NOCExecDriver, NOCExecDriverError

# pylint: disable=invalid-name,missing-docstring,protected-access


class TestNOCExecDriver(unittest.TestCase):

    def setUp(self):
        self.c = NOCExecDriver(device="d", driver_protocols=["ssh", "telnet"])

    def test_init(self):
        self.assertEqual(self.c._device, "d")
        self.assertEqual(self.c._login, "")
        self.assertEqual(self.c._password, "")
        self.assertEqual(self.c._port, 22)
        self.assertEqual(self.c._timeout, 5)
        self.assertEqual(self.c._protocol, SSHClient)
        self.assertEqual(self.c._hostname, "d")
        self.assertEqual(self.c.cli, None)
        with self.assertRaises(NOCExecDriverError):
            NOCExecDriver(device="d", driver_protocols=[], protocol="ssh")

    def test_init_client(self):
        self.c._protocol = mock.Mock()
        self.c.init_client()
        self.c._protocol.assert_called_with(device='d', login='', password='',
                                            port=22, timeout=5)
        self.c.cli = self.c._protocol.return_value

    def test_disconnect(self):
        self.c.disconnect()  # cli now is None
        self.c.cli = mock.Mock()
        self.c.disconnect()
        self.c.cli.disconnect.assert_called_with()
