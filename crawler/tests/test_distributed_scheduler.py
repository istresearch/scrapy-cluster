'''
Offline tests
'''
from builtins import object
from unittest import TestCase
import mock
from mock import MagicMock
from crawling.distributed_scheduler import DistributedScheduler
from scrapy.http import Request
from scrapy.utils.reqser import request_to_dict
from scutils.redis_throttled_queue import RedisThrottledQueue


class ThrottleMixin(object):

    @mock.patch('crawling.distributed_scheduler.DistributedScheduler' \
                '.update_ipaddress')
    @mock.patch('crawling.distributed_scheduler.DistributedScheduler' \
                '.setup_zookeeper')
    def setUp(self, u, z):
        self.scheduler = DistributedScheduler(MagicMock(), False, 60, 10, 3,
                                              MagicMock(), 10, 60, False, 60,
                                              False, False, '.*', True, 3600,
                                              None, 600, 600)
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
        req.meta["domain_max_pages"] = None
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
        self.scheduler.dupefilter.request_seen = MagicMock(return_value=True)
        self.assertEqual(self.scheduler.enqueue_request(self.req), None)

        # test global page limit reached
        self.scheduler.global_page_per_domain_filter = MagicMock(return_value=True)
        self.assertEqual(self.scheduler.enqueue_request(self.req), None)

        # test per domain page limit reached
        self.scheduler.domain_max_page_filter = MagicMock(return_value=True)
        self.assertEqual(self.scheduler.enqueue_request(self.req), None)

        # test request not expiring and queue seen
        self.scheduler.queue_keys = ['link:ex.com:queue']
        self.extract = MagicMock(return_value={"domain": 'ex', "suffix": 'com'})
        self.scheduler.is_blacklisted = MagicMock(return_value=False)
        self.scheduler.dupefilter.request_seen = MagicMock(return_value=False)
        self.scheduler.global_page_per_domain_filter.request_page_limit_reached = MagicMock(return_value=False)
        self.scheduler.domain_max_page_filter.request_page_limit_reached = MagicMock(return_value=False)
        self.scheduler.queue_dict['link:ex.com:queue'] = [MagicMock(), 0]
        self.scheduler.queue_dict['link:ex.com:queue'][0].push = MagicMock(
                                                    side_effect=Exception("1"))
        try:
            self.scheduler.enqueue_request(self.req)
            # this should not be reached
            self.assertFalse(True)
        except Exception as e:
            self.assertEqual(str(e), "1")

        # test request not expiring and queue not seen
        self.scheduler.redis_conn.zadd = MagicMock(side_effect=Exception("2"))
        self.scheduler.queue_keys = []
        try:
            self.scheduler.enqueue_request(self.req)
            # this should not be reached
            self.assertFalse(True)
        except Exception as e:
            self.assertEqual(str(e), "2")

        # test whole domain blacklisted, but we allow it
        self.scheduler.black_domains = ['ex.com']
        try:
            self.scheduler.enqueue_request(self.req)
            # this should not be reached
            self.assertFalse(True)
        except Exception as e:
            self.assertEqual(str(e), "2")

        # test dont allow blacklist domains back into the queue
        self.scheduler.backlog_blacklist = False
        self.scheduler.enqueue_request(self.req)

        # test allow domain back into queue since not blacklisted
        self.scheduler.black_domains = ['ex2.com']
        self.scheduler.backlog_blacklist = False
        try:
            self.scheduler.enqueue_request(self.req)
            self.assertFalse(True)
        except Exception as e:
            self.assertEqual(str(e), "2")
        # reset
        self.scheduler.black_domains = []
        self.scheduler.backlog_blacklist = True

        # test request expired
        self.req.meta['expires'] = 1
        self.assertEqual(self.scheduler.enqueue_request(self.req), None)

        # test request blacklisted via stop or expire from redis-monitor
        self.scheduler.is_blacklisted = MagicMock(return_value=True)
        self.assertEqual(self.scheduler.enqueue_request(self.req), None)


class TestDistributedSchedulerFindItem(ThrottleMixin, TestCase):

    def test_find_item(self):
        # test finding an item
        self.scheduler.queue_keys = ["link:ex.com:queue"]
        self.scheduler.queue_dict = {"link:ex.com:queue": [MagicMock(), 0]}
        self.scheduler.queue_dict["link:ex.com:queue"][0].pop = MagicMock(return_value='item')
        self.assertEqual(self.scheduler.find_item(), 'item')

        # test failed to find an item
        self.scheduler.queue_dict["link:ex.com:queue"][0].pop = MagicMock(return_value=None)
        self.assertEqual(self.scheduler.find_item(), None)

        # test skip due to blacklist
        self.scheduler.black_domains = ['ex.com']
        self.scheduler.queue_dict["link:ex.com:queue"][0].pop = MagicMock(side_effect=Exception("bad"))
        self.assertEqual(self.scheduler.find_item(), None) # should also not raise exception


