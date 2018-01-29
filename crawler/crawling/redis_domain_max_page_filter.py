# coding=utf-8
import tldextract
from scrapy.dupefilters import BaseDupeFilter
from scrapy.utils.reqser import request_to_dict


class RFDomainMaxPageFilter(BaseDupeFilter):
    '''
    Redis-based max page filter.
    This filter is applied per domain.
    Using this filter the maximum number of pages crawled
    for a particular domain is bounded.
    '''

    def __init__(self, server, key, timeout):
        '''
        Initialize page number filter

        @param server: the redis connection
        @param key: the key to store the fingerprints

        @param timeout: number of seconds a given key will remain once idle
        '''
        self.server = server
        # key_start equals: self.spider.name + ':domain_max_page_filter'
        self.key_start = key
        self.timeout = timeout
        # set up tldextract
        self.extract = tldextract.TLDExtract()

    def request_page_limit_reached(self, request, spider):
        # Collect items composing the redis key
        # grab the tld of the request
        req_dict = request_to_dict(request, spider)
        ex_res = self.extract(req_dict['url'])
        domain = "{d}.{s}".format(d=ex_res.domain, s=ex_res.suffix)

        # grab the crawl id
        crawl_id = req_dict['meta']['crawlid']

        # domain max page limit
        pagelimit = req_dict['meta']['domain_max_pages']

        # Compose the redis key
        composite_key = self.key_start + ':' + domain + ':' + crawl_id

        # Add new key if it doesn't exist
        if not self.server.exists(composite_key):
            self.server.set(composite_key, 0)

        # Stop incrementing the key when the limit is reached
        page_count = int(self.server.get(composite_key))
        if page_count >= pagelimit:
            # Prevent key expiration while the crawl continues by updating the expiration time
            self.server.expire(composite_key, self.timeout)
            return True

        # Increment key
        page_count = int(self.server.incr(composite_key))
        # Set key expiration
        self.server.expire(composite_key, self.timeout)

        return page_count >= pagelimit

    def close(self, reason):
        '''
        Delete data on close. Called by scrapy's scheduler
        '''
        self.clear()

    def clear(self):
        '''
        The page number per domain has a TTL so you shouldn't clear it
        '''
        pass
