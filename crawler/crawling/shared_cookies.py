import redis
import pickle

from scrapy.downloadermiddlewares.cookies import CookiesMiddleware


class SharedCookiesMiddleware(CookiesMiddleware):
    '''
    Shared Cookies Middleware to share same cookies between crawl Nodes.
    '''

    def __init__(self, debug=True, server=None):
        CookiesMiddleware.__init__(self, debug)
        self.redis_conn = server
        self.debug = debug

    @classmethod
    def from_crawler(cls, crawler):
        server = redis.Redis(host=crawler.settings.get('REDIS_HOST'),
                             port=crawler.settings.get('REDIS_PORT'),
                             db=crawler.settings.get('REDIS_DB'))
        return cls(crawler.settings.getbool('COOKIES_DEBUG'), server)

    def process_request(self, request, spider):
        if 'dont_merge_cookies' in request.meta:
            return
        cookiejarkey = "{spiderid}:sharedcookies:{crawlid}".format(
                        spiderid=request.meta.get("spiderid"),
                        crawlid=request.meta.get("crawlid"))

        jar = self.jars[cookiejarkey]
        jar.clear()
        if self.redis_conn.exists(cookiejarkey):
            data = self.redis_conn.get(cookiejarkey)
            jar = pickle.loads(data)

        cookies = self._get_request_cookies(jar, request)
        for cookie in cookies:
            jar.set_cookie_if_ok(cookie, request)

        # set Cookie header
        request.headers.pop('Cookie', None)
        jar.add_cookie_header(request)
        self._debug_cookie(request, spider)
        self.redis_conn.set(cookiejarkey, pickle.dumps(jar))

    def process_response(self, request, response, spider):
        if request.meta.get('dont_merge_cookies', False):
            return response
        cookiejarkey = "{spiderid}:sharedcookies:{crawlid}".format(
                        spiderid=request.meta.get("spiderid"),
                        crawlid=request.meta.get("crawlid"))
        # extract cookies from Set-Cookie and drop invalid/expired cookies

        jar = self.jars[cookiejarkey]
        jar.clear()

        if self.redis_conn.exists(cookiejarkey):
            data = self.redis_conn.get(cookiejarkey)
            jar = pickle.loads(data)

        jar.extract_cookies(response, request)
        self._debug_set_cookie(response, spider)
        self.redis_conn.set(cookiejarkey, pickle.dumps(jar))
        return response