class TestDistributedSchedulerRequestFromFeed(ThrottleMixin, TestCase):
    def test_request_from_feed(self):
        self.req = self.get_request()
        feed = {
            "url": "http://ex.com",
            "crawlid": "abc123",
            "appid": "myapp",
            "spiderid": "link",
        }
        out = self.scheduler.request_from_feed(feed)
        self.assertEqual(out.url, 'http://ex.com')
        for key in out.meta:
            self.assertEqual(out.meta[key], self.req.meta[key])


class TestDistributedSchedulerNextRequest(ThrottleMixin, TestCase):

    @mock.patch('time.time', return_value=5)
    def test_next_request(self, t):
        self.req = self.get_request()

        # test update queues
        self.scheduler.update_time = 1
        self.scheduler.update_interval = 2
        self.scheduler.create_queues = MagicMock(side_effect=Exception("q"))
        try:
            self.scheduler.next_request()
            # this should not be reached
            self.assertFalse(True)
        except Exception as e:
            print("str", e, e == "q", e == "'q'", e == 'q')
            self.assertEqual(str(e), "q")

        # test update ip address
        self.scheduler.update_time = 4
        self.scheduler.update_ipaddress = MagicMock(side_effect=Exception("ip"))
        self.scheduler.update_ip_time = 1
        self.scheduler.ip_update_interval = 2
        try:
            self.scheduler.next_request()
            # this should not be reached
            self.assertFalse(True)
        except Exception as e:
            self.assertEqual(str(e), "ip")

        # test request from feed
        feed = {
            "url": "http://ex.com",
            "crawlid": "abc123",
            "appid": "myapp",
            "spiderid": "link",
        }
        self.scheduler.find_item = MagicMock(return_value=feed)
        out = self.scheduler.next_request()
        self.assertEqual(out.url, 'http://ex.com')
        for key in out.meta:
            self.assertEqual(out.meta[key], self.req.meta[key])

        # test request from feed with cookies
        feed = {
            "url": "http://ex.com",
            "crawlid": "abc123",
            "appid": "myapp",
            "spiderid": "link",
            "cookie": "authenticated=true;privacy=10"
        }
        self.req.meta['cookie'] = "authenticated=true;privacy=10"  # add cookie to req since we are not testing this
        self.scheduler.find_item = MagicMock(return_value=feed)
        out = self.scheduler.next_request()
        self.assertEqual(out.url, 'http://ex.com')
        for key in out.meta:
            self.assertEqual(out.meta[key], self.req.meta[key])
        self.assertEqual(out.cookies, self.scheduler.parse_cookie(feed["cookie"]))
        self.req.meta['cookie'] = None  # reset

        # test request from serialized request
        exist_req = Request('http://ex.com')
        exist_req.meta["crawlid"] = "abc123"
        exist_req.meta["appid"] = "myapp"
        exist_req.meta["spiderid"] = "link"
        exist_item = request_to_dict(exist_req)
        self.scheduler.find_item = MagicMock(return_value=exist_item)
        out = self.scheduler.next_request()
        self.assertEqual(out.url, 'http://ex.com')
        for key in out.meta:
            self.assertEqual(out.meta[key], exist_req.meta[key])

        # test request from serialized request with supplied cookie
        exist_req = Request('http://ex.com', cookies={'auth':'101'})
        exist_item = request_to_dict(exist_req)
        self.scheduler.find_item = MagicMock(return_value=exist_item)
        out = self.scheduler.next_request()
        self.assertEqual(out.url, 'http://ex.com')
        for key in out.meta:
            self.assertEqual(out.meta[key], exist_req.meta[key])
        self.assertEqual(out.cookies, exist_req.cookies)
        self.req.meta['cookie'] = None  # reset

        # test request from serialized request with meta cookie
        exist_req = Request('http://ex.com')
        exist_req.meta["crawlid"] = "abc123"
        exist_req.meta["appid"] = "myapp"
        exist_req.meta["spiderid"] = "link"
        exist_req.meta["cookie"] = {'authenticated': False, 'privacy':9}
        exist_item = request_to_dict(exist_req)
        self.scheduler.find_item = MagicMock(return_value=exist_item)
        out = self.scheduler.next_request()
        self.assertEqual(out.url, 'http://ex.com')
        for key in out.meta:
            self.assertEqual(out.meta[key], exist_req.meta[key])
        self.assertEqual(out.cookies, exist_req.meta['cookie'])

        # test didn't get item
        self.scheduler.find_item = MagicMock(return_value=None)
        self.assertEqual(self.scheduler.next_request(), None)


