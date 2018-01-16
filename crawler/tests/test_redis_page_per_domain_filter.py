'''
Offline tests
'''
from unittest import TestCase
from mock import MagicMock
from crawling.redis_page_per_domain_filter import RFPagePerDomainFilter
from scrapy.http import Request


class TestRedisPagePerDomainFilter(TestCase):

    def setUp(self):
        self.limit = RFPagePerDomainFilter(MagicMock(), 'key', 5, 600)

    def test_page_per_domain_filter(self):
        req = Request('http://example.com')
        req.meta['crawlid'] = "abc123"

        self.limit.server.expire = MagicMock()

        # successfully added
        self.limit.server.incr = MagicMock(return_value=4)
        self.assertFalse(self.limit.request_page_limit_reached(req, None))

        # unsuccessfully added
        self.limit.server.incr = MagicMock(return_value=5)
        self.assertTrue(self.limit.request_page_limit_reached(req, None))
