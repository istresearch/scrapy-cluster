'''
Online integration tests
'''
from builtins import next

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
from time import sleep


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
    consumer = None

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
            'tests.online.CustomMonitor': 100,
        }
        self.redis_monitor.redis_conn = redis.Redis(
            host=self.redis_monitor.settings['REDIS_HOST'],
            port=self.redis_monitor.settings['REDIS_PORT'],
            db=self.redis_monitor.settings['REDIS_DB'],
            password=self.redis_monitor.settings['REDIS_PASSWORD'],
            decode_responses=True)
        self.redis_monitor.lock_redis_conn = redis.Redis(
            host=self.redis_monitor.settings['REDIS_HOST'],
            port=self.redis_monitor.settings['REDIS_PORT'],
            db=self.redis_monitor.settings['REDIS_DB'],
            password=self.redis_monitor.settings['REDIS_PASSWORD'])

        self.redis_monitor._load_plugins()
        self.redis_monitor.stats_dict = {}

        self.consumer = KafkaConsumer(
            "demo_test.outbound_firehose",
            bootstrap_servers=self.redis_monitor.settings['KAFKA_HOSTS'],
            group_id="demo-id",
            auto_commit_interval_ms=10,
            consumer_timeout_ms=5000,
            auto_offset_reset='earliest',
            value_deserializer=lambda m: m.decode('utf-8')
        )
        sleep(1)

    def test_process_item(self):
        # set the info flag
        key = "info-test:blah"
        value = "ABC1234"
        self.redis_monitor.redis_conn.set(key, value)

        # process the request
        plugin = list(self.redis_monitor.plugins_dict.items())[0][1]
        self.redis_monitor._process_plugin(plugin)

        # ensure the key is gone
        self.assertEqual(self.redis_monitor.redis_conn.get(key), None)
        self.redis_monitor.close()
        sleep(10)
        # now test the message was sent to kafka
        success = {
            u'info-test': "ABC1234",
            u"appid": u"someapp"
        }

        message_count = 0
        m = next(self.consumer)

        if m is None:
            pass
        else:
            the_dict = json.loads(m.value)
            self.assertEqual(success, the_dict)
            message_count += 1

        self.assertEqual(message_count, 1)

    def tearDown(self):
        # if for some reason the tests fail, we end up falling behind on
        # the consumer
        for m in self.consumer:
            pass
        self.consumer.close()

if __name__ == '__main__':
    unittest.main()
