'''
Online link spider test
'''
from __future__ import print_function
from future import standard_library
standard_library.install_aliases()
from builtins import next
import unittest
from unittest import TestCase
import time

import sys
from os import path
sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))

import scrapy
import redis
from redis.exceptions import ConnectionError
import json
import threading, time
from crawling.spiders.link_spider import LinkSpider
from scrapy.utils.project import get_project_settings
from twisted.internet import reactor
from scrapy.crawler import CrawlerRunner
from kafka import KafkaConsumer


class CustomSpider(LinkSpider):
    '''
    Overridden link spider for testing
    '''
    name = "test-spider"


class TestLinkSpider(TestCase):

    example_feed = "{\"allowed_domains\":null,\"allow_regex\":null,\""\
        "crawlid\":\"abc12345\",\"url\":\"istresearch.com\",\"expires\":0,\""\
        "ts\":1461549923.7956631184,\"priority\":1,\"deny_regex\":null,\""\
        "cookie\":null,\"attrs\":null,\"appid\":\"test\",\"spiderid\":\""\
        "test-spider\",\"useragent\":null,\"deny_extensions\":null,\"maxdepth\":0}"

    def setUp(self):
        self.settings = get_project_settings()
        self.settings.set('KAFKA_TOPIC_PREFIX', "demo_test")
        # set up redis
        self.redis_conn = redis.Redis(host=self.settings['REDIS_HOST'],
                                      port=self.settings['REDIS_PORT'],
                                      db=self.settings['REDIS_DB'],
                                      decode_responses=True)
        try:
            self.redis_conn.info()
        except ConnectionError:
            print("Could not connect to Redis")
            # plugin is essential to functionality
            sys.exit(1)

        # clear out older test keys if any
        keys = self.redis_conn.keys("test-spider:*")
        for key in keys:
            self.redis_conn.delete(key)

        # set up kafka to consumer potential result
        self.consumer = KafkaConsumer(
            "demo_test.crawled_firehose",
            bootstrap_servers=self.settings['KAFKA_HOSTS'],
            group_id="demo-id",
            auto_commit_interval_ms=10,
            consumer_timeout_ms=5000,
            auto_offset_reset='earliest',
            value_deserializer=lambda m: m.decode('utf-8')
        )
        time.sleep(1)

    def test_crawler_process(self):
        runner = CrawlerRunner(self.settings)
        d = runner.crawl(CustomSpider)
        d.addBoth(lambda _: reactor.stop())
        # add crawl to redis
        key = "test-spider:istresearch.com:queue"
        self.redis_conn.zadd(key, self.example_feed, -99)

        # run the spider, give 20 seconds to see the url, crawl it,
        # and send to kafka. Then we kill the reactor
        def thread_func():
            time.sleep(20)
            reactor.stop()

        thread = threading.Thread(target=thread_func)
        thread.start()
        reactor.run()

        message_count = 0
        m = next(self.consumer)

        if m is None:
            pass
        else:
            the_dict = json.loads(m.value)
            if the_dict is not None and the_dict['appid'] == 'test' \
                    and the_dict['crawlid'] == 'abc12345':
                message_count += 1

        self.assertEqual(message_count, 1)

    def tearDown(self):
        keys = self.redis_conn.keys('stats:crawler:*:test-spider:*')
        keys = keys + self.redis_conn.keys('test-spider:*')
        for key in keys:
            self.redis_conn.delete(key)

        # if for some reason the tests fail, we end up falling behind on
        # the consumer
        for m in self.consumer:
            pass
        self.consumer.close()

if __name__ == '__main__':
    unittest.main()
