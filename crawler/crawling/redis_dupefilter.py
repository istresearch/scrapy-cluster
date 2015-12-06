from scrapy.dupefilters import BaseDupeFilter
from scrapy.utils.request import request_fingerprint


class RFPDupeFilter(BaseDupeFilter):
    '''
    Redis-based request duplication filter
    '''

    def __init__(self, server, key, timeout):
        '''
        Initialize duplication filter

        @param server: the redis connection
        @param key: the key to store the fingerprints
        @param timeout: number of seconds a given key will remain once idle
        '''
        self.server = server
        self.key = key
        self.timeout = timeout

    def request_seen(self, request):
        fp = request_fingerprint(request)
        c_id = request.meta['crawlid']

        added = self.server.sadd(self.key + ":" + c_id, fp)
        self.server.expire(self.key + ":" + c_id, self.timeout)

        return not added

    def close(self, reason):
        '''
        Delete data on close. Called by scrapy's scheduler
        '''
        self.clear()

    def clear(self):
        '''
        Clears fingerprints data
        '''
        self.server.delete(self.key)
