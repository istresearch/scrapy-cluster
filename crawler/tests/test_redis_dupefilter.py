'''
Offline tests
'''
from unittest import TestCase
from mock import MagicMock
from crawling.redis_dupefilter import RFPDupeFilter
from scrapy.http import Request


class TestRedisDupefilter(TestCase):

    def setUp(self):
        self.dupe = RFPDupeFilter(MagicMock(), 'key', 1)

    def test_dupe_filter(self):
        req = Request('http://example.com')
        req.meta['crawlid'] = "abc123"

        self.dupe.server.expire = MagicMock()

        # successfully added
        self.dupe.server.sadd = MagicMock(return_value=1)
        self.assertFalse(self.dupe.request_seen(req))

        # unsuccessfully added
        self.dupe.server.sadd = MagicMock(return_value=0)
        self.assertTrue(self.dupe.request_seen(req))
