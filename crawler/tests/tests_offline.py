'''
Offline tests
'''

import unittest
from unittest import TestCase
import mock
from mock import MagicMock

import sys
from os import path
sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))

from crawling.redis_dupefilter import RFPDupeFilter
from crawling.redis_retry_middleware import RedisRetryMiddleware
from crawling.distributed_scheduler import DistributedScheduler
from crawling.spiders.link_spider import LinkSpider

from scrapy.http import HtmlResponse
from scrapy.http import Request
from crawling.items import RawResponseItem

import Queue
import time

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

class ThrottleMixin(object):

    @mock.patch('crawling.distributed_scheduler.DistributedScheduler' \
                '.update_ipaddress')
    @mock.patch('crawling.distributed_scheduler.DistributedScheduler' \
                '.setup_zookeeper')
    def setUp(self, u, z):
        self.scheduler = DistributedScheduler(MagicMock(), False, 60, 10, 3,
            MagicMock(), 10, 60, False, 60, False, False)
        self.scheduler.open(MagicMock())
        self.scheduler.my_ip = 'ip'
        self.scheduler.spider.name = 'link'
        self.req = None

    def get_request(self):
        req = None

        # required
        req = Request('http://ex.com')
        req.meta['crawlid'] = "abc123"
        req.meta['appid'] = "myapp"

        req.meta['url'] = "http://ex.com"
        req.meta['spiderid'] = "link"
        req.meta["attrs"] = None
        req.meta["allowed_domains"] = None
        req.meta["allow_regex"] = None
        req.meta["deny_regex"] = None
        req.meta["deny_extensions"] = None
        req.meta['curdepth'] = 0
        req.meta["maxdepth"] = 0
        req.meta['priority'] = 0
        req.meta['retry_times'] = 0
        req.meta['expires'] = 0
        req.meta['useragent'] = None
        req.meta['cookie'] = None

        return req

class TestDistributedSchedulerEnqueueRequest(ThrottleMixin, TestCase):

    @mock.patch('time.time', return_value=5)
    def test_enqueue_request(self, t):
        self.req = self.get_request()

        # test request already seen
        self.scheduler.dupefilter.request_seen = MagicMock(return_value = True)
        self.assertEquals(self.scheduler.enqueue_request(self.req), None)

        # test request not expiring and queue seen
        self.scheduler.queue_keys = ['link:ex.com:queue']
        self.extract = MagicMock(return_value={"domain":'ex', "suffix":'com'})
        self.scheduler.is_blacklisted = MagicMock(return_value=False)
        self.scheduler.dupefilter.request_seen = MagicMock(return_value = False)
        self.scheduler.queue_dict['link:ex.com:queue'] = MagicMock()
        self.scheduler.queue_dict['link:ex.com:queue'].push = \
                                            MagicMock(side_effect=KeyError("1"))
        try:
            self.scheduler.enqueue_request(self.req)
            # this should not be reached
            self.assertFalse(True)
        except KeyError as error:
            self.assertEqual(error.message, "1")

        # test request not expiring and queue not seen
        self.scheduler.redis_conn.zadd = MagicMock(side_effect=KeyError("2"))
        self.scheduler.queue_keys = []
        try:
            self.scheduler.enqueue_request(self.req)
            # this should not be reached
            self.assertFalse(True)
        except KeyError as error:
            self.assertEqual(error.message, "2")

        # test request expired
        self.req.meta['expires'] = 1
        self.assertEqual(self.scheduler.enqueue_request(self.req), None)

        # test request blacklisted via stop or expire from redis-monitor
        self.scheduler.is_blacklisted = MagicMock(return_value=True)
        self.assertEqual(self.scheduler.enqueue_request(self.req), None)

class TestDistributedSchedulerFindItem(ThrottleMixin, TestCase):

    def test_find_item(self):
        # test finding an item
        self.scheduler.queue_keys = ["ex.com"]
        self.scheduler.queue_dict = {"ex.com":MagicMock()}
        self.scheduler.queue_dict["ex.com"].pop = MagicMock(return_value='item')
        self.assertEqual(self.scheduler.find_item(), 'item')

        # test failed to find an item
        self.scheduler.queue_dict["ex.com"].pop = MagicMock(return_value=None)
        self.assertEqual(self.scheduler.find_item(), None)

class TestDistributedSchedulerNextRequest(ThrottleMixin, TestCase):

    @mock.patch('time.time', return_value=5)
    def test_next_request(self, t):
        self.req = self.get_request()

        # test update queues
        self.scheduler.update_time = 1
        self.scheduler.update_interval = 2
        self.scheduler.update_queues = MagicMock(side_effect=KeyError("q"))
        try:
            self.scheduler.next_request()
            # this should not be reached
            self.assertFalse(True)
        except KeyError as error:
            self.assertEqual(error.message, "q")

        # test update ip address
        self.scheduler.update_time = 4
        self.scheduler.update_ipaddress = MagicMock(side_effect=KeyError("ip"))
        self.scheduler.update_ip_time = 1
        self.scheduler.ip_update_interval = 2
        try:
            self.scheduler.next_request()
            # this should not be reached
            self.assertFalse(True)
        except KeyError as error:
            self.assertEqual(error.message, "ip")

        # test got item
        self.scheduler.find_item = MagicMock(
                                        return_value={"url":"http://ex.com",
                                                    "crawlid":"abc123",
                                                    "appid":"myapp",
                                                    "spiderid":"link"})
        out = self.scheduler.next_request()
        self.assertEquals(out.url, 'http://ex.com')
        for key in out.meta:
            self.assertEqual(out.meta[key], self.req.meta[key])

        # test didn't get item
        self.scheduler.find_item = MagicMock(return_value=None)
        self.assertEquals(self.scheduler.next_request(), None)

