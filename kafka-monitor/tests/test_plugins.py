'''
Offline tests
'''

import unittest
from unittest import TestCase
from mock import MagicMock

import sys
from os import path
sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))

from kafka_monitor import KafkaMonitor
from plugins.scraper_handler import ScraperHandler
from plugins.base_handler import BaseHandler
from plugins.action_handler import ActionHandler
from plugins.stats_handler import StatsHandler
from plugins.zookeeper_handler import ZookeeperHandler
import copy

from kafka.common import OffsetOutOfRangeError
from jsonschema import Draft4Validator
import tldextract

class TestPlugins(TestCase):

    def test_default_handler(self):
        handler = BaseHandler()
        try:
            handler.setup("s")
            self.fail("base setup should be abstract")
        except NotImplementedError:
            pass

        try:
            handler.handle({})
            self.fail("base handler should be abstract")
        except NotImplementedError:
            pass

    def test_scrape_handler(self):
        valid = {
            "url": "www.stuff.com",
            "crawlid": "abc124",
            "appid": "testapp",
            "spiderid": "link",
            "priority": 5,
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
            self.assertEqual("added", str(e))

        # check timeout is added
        handler.redis_conn.zadd = MagicMock()
        handler.redis_conn.set = MagicMock(side_effect=AssertionError("expires"))
        valid['expires'] = 124242
        try:
            handler.handle(valid)
            self.fail("Expires not called")
        except AssertionError as e:
            self.assertEqual("expires", str(e))

    def test_action_handler(self):
        handler = ActionHandler()
        handler.redis_conn = MagicMock()
        handler.redis_conn.set = MagicMock(side_effect=AssertionError("added"))

        valid = {
            "uuid": "abaksdjb",
            "crawlid": "abc124",
            "appid": "testapp",
            "spiderid": "link",
            "action": "info",
        }

        try:
            handler.handle(valid)
            self.fail("Added not called")
        except AssertionError as e:
            self.assertEqual("added", str(e))

    def test_stats_handler(self):
        handler = StatsHandler()
        handler.redis_conn = MagicMock()
        handler.redis_conn.set = MagicMock(side_effect=AssertionError("added"))

        valid = {
            "uuid":"abaksdjb",
            "appid":"testapp",
            "stats":"all",
        }

        try:
            handler.handle(valid)
            self.fail("Added not called")
        except AssertionError as e:
            self.assertEqual("added", str(e))

    def test_zookeeper_handler(self):
        handler = ZookeeperHandler()
        handler.redis_conn = MagicMock()
        handler.redis_conn.set = MagicMock(side_effect=AssertionError("added"))

        valid = {
            "uuid": "abaksdjb",
            "appid": "testapp",
            "domain": "ebay.com",
            "action": "domain-update",
            "window": 15,
            "hits":  10,
            "scale": 1.0
        }

        try:
            handler.handle(valid)
            self.fail("Added not called")
        except AssertionError as e:
            self.assertEqual("added", str(e))

    def test_bad_plugins(self):
        class ForgotSchema(BaseHandler):
            def handle(self, d):
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
        except NotImplementedError:
            pass
