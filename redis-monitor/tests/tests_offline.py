'''
Offline tests
'''

import unittest
from unittest import TestCase
import mock
from mock import MagicMock

import sys
from os import path
sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))

from redis_monitor import RedisMonitor
from plugins.base_monitor import BaseMonitor
from plugins.kafka_base_monitor import KafkaBaseMonitor
from plugins.expire_monitor import ExpireMonitor
from plugins.info_monitor import InfoMonitor
from plugins.stop_monitor import StopMonitor
import copy

import settings
import pickle
import re

class TestRedisMonitor(TestCase):

    def setUp(self):
        self.redis_monitor = RedisMonitor("settings.py")

    def test_load_plugins(self):
        # test loading default plugins
        assert_keys = [100,200,300]
        self.redis_monitor._load_plugins()
        self.assertEqual(self.redis_monitor.plugins_dict.keys(), assert_keys)

        # test removing a plugin from settings
        assert_keys = [100,300]
        self.redis_monitor.settings.PLUGINS = {
            'plugins.stop_monitor.StopMonitor': None,
        }
        self.redis_monitor._load_plugins()
        self.assertEqual(self.redis_monitor.plugins_dict.keys(), assert_keys)
        self.redis_monitor.default_plugins['plugins.stop_monitor.StopMonitor'] = 200

        # fail if the class is not found
        self.redis_monitor.settings.PLUGINS = {
            'plugins.crazy_class.CrazyHandler': 400,
        }
        self.assertRaises(ImportError, self.redis_monitor._load_plugins)
        del self.redis_monitor.default_plugins['plugins.crazy_class.CrazyHandler']
        self.redis_monitor.settings.PLUGINS = {}

    def test_active_plugins(self):
        # test that exceptions are caught within each plugin
        # assuming now all plugins are loaded
        self.redis_monitor._load_plugins()

        # BaseExceptions are never raised normally
        self.redis_monitor.plugins_dict.items()[0][1]['instance'].handle = MagicMock(side_effect=BaseException("info"))
        self.redis_monitor.plugins_dict.items()[1][1]['instance'].handle = MagicMock(side_effect=BaseException("stop"))
        self.redis_monitor.plugins_dict.items()[2][1]['instance'].handle = MagicMock(side_effect=BaseException("expire"))
        self.redis_monitor.redis_conn = MagicMock()
        self.redis_monitor.redis_conn.scan_iter = MagicMock()
        # lets just assume the regex worked
        self.redis_monitor.redis_conn.scan_iter.return_value = ['somekey1']

        # info
        try:
            plugin = self.redis_monitor.plugins_dict.items()[0][1]
            self.redis_monitor._process_plugin(plugin)
            self.fail("Info not called")
        except BaseException as e:
            self.assertEquals("info", e.message)

        # action
        try:
            plugin = self.redis_monitor.plugins_dict.items()[1][1]
            self.redis_monitor._process_plugin(plugin)
            self.fail("Stop not called")
        except BaseException as e:
            self.assertEquals("stop", e.message)

        # expire
        try:
            plugin = self.redis_monitor.plugins_dict.items()[2][1]
            self.redis_monitor._process_plugin(plugin)
            self.fail("Expire not called")
        except BaseException as e:
            self.assertEquals("expire", e.message)

        # test that an exception within a handle method is caught
        try:
            self.redis_monitor.plugins_dict.items()[0][1]['instance'].handle = MagicMock(side_effect=Exception("normal"))
            plugin = self.redis_monitor.plugins_dict.items()[0][1]
            self.redis_monitor._process_plugin(plugin)
        except Exception as e:
            self.fail("Normal Exception not handled")

class TestBasePlugins(TestCase):
    def test_bad_plugins(self):
        class ForgotRegex(BaseMonitor):
            def handle(self,c,d):
                pass
        class ForgotHandle(BaseMonitor):
            regex = "*:*:stuff"

        handler = ForgotRegex()
        try:
            handler.setup("s")
            self.fail("did not raise error")
        except NotImplementedError as e:
            pass
        handler.handle('key', 'value')

        handler = ForgotHandle()
        handler.setup("s")
        try:
            handler.handle('a', 'b')
            self.fail("did not raise error")
        except NotImplementedError as e:
            pass

    def test_default_monitor(self):
        handler = BaseMonitor()
        try:
            handler.setup("s")
            self.fail("base setup should be abstract")
        except NotImplementedError as e:
            pass

        try:
            handler.handle('a', 'b')
            self.fail("base handler should be abstract")
        except NotImplementedError as e:
            pass

class RegexFixer(object):
    def fix_re(self, regex):
        # redis key finding is different than regex finding
        return re.sub('\*', '.+', regex)

