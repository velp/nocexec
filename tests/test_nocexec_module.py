"""
Tests for module nocexec.__init__
"""

import unittest
try:
    from unittest import mock
except ImportError:  # pragma: no cover
    import mock
import pexpect
import ncclient
from ncclient.operations.rpc import RPCError
from ncclient.xml_ import NCElement
from ncclient.transport.errors import AuthenticationError, TransportError
from nocexec import SSHClient, NetConfClient
from nocexec.exception import SSHClientError, NetConfClientError, \
    SSHClientExecuteCmdError, NetConfClientExecuteCmdError

# pylint: disable=invalid-name,protected-access,missing-docstring
good_reply = """<rpc-reply message-id="urn:uuid:1">
                <ok/>
              </rpc-reply>"""
bad_reply = """<rpc-reply message-id="urn:uuid:1">
             </rpc-reply>"""
comp_reply = """<rpc-reply message-id="urn:uuid:1">
                  <configuration-information>
                    <configuration-output>
                      test
                    </configuration-output>
                  </configuration-information>
                </rpc-reply>"""
empty_comp_reply = """<rpc-reply message-id="urn:uuid:1">
                        <configuration-information>
                          <configuration-output>
                          </configuration-output>
                        </configuration-information>
                      </rpc-reply>"""


class TestSSHClient(unittest.TestCase):

    def setUp(self):
        self.c = SSHClient(device="test",
                           login="user",
                           password="pass")
        # mocking pexpect
        self.c.cli = mock.Mock()

    @mock.patch('nocexec.SSHClient.connect')
    @mock.patch('nocexec.SSHClient.disconnect')
    # pylint: disable=no-self-use
    def test_context(self, mock_disconnect, mock_connect):
        with SSHClient():
            mock_connect.assert_called_with()
        mock_disconnect.assert_called_with()

    def test_disconnect(self):
        self.c.disconnect()
        self.c.cli.close.assert_called_with()

    @mock.patch('pexpect.spawn')
    def test_connect(self, mock_spawn):
        opts = " ".join(["-o%s=%s" % (k, v)
                         for k, v in self.c.ssh_options.items()])
        cmd = 'ssh {0} user@test'.format(opts)
        # Check normal connect
        mock_spawn.return_value.expect.return_value = 0
        self.c.connect()
        # check spawn command
        mock_spawn.assert_called_with(cmd, timeout=5)
        # check enter password
        mock_spawn.return_value.sendline.assert_called_with("pass")
        # check result
        self.assertEqual(self.c.cli, mock_spawn.return_value)
        # Check welcome expect errors
        for code in [1, 2]:
            mock_spawn.return_value.expect.return_value = code
            with self.assertRaises(SSHClientError):
                self.c.connect()
        # Check password expect errors
        for code in [2, 3, 4]:
            mock_spawn.return_value.expect.side_effect = [0, code]
            with self.assertRaises(SSHClientError):
                self.c.connect()
        # Check spawn error
        mock_spawn.return_value = None
        with self.assertRaises(SSHClientError) as err:
            self.c.connect()
        self.assertEqual(self.c.cli, None)
        self.assertIn("SSH spawn error to host test", str(err.exception))

    def test_execute(self):
        self.c.cli.before.splitlines.return_value = ["line0", "line1"]
        res = self.c.execute(command="test", wait=["#"])
        self.c.cli.sendline.assert_called_with("test")
        self.c.cli.expect.assert_called_with(
            ["#", pexpect.TIMEOUT, pexpect.EOF], timeout=10)
        self.assertEqual(len(res), 2)
        for indx in [0, 1]:
            self.assertEqual(res[indx], "line%s" % indx)
        # check expect EOF
        self.c.cli.expect.return_value = 1
        with self.assertRaises(SSHClientExecuteCmdError) as err:
            self.c.execute(command="test")
        self.assertIn("Execute command 'test' EOF error", str(err.exception))
        # check expect timeout
        self.c.cli.expect.return_value = 0
        with self.assertRaises(SSHClientExecuteCmdError) as err:
            self.c.execute(command="test")
        self.assertIn("Execute command 'test' timeout", str(err.exception))

    def test_send(self):
        self.c.send("test")
        self.c.cli.sendline.assert_called_with("test")


