from mock import MagicMock, patch
from unittest import TestCase
from scutils.zookeeper_watcher import ZookeeperWatcher
from kazoo.client import KazooState
from kazoo.exceptions import ZookeeperError, KazooException

class TestZookeeperWatcher(TestCase):

    def setUp(self):

        zoo_client = MagicMock()
        zoo_client.get = MagicMock(return_value=(b'data', 'blah'))

        with patch('scutils.zookeeper_watcher.KazooClient') as k:
            k.return_value = zoo_client
            self.zoo_watcher = ZookeeperWatcher(
                                hosts='localhost',
                                filepath='/mypath',
                                pointer=False, ensure=True,
                                valid_init=True)

    def test_ping(self):
        self.zoo_watcher.zoo_client.server_version = MagicMock()
        self.assertTrue(self.zoo_watcher.ping())
        self.zoo_watcher.zoo_client.server_version = MagicMock(side_effect=KazooException)
        self.assertFalse(self.zoo_watcher.ping())

    def test_get_file_contents(self):
        self.zoo_watcher.old_pointed = 'old_pointed'
        self.zoo_watcher.old_data = 'old_data'

        self.zoo_watcher.pointer = False
        self.assertEqual(self.zoo_watcher.get_file_contents(), 'old_data')

        self.zoo_watcher.pointer = True
        self.assertEqual(self.zoo_watcher.get_file_contents(), 'old_data')

        self.zoo_watcher.pointer = True
        self.assertEqual(self.zoo_watcher.get_file_contents(True), 'old_pointed')

    def test_compare_pointer(self):
        self.zoo_watcher.old_pointed = '/path1'

        self.assertTrue(self.zoo_watcher.compare_pointer('/path2'))

        self.zoo_watcher.old_pointed = '/path1'

        self.assertFalse(self.zoo_watcher.compare_pointer('/path1'))

    def test_compare_data(self):
        self.zoo_watcher.old_data = 'old_data'

        self.assertTrue(self.zoo_watcher.compare_data('new_data'))

        self.zoo_watcher.old_data = 'same_data'
        self.assertFalse(self.zoo_watcher.compare_data('same_data'))

    def test_set_valid(self):
        self.zoo_watcher.is_valid = MagicMock(return_value=True)
        self.zoo_watcher.valid_handler = MagicMock()
        self.zoo_watcher.set_valid(False)

        self.zoo_watcher.valid_handler.assert_called_once_with(True)

    def test_call_valid(self):
        self.the_bool = False
        def the_set(state):
            self.the_bool = True

        self.zoo_watcher.valid_handler = the_set
        self.zoo_watcher.call_valid(True)

        self.assertTrue(self.the_bool)

    def test_call_config(self):
        self.the_bool = False
        def the_set(state):
            self.the_bool = True

        self.zoo_watcher.config_handler = the_set
        self.zoo_watcher.call_config(True)

        self.assertTrue(self.the_bool)

    def test_call_error(self):
        self.the_bool = False
        def the_set(state):
            self.the_bool = True

        self.zoo_watcher.error_handler = the_set
        self.zoo_watcher.call_error(True)

        self.assertTrue(self.the_bool)