class TestInfoPlugin(TestCase, RegexFixer):

    def setUp(self):
        self.plugin = InfoMonitor()
        self.plugin.redis_conn = MagicMock()

    def test_info_regex(self):
        regex = self.fix_re(self.plugin.regex)
        self.assertEquals(re.findall(regex, 'info:stuff:stuff'), ['info:stuff:stuff'])
        self.assertEquals(re.findall(regex, 'info:stuff:stuff:stuff'), ['info:stuff:stuff:stuff'])
        self.assertEquals(re.findall(regex, 'info:stuff'), [])

    def test_info_get_bin(self):
        v1 = "stuff"
        v1 = pickle.dumps(v1)
        v2 = 200
        self.plugin.redis_conn.zscan_iter = MagicMock(return_value=[(v1,v2)])
        ret_val = self.plugin._get_bin('key')
        self.assertEquals(ret_val, {-200: ['stuff']})

    def test_info_get_crawlid(self):
        master = {}
        master['uuid'] = 'ABC123'
        master['total_pending'] = 0
        master['server_time'] = 5
        master['crawlid'] = "crawlIDHERE"

        elements = 'info:link:testapp:crawlIDHERE'.split(":")
        dict = {}
        dict['spiderid'] = elements[1]
        dict['appid'] = elements[2]
        dict['crawlid'] = elements[3]

        self.plugin.redis_conn.exists = MagicMock(return_value=True)
        self.plugin.redis_conn.get = MagicMock(return_value=10)
        self.plugin.redis_conn.scan_iter = MagicMock(return_value=['theKey:bingo.com'])
        self.plugin._get_bin = MagicMock(return_value={-200: [{'appid':"testapp", "priority":10, 'crawlid':'crawlIDHERE'}]})

        result = self.plugin._build_crawlid_info(master, dict)

        success = {
            'server_time': 5,
            'crawlid': 'crawlIDHERE',
            'total_pending': 1,
            'expires': 10,
            'total_domains': 1,
            'appid': 'testapp',
            'domains': {
                'bingo.com': {
                    'low_priority': 10,
                    'high_priority': 10,
                    'total': 1
            }},
            'uuid': 'ABC123'
        }

        self.assertEquals(result, success)

    def test_info_get_appid(self):
        master = {}
        master['uuid'] = 'ABC123'
        master['total_pending'] = 0
        master['server_time'] = 5
        elements = 'info:link:testapp'.split(":")
        dict = {}
        dict['spiderid'] = elements[1]
        dict['appid'] = elements[2]

        self.plugin.redis_conn.exists = MagicMock(return_value=True)
        self.plugin.redis_conn.get = MagicMock(return_value=10)
        self.plugin.redis_conn.scan_iter = MagicMock(return_value=['theKey:bingo.com'])
        self.plugin._get_bin = MagicMock(return_value={-200: [{'appid':"testapp", "priority":20, 'crawlid':'cool'}]})

        result = self.plugin._build_appid_info(master, dict)

        success = {
            'server_time': 5,
            'uuid': 'ABC123',
            'total_pending': 1,
            'total_domains': 1,
            'total_crawlids': 1,
            'appid': 'testapp',
            'crawlids': {
                'cool': {
                    'domains': {
                        'bingo.com': {
                            'low_priority': 20,
                            'high_priority': 20,
                            'total': 1
                    }},
                    'distinct_domains': 1,
                    'total': 1,
                    'expires': 10
            }}}

        self.assertEquals(result, success)

class TestStopPlugin(TestCase, RegexFixer):
    def test_stop_monitor_mini_purge(self):
        pass

class TestExpirePlugin(TestCase, RegexFixer):
    def test_expire_monitor_time(self):
        pass

#
# class TestPlugins(TestCase):
#
#     def test_scrape_handler(self):
#         valid = {
#             "url":"www.stuff.com",
#             "crawlid":"abc124",
#             "appid":"testapp",
#             "spiderid":"link",
#             "priority":5,
#         }
#         handler = ScraperHandler()
#         handler.extract = tldextract.TLDExtract()
#         handler.redis_conn = MagicMock()
#
#         # check it is added to redis
#         handler.redis_conn.zadd = MagicMock(side_effect=AssertionError("added"))
#         try:
#             handler.handle(valid)
#             self.fail("Action not called")
#         except AssertionError as e:
#             self.assertEquals("added", e.message)
#
#         # check timeout is added
#         handler.redis_conn.zadd = MagicMock()
#         handler.redis_conn.set = MagicMock(side_effect=AssertionError("expires"))
#         valid['expires'] = 124242
#         try:
#             handler.handle(valid)
#             self.fail("Expires not called")
#         except AssertionError as e:
#             self.assertEquals("expires", e.message)
#
#     def test_action_handler(self):
#         handler = ActionHandler()
#         handler.redis_conn = MagicMock()
#         handler.redis_conn.set = MagicMock(side_effect=AssertionError("added"))
#
#         valid = {
#             "uuid":"abaksdjb",
#             "crawlid":"abc124",
#             "appid":"testapp",
#             "spiderid":"link",
#             "action":"info",
#         }
#
#         try:
#             handler.handle(valid)
#             self.fail("Added not called")
#         except AssertionError as e:
#             self.assertEquals("added", e.message)


if __name__ == '__main__':
    unittest.main()