class TestDistributedSchedulerChangeConfig(ThrottleMixin, TestCase):

    def test_change_config(self):
        good_string = ""\
          "domains:\n"\
          "  dmoztools.net:\n"\
          "      window: 60\n"\
          "      hits: 60\n"\
          "      scale: 1.0\n"\
          "  wikipedia.org:\n"\
          "      window: 60\n"\
          "      hits: 30"
        bad_string1 = "blahrg\ndumb"
        bad_string2 = None
        bad_string3 = ""

        self.scheduler.load_domain_config = MagicMock(side_effect=Exception("1"))
        self.scheduler.error_config = MagicMock(side_effect=Exception("2"))
        self.scheduler.create_queues = MagicMock(side_effect=Exception("3"))

        try:
            self.scheduler.change_config(good_string)
            self.assertFalse(True)
        except Exception as e:
            self.assertEqual(str(e), "1")

        try:
            self.scheduler.change_config(bad_string1)
            self.assertFalse(True)
        except Exception as e:
            self.assertEqual(str(e), "1")

        try:
            self.scheduler.change_config(bad_string2)
            self.assertFalse(True)
        except Exception as e:
            self.assertEqual(str(e), "2")

        try:
            self.scheduler.change_config(bad_string3)
            self.assertFalse(True)
        except Exception as e:
            self.assertEqual(str(e), "2")


class TestDistributedSchedulerLoadDomainConfig(ThrottleMixin, TestCase):

    def test_load_domain_config(self):
        good_yaml_dict = {
            "blacklist": ["blah.com"],
            "domains": {
                "ex1.com": {
                    "window": 60,
                    "hits": 10,
                    "scale": 1
                },
                "ex2.com": {
                    "window": 60,
                    "hits": 10
                }
            }
        }
        bad_yaml_dict1 = {
            "blarg": ['stuff']
        }
        bad_yaml_dict2 = {
            "domains": {
                "stuff.com": {
                    "window": 60
                },
                "stuff2.com": {
                    "hits": 10
                }
            }
        }
        result_yaml = {}
        result_yaml['ex1.com'] = good_yaml_dict['domains']['ex1.com']
        result_yaml['ex2.com'] = good_yaml_dict['domains']['ex2.com']

        # correctly loaded
        self.scheduler.load_domain_config(good_yaml_dict)
        self.assertEqual(self.scheduler.domain_config, result_yaml)
        self.assertEqual(self.scheduler.black_domains, ["blah.com"])

        # both are not correct yaml setups
        self.scheduler.load_domain_config(bad_yaml_dict1)
        self.assertEqual(self.scheduler.domain_config, {})

        self.scheduler.load_domain_config(bad_yaml_dict2)
        self.assertEqual(self.scheduler.domain_config, {})


class TestDistributedSchedulerUpdateDomainQueues(ThrottleMixin, TestCase):

    def test_update_domain_queues(self):
        # test without scale factor
        self.scheduler.domain_config = {
            "ex1.com": {
                "window": 50,
                "hits": 10,
                "scale": 1
            }
        }
        q = RedisThrottledQueue(MagicMock(), MagicMock(), 100, 100)
        self.scheduler.queue_dict = {'link:ex1.com:queue': [q, 0]}

        self.scheduler.update_domain_queues()
        self.assertEqual(self.scheduler.queue_dict['link:ex1.com:queue'][0].window, 50)
        self.assertEqual(self.scheduler.queue_dict['link:ex1.com:queue'][0].limit, 10)

        # test with scale factor
        self.scheduler.domain_config = {
            "ex2.com": {
                "window": 50,
                "hits": 10,
                "scale": 0.5
            }
        }
        q = RedisThrottledQueue(MagicMock(), MagicMock(), 100, 100)
        self.scheduler.queue_dict = {'link:ex2.com:queue': [q, 0]}

        self.scheduler.update_domain_queues()
        self.assertEqual(self.scheduler.queue_dict['link:ex2.com:queue'][0].window, 50)
        # the scale factor effects the limit only
        self.assertEqual(self.scheduler.queue_dict['link:ex2.com:queue'][0].limit, 5)


