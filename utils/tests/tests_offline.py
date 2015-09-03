'''
Offline utility tests
'''

import unittest
from unittest import TestCase
import mock
from mock import MagicMock

import os
import sys
import time
import contextlib
import json
from testfixtures import LogCapture
from os import path
sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))

from method_timer import MethodTimer
from log_factory import LogFactory
from log_factory import LogObject
from settings_wrapper import SettingsWrapper

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

    defaults = {"STRING":"stuff", "DICT":{"value":"other stuff"}}

    def setUp(self):
        self.wrapper = SettingsWrapper()

    def test_no_defaults(self):
        self.wrapper._load_defaults()
        sets = self.wrapper.settings()
        self.assertEqual(sets, {})

    def test_load_default(self):
        self.wrapper.default_settings = "test_default_settings"
        self.wrapper._load_defaults()
        sets = self.wrapper.settings()
        self.assertEqual(sets, self.defaults)

    def test_no_override(self):
        # test no prior defaults
        self.wrapper.my_settings = {}
        self.wrapper._load_custom()
        sets = self.wrapper.settings()
        self.assertEqual(sets, {})

        self.wrapper.default_settings = "test_default_settings"
        self.wrapper._load_defaults()
        self.wrapper._load_custom()
        sets = self.wrapper.settings()
        self.assertEqual(sets, self.defaults)

    def test_override_default(self):
        self.wrapper.default_settings = "test_default_settings"
        self.wrapper._load_defaults()
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

class TestLogFactory(TestCase):
    def setUp(self):
        self.logger = LogFactory.get_instance(name='test',
                dir='./', level='DEBUG')

    def test_debug_log(self):
        self.logger.log_level = 'DEBUG'
        with LogCapture() as l:
            self.logger.debug('debug message')
            self.logger.info('info message')
        l.check(
            ('test','DEBUG','debug message'),
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
            ('test','WARNING','warn message'),
        )

    def test_warn_log(self):
        self.logger.log_level = 'WARN'
        with LogCapture() as l:
            self.logger.info('info message')
            self.logger.warn('warn message')
            self.logger.critical('critical message')
        l.check(
            ('test','WARNING','warn message'),
            ('test','CRITICAL','critical message'),
        )

    def test_error_log(self):
        self.logger.log_level = 'ERROR'
        with LogCapture() as l:
            self.logger.warn('warn message')
            self.logger.error('error message')
            self.logger.critical('critical message')

        l.check(
            ('test','ERROR','error message'),
            ('test','CRITICAL','critical message'),
        )

    def test_critical_log(self):
        self.logger.log_level = 'CRITICAL'
        with LogCapture() as l:
            self.logger.error('error message')
            self.logger.critical('critical message')

        l.check(
            ('test','CRITICAL','critical message'),
        )

class TestLogJSONFile(TestCase):
    def setUp(self):
        self.logger = LogObject(name='test', json=True,
                dir='tests', level='INFO', stdout=False, file='test.log')
        self.test_file = 'tests/test'

    def test_log_file_json(self):
        self.logger._get_time = MagicMock(return_value=5)
        self.logger.info("Test log")
        with open(self.test_file + '.log', 'r') as f:
            read_data = f.read()
            the_dict = json.loads(read_data)
            del the_dict['timestamp']
            self.assertEqual(the_dict,{"message": "Test log", "level": "INFO"})

    def tearDown(self):
        os.remove(self.test_file + '.log')
        os.remove(self.test_file + '.lock')

if __name__ == '__main__':
    unittest.main()
