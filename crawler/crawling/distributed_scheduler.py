from scrapy.utils.misc import load_object
from scrapy.http import Request
from scrapy.conf import settings

import redis
import json
import random
import time
import tldextract
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
    to moderate different domain scrape requests within a distributed scrapy
    cluster
    '''
    redis_conn = None # the redis connection
    queue_dict = None # the dict of throttled queues
    spider = None # the spider using this scheduler
    queue_keys = None # the list of current queues
    queue_class = None # the class to use for the queue
    dupefilter = None # the redis dupefilter
    update_time = 0 # the last time the queues were updated
    update_interval = 0 # how often to update the queues
    extract = None # the tld extractor
    item_retries = 0 # the number of extra tries to get an item

    def __init__(self, server, persist, update_int, timeout, retries):
        '''
        Initialize the scheduler
        '''
        self.redis_conn = server
        self.persist = persist
        self.queue_dict = {}
        self.update_interval = update_int
        self.rfp_timeout = timeout
        self.item_retires = retries

        # set up tldextract
        self.extract = tldextract.TLDExtract()

    def update_queues(self):
        '''
        Updates the in memory list of the redis queues
        Creates new queue instances if it does not have them
        '''
        self.queue_keys = self.redis_conn.keys(self.spider.name + ":*:queue")

        for key in self.queue_keys:
            if key not in self.queue_dict:
                self.queue_dict[key] = RedisPriorityQueue(self.redis_conn, key)

    @classmethod
    def from_settings(cls, settings):
        server = redis.Redis(host=settings.get('REDIS_HOST'),
                                            port=settings.get('REDIS_PORT'))
        persist = settings.get('SCHEDULER_PERSIST', True)
        up_int = settings.get('SCHEDULER_QUEUE_REFRESH', 10)
        timeout = settings.get('DUPEFILTER_TIMEOUT', 600)
        retries = settings.get('SCHEDULER_ITEM_RETRIES', 3)

        return cls(server, persist, up_int, timeout, retries)

    @classmethod
    def from_crawler(cls, crawler):
        return cls.from_settings(crawler.settings)

    def open(self, spider):
        self.spider = spider
        self.update_queues()
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
        Pushes a request from the spider into the proper queue
        '''
        if not request.dont_filter and self.dupefilter.request_seen(request):
            return
        req_dict = self.request_to_dict(request)

        if not self.is_blacklisted(req_dict['meta']['appid'],
                                    req_dict['meta']['crawlid']):
            # grab the tld of the request
            ex_res = self.extract(req_dict['url'])
            key = "{sid}:{dom}.{suf}:queue".format(
                sid=req_dict['meta']['spiderid'],
                dom=ex_res.domain,
                suf=ex_res.suffix)

            curr_time = time.time()

            # insert if crawl never expires (0) or time < expires
            if req_dict['meta']['expires'] == 0 or \
                    curr_time < req_dict['meta']['expires']:
                # we may already have the queue in memory
                if key in self.queue_keys:
                    self.queue_dict[key].push(req_dict,
                                            req_dict['meta']['priority'])
                else:
                    # shoving into a new redis queue, negative b/c of sorted sets
                    # this will populate ourself and other schedulers when
                    # they call update_queues
                    self.redis_conn.zadd(key, pickle.dumps(req_dict, protocol=-1),
                                        -req_dict['meta']['priority'])

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
        Finds an item from the queues
        '''
        random.shuffle(self.queue_keys)
        count = 0

        while count <= self.item_retries:
            for key in self.queue_keys:
                # the throttled queue only returns an item if it is allowed
                item = self.queue_dict[key].pop()

                if item:
                    return item
            # we want the spiders to get slightly out of sync
            # with each other for better performance
            time.sleep(random.random())
            count = count + 1

        return None

    def next_request(self):
        '''
        Logic to handle getting a new url request, from a bunch of
        different queues
        '''
        t = time.time()
        # update the redis queues every so often
        if t - self.update_time > self.update_interval:
            self.update_time = t
            self.update_queues()

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
            if "useragent" not in item:
                item['useragent'] = None
            if "cookie" not in item:
                item['cookie'] = None

            for key in ('attrs', 'allowed_domains', 'curdepth', 'maxdepth',
                    'appid', 'crawlid', 'spiderid', 'priority', 'retry_times',
                    'expires', 'allow_regex', 'deny_regex', 'deny_extensions',
                    'useragent', 'cookie'):
                req.meta[key] = item[key]

            # extra check to add items to request
            if item['useragent'] is not None:
                req.headers['User-Agent'] = item['useragent']
            if item['cookie'] is not None:
                if isinstance(item['cookie'], dict):
                    req.cookies = item['cookie']
                elif isinstance(item['cookie'], basestring):
                    req.cookies = self.parse_cookie(item['cookie'])

            return req

        return None

    def parse_cookie(self, string):
        '''
        Parses a cookie string like returned in a Set-Cookie header
        @param string: The cookie string
        @return: the cookie dict
        '''
        results = re.findall('([^=]+)=([^\;]+);?\s?', string)
        my_dict = {}
        for item in results:
            my_dict[item[0]] = item[1]

        return my_dict

    def has_pending_requests(self):
        '''
        We never want to say we have pending requests
        If this returns True scrapy sometimes hangs.
        '''
        return False
