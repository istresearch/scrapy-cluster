from unittest import TestCase
import mock
from mock import MagicMock
from crawling.meta_passthrough_middleware import MetaPassthroughMiddleware
from scrapy.http import Request
from scrapy import Item

class TestMetaPassthroughMiddleware(TestCase):

    @mock.patch('crawling.meta_passthrough_middleware' \
                '.MetaPassthroughMiddleware.setup')
    def setUp(self, s):
        self.mpm = MetaPassthroughMiddleware(MagicMock())
        self.mpm.logger = MagicMock()
        self.mpm.logger.debug = MagicMock()

    def test_mpm_middleware(self):
        # create fake response
        a = MagicMock()
        a.meta = {
            'key1': 'value1',
            'key2': 'value2'
        }

        yield_count = 0
        # test all types of results from a spider
        # dicts, items, or requests
        test_list = [
            {},
            Item(),
            Request('http://istresearch.com')
        ]

        for item in self.mpm.process_spider_output(a, test_list, MagicMock()):
            if isinstance(item, Request):
                self.assertEqual(a.meta, item.meta)
            yield_count += 1

        self.assertEqual(yield_count, 3)

        # 1 debug for the method, 1 debug for the request
        self.assertEqual(self.mpm.logger.debug.call_count, 2)

        # test meta unchanged if already exists
        r = Request('http://aol.com')
        r.meta['key1'] = 'othervalue'

        for item in self.mpm.process_spider_output(a, [r], MagicMock()):
            # key1 value1 did not pass through, since it was already set
            self.assertEqual(item.meta['key1'], 'othervalue')
            # key2 was not set, therefor it passed through
            self.assertEqual(item.meta['key2'], 'value2')