class TestNetConfClient(unittest.TestCase):

    def setUp(self):
        self.c = NetConfClient(device="test",
                               login="user",
                               password="pass")
        # mocking pexpect
        self.c.cli = mock.Mock()
        # for xml
        device_handler = ncclient.manager.make_device_handler(
            {'name': 'junos'})
        self.tr = device_handler.transform_reply()

    @mock.patch('nocexec.NetConfClient.connect')
    @mock.patch('nocexec.NetConfClient.disconnect')
    def test_context(self, mock_disconnect, mock_connect):
        with NetConfClient():
            mock_connect.assert_called_with()
        mock_disconnect.assert_called_with()
        # Check default rcp errors
        self.assertEqual(self.c.ignore_rpc_errors, ["statement not found",
                                                    "no entry for"])

    def test_disconnect(self):
        self.c.disconnect()
        self.c.cli.close_session.assert_called_with()

    def test_ignored_rpc_error(self):
        self.assertTrue(self.c._ignored_rpc_error(
            Exception("statement not found")))
        self.assertTrue(self.c._ignored_rpc_error(
            Exception("no entry for")))
        self.assertFalse(self.c._ignored_rpc_error(Exception("test")))

    @mock.patch('ncclient.manager.connect')
    def test_connect(self, mock_manager):
        self.c.connect()
        # check None connection
        mock_manager.return_value = None
        with self.assertRaises(NetConfClientError) as err:
            self.c.connect()
        self.assertEqual(str(err.exception), "Connection to 'test' error: "
                         "manager return None object")
        # check authentication error
        mock_manager.side_effect = AuthenticationError("test error")
        with self.assertRaises(NetConfClientError) as err:
            self.c.connect()
        self.assertEqual(str(err.exception), "Authentication failed on 'test'")
        # check authentication error
        mock_manager.side_effect = TransportError("test error")
        with self.assertRaises(NetConfClientError) as err:
            self.c.connect()
        self.assertEqual(str(err.exception),
                         "Connection to 'test' error: test error")

    def test_locking(self):

        # check lock
        self.c.cli.lock.return_value = NCElement(
            good_reply, self.tr)
        self.assertTrue(self.c._locking("lock"))
        self.assertTrue(self.c._configuration_lock)
        # check unlock
        self.c.cli.unlock.return_value = NCElement(
            good_reply, self.tr)
        self.assertTrue(self.c._locking("unlock"))
        self.assertFalse(self.c._configuration_lock)
        # check other action
        self.assertTrue(self.c._locking("test"))
        self.assertTrue(self.c._configuration_lock)
        # bad RCP reply lock
        self.c.cli.lock.return_value = NCElement(bad_reply, self.tr)
        self.assertFalse(self.c._locking("lock"))
        # bad RCP reply unlock
        self.c.cli.unlock.return_value = NCElement(
            bad_reply, self.tr)
        self.assertFalse(self.c._locking("unlock"))
        # check RPCError
        self.c.cli.lock.side_effect = RPCError(mock.MagicMock())
        self.assertFalse(self.c._locking("lock"))
        self.c.cli.unlock.side_effect = RPCError(mock.MagicMock())
        self.assertFalse(self.c._locking("unlock"))

    @mock.patch('nocexec.NetConfClient._locking')
    def test_lock(self, mock_locking):
        self.assertEqual(self.c.lock(), mock_locking.return_value)
        mock_locking.assert_called_with(action="lock")
        # already locked
        mock_locking.reset_mock()
        self.c._configuration_lock = True
        self.assertTrue(self.c.lock())
        mock_locking.assert_not_called()

    @mock.patch('nocexec.NetConfClient._locking')
    def test_unlock(self, mock_locking):
        # not locked
        self.assertTrue(self.c.unlock())
        mock_locking.assert_not_called()
        # unlock
        self.c._configuration_lock = True
        self.assertEqual(self.c.unlock(), mock_locking.return_value)
        mock_locking.assert_called_with(action="unlock")

    def test_edit(self):
        mock_lc = self.c.cli.load_configuration
        self.assertEqual(self.c.edit("test"), mock_lc.return_value)
        mock_lc.assert_called_with(action='set', config=["test"])
        # check tostring
        mock_lc.return_value = mock.Mock()
        self.assertEqual(self.c.edit("test", tostring=True),
                         mock_lc.return_value.tostring)
        # RPC error
        mock_lc.side_effect = RPCError(mock.MagicMock())
        with self.assertRaises(NetConfClientExecuteCmdError) as err:
            self.c.edit("test")
        self.assertIn(
            "Executing the editing command 'test' error", str(err.exception))
        # ignore RPC error
        with mock.patch('nocexec.NetConfClient._ignored_rpc_error') as mock_ig:
            mock_ig.return_value = True
            self.assertEqual(self.c.edit("test"), None)
            mock_ig.assert_called_with(mock_lc.side_effect)

    def test_view(self):
        mock_cmd = self.c.cli.command
        self.assertEqual(self.c.view("test"), mock_cmd.return_value)
        # check tostring
        mock_cmd.return_value = mock.Mock()
        self.assertEqual(self.c.view("test", tostring=True),
                         mock_cmd.return_value.tostring)
        # RPC error
        mock_cmd.side_effect = RPCError(mock.MagicMock())
        with self.assertRaises(NetConfClientExecuteCmdError) as err:
            self.c.view("test")
        self.assertIn(
            "Execute the view command 'test' error", str(err.exception))
        # ignore RPC error
        with mock.patch('nocexec.NetConfClient._ignored_rpc_error') as mock_ig:
            mock_ig.return_value = True
            self.assertEqual(self.c.view("test"), None)
            mock_ig.assert_called_with(mock_cmd.side_effect)

    def test_compare(self):
        mock_compare = self.c.cli.compare_configuration
        mock_compare.return_value = NCElement(comp_reply, self.tr)
        self.assertEqual(self.c.compare().replace(" ", ""), "\ntest\n")
        mock_compare.assert_called_with(0)
        # ither version
        self.assertEqual(self.c.compare(10).replace(" ", ""), "\ntest\n")
        mock_compare.assert_called_with(10)
        # empty compare
        mock_compare.return_value = NCElement(
            empty_comp_reply, self.tr)
        self.assertEqual(self.c.compare(), None)

    def test_commit(self):
        mock_commit = self.c.cli.commit
        mock_commit.return_value = NCElement(good_reply, self.tr)
        self.assertTrue(self.c.commit())
        # bad reply
        mock_commit.return_value = NCElement(bad_reply, self.tr)
        self.assertFalse(self.c.commit())
        # RPC error
        mock_commit.side_effect = RPCError(mock.MagicMock())
        self.assertFalse(self.c.commit())

    def test_validate(self):
        mock_validate = self.c.cli.validate
        self.assertTrue(self.c.validate())
        mock_validate.assert_called_with()
        # RPC error
        mock_validate.side_effect = RPCError(mock.MagicMock())
        self.assertFalse(self.c.validate())
