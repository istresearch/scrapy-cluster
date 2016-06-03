'''
Offline utility tests
'''
from __future__ import print_function
from unittest import TestCase
from scutils.settings_wrapper import SettingsWrapper
import six


class TestSettingsWrapper(TestCase):

    defaults = {"STRING": "stuff", "DICT": {"value": "other stuff"}}

    def setUp(self):
        self.wrapper = SettingsWrapper()
        self.wrapper.my_settings = {}

    def test_no_defaults(self):
        self.wrapper.my_settings = {}
        self.wrapper._load_defaults()
        sets = self.wrapper.settings()
        self.assertEqual(sets, {})

    def test_load_default(self):
        self.wrapper._load_defaults("default_settings.py")
        sets = self.wrapper.settings()
        self.assertEqual(sets, self.defaults)

    def test_no_override(self):
        # test no prior defaults
        self.wrapper.my_settings = {}
        self.wrapper._load_custom()
        sets = self.wrapper.settings()
        self.assertEqual(sets, {})

        self.wrapper._load_defaults("default_settings.py")
        self.wrapper._load_custom()
        sets = self.wrapper.settings()
        self.assertEqual(sets, self.defaults)

    def test_override_default(self):
        self.wrapper._load_defaults("default_settings.py")
        self.wrapper._load_custom("override_defaults.py")
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
        six.assertCountEqual(self, real, sets)
