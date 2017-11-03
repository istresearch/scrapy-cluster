'''
Offline tests
'''
from builtins import object

from unittest import TestCase
from mock import MagicMock

from plugins.base_monitor import BaseMonitor
from plugins.expire_monitor import ExpireMonitor
from plugins.info_monitor import InfoMonitor
from plugins.stop_monitor import StopMonitor
from plugins.stats_monitor import StatsMonitor
from plugins.zookeeper_monitor import ZookeeperMonitor

import ujson
import re
from kazoo.exceptions import ZookeeperError


class TestBasePlugins(TestCase):
    def test_bad_plugins(self):
        class ForgotRegex(BaseMonitor):
            def handle(self, c, d):
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
        except NotImplementedError:
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
        except NotImplementedError:
            pass


class RegexFixer(object):
    def fix_re(self, regex):
        # redis key finding is different than regex finding
        return re.sub('\*', '.+', regex)


class TestInfoPlugin(TestCase, RegexFixer):

    def setUp(self):
        self.plugin = InfoMonitor()
        self.plugin.redis_conn = MagicMock()
        self.plugin.logger = MagicMock()

    def test_info_regex(self):
        regex = self.fix_re(self.plugin.regex)
        self.assertEqual(re.findall(regex, 'info:stuff:stuff'), ['info:stuff:stuff'])
        self.assertEqual(re.findall(regex, 'info:stuff:stuff:stuff'), ['info:stuff:stuff:stuff'])
        self.assertEqual(re.findall(regex, 'info:stuff'), [])

    def test_info_get_bin(self):
        v1 = "stuff"
        v1 = ujson.dumps(v1)
        v2 = 200
        self.plugin.redis_conn.zscan_iter = MagicMock(return_value=[(v1, v2)])
        ret_val = self.plugin._get_bin('key')
        self.assertEqual(ret_val, {-200: ['stuff']})

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
        self.plugin._get_bin = MagicMock(return_value={-200: [{
                                         'appid': "testapp", "priority": 10,
                                         'crawlid': 'crawlIDHERE'}]})

        result = self.plugin._build_crawlid_info(master, dict)

        success = {
            'server_time': 5,
            'crawlid': 'crawlIDHERE',
            'spiderid': 'link',
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

        self.assertEqual(result, success)

    def test_info_get_appid(self):
        master = {}
        master['uuid'] = 'ABC123'
        master['total_pending'] = 0
        master['server_time'] = 5
        elements = 'info:link:testapp'.split(":")
        dict = {}
        dict['spiderid'] = elements[1]
        dict['appid'] = elements[2]

        self.plugin.redis_conn.scan_iter = MagicMock(return_value=[
                                                     'theKey:bingo.com'])
        self.plugin._get_bin = MagicMock(return_value={-200: [{
                                         'appid': "testapp", "priority": 20,
                                         'crawlid': 'cool', 'expires': 10}]})

        result = self.plugin._build_appid_info(master, dict)

        success = {
            'server_time': 5,
            'uuid': 'ABC123',
            'total_pending': 1,
            'total_domains': 1,
            'total_crawlids': 1,
            'appid': 'testapp',
            'spiderid': 'link',
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

        self.assertEqual(result, success)


class TestStopPlugin(TestCase, RegexFixer):
    def setUp(self):
        self.plugin = StopMonitor()
        self.plugin.redis_conn = MagicMock()
        self.plugin.logger = MagicMock()

    def test_stop_regex(self):
        regex = self.fix_re(self.plugin.regex)
        self.assertEqual(re.findall(regex, 'stop:spider:app:crawl'),
                          ['stop:spider:app:crawl'])
        self.assertEqual(re.findall(regex, 'stop:spider:app'),
                          ['stop:spider:app'])
        self.assertEqual(re.findall(regex, 'stop:stuff'), [])

    def test_stop_monitor_mini_purge(self):
        self.plugin.redis_conn.scan_iter = MagicMock(return_value=['link:istresearch.com:queue'])
        self.plugin.redis_conn.zscan_iter = MagicMock(return_value=[
            ['{"crawlid":"crawl", "appid":"app"}'],
            ['{"crawlid":"crawl", "appid":"foo"}'],
        ])

        self.assertEqual(self.plugin._mini_purge("link", "app", "crawl"), 1)


class TestExpirePlugin(TestCase, RegexFixer):
    def setUp(self):
        self.plugin = ExpireMonitor()
        self.plugin.redis_conn = MagicMock()
        self.plugin.logger = MagicMock()

    def test_stop_regex(self):
        regex = self.fix_re(self.plugin.regex)
        self.assertEqual(re.findall(regex, 'timeout:blah1:blah2:bla3'),
                          ['timeout:blah1:blah2:bla3'])
        self.assertEqual(re.findall(regex, 'timeout:blah1:blah2'), [])

    def test_expire_monitor_time(self):
        # if the stop monitor passes then this is just testing whether
        # the handler acts on the key only if it has expired
        self.plugin._purge_crawl = MagicMock(side_effect=Exception(
                                             "throw once"))

        self.plugin._get_current_time = MagicMock(return_value=5)

        # not timed out
        if self.plugin.check_precondition("key:stuff:blah:blah", 6):
            self.plugin.handle("key:stuff:blah:blah", 6)

        # timed out
        try:
            if self.plugin.check_precondition("key:stuff:blah:blah", 4):
                self.plugin.handle("key:stuff:blah:blah", 4)
            self.fail("Expire not called")
        except BaseException as e:
            self.assertEqual("throw once", str(e))

class TestStatsPlugin(TestCase, RegexFixer):
    def setUp(self):
        self.plugin = StatsMonitor()
        self.plugin.redis_conn = MagicMock()
        self.plugin.logger = MagicMock()
        self.plugin._get_key_value = MagicMock(return_value = 5)

    def test_stats_regex(self):
        regex = self.fix_re(self.plugin.regex)
        self.assertEqual(re.findall(regex, 'statsrequest:crawler:testApp'),
                          ['statsrequest:crawler:testApp'])
        self.assertEqual(re.findall(regex, 'statsrequest:crawler'), [])

    def _assert_thrown(self, key, equals):
        try:
            self.plugin.handle(key, 'blah')
            self.fail(equals + " exception not thrown")
        except Exception as e:
            self.assertEqual(equals, str(e))

    def test_stats_handle(self):
        # trying to make sure that everything is called
        self.plugin.get_all_stats = MagicMock(side_effect=Exception("all"))
        self.plugin.get_kafka_monitor_stats = MagicMock(side_effect=Exception("kafka"))
        self.plugin.get_redis_monitor_stats = MagicMock(side_effect=Exception("redis"))
        self.plugin.get_crawler_stats = MagicMock(side_effect=Exception("crawler"))
        self.plugin.get_spider_stats = MagicMock(side_effect=Exception("spider"))
        self.plugin.get_machine_stats = MagicMock(side_effect=Exception("machine"))
        self.plugin.get_queue_stats = MagicMock(side_effect=Exception("queue"))

        self._assert_thrown("statsrequest:all:appid", "all")
        self._assert_thrown("statsrequest:kafka-monitor:appid", "kafka")
        self._assert_thrown("statsrequest:redis-monitor:appid", "redis")
        self._assert_thrown("statsrequest:crawler:appid", "crawler")
        self._assert_thrown("statsrequest:spider:appid", "spider")
        self._assert_thrown("statsrequest:queue:appid", "queue")

    def test_stats_get_spider(self):
        stat_keys = [
            'stats:crawler:host1:link:200:3600',
            'stats:crawler:host2:link:200:lifetime',
            'stats:crawler:host1:link:504:86400',
            'stats:crawler:host3:link:200:86400',
            'stats:crawler:host2:link:ABCDEF',
            'stats:crawler:host3:link:ABCDEF',
            'stats:crawler:host1:link:123345',
            'stats:crawler:host2:other:403:lifetime',
            'stats:crawler:host1:other:200:3600',
            'stats:crawler:host2:other:ABCDEF1',
        ]

        # set up looping calls to redis_conn.keys()
        def side_effect(*args):
            return stat_keys

        self.plugin.redis_conn.keys = MagicMock(side_effect=side_effect)

        result = self.plugin.get_spider_stats()
        good = {
            'spiders': {
                'unique_spider_count': 2,
                'total_spider_count': 4,
                'other': {'count': 1, '200': {'3600': 5}, '403': {'lifetime': 5}},
                'link': {'count': 3, '200': {'lifetime': 5, '86400': 5, '3600': 5}, '504': {'86400': 5}
                }
            }
        }
        self.assertEqual(result, good)

    def test_stats_get_machine(self):
        # tests stats on three different machines, with different spiders
        # contributing to the same or different stats
        self.plugin.redis_conn.keys = MagicMock(return_value=[
                                                'stats:crawler:host1:link:200:3600',
                                                'stats:crawler:host2:link:200:lifetime',
                                                'stats:crawler:host1:link:504:86400',
                                                'stats:crawler:host2:other:403:lifetime',
                                                'stats:crawler:host3:link:200:86400',
                                                'stats:crawler:host1:other:200:3600',
                                                ])
        result = self.plugin.get_machine_stats()
        good = {
            'machines': {
                'count': 3,
                'host1': {'200': {'3600': 10},'504': {'86400': 5}},
                'host2': {'200': {'lifetime': 5},'403': {'lifetime': 5}},
                'host3': {'200': {'86400': 5}}
            }
        }
        self.assertEqual(result, good)

    def test_stats_get_queue(self):
        # tests stats on three different machines, with different spiders
        # contributing to the same or different stats
        self.plugin.redis_conn.keys = MagicMock(return_value=[
                                                'link:istresearch.com:queue',
                                                'link:yellowpages.com:queue',
                                                'link:cnn.com:queue',
                                                'wandering:dmoztools.net:queue',
                                                'wandering:craigslist.org:queue',
                                                ])
        results = [5, 10, 11, 1, 3]

        def ret_val(*args):
            return results.pop(0)

        self.plugin.redis_conn.zcard = MagicMock(side_effect=ret_val)

        result = self.plugin.get_queue_stats()
        good = {
            'queues': {
                'total_backlog': 30,
                'queue_link': {
                    'spider_backlog': 26,
                    'num_domains': 3,
                    'domains': [
                        {'domain': 'istresearch.com', 'backlog': 5},
                        {'domain': 'yellowpages.com', 'backlog': 10},
                        {'domain': 'cnn.com', 'backlog': 11}
                    ]
                },
                'queue_wandering': {
                    'spider_backlog': 4,
                    'num_domains': 2,
                    'domains': [
                        {'domain': 'dmoztools.net', 'backlog': 1},
                        {'domain': 'craigslist.org', 'backlog': 3},
                    ]
                }
            }
        }
        self.assertEqual(result, good)

    def test_stats_get_plugin(self):
        self.plugin.redis_conn.keys = MagicMock(return_value=[
                                                'stats:main:total:3600',
                                                'stats:main:total:lifetime',
                                                'stats:main:pluginX:86400',
                                                'stats:main:pluginX:lifetime',
                                                'stats:main:fail:3600',
                                                'stats:main:fail:68000'
                                                ])
        result = self.plugin._get_plugin_stats('main')
        good = {
            "plugins": {
                "pluginX": {"lifetime": 5, "86400": 5}
            },
            "total": {"lifetime": 5, "3600": 5},
            "fail": {"68000": 5, "3600": 5}
        }
        self.assertEqual(result, good)

class TestZookeeperPlugin(TestCase, RegexFixer):
    def setUp(self):
        self.plugin = ZookeeperMonitor()
        self.plugin.redis_conn = MagicMock()
        self.plugin.logger = MagicMock()
        self.plugin._send_to_kafka = MagicMock()
        self.plugin.zoo_client = MagicMock()
        self.plugin.zoo_client.get = MagicMock()
        self.plugin.zoo_client.set = MagicMock()
        self.plugin.path = "/some/path"

    def test_zk_regex(self):
        regex = self.fix_re(self.plugin.regex)
        self.assertEqual(re.findall(regex, 'zk:blah1:blah2:bla3'),
                          ['zk:blah1:blah2:bla3'])
        self.assertEqual(re.findall(regex, 'zk:blah1:blah2'), [])

    def test_zk_handle_du(self):
        # domain update
        s = b'blacklist: []\ndomains:\n  dmoztools.net: {hits: 60, scale: 1.0, window: 60}\n'
        val = '{"uuid":"blah123","hits":15,"scale":0.9,"window":60}'
        expected = b'blacklist: []\ndomains:\n  cnn.com:\n    hits: 15\n    scale: 0.9\n    window: 60\n  dmoztools.net:\n    hits: 60\n    scale: 1.0\n    window: 60\n'
        self.plugin.zoo_client.get = MagicMock(return_value=(s,))
        self.plugin.handle(key="zk:domain-update:cnn.com:testapp", value=val)
        self.plugin.zoo_client.set.assert_called_once_with("/some/path", expected)

    def test_zk_handle_dr(self):
        # domain remove
        s = b'blacklist: []\ndomains:\n  dmoztools.net: {hits: 60, scale: 1.0, window: 60}\n'
        val = '{"uuid":"blah123"}'
        expected = b'blacklist: []\ndomains: {}\n'
        self.plugin.zoo_client.get = MagicMock(return_value=(s,))
        self.plugin.handle(key="zk:domain-remove:dmoztools.net:testapp", value=val)
        self.plugin.zoo_client.set.assert_called_once_with("/some/path", expected)

    def test_zk_handle_bu(self):
        # blacklist update
        s = b'blacklist: []\ndomains: {}\n'
        val = '{"uuid":"blah123"}'
        expected = b'blacklist:\n- bingo.com\ndomains: {}\n'
        self.plugin.zoo_client.get = MagicMock(return_value=(s,))
        self.plugin.handle(key="zk:blacklist-update:bingo.com:testapp", value=val)
        self.plugin.zoo_client.set.assert_called_once_with("/some/path", expected)

    def test_zk_handle_br(self):
        # blacklist remove
        s = b'blacklist: [bingo.com]\ndomains: {}\n'
        val = '{"uuid":"blah123"}'
        expected = b'blacklist: []\ndomains: {}\n'
        self.plugin.zoo_client.get = MagicMock(return_value=(s,))
        self.plugin.handle(key="zk:blacklist-remove:bingo.com:testapp", value=val)
        self.plugin.zoo_client.set.assert_called_once_with("/some/path", expected)

    def test_zk_errors(self):
        self.plugin._get_current_time = MagicMock(return_value=5)
        # test error on get
        self.plugin.zoo_client.get = MagicMock(side_effect=ZookeeperError)
        val = '{"uuid":"blah123"}'
        self.plugin.handle(key="zk:blacklist-update:bingo.com:testapp", value=val)
        expected = {'domain': 'bingo.com',
                    'server_time': 5,
                    'uuid': u'blah123',
                    'appid': 'testapp',
                    'error': 'Unable to load Zookeeper config',
                    'action': 'blacklist-update'}
        self.plugin._send_to_kafka.assert_called_once_with(expected)
        self.plugin._send_to_kafka.reset_mock()

        # set error on set
        self.plugin.zoo_client.get.reset_mock()
        self.plugin.zoo_client.set = MagicMock(side_effect=ZookeeperError)
        self.plugin.handle(key="zk:blacklist-update:bingo.com:testapp", value=val)
        expected = {'domain': 'bingo.com',
                    'server_time': 5,
                    'uuid': u'blah123',
                    'appid': 'testapp',
                    'error': "Unable to store Zookeeper config",
                    'action': 'blacklist-update'}
        self.plugin._send_to_kafka.assert_called_once_with(expected)
