'''
Offline tests
'''
from builtins import range
from unittest import TestCase
from mock import MagicMock
from crawling.spiders.wandering_spider import WanderingSpider
from scrapy.http import HtmlResponse
from scrapy.http import Request
from crawling.items import RawResponseItem


class TestWanderingSpider(TestCase):

    def setUp(self):
        self.spider = WanderingSpider()
        self.spider._logger = MagicMock()
        self.spider.stats_dict = {}

    def get_meta(self):
        item = {}
        item['crawlid'] = "abc123"
        item['appid'] = "myapp"
        item['spiderid'] = "link"
        item["attrs"] = {}
        item["allowed_domains"] = ()
        item["allow_regex"] = ()
        item["deny_regex"] = ()
        item["deny_extensions"] = None
        item['curdepth'] = 0
        item["maxdepth"] = 1
        item["domain_max_pages"] = None
        item['priority'] = 0
        item['retry_times'] = 0
        item['expires'] = 0

        return item

    def evaluate(self, meta_object,
                text, expected_raw, expected_requests):
        request = Request(url='http://www.drudgereport.com',
                          meta=meta_object)
        response = HtmlResponse('drudge.url', body=text, request=request,
                                encoding='utf8')

        raw_item_count = 0
        request_count = 0

        for x in self.spider.parse(response):
            if isinstance(x, RawResponseItem):
                raw_item_count = raw_item_count + 1
            elif isinstance(x, Request):
                request_count = request_count + 1

        self.assertEqual(raw_item_count, expected_raw)
        self.assertEqual(request_count, expected_requests)

    def test_link_spider_parse(self):
        with open('tests/drudge.html', 'r') as file:
            text = file.read()

            curr_meta = self.get_meta()

            # should always yield one request
            for i in range(0, 100):
                self.evaluate(curr_meta, text, 1, 1)

            # link following tests ran via link spider
