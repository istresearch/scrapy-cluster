'''
Online integration tests
'''

import unittest
from unittest import TestCase
from mock import MagicMock

import sys
from os import path
sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))

from kafka_monitor import KafkaMonitor
from plugins.action_handler import ActionHandler

import settings
import redis
import json


# setup custom class to handle our requests
class CustomHandler(ActionHandler):
    def handle(self, dict):
        key = "cluster:test"
        self.redis_conn.set(key, dict['uuid'])


class TestKafkaMonitor(TestCase):

    def setUp(self):
        self.kafka_monitor = KafkaMonitor("localsettings.py")
        new_settings = self.kafka_monitor.wrapper.load("localsettings.py")
        new_settings['KAFKA_INCOMING_TOPIC'] = "demo.incoming_test"
        new_settings['STATS_TOTAL'] = False
        new_settings['STATS_PLUGINS'] = False
        new_settings['PLUGINS'] = {
            'plugins.scraper_handler.ScraperHandler': None,
            'plugins.action_handler.ActionHandler': None,
            'tests.tests_online.CustomHandler': 100,
        }

        self.kafka_monitor.wrapper.load = MagicMock(return_value=new_settings)
        self.kafka_monitor.setup()
        self.kafka_monitor._setup_kafka()
        self.kafka_monitor._load_plugins()
        self.kafka_monitor._setup_stats()
        self.kafka_monitor.logger = MagicMock()

        self.redis_conn = redis.Redis(
            host=self.kafka_monitor.settings['REDIS_HOST'],
            port=self.kafka_monitor.settings['REDIS_PORT'])

    def test_feed(self):
        json_req = "{\"uuid\":\"mytestid\"," \
            "\"appid\":\"testapp\",\"action\":\"info\",\"spiderid\":\"link\"}"
        parsed = json.loads(json_req)

        self.kafka_monitor.feed(parsed)

    def test_run(self):
        self.kafka_monitor._process_messages()
        self.assertTrue(self.redis_conn.exists("cluster:test"))
        value = self.redis_conn.get("cluster:test")
        self.assertEqual(value, "mytestid")

    def tearDown(self):
        self.redis_conn.delete("cluster:test")

if __name__ == '__main__':
    unittest.main()
