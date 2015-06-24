from scrapy.utils.misc import load_object
from scrapy.http import Request
from scrapy.conf import settings

import redis
import json
import random
import time
import urllib
import re

from redis_dupefilter import RFPDupeFilter
from redis_queue import RedisPriorityQueue

try:
    import cPickle as pickle
except ImportError:
    import pickle

class DistributedScheduler(object):
    '''
    Scrapy request scheduler that utilizes Priority Queues
    to moderate scrape requests within a distributed scrapy
    cluster
    '''
    redis_conn = None # the redis connection
    queue = None # the queue to use for crawling
    spider = None # the spider using this scheduler
    queue_class = None # the class to use for the queue
    dupefilter = None # the redis dupefilter
    item_retries = 0 # the number of extra tries to get an item

    def __init__(self, server, persist, timeout, retries):
        '''
        Initialize the scheduler
        '''
        self.redis_conn = server
        self.persist = persist
        self.rfp_timeout = timeout
        self.item_retires = retries

    def setup(self):
        '''
        Used to initialize things when using mock
        spider.name is not set yet
        '''
        self.queue = RedisPriorityQueue(self.redis_conn,
                                        self.spider.name + ":queue")

    @classmethod
    def from_settings(cls, settings):
        server = redis.Redis(host=settings.get('REDIS_HOST'),
                                            port=settings.get('REDIS_PORT'))
        persist = settings.get('SCHEDULER_PERSIST', True)
        timeout = settings.get('DUPEFILTER_TIMEOUT', 600)
        retries = settings.get('SCHEDULER_ITEM_RETRIES', 3)

        return cls(server, persist, timeout, retries)

    @classmethod
    def from_crawler(cls, crawler):
        return cls.from_settings(crawler.settings)

    def open(self, spider):
        self.spider = spider
        self.setup()
        self.dupefilter = RFPDupeFilter(self.redis_conn,
                            self.spider.name + ':dupefilter', self.rfp_timeout)

    def close(self, reason):
        if not self.persist:
            self.dupefilter.clear()
            self.queue.clear()

    def is_blacklisted(self, appid, crawlid):
        '''
        Checks the redis blacklist for crawls that should not be propagated
        either from expiring or stopped
        @return: True if the appid crawlid combo is blacklisted
        '''
        key_check = '{appid}||{crawlid}'.format(appid=appid,
                                                crawlid=crawlid)
        redis_key = self.spider.name + ":blacklist"
        return self.redis_conn.sismember(redis_key, key_check)

    def enqueue_request(self, request):
        '''
        Pushes a request from the spider back into the queue
        '''
        if not request.dont_filter and self.dupefilter.request_seen(request):
            return
        req_dict = self.request_to_dict(request)

        if not self.is_blacklisted(req_dict['meta']['appid'],
                                    req_dict['meta']['crawlid']):
            key = "{sid}:queue".format(sid=req_dict['meta']['spiderid'])
            curr_time = time.time()

            # insert if crawl never expires (0) or time < expires
            if req_dict['meta']['expires'] == 0 or \
                    curr_time < req_dict['meta']['expires']:
                self.queue.push(req_dict, req_dict['meta']['priority'])

    def request_to_dict(self, request):
        '''
        Convert Request object to a dict.
        modified from scrapy.utils.reqser
        '''
        req_dict = {
            # urls should be safe (safe_string_url)
            'url': request.url.decode('ascii'),
            'method': request.method,
            'headers': dict(request.headers),
            'body': request.body,
            'cookies': request.cookies,
            'meta': request.meta,
            '_encoding': request._encoding,
            'priority': request.priority,
            'dont_filter': request.dont_filter,
             # callback/errback are assumed to be a bound instance of the spider
            'callback': None if request.callback is None else request.callback.func_name,
            'errback': None if request.errback is None else request.errback.func_name,
        }
        return req_dict

    def find_item(self):
        '''
        Finds an item from the queue
        '''
        count = 0

        while count <= self.item_retries:
            item = self.queue.pop()
            if item:
                # very basic limiter
                time.sleep(1)
                return item
            # we want the spiders to get slightly out of sync
            # with each other for better performance
            time.sleep(random.random())
            count = count + 1

        return None

    def next_request(self):
        '''
        Logic to handle getting a new url request
        '''
        t = time.time()

        item = self.find_item()
        if item:
            try:
                req = Request(item['url'])
            except ValueError:
                # need absolute url
                # need better url validation here
                req = Request('http://' + item['url'])

            if 'meta' in item:
                item = item['meta']

            # defaults
            if "attrs" not in item:
                item["attrs"] = {}
            if "allowed_domains" not in item:
                item["allowed_domains"] = ()
            if "allow_regex" not in item:
                item["allow_regex"] = ()
            if "deny_regex" not in item:
                item["deny_regex"] = ()
            if "deny_extensions" not in item:
                item["deny_extensions"] = None
            if 'curdepth' not in item:
                item['curdepth'] = 0
            if "maxdepth" not in item:
                item["maxdepth"] = 0
            if "priority" not in item:
                item['priority'] = 0
            if "retry_times" not in item:
                item['retry_times'] = 0
            if "expires" not in item:
                item['expires'] = 0

            for key in ('attrs', 'allowed_domains', 'curdepth', 'maxdepth',
                    'appid', 'crawlid', 'spiderid', 'priority', 'retry_times',
                    'expires', 'allow_regex', 'deny_regex', 'deny_extensions'):
                req.meta[key] = item[key]

            return req

        return None

    def has_pending_requests(self):
        '''
        We never want to say we have pending requests
        If this returns True scrapy sometimes hangs.
        '''
        return False
