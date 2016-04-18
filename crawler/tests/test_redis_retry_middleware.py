'''
Offline tests
'''
from unittest import TestCase
from mock import MagicMock
from crawling.redis_retry_middleware import RedisRetryMiddleware
from scrapy.http import Request


class TestRedisRetryMiddleware(TestCase):

    def setUp(self):
        self.retry = RedisRetryMiddleware(MagicMock())
        self.retry.max_retry_times = 1

    def test_retries(self):
        req = Request('http://example.com')
        req.meta['retry_times'] = 0
        req.meta['priority'] = 70

        # number of retries less than max
        out = self.retry._retry(req, 'stuff', MagicMock())
        self.assertEqual(req.url, out.url)
        self.assertEqual(60, out.meta['priority'])

        # over max
        self.assertEqual(self.retry._retry(out, 'stuff', MagicMock()), None)
