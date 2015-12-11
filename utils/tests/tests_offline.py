'''
Offline utility tests
'''

import unittest
from unittest import TestCase
import os
import time
import json
import copy

from mock import MagicMock
from testfixtures import LogCapture
from redis.exceptions import WatchError

from scutils.method_timer import MethodTimer
from scutils.log_factory import LogFactory, LogObject
from scutils.settings_wrapper import SettingsWrapper
from scutils.stats_collector import AbstractCounter
from scutils.redis_throttled_queue import RedisThrottledQueue


class TestMethodTimer(TestCase):

    def test_under(self):
        @MethodTimer.timeout(1, False)
        def method():
            time.sleep(0.5)
            return True
        result = method()
        self.assertTrue(result)

    def test_over(self):
        @MethodTimer.timeout(1, "STUFF")
        def method():
            time.sleep(1.5)
            return True
        result = method()
        self.assertEqual(result, "STUFF")

    def test_params(self):
        @MethodTimer.timeout(1, "STUFF2")
        def method(param1, param2, param3):
            time.sleep(1.5)
            return True
        result = method(True, "Stuff", ['item'])
        self.assertEqual(result, "STUFF2")


class TestSettingsWrapper(TestCase):

    defaults = {"STRING": "stuff", "DICT": {"value": "other stuff"}}

    def setUp(self):
        self.wrapper = SettingsWrapper()

    def test_no_defaults(self):
        self.wrapper._load_defaults()
        sets = self.wrapper.settings()
        self.assertEqual(sets, {})

    def test_load_default(self):
        self.wrapper._load_defaults("test_default_settings.py")
        sets = self.wrapper.settings()
        self.assertEqual(sets, self.defaults)

    def test_no_override(self):
        # test no prior defaults
        self.wrapper.my_settings = {}
        self.wrapper._load_custom()
        sets = self.wrapper.settings()
        self.assertEqual(sets, {})

        self.wrapper._load_defaults("test_default_settings.py")
        self.wrapper._load_custom()
        sets = self.wrapper.settings()
        self.assertEqual(sets, self.defaults)

    def test_override_default(self):
        self.wrapper._load_defaults("test_default_settings.py")
        self.wrapper._load_custom("test_override_defaults.py")
        sets = self.wrapper.settings()
        actual = {
            'NEW_DICT': {
                'other': 'stuff'
            },
            'MY_STRING': 'cool',
            'DICT': {
                'append': 'value',
                'value': 'override'
            },
            'STRING': 'my stuff',
            'NEW_LIST': ['item1']
        }
        self.assertEqual(sets, actual)

    def test_load_string(self):
        s = """STRING = \"my stuff\"\nMY_STRING = \"cool\"\nNEW_LIST = [\'item2\']"""

        real = {
            'STRING': 'my stuff',
            'MY_STRING': 'cool',
            'NEW_LIST': ['item2']
        }

        sets = self.wrapper.load_from_string(s)
        self.assertItemsEqual(real, sets)


class TestLogFactory(TestCase):
    def setUp(self):
        self.logger = LogFactory.get_instance(name='test',
                                              dir='./', level='DEBUG',
                                              propagate=True)

    def test_debug_log(self):
        self.logger.log_level = 'DEBUG'
        with LogCapture() as l:
            self.logger.debug('debug message')
            self.logger.info('info message')
        l.check(
            ('test', 'DEBUG', 'debug message'),
            ('test', 'INFO', 'info message'),
        )

    def test_info_log(self):
        self.logger.log_level = 'INFO'
        with LogCapture() as l:
            self.logger.debug('debug message')
            self.logger.info('info message')
            self.logger.warn('warn message')
        l.check(
            ('test', 'INFO', 'info message'),
            ('test', 'WARNING', 'warn message'),
        )

    def test_warn_log(self):
        self.logger.log_level = 'WARN'
        with LogCapture() as l:
            self.logger.info('info message')
            self.logger.warn('warn message')
            self.logger.error('error message')
        l.check(
            ('test', 'WARNING', 'warn message'),
            ('test', 'ERROR', 'error message'),
        )

    def test_error_log(self):
        self.logger.log_level = 'ERROR'
        with LogCapture() as l:
            self.logger.warn('warn message')
            self.logger.error('error message')
            self.logger.critical('critical message')

        l.check(
            ('test', 'ERROR', 'error message'),
            ('test', 'CRITICAL', 'critical message'),
        )

    def test_critical_log(self):
        self.logger.log_level = 'CRITICAL'
        with LogCapture() as l:
            self.logger.error('error message')
            self.logger.critical('critical message')

        l.check(
            ('test', 'CRITICAL', 'critical message'),
        )

