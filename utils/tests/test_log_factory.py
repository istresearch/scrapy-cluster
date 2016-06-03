'''
Offline utility tests
'''

from unittest import TestCase
import os
import json
import copy
import six

from mock import MagicMock
from testfixtures import LogCapture

from scutils.log_factory import LogFactory, LogObject


class TestLogFactory(TestCase):
    def setUp(self):
        self.logger = LogFactory.get_instance(name='test',
                                              dir='./', level='DEBUG',
                                              propagate=True)

    def test_name_as_property(self):
        self.assertEqual('test', self.logger.name)

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
            six.assertCountEqual(self, the_dict, {
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
