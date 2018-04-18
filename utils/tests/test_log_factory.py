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

    def test_include_extra_log(self):
        self.logger.log_level = 'INFO'
        self.logger.include_extra = True
        with LogCapture() as l:
            self.logger.info('info message', {"test": 1})

        l.check(
            ('test', 'INFO', "info message {'test': 1}"),
        )

        # don't output an empty dict
        with LogCapture() as l:
            self.logger.info('info message2', {})

        l.check(
            ('test', 'INFO', "info message2"),
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

class TestLogCallbacks(TestCase):
    def setUp(self):
        self.logger = LogObject(name='test', json=True,
                                dir='.', level='INFO', stdout=False,
                                )
        self.logger.x = 1

    def test_log_callbacks_integration(self):
        def add_1(log_message=None, log_extra=None):
            self.logger.x += 1

        def negate(log_message=None, log_extra=None):
            self.logger.x *= -1

        def multiply_5(log_message=None, log_extra=None):
            self.logger.x *= 5

        self.logger.register_callback('<=INFO', add_1, {'key': 'val1'})
        self.logger.register_callback('<=INFO', negate, {'key': 'val2'})
        self.logger.register_callback('<=INFO', multiply_5)

        self.logger.x = 1
        self.logger.log_level = 'INFO'
        self.logger.info('info message')
        self.assertEqual(5, self.logger.x)

        self.logger.x = 1
        self.logger.log_level = 'INFO'
        self.logger.info('info message', extra={'key': 'val1'})
        self.assertEqual(10, self.logger.x)

        self.logger.x = 1
        self.logger.log_level = 'INFO'
        self.logger.info('info message', extra={'key': 'val2'})
        self.assertEqual(-5, self.logger.x)

        # Callback shouldn't fire
        self.logger.x = 1
        self.logger.log_level = 'CRITICAL'
        self.logger.info('info message')
        self.assertEqual(1, self.logger.x)

        # Callback shouldn't fire
        self.logger.x = 1
        self.logger.log_level = 'INFO'
        self.logger.warning('warning message')
        self.assertEqual(1, self.logger.x)

    def test_parse_log_level(self):
        log_range = self.logger.cb_handler.parse_log_level("<=INFO")
        self.assertEqual([0,1], log_range)

        log_range = self.logger.cb_handler.parse_log_level("<INFO")
        self.assertEqual([0], log_range)

        log_range = self.logger.cb_handler.parse_log_level(">=WARNING")
        self.assertEqual([2,3,4], log_range)

        log_range = self.logger.cb_handler.parse_log_level(">WARN")
        self.assertEqual([3,4], log_range)

        log_range = self.logger.cb_handler.parse_log_level("=INFO")
        self.assertEqual([1], log_range)

        log_range = self.logger.cb_handler.parse_log_level("CRITICAL")
        self.assertEqual([4], log_range)

    def test_register_callback(self):
        def add_1(log_obj, log_message=None, log_extra=None):
            pass

        def add_2(log_obj, log_message=None, log_extra=None):
            pass

        def add_3(log_obj, log_message=None, log_extra=None):
            pass

        def add_4(log_obj, log_message=None, log_extra=None):
            pass

        self.logger.register_callback('>=INFO', add_1)
        self.logger.register_callback('<=WARN', add_2)
        self.logger.register_callback('ERROR', add_3)
        self.logger.register_callback('*', add_4)

        callbacks = [cb for cb,criteria in self.logger.cb_handler.callbacks['DEBUG']]
        self.assertEqual([add_2, add_4], callbacks)

        callbacks = [cb for cb,criteria in self.logger.cb_handler.callbacks['INFO']]
        self.assertEqual([add_1, add_2, add_4], callbacks)

        callbacks = [cb for cb,criteria in self.logger.cb_handler.callbacks['WARNING']]
        self.assertEqual([add_1, add_2, add_4], callbacks)

        callbacks = [cb for cb,criteria in self.logger.cb_handler.callbacks['ERROR']]
        self.assertEqual([add_1, add_3, add_4], callbacks)

        callbacks = [cb for cb,criteria in self.logger.cb_handler.callbacks['CRITICAL']]
        self.assertEqual([add_1, add_4], callbacks)

    def test_fire_callbacks_basic_1(self):
        def add_1(log_message=None, log_extra=None):
            self.logger.x += 1

        def negate(log_message=None, log_extra=None):
            self.logger.x *= -1

        def multiply_5(log_message=None, log_extra=None):
            self.logger.x *= 5

        self.logger.register_callback('<=INFO', add_1)
        self.logger.register_callback('INFO', negate)
        self.logger.register_callback('<CRITICAL', add_1)
        self.logger.register_callback('>DEBUG', multiply_5)

        self.logger.x = 0
        self.logger.log_level = 'DEBUG'
        self.logger.cb_handler.fire_callbacks('DEBUG')
        self.assertEqual(2, self.logger.x)

        self.logger.x = 0
        self.logger.log_level = 'INFO'
        self.logger.cb_handler.fire_callbacks('INFO')
        self.assertEqual(0, self.logger.x)

        self.logger.x = 0
        self.logger.log_level = 'WARNING'
        self.logger.cb_handler.fire_callbacks('WARNING')
        self.assertEqual(5, self.logger.x)

        self.logger.x = 0
        self.logger.log_level = 'ERROR'
        self.logger.cb_handler.fire_callbacks('ERROR')
        self.assertEqual(5, self.logger.x)

        self.logger.x = 0
        self.logger.log_level = 'CRITICAL'
        self.logger.cb_handler.fire_callbacks('CRITICAL')
        self.assertEqual(0, self.logger.x)

    def test_fire_callbacks_basic_2(self):
        def add_1(log_message=None, log_extra=None):
            self.logger.x += 1

        def negate(log_message=None, log_extra=None):
            self.logger.x *= -1

        def multiply_5(log_message=None, log_extra=None):
            self.logger.x *= 5

        self.logger.register_callback('>DEBUG', add_1)
        self.logger.register_callback('=WARNING', negate)
        self.logger.register_callback('<INFO', add_1)
        self.logger.register_callback('>=INFO', multiply_5)
        self.logger.register_callback('*', add_1)

        self.logger.x = 0
        self.logger.log_level = 'DEBUG'
        self.logger.cb_handler.fire_callbacks('DEBUG')
        self.assertEqual(2, self.logger.x)

        self.logger.x = 0
        self.logger.log_level = 'INFO'
        self.logger.cb_handler.fire_callbacks('INFO')
        self.assertEqual(6, self.logger.x)

        self.logger.x = 0
        self.logger.log_level = 'WARNING'
        self.logger.cb_handler.fire_callbacks('WARNING')
        self.assertEqual(-4, self.logger.x)

        self.logger.x = 0
        self.logger.log_level = 'ERROR'
        self.logger.cb_handler.fire_callbacks('ERROR')
        self.assertEqual(6, self.logger.x)

        self.logger.x = 0
        self.logger.log_level = 'CRITICAL'
        self.logger.cb_handler.fire_callbacks('CRITICAL')
        self.assertEqual(6, self.logger.x)

    def test_preserve_data(self):
        self.logger._get_time = MagicMock(return_value='2015-11-12T10:11:12.0Z')
        message = "THIS IS A TEST"
        extras = {"key": "value", 'a': [1, 2, 3]}
        extras_add = self.logger.add_extras(extras, 'INFO')

        def cb(log_message=None, log_extra=None):
            self.assertEqual(log_message, message)
            self.assertEqual(log_extra, extras_add)

        self.logger.register_callback('>DEBUG', cb)
        self.logger.log_level = 'INFO'
        self.logger.info(message, extras)

    def tearDown(self):
        os.remove('main.log')
        os.remove('main.lock')
