from scrapy.dupefilters import BaseDupeFilter


class PagePerHostFilter(BaseDupeFilter):
    '''
    Redis-based request duplication filter
    '''
    def __init__(self, server, key, page_limit, timeout):
        '''
        Initialize duplication filter

        @param server: the redis connection
        @param key: the key to store the fingerprints
        @param timeout: number of seconds a given key will remain once idle
        '''
        self.server = server
        self.key = key
        self.page_limit = page_limit
        self.timeout = timeout

    def reached_page_limit(self, request):
        c_id = request.meta['crawlid']

        page_count = self.server.incr(self.key + ":" + c_id)
        self.server.expire(self.key + ":" + c_id, self.timeout)

        return page_count >= self.page_limit

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