class TestDistributedSchedulerChangeConfig(ThrottleMixin, TestCase):

    def test_change_config(self):
        good_string = ""\
          "domains:\n"\
          "  dmoz.org:\n"\
          "      window: 60\n"\
          "      hits: 60\n"\
          "      scale: 1.0\n"\
          "  wikipedia.org:\n"\
          "      window: 60\n"\
          "      hits: 30"
        bad_string1 = "blahrg\ndumb"
        bad_string2 = None
        bad_string3 = ""

        self.scheduler.setup_domains = MagicMock(side_effect=Exception("1"))
        self.scheduler.error_config = MagicMock(side_effect=Exception("2"))
        self.scheduler.update_queues = MagicMock(side_effect=Exception("3"))

        try:
            self.scheduler.change_config(good_string)
            self.assertFalse(True)
        except Exception as error:
            self.assertEqual(error.message, "1")

        try:
            self.scheduler.change_config(bad_string1)
            self.assertFalse(True)
        except Exception as error:
            self.assertEqual(error.message, "1")

        try:
            self.scheduler.change_config(bad_string2)
            self.assertFalse(True)
        except Exception as error:
            self.assertEqual(error.message, "2")

        try:
            self.scheduler.change_config(bad_string3)
            self.assertFalse(True)
        except Exception as error:
            self.assertEqual(error.message, "2")

class TestDistributedSchedulerSetupDomains(ThrottleMixin, TestCase):

    def test_setup_domains(self):
        self.fail('No test')
        pass

class TestDistributedSchedulerErrorConfig(ThrottleMixin, TestCase):

    def test_error_config(self):
        self.fail('No test')
        pass

class TestDistributedSchedulerFitScale(ThrottleMixin, TestCase):

    def test_fit_scale(self):
        self.fail('No test')
        pass

class TestDistributedSchedulerUpdateQueues(ThrottleMixin, TestCase):

    def test_update_queues(self):
        queues = ['link:ex1:queue', 'link:ex2:queue', 'link:ex3:queue']
        self.scheduler.redis_conn.keys = MagicMock(return_value=queues)

        # test basic
        self.scheduler.update_queues()
        expected = ['ex1:throttle_window',
                    'ex2:throttle_window',
                    'ex3:throttle_window']
        for key in self.scheduler.queue_dict:
            self.assertTrue(self.scheduler.queue_dict[key].window_key
                            in expected)

        # test type
        self.scheduler.add_type = True
        self.scheduler.queue_dict = {}
        expected = ['link:ex1:throttle_window',
                    'link:ex2:throttle_window',
                    'link:ex3:throttle_window']
        self.scheduler.update_queues()
        for key in self.scheduler.queue_dict:
            self.assertTrue(self.scheduler.queue_dict[key].window_key
                            in expected)

        # test ip
        self.scheduler.add_ip = True
        self.scheduler.add_type = False
        self.scheduler.queue_dict = {}
        expected = ['ip:ex1:throttle_window',
                    'ip:ex2:throttle_window',
                    'ip:ex3:throttle_window']
        self.scheduler.update_queues()
        for key in self.scheduler.queue_dict:
            self.assertTrue(self.scheduler.queue_dict[key].window_key
                            in expected)

        # test type and ip
        self.scheduler.add_ip = True
        self.scheduler.add_type = True
        self.scheduler.queue_dict = {}
        expected = ['link:ip:ex1:throttle_window',
                    'link:ip:ex2:throttle_window',
                    'link:ip:ex3:throttle_window']
        self.scheduler.update_queues()
        for key in self.scheduler.queue_dict:
            self.assertTrue(self.scheduler.queue_dict[key].window_key
                            in expected)

class TestDistributedSchedulerParseCookie(ThrottleMixin, TestCase):

    def test_parse_cookie(self):
        cookie = "blah=stuff; expires=Thu, 18 May 2017 12:42:29 GMT; path"\
        "=/; Domain=.domain.com"
        result = {
            "blah":"stuff",
            "expires":"Thu, 18 May 2017 12:42:29 GMT",
            "path":"/",
            "Domain":".domain.com",
        }

        self.assertEqual(result, self.scheduler.parse_cookie(cookie))

class TestLinkSpider(TestCase):

    def setUp(self):
        self.spider = LinkSpider()
        self.spider._logger = MagicMock()

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
        item['priority'] = 0
        item['retry_times'] = 0
        item['expires'] = 0

        return item

    def do_test(self, meta_object,
                            text, expected_raw, expected_requests):
        request = Request(url='http://www.drudgereport.com',
                        meta=meta_object)
        response = HtmlResponse('drudge.url', body=text, request=request)

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

            # test too deep
            curr_meta['maxdepth'] = 1
            curr_meta['curdepth'] = 1
            self.do_test(curr_meta, text, 1, 0)

            # test raw depth recursion
            curr_meta['curdepth'] = 0
            self.do_test(curr_meta, text, 1, 391)

            # test allowed_domains filter
            curr_meta['allowed_domains'] = ['foxnews.com']
            self.do_test(curr_meta, text, 1, 4)

            # test allow regex filter
            curr_meta['allowed_domains'] = ()
            curr_meta['allow_regex'] = ['.*shock.*']
            self.do_test(curr_meta, text, 1, 1)

            # test deny regex filter
            curr_meta['allow_regex'] = ()
            curr_meta['deny_regex'] = ['.*.com.*']
            self.do_test(curr_meta, text, 1, 43)

            # test deny_extensions filter
            curr_meta['deny_regex'] = ()
            # no pages that end in .html
            curr_meta['deny_extensions'] = ['html']
            self.do_test(curr_meta, text, 1, 329)

if __name__ == '__main__':
    unittest.main()