class TestLogJSONFile(TestCase):
    def setUp(self):
        self.logger = LogObject(name='test', json=True,
                                dir='.', level='INFO', stdout=False,
                                file='test.log')
        self.test_file = './test'

    def test_log_file_json(self):
        self.logger._get_time = MagicMock(return_value='2015-11-12T10:11:12.0Z')
        self.logger.info("Test log")
        with open(self.test_file + '.log', 'r') as f:
            read_data = f.read()
            the_dict = json.loads(read_data)
            self.assertItemsEqual(the_dict, {
                "message": "Test log",
                "level": "INFO",
                "logger":"test",
                "timestamp":"2015-11-12T10:11:12.0Z"})

    def test_preserve_extra(self):
        self.logger.log_level = 'DEBUG'
        before = {"some": "dict", "a": 1}
        preserve = copy.deepcopy(before)
        with LogCapture() as l:
            self.logger.debug("my message", extra=before)

        self.assertEqual(preserve, before)

    def tearDown(self):
        os.remove(self.test_file + '.log')
        os.remove(self.test_file + '.lock')


class TestStatsAbstract(TestCase):

    def test_default_key(self):
        ac = AbstractCounter()
        self.assertEqual('default_counter', ac.get_key())

    def test_overloaded_key(self):
        ac = AbstractCounter('aKey')
        self.assertEqual('aKey', ac.get_key())

    def test_not_implemented(self):
        ac = AbstractCounter()

        try:
            ac.increment()
            self.fail("increment should be abstract")
        except NotImplementedError:
            pass

        try:
            ac.value()
            self.fail("value should be abstract")
        except NotImplementedError:
            pass

        try:
            ac.expire()
            self.fail("expire should be abstract")
        except NotImplementedError:
            pass

        try:
            ac.increment()
            self.fail("increment should be abstract")
        except NotImplementedError:
            pass


class TestUnmoderatedRedisThrottledQueue(TestCase):

    def setUp(self):
        # limit is 2 hits in the window
        self.queue = RedisThrottledQueue(MagicMock(), MagicMock(), 1, 2)

    def test_unmoderated(self):
        # an unmoderated queue is really just testing the number
        # of hits in a given window
        self.queue.redis_conn.zcard = MagicMock(return_value=0)
        self.assertTrue(self.queue.allowed())

        self.queue.redis_conn.zcard = MagicMock(return_value=1)
        self.assertTrue(self.queue.allowed())

        self.queue.redis_conn.zcard = MagicMock(return_value=2)
        self.assertFalse(self.queue.allowed())

        # mock exception raised even with good hits
        self.queue.redis_conn.zcard = MagicMock(return_value=0,
                                                side_effect=WatchError)
        self.assertFalse(self.queue.allowed())


class TestModeratedRedisThrottledQueue(TestCase):

    def setUp(self):
        self.queue = RedisThrottledQueue(MagicMock(), MagicMock(), 4, 2, True)

    def test_moderated(self):
        # a moderated queue should pop ~ every x seconds
        # we already tested the window limit in the unmoderated test
        self.queue.is_moderated = MagicMock(return_value=True)
        self.assertFalse(self.queue.allowed())

        self.queue.is_moderated = MagicMock(return_value=False)
        self.queue.test_hits = MagicMock(return_value=True)
        self.assertTrue(self.queue.allowed())

        # mock exception raised even with good moderation
        self.queue.test_hits = MagicMock(side_effect=WatchError)
        self.assertFalse(self.queue.allowed())

if __name__ == '__main__':
    unittest.main()
