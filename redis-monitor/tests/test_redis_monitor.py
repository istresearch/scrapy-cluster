'''
Offline tests
'''
from unittest import TestCase
from mock import MagicMock
from mock import call
from redis_monitor import RedisMonitor
import mock
import socket
import time


class TestRedisMonitor(TestCase):

    def setUp(self):
        self.redis_monitor = RedisMonitor("settings.py", True)
        self.redis_monitor.settings = self.redis_monitor.wrapper.load("settings.py")
        self.redis_monitor.logger = MagicMock()

    def test_load_plugins(self):
        # test loading default plugins
        assert_keys = [100, 200, 300, 400, 500]
        self.redis_monitor._load_plugins()
        self.assertEqual(list(self.redis_monitor.plugins_dict.keys()), assert_keys)

        # test removing a plugin from settings
        assert_keys = [100, 300, 400, 500]
        self.redis_monitor.settings['PLUGINS'] \
            ['plugins.stop_monitor.StopMonitor'] = None
        self.redis_monitor._load_plugins()
        self.assertEqual(list(self.redis_monitor.plugins_dict.keys()), assert_keys)
        self.redis_monitor.settings['PLUGINS'] \
            ['plugins.stop_monitor.StopMonitor'] = 200

        # fail if the class is not found
        self.redis_monitor.settings['PLUGINS'] \
            ['plugins.crazy_class.CrazyHandler'] = 400,

        self.assertRaises(ImportError, self.redis_monitor._load_plugins)
        del self.redis_monitor.settings['PLUGINS'] \
            ['plugins.crazy_class.CrazyHandler']
        self.redis_monitor.settings['PLUGINS'] = {}

    def test_active_plugins(self):
        # test that exceptions are caught within each plugin
        # assuming now all plugins are loaded
        self.redis_monitor._load_plugins()
        self.redis_monitor.stats_dict = {}

        # BaseExceptions are never raised normally
        list(self.redis_monitor.plugins_dict.items())[0][1]['instance'].handle = MagicMock(side_effect=BaseException("info"))
        list(self.redis_monitor.plugins_dict.items())[1][1]['instance'].handle = MagicMock(side_effect=BaseException("stop"))
        list(self.redis_monitor.plugins_dict.items())[2][1]['instance'].handle = MagicMock(side_effect=BaseException("expire"))
        self.redis_monitor.redis_conn = MagicMock()
        self.redis_monitor.redis_conn.scan_iter = MagicMock()
        self.redis_monitor._create_lock_object = MagicMock()

        # lets just assume the regex worked
        self.redis_monitor.redis_conn.scan_iter.return_value = ['somekey1']

        # info
        try:
            plugin = list(self.redis_monitor.plugins_dict.items())[0][1]
            self.redis_monitor._process_plugin(plugin)
            self.fail("Info not called")
        except BaseException as e:
            self.assertEqual("info", str(e))

        # action
        try:
            plugin = list(self.redis_monitor.plugins_dict.items())[1][1]
            self.redis_monitor._process_plugin(plugin)
            self.fail("Stop not called")
        except BaseException as e:
            self.assertEqual("stop", str(e))

        # expire
        try:
            plugin = list(self.redis_monitor.plugins_dict.items())[2][1]
            self.redis_monitor._process_plugin(plugin)
            self.fail("Expire not called")
        except BaseException as e:
            self.assertEqual("expire", str(e))

        # test that an exception within a handle method is caught
        self.redis_monitor._process_failures = MagicMock()
        self.redis_monitor._increment_fail_stat = MagicMock()
        try:
            list(self.redis_monitor.plugins_dict.items())[0][1]['instance'].handle = MagicMock(side_effect=Exception("normal"))
            plugin = list(self.redis_monitor.plugins_dict.items())[0][1]
            self.redis_monitor._process_plugin(plugin)

        except Exception as e:
            self.fail("Normal Exception not handled")

        self.assertTrue(self.redis_monitor._increment_fail_stat.called)
        self.assertTrue(self.redis_monitor._process_failures.called)

    def test_locking_actions(self):
        # tests for _process_plugins with locking
        self.redis_monitor._load_plugins()
        self.redis_monitor.redis_conn = MagicMock()
        self.redis_monitor.redis_conn = MagicMock()
        self.redis_monitor.redis_conn.scan_iter = MagicMock()
        self.redis_monitor.redis_conn.get = MagicMock(return_value=5)

        lock = MagicMock()
        lock.acquire
        lock.acquire = MagicMock(return_value=False)
        lock.release = MagicMock()
        lock._held = False
        self.redis_monitor._create_lock_object = MagicMock(return_value=lock)

        self.redis_monitor._increment_fail_stat = MagicMock()
        self.redis_monitor._process_failures = MagicMock()
        self.redis_monitor._process_key_val = MagicMock()
        # lets just assume the regex worked
        self.redis_monitor.redis_conn.scan_iter.return_value = ['somekey1']

        plugin = {'instance': 'test',
                  'regex': 'abc123'}

        # test didnt acquire lock
        self.redis_monitor._process_key_val.assert_not_called()
        self.redis_monitor._process_plugin(plugin)
        self.redis_monitor._process_key_val.assert_not_called()
        lock.release.assert_not_called()

        # test got lock
        lock.acquire = MagicMock(return_value=True)
        lock._held = True
        self.redis_monitor._process_plugin(plugin)
        self.redis_monitor._process_key_val.assert_called_once_with('test', 'somekey1', 5)
        # test lock released
        lock.release.assert_called_once_with()

        # test lock not held not released
        lock._held = False
        lock.release.reset_mock()
        self.redis_monitor._process_plugin(plugin)
        lock.release.assert_not_called()


    def test_load_stats_plugins(self):
        # lets assume we are loading the default plugins
        self.redis_monitor._load_plugins()
        self.redis_monitor.redis_conn = MagicMock()

        # test no rolling stats
        self.redis_monitor.stats_dict = {}
        self.redis_monitor.settings['STATS_TIMES'] = []
        self.redis_monitor._setup_stats_plugins()
        defaults = [
            'ExpireMonitor',
            'StopMonitor',
            'InfoMonitor',
            'StatsMonitor',
            'ZookeeperMonitor'
        ]

        self.assertEqual(
            sorted(self.redis_monitor.stats_dict['plugins'].keys()),
            sorted(defaults))

        for key in self.redis_monitor.plugins_dict:
            plugin_name = self.redis_monitor.plugins_dict[key]['instance'].__class__.__name__
            self.assertEqual(
                list(self.redis_monitor.stats_dict['plugins'][plugin_name].keys()),
                ['lifetime'])

        # test good/bad rolling stats
        self.redis_monitor.stats_dict = {}
        self.redis_monitor.settings['STATS_TIMES'] = [
            'SECONDS_15_MINUTE',
            'SECONDS_1_HOUR',
            'SECONDS_DUMB',
        ]
        good = [
            'lifetime', # for totals, not DUMB
            '900',
            '3600',
        ]

        self.redis_monitor._setup_stats_plugins()

        self.assertEqual(
            sorted(self.redis_monitor.stats_dict['plugins'].keys()),
            sorted(defaults))

        for key in self.redis_monitor.plugins_dict:
            plugin_name = self.redis_monitor.plugins_dict[key]['instance'].__class__.__name__
            self.assertEqual(
                sorted([str(x) for x in self.redis_monitor.stats_dict['plugins'][plugin_name].keys()]),
                sorted(good))

        for plugin_key in self.redis_monitor.stats_dict['plugins']:
            k1 = 'stats:redis-monitor:{p}'.format(p=plugin_key)
            for time_key in self.redis_monitor.stats_dict['plugins'][plugin_key]:
                if time_key == 0:
                    self.assertEqual(
                        self.redis_monitor.stats_dict['plugins'][plugin_key][0].key,
                        '{k}:lifetime'.format(k=k1)
                        )
                else:
                    self.assertEqual(
                        self.redis_monitor.stats_dict['plugins'][plugin_key][time_key].key,
                        '{k}:{t}'.format(k=k1, t=time_key)
                        )

    def test_main_loop(self):
        self.redis_monitor._load_plugins()
        self.redis_monitor._process_plugin = MagicMock(side_effect=Exception(
                                                       "normal"))

        try:
            self.redis_monitor._main_loop()
            self.fail("_process_plugin not called")
        except BaseException as e:
            self.assertEqual("normal", str(e))

    def test_precondition(self):
        self.redis_monitor.stats_dict = {}
        instance = MagicMock()
        instance.check_precondition = MagicMock(return_value=False)
        instance.handle = MagicMock(side_effect=Exception("handler"))
        key = 'stuff'
        value = 'blah'

        # this should not raise an exception
        self.redis_monitor._process_key_val(instance, key, value)

        # this should
        instance.check_precondition = MagicMock(return_value=True)
        try:
            self.redis_monitor._process_key_val(instance, key, value)
            self.fail('handler not called')
        except BaseException as e:
            self.assertEqual('handler', str(e))

    def test_get_fail_key(self):
        key = 'test'
        result = 'lock:test:failures'
        self.assertEqual(self.redis_monitor._get_fail_key(key), result)

    def test_process_failures(self):
        self.redis_monitor.settings = {'RETRY_FAILURES':True,
                                       'RETRY_FAILURES_MAX': 3}
        self.redis_monitor._get_fail_key = MagicMock(return_value='the_key')
        self.redis_monitor.redis_conn = MagicMock()
        self.redis_monitor.redis_conn.set = MagicMock()

        # test not set
        self.redis_monitor.redis_conn.get = MagicMock(return_value=None)
        self.redis_monitor._process_failures('key1')
        self.redis_monitor.redis_conn.set.assert_called_once_with('the_key', 1)

        # test set
        self.redis_monitor.redis_conn.set.reset_mock()
        self.redis_monitor.redis_conn.get = MagicMock(return_value=2)
        self.redis_monitor._process_failures('key1')
        self.redis_monitor.redis_conn.set.assert_called_once_with('the_key', 3)

        # test exceeded
        self.redis_monitor.redis_conn.delete = MagicMock()
        self.redis_monitor.redis_conn.set.reset_mock()
        self.redis_monitor.redis_conn.get = MagicMock(return_value=3)
        self.redis_monitor._process_failures('key1')
        calls = [call('the_key'), call('key1')]
        self.redis_monitor.redis_conn.delete.assert_has_calls(calls)

    @mock.patch('socket.gethostname', return_value='host')
    @mock.patch('time.time', return_value=5)
    def test_report_self(self, h, t):
        self.redis_monitor.my_uuid = '1234'
        self.redis_monitor.redis_conn = MagicMock()
        self.redis_monitor.redis_conn.set = MagicMock()
        self.redis_monitor.redis_conn.expire = MagicMock()

        self.redis_monitor._report_self()
        self.redis_monitor.redis_conn.set.assert_called_once_with('stats:redis-monitor:self:host:1234', 5)
        self.redis_monitor.redis_conn.expire.assert_called_once_with('stats:redis-monitor:self:host:1234', 120)

