'''
Online integration tests
'''

import unittest
from unittest import TestCase
from mock import MagicMock

import sys
from os import path

sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
from redis_monitor import RedisMonitor
from plugins.kafka_base_monitor import KafkaBaseMonitor
from kafka import KafkaConsumer

import settings
import redis
import json


class CustomMonitor(KafkaBaseMonitor):
    '''
    Custom Monitor so we can run this test live without interference
    '''
    regex = "info-test:*"

    def setup(self, settings):
        KafkaBaseMonitor.setup(self, settings)

    def handle(self, key, value):
        return_dict = {
            "info-test": value,
            "appid": "someapp"
        }
        self._send_to_kafka(return_dict)
        self.redis_conn.delete(key)


class TestRedisMonitor(TestCase):

    maxDiff = None
    queue_key = "link:istresearch.com:queue"

    def setUp(self):
        self.redis_monitor = RedisMonitor("localsettings.py")
        self.redis_monitor.settings = self.redis_monitor.wrapper.load("localsettings.py")
        self.redis_monitor.logger = MagicMock()
        self.redis_monitor.settings['KAFKA_TOPIC_PREFIX'] = "demo_test"
        self.redis_monitor.settings['STATS_TOTAL'] = False
        self.redis_monitor.settings['STATS_PLUGINS'] = False
        self.redis_monitor.settings['PLUGINS'] = {
            'plugins.info_monitor.InfoMonitor': None,
            'plugins.stop_monitor.StopMonitor': None,
            'plugins.expire_monitor.ExpireMonitor': None,
            'tests.tests_online.CustomMonitor': 100,
        }
        self.redis_monitor.redis_conn = redis.Redis(
            host=self.redis_monitor.settings['REDIS_HOST'],
            port=self.redis_monitor.settings['REDIS_PORT'],
            db=self.redis_monitor.settings['REDIS_DB'])

        self.redis_monitor._load_plugins()
        self.redis_monitor.stats_dict = {}

        self.consumer = KafkaConsumer(
            "demo_test.outbound_firehose",
            bootstrap_servers=self.redis_monitor.settings['KAFKA_HOSTS'],
            group_id="demo-id",
            consumer_timeout_ms=5000,
        )

    def test_process_item(self):
        # set the info flag
        key = "info-test:blah"
        value = "ABC123"
        self.redis_monitor.redis_conn.set(key, value)

        # process the request
        plugin = self.redis_monitor.plugins_dict.items()[0][1]
        self.redis_monitor._process_plugin(plugin)

        # ensure the key is gone
        self.assertEquals(self.redis_monitor.redis_conn.get(key), None)

    def test_sent_to_kafka(self):
        success = {
            u'info-test': "ABC123",
            u"appid": u"someapp"
        }

        # ensure it was sent out to kafka
        message_count = 0
        for message in self.consumer:
            if message is None:
                break
            else:
                the_dict = json.loads(message.value)
                self.assertEquals(success, the_dict)
                message_count += 1

        self.assertEquals(message_count, 1)

    def tearDown(self):
        self.redis_monitor.close()
        self.consumer.close()

if __name__ == '__main__':
    unittest.main()
