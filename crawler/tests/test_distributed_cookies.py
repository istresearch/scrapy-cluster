from unittest import TestCase
import mock
from mock import MagicMock
import tldextract
import jsonpickle
from crawling.distributed_cookies import DistributedCookiesMiddleware, ClearCookiesMiddleware
from scrapy.http import Request, Response
from scrapy.spiders import Spider
from scrapy import Item, Field


class TestDistributedCookiesMiddleware(TestCase):

    @mock.patch('crawling.distributed_cookies.DistributedCookiesMiddleware.setup')
    def setUp(self, s):
        self.dcm = DistributedCookiesMiddleware(MagicMock())
        self.dcm.debug = False
        self.dcm.logger = MagicMock()
        self.dcm.logger.debug = MagicMock()
        self.dcm.redis_conn = MagicMock()
        self.dcm.redis_conn.keys = MagicMock(return_value=[])
        self.dcm.redis_conn.get = MagicMock(return_value=None)
        self.dcm.redis_conn.psetex = MagicMock()
        self.dcm.redis_conn.set = MagicMock()
        self.dcm.distributed_cookies_timeout = None
        self.dcm.extract = tldextract.TLDExtract()

    @mock.patch('crawling.distributed_cookies.DistributedCookiesMiddleware._update_cookiejar')
    def _update_cookiejar(self, request, cookiejar, spider):
        encoded_cookiejar = jsonpickle.dumps(cookiejar)
        self.dcm.redis_conn.keys = MagicMock(return_value=[self.dcm._get_key(request, spider)])
        self.dcm.redis_conn.get = MagicMock(return_value=encoded_cookiejar)
        self.dcm._update_cookiejar(request, cookiejar, spider)

    def test_dcm_middleware(self):
        spider = Spider('foo')
        request = Request('http://istresearch.com')
        request.meta['crawlid'] = 'abc123'
        assert self.dcm.process_request(request, spider) is None
        assert 'Cookie' not in request.headers

        self.dcm.distributed_cookies_timeout = 1000  # for testing all the lines in _update_cookiejar

        headers = {'Set-Cookie': 'C1=value1; path=/'}
        response = Response('http://istresearch.com', headers=headers)
        assert self.dcm.process_response(request, response, spider) is response

        request2 = Request('http://istresearch.com/sub1/')
        request2.meta['crawlid'] = 'abc123'
        assert self.dcm.process_request(request2, spider) is None
        # self.assertEqual(request2.headers.get('Cookie'), 'C1=value1')


class TestClearCookiesMiddleware(TestCase):
    @mock.patch('crawling.distributed_cookies.ClearCookiesMiddleware.setup')
    def setUp(self, s):
        self.ccm = ClearCookiesMiddleware(MagicMock())
        self.ccm.logger = MagicMock()
        self.ccm.logger.debug = MagicMock()
        self.ccm.extract = tldextract.TLDExtract()
        self.ccm.redis_conn = MagicMock()
        self.ccm.redis_conn.keys = MagicMock(return_value=['foo:istresearch.com:abc123:cookiejar'])
        self.ccm.redis_conn.delete = MagicMock()

    def test_ccm_middleware(self):
        class TestItem(Item):
            crawlid = Field()
            url = Field()

        spider = Spider('foo')
        response = MagicMock()

        a = TestItem()
        a['crawlid'] = 'abc123'
        a['url'] = 'http://istresearch.com'

        test_list = [
            {},
            a,
            Request('http://istresearch.com')
        ]
        yield_count = 0
        for item in self.ccm.process_spider_output(response, test_list, spider):
            if isinstance(item, Item):
                self.assertEquals(a.get('crawlid'), item.get('crawlid'))
                self.assertEquals(a.get('url'), item.get('url'))
            yield_count += 1
        self.assertEquals(yield_count, 3)
