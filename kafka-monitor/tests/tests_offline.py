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

from kafka_monitor import KafkaMonitor
from plugins.scraper_handler import ScraperHandler
from plugins.base_handler import BaseHandler
from plugins.action_handler import ActionHandler
import copy

from kafka.common import OffsetOutOfRangeError
from jsonschema import ValidationError
from jsonschema import Draft4Validator
import tldextract

class ExampleHandler(BaseHandler):
    schema = "crazy_schema.json"

    def setup(self, settings):
        pass

class TestKafkaMonitor(TestCase):

    def setUp(self):
        self.kafka_monitor = KafkaMonitor("settings.py", True)
        self.kafka_monitor.settings = self.kafka_monitor.wrapper.load("settings.py")
        self.kafka_monitor.logger = MagicMock()

    def test_load_plugins(self):
        # test loading default plugins
        assert_keys = [100,200]
        self.kafka_monitor._load_plugins()
        self.assertEqual(self.kafka_monitor.plugins_dict.keys(), assert_keys)

        # test removing a plugin from settings
        assert_keys = [200]
        self.kafka_monitor.settings['PLUGINS'] \
            ['plugins.scraper_handler.ScraperHandler'] = None
        self.kafka_monitor._load_plugins()
        self.assertEqual(self.kafka_monitor.plugins_dict.keys(), assert_keys)
        self.kafka_monitor.settings['PLUGINS'] \
            ['plugins.scraper_handler.ScraperHandler'] = 100

        # fail if the class is not found
        self.kafka_monitor.settings['PLUGINS'] \
            ['plugins.crazy_class.CrazyHandler'] = 300
        self.assertRaises(ImportError, self.kafka_monitor._load_plugins)
        del self.kafka_monitor.settings['PLUGINS'] \
            ['plugins.crazy_class.CrazyHandler']

        # Throw error if schema could not be found
        self.kafka_monitor.settings['PLUGINS'] \
            ['tests.tests_offline.ExampleHandler'] = 300,
       # self.kafka_monitor.default_plugins = copy.deepcopy(self.defaults)
        self.assertRaises(IOError, self.kafka_monitor._load_plugins)
        # del self.kafka_monitor.default_plugins.pop('tests.tests_offline.ExampleHandler')
        del self.kafka_monitor.settings['PLUGINS'] \
            ['tests.tests_offline.ExampleHandler']

    def test_load_stats_total(self):
        self.fail("Not implemented")
        pass

    def test_load_stats_plugins(self):
        self.fail("Not implemented")
        pass

    def test_process_messages(self):
        self.kafka_monitor.consumer = MagicMock()
        self.kafka_monitor.stats_dict = {}

        # handle kafka offset errors
        self.kafka_monitor.consumer.get_messages = MagicMock(
                        side_effect=OffsetOutOfRangeError("1"))
        try:
            self.kafka_monitor._process_messages()
        except OffsetOutOfRangeError:
            self.fail("_process_messages did not handle Kafka Offset Error")

        # handle bad json errors
        message_string = "{\"sdasdf   sd}"
        # fake class so we can use dot notation
        class a:
            pass
        m = a()
        m.message = a()
        m.message.value = message_string
        messages = [m]
        self.kafka_monitor.consumer.get_messages = MagicMock(
                                                        return_value=messages)
        try:
            self.kafka_monitor._process_messages()
        except OffsetOutOfRangeError:
            self.fail("_process_messages did not handle bad json")

        # set up to process messages
        self.kafka_monitor.consumer.get_messages = MagicMock(
                                                        return_value=messages)
        self.kafka_monitor._load_plugins()
        self.kafka_monitor.validator = self.kafka_monitor.extend_with_default(Draft4Validator)
        self.kafka_monitor.plugins_dict.items()[0][1]['instance'].handle = MagicMock(side_effect=AssertionError("scrape"))
        self.kafka_monitor.plugins_dict.items()[1][1]['instance'].handle = MagicMock(side_effect=AssertionError("action"))


        # test that handler function is called for the scraper
        message_string = "{\"url\":\"www.stuff.com\",\"crawlid\":\"1234\"," \
            "\"appid\":\"testapp\"}"
        m.message.value = message_string
        messages = [m]
        try:
            self.kafka_monitor._process_messages()
            self.fail("Scrape not called")
        except AssertionError as e:
            self.assertEquals("scrape", e.message)

        # test that handler function is called for the actions
        message_string = "{\"uuid\":\"blah\",\"crawlid\":\"1234\"," \
            "\"appid\":\"testapp\",\"action\":\"info\",\"spiderid\":\"link\"}"
        m.message.value = message_string
        messages = [m]
        try:
            self.kafka_monitor._process_messages()
            self.fail("Action not called")
        except AssertionError as e:
            self.assertEquals("action", e.message)

class TestPlugins(TestCase):

    def test_default_handler(self):
        handler = BaseHandler()
        try:
            handler.setup("s")
            self.fail("base setup should be abstract")
        except NotImplementedError as e:
            pass

        try:
            handler.handle({})
            self.fail("base handler should be abstract")
        except NotImplementedError as e:
            pass

    def test_scrape_handler(self):
        valid = {
            "url":"www.stuff.com",
            "crawlid":"abc124",
            "appid":"testapp",
            "spiderid":"link",
            "priority":5,
        }
        handler = ScraperHandler()
        handler.extract = tldextract.TLDExtract()
        handler.redis_conn = MagicMock()

        # check it is added to redis
        handler.redis_conn.zadd = MagicMock(side_effect=AssertionError("added"))
        try:
            handler.handle(valid)
            self.fail("Action not called")
        except AssertionError as e:
            self.assertEquals("added", e.message)

        # check timeout is added
        handler.redis_conn.zadd = MagicMock()
        handler.redis_conn.set = MagicMock(side_effect=AssertionError("expires"))
        valid['expires'] = 124242
        try:
            handler.handle(valid)
            self.fail("Expires not called")
        except AssertionError as e:
            self.assertEquals("expires", e.message)

    def test_action_handler(self):
        handler = ActionHandler()
        handler.redis_conn = MagicMock()
        handler.redis_conn.set = MagicMock(side_effect=AssertionError("added"))

        valid = {
            "uuid":"abaksdjb",
            "crawlid":"abc124",
            "appid":"testapp",
            "spiderid":"link",
            "action":"info",
        }

        try:
            handler.handle(valid)
            self.fail("Added not called")
        except AssertionError as e:
            self.assertEquals("added", e.message)

    def test_bad_plugins(self):
        class ForgotSchema(BaseHandler):
            def handle(self,d):
                pass
        class ForgotHandle(BaseHandler):
            schema = "mySchema"

        handler = ForgotSchema()
        try:
            handler.setup("s")
            self.fail("did not raise error")
        except NotImplementedError as e:
            pass
        handler.handle({})

        handler = ForgotHandle()
        handler.setup("s")
        try:
            handler.handle({})
            self.fail("did not raise error")
        except NotImplementedError as e:
            pass

if __name__ == '__main__':
    unittest.main()