'''
Offline tests
'''
from unittest import TestCase
import mock
from mock import MagicMock
from crawling.distributed_scheduler import DistributedScheduler
from scrapy.http import Request
from scutils.redis_throttled_queue import RedisThrottledQueue


class ThrottleMixin(object):

    @mock.patch('crawling.distributed_scheduler.DistributedScheduler' \
                '.update_ipaddress')
    @mock.patch('crawling.distributed_scheduler.DistributedScheduler' \
                '.setup_zookeeper')
    def setUp(self, u, z):
        self.scheduler = DistributedScheduler(MagicMock(), False, 60, 10, 3,
                                              MagicMock(), 10, 60, False, 60,
                                              False, False, '.*')
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
        self.scheduler.dupefilter.request_seen = MagicMock(return_value=True)
        self.assertEquals(self.scheduler.enqueue_request(self.req), None)

        # test request not expiring and queue seen
        self.scheduler.queue_keys = ['link:ex.com:queue']
        self.extract = MagicMock(return_value={"domain": 'ex', "suffix": 'com'})
        self.scheduler.is_blacklisted = MagicMock(return_value=False)
        self.scheduler.dupefilter.request_seen = MagicMock(return_value=False)
        self.scheduler.queue_dict['link:ex.com:queue'] = MagicMock()
        self.scheduler.queue_dict['link:ex.com:queue'].push = MagicMock(
                                                    side_effect=KeyError("1"))
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
        self.scheduler.queue_dict = {"ex.com": MagicMock()}
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
        self.scheduler.create_queues = MagicMock(side_effect=KeyError("q"))
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
                                        return_value={"url": "http://ex.com",
                                                      "crawlid": "abc123",
                                                      "appid": "myapp",
                                                      "spiderid": "link"})
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

        self.scheduler.load_domain_config = MagicMock(side_effect=Exception("1"))
        self.scheduler.error_config = MagicMock(side_effect=Exception("2"))
        self.scheduler.create_queues = MagicMock(side_effect=Exception("3"))

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


class TestDistributedSchedulerLoadDomainConfig(ThrottleMixin, TestCase):

    def test_load_domain_config(self):
        good_yaml_dict = {
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
        self.scheduler.queue_dict = {'link:ex1.com:queue': q}

        self.scheduler.update_domain_queues()
        self.assertEqual(self.scheduler.queue_dict['link:ex1.com:queue'].window, 50)
        self.assertEqual(self.scheduler.queue_dict['link:ex1.com:queue'].limit, 10)

        # test with scale factor
        self.scheduler.domain_config = {
            "ex2.com": {
                "window": 50,
                "hits": 10,
                "scale": 0.5
            }
        }
        q = RedisThrottledQueue(MagicMock(), MagicMock(), 100, 100)
        self.scheduler.queue_dict = {'link:ex2.com:queue': q}

        self.scheduler.update_domain_queues()
        self.assertEqual(self.scheduler.queue_dict['link:ex2.com:queue'].window, 50)
        # the scale factor effects the limit only
        self.assertEqual(self.scheduler.queue_dict['link:ex2.com:queue'].limit, 5)


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
        self.scheduler.queue_dict = {'link:ex1.com:queue': q}

        self.scheduler.error_config('stuff')

        self.assertEqual(self.scheduler.queue_dict['link:ex1.com:queue'].window, 7)
        self.assertEqual(self.scheduler.queue_dict['link:ex1.com:queue'].limit, 5)
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
            self.assertTrue(self.scheduler.queue_dict[key].window_key
                            in expected)

        # test type
        self.scheduler.add_type = True
        self.scheduler.queue_dict = {}
        expected = ['link:ex1:throttle_window',
                    'link:ex2:throttle_window',
                    'link:ex3:throttle_window']
        self.scheduler.create_queues()
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
        self.scheduler.create_queues()
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
        self.scheduler.create_queues()
        for key in self.scheduler.queue_dict:
            self.assertTrue(self.scheduler.queue_dict[key].window_key
                            in expected)


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
