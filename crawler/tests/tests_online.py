'''
Online link spider test
'''
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
from kafka import KafkaClient, SimpleConsumer


class CustomSpider(LinkSpider):
    '''
    Overridden link spider for testing
    '''
    name = "test-spider"


class TestLinkSpider(TestCase):

    example_feed = "\x80\x02}q\x00(X\x0f\x00\x00\x00allowed_domainsq\x01NX"\
        "\x0b\x00\x00\x00allow_regexq\x02NX\a\x00\x00\x00crawlidq\x03X\x19"\
        "\x00\x00\x0001234567890abcdefghijklmnq\x04X\x03\x00\x00\x00urlq\x05X"\
        "\x13\x00\x00\x00www.istresearch.comq\x06X\a\x00\x00\x00expiresq\aK"\
        "\x00X\b\x00\x00\x00priorityq\bK\x01X\n\x00\x00\x00deny_regexq\tNX\b"\
        "\x00\x00\x00spideridq\nX\x0b\x00\x00\x00test-spiderq\x0bX\x05\x00"\
        "\x00\x00attrsq\x0cNX\x05\x00\x00\x00appidq\rX\a\x00\x00\x00testappq"\
        "\x0eX\x06\x00\x00\x00cookieq\x0fNX\t\x00\x00\x00useragentq\x10NX\x0f"\
        "\x00\x00\x00deny_extensionsq\x11NX\b\x00\x00\x00maxdepthq\x12K\x00u."

    def setUp(self):
        self.settings = get_project_settings()
        self.settings.set('KAFKA_TOPIC_PREFIX', "demo_test")
        # set up redis
        self.redis_conn = redis.Redis(host=self.settings['REDIS_HOST'],
                                      port=self.settings['REDIS_PORT'])
        try:
            self.redis_conn.info()
        except ConnectionError:
            print "Could not connect to Redis"
            # plugin is essential to functionality
            sys.exit(1)

        # clear out older test keys if any
        keys = self.redis_conn.keys("test-spider:*")
        for key in keys:
            self.redis_conn.delete(key)

        # set up kafka to consumer potential result
        self.kafka_conn = KafkaClient(self.settings['KAFKA_HOSTS'])
        self.kafka_conn.ensure_topic_exists("demo_test.crawled_firehose")
        self.consumer = SimpleConsumer(
            self.kafka_conn,
            "demo-id",
            "demo_test.crawled_firehose",
            buffer_size=1024*100,
            fetch_size_bytes=1024*100,
            max_buffer_size=None
        )
        # move cursor to end of kafka topic
        self.consumer.seek(0, 2)

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

        # ensure it was sent out to kafka
        message_count = 0
        for message in self.consumer.get_messages():
            if message is None:
                break
            else:
                the_dict = json.loads(message.message.value)
                if the_dict is not None and the_dict['appid'] == 'testapp' \
                        and the_dict['crawlid'] == '01234567890abcdefghijklmn':
                    message_count += 1

        self.assertEquals(message_count, 1)

    def tearDown(self):
        keys = self.redis_conn.keys('stats:crawler:*:test-spider:*')
        keys = keys + self.redis_conn.keys('test-spider:*')
        for key in keys:
            self.redis_conn.delete(key)

if __name__ == '__main__':
    unittest.main()
