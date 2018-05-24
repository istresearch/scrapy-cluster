'''
Offline tests
'''
from unittest import TestCase
from mock import MagicMock
from crawling.redis_global_page_per_domain_filter import RFGlobalPagePerDomainFilter
from crawling.redis_domain_max_page_filter import RFDomainMaxPageFilter
from scrapy.http import Request


class TestRedisPagePerDomainFilter(TestCase):

    def setUp(self):
        self.global_limit = RFGlobalPagePerDomainFilter(MagicMock(), 'key', 5, 600)
        self.per_domain_limit = RFDomainMaxPageFilter(MagicMock(), 'key', 600)

    def test_global_page_per_domain_filter(self):
        req = Request('http://example.com')
        req.meta['crawlid'] = "abc123"

        self.global_limit.server.expire = MagicMock()

        # successfully added
        self.global_limit.server.incr = MagicMock(return_value=4)
        self.assertFalse(self.global_limit.request_page_limit_reached(req, None))

        # unsuccessfully added
        self.global_limit.server.incr = MagicMock(return_value=5)
        self.assertTrue(self.global_limit.request_page_limit_reached(req, None))

    def test_domain_max_page_filter(self):
        req = Request('http://example.com')
        req.meta['crawlid'] = "abc123"
        req.meta['domain_max_pages'] = 5

        self.per_domain_limit.server.expire = MagicMock()

        # successfully added
        self.per_domain_limit.server.incr = MagicMock(return_value=4)
        self.assertFalse(self.per_domain_limit.request_page_limit_reached(req, None))

        # unsuccessfully added
        self.per_domain_limit.server.incr = MagicMock(return_value=6)
        self.assertTrue(self.per_domain_limit.request_page_limit_reached(req, None))
