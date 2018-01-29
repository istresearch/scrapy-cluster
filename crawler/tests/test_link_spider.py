'''
Offline tests
'''
from unittest import TestCase
from mock import MagicMock
from crawling.spiders.link_spider import LinkSpider
from scrapy.http import HtmlResponse
from scrapy.http import Request
from crawling.items import RawResponseItem


class TestLinkSpider(TestCase):

    def setUp(self):
        self.spider = LinkSpider()
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
            text = str(file.read())

            curr_meta = self.get_meta()

            # test too deep
            curr_meta['maxdepth'] = 1
            curr_meta['curdepth'] = 1
            self.evaluate(curr_meta, text, 1, 0)

            # test raw depth recursion
            curr_meta['curdepth'] = 0
            self.evaluate(curr_meta, text, 1, 391)

            # test allowed_domains filter
            curr_meta['allowed_domains'] = ['foxnews.com']
            self.evaluate(curr_meta, text, 1, 4)

            # test allow regex filter
            curr_meta['allowed_domains'] = ()
            curr_meta['allow_regex'] = ['.*shock.*']
            self.evaluate(curr_meta, text, 1, 1)

            # test deny regex filter
            curr_meta['allow_regex'] = ()
            curr_meta['deny_regex'] = ['.*.com.*']
            self.evaluate(curr_meta, text, 1, 43)

            # test deny_extensions filter
            curr_meta['deny_regex'] = ()
            # no pages that end in .html
            curr_meta['deny_extensions'] = ['html']
            self.evaluate(curr_meta, text, 1, 329)