class TestDistributedSchedulerErrorConfig(ThrottleMixin, TestCase):

    def test_error_config(self):
        self.scheduler.domain_config = {
            "ex1.com": {
                "window": 50,
                "hits": 10
            }
        }
        self.scheduler.window = 7
        self.scheduler.hits = 5
        q = RedisThrottledQueue(MagicMock(), MagicMock(), 100, 100)
        self.scheduler.queue_dict = {'link:ex1.com:queue': [q, 0]}

        self.scheduler.error_config('stuff')

        self.assertEqual(self.scheduler.queue_dict['link:ex1.com:queue'][0].window, 7)
        self.assertEqual(self.scheduler.queue_dict['link:ex1.com:queue'][0].limit, 5)
        self.assertEqual(self.scheduler.domain_config, {})


class TestDistributedSchedulerFitScale(ThrottleMixin, TestCase):

    def test_fit_scale(self):
        # assert max
        self.assertEqual(self.scheduler.fit_scale(1.1), 1.0)

        # assert min
        self.assertEqual(self.scheduler.fit_scale(-1.9), 0.0)

        # assert normal
        self.assertEqual(self.scheduler.fit_scale(0.51), 0.51)


class TestDistributedSchedulerCreateQueues(ThrottleMixin, TestCase):

    def test_create_queues(self):
        queues = ['link:ex1:queue', 'link:ex2:queue', 'link:ex3:queue']
        self.scheduler.redis_conn.keys = MagicMock(return_value=queues)

        # test basic
        self.scheduler.create_queues()
        expected = ['ex1:throttle_window',
                    'ex2:throttle_window',
                    'ex3:throttle_window']
        for key in self.scheduler.queue_dict:
            self.assertTrue(self.scheduler.queue_dict[key][0].window_key
                            in expected)

        # test type
        self.scheduler.add_type = True
        self.scheduler.queue_dict = {}
        expected = ['link:ex1:throttle_window',
                    'link:ex2:throttle_window',
                    'link:ex3:throttle_window']
        self.scheduler.create_queues()
        for key in self.scheduler.queue_dict:
            self.assertTrue(self.scheduler.queue_dict[key][0].window_key
                            in expected)

        # test ip
        self.scheduler.add_ip = True
        self.scheduler.add_type = False
        self.scheduler.queue_dict = {}
        expected = ['ip:ex1:throttle_window',
                    'ip:ex2:throttle_window',
                    'ip:ex3:throttle_window']
        self.scheduler.create_queues()
        for key in self.scheduler.queue_dict:
            self.assertTrue(self.scheduler.queue_dict[key][0].window_key
                            in expected)

        # test type and ip
        self.scheduler.add_ip = True
        self.scheduler.add_type = True
        self.scheduler.queue_dict = {}
        expected = ['link:ip:ex1:throttle_window',
                    'link:ip:ex2:throttle_window',
                    'link:ip:ex3:throttle_window']
        self.scheduler.create_queues()
        for key in self.scheduler.queue_dict:
            self.assertTrue(self.scheduler.queue_dict[key][0].window_key
                            in expected)


class TestDistributedSchedulerExpireQueues(ThrottleMixin, TestCase):

    @mock.patch('time.time', return_value=5)
    def test_expire_queues(self, t):
        self.scheduler.queue_dict = {'key1':[MagicMock(), 3]}
        self.scheduler.queue_keys = []

        # assert not expired
        self.scheduler.queue_timeout = 3
        self.scheduler.expire_queues()
        self.assertTrue('key1' in self.scheduler.queue_dict)

        # assert expired
        self.scheduler.queue_timeout = 1
        self.scheduler.expire_queues()
        self.assertTrue('key1' not in self.scheduler.queue_dict.keys())

        # assert remove from queue_keys also
        self.scheduler.queue_dict = {'key1':[MagicMock(), 3]}
        self.scheduler.queue_keys = ['key1']
        self.scheduler.expire_queues()
        self.assertTrue('key1' not in self.scheduler.queue_dict.keys())
        self.assertTrue('key1' not in self.scheduler.queue_keys)


class TestDistributedSchedulerParseCookie(ThrottleMixin, TestCase):

    def test_parse_cookie(self):
        cookie = "blah=stuff; expires=Thu, 18 May 2017 12:42:29 GMT; path"\
        "=/; Domain=.domain.com"
        result = {
            "blah": "stuff",
            "expires": "Thu, 18 May 2017 12:42:29 GMT",
            "path": "/",
            "Domain": ".domain.com",
        }

        self.assertEqual(result, self.scheduler.parse_cookie(cookie))
