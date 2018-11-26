from __future__ import print_function
import sys
import redis
import tldextract
import jsonpickle

from scrapy import Item
from scrapy.exceptions import NotConfigured
from redis.exceptions import ConnectionError
from scrapy.http.cookies import CookieJar
from scrapy.downloadermiddlewares.cookies import CookiesMiddleware

from scutils.log_factory import LogFactory


class DistributedCookiesMiddleware(CookiesMiddleware):
    '''
    This middleware enable working with cookies for requests having the same crawlid
    '''

    def __init__(self, settings):
        super(DistributedCookiesMiddleware, self).__init__()
        debug = settings.getbool('COOKIES_DEBUG')
        self.redis_conn = None
        self.logger = None
        self.cookiejar_keys = None
        self.distributed_cookies_timeout = None

        self.extract = tldextract.TLDExtract()
        self.debug = debug
        self.setup(settings)

    @classmethod
    def from_crawler(cls, crawler):
        if not crawler.settings.getbool('COOKIES_ENABLED'):
            raise NotConfigured
        return cls(crawler.settings)

    def setup(self, settings):
        '''
        Does the actual setup of the middleware
        '''

        # set up the default sc logger
        my_level = settings.get('SC_LOG_LEVEL', 'INFO')
        my_name = settings.get('SC_LOGGER_NAME', 'sc-logger')
        my_output = settings.get('SC_LOG_STDOUT', True)
        my_json = settings.get('SC_LOG_JSON', False)
        my_dir = settings.get('SC_LOG_DIR', 'logs')
        my_bytes = settings.get('SC_LOG_MAX_BYTES', '10MB')
        my_file = settings.get('SC_LOG_FILE', 'main.log')
        my_backups = settings.get('SC_LOG_BACKUPS', 5)

        self.distributed_cookies_timeout = settings.get('DISTRIBUTED_COOKIES_TIMEOUT', None)

        self.logger = LogFactory.get_instance(json=my_json, name=my_name, stdout=my_output, level=my_level, dir=my_dir,
                                              file=my_file, bytes=my_bytes, backups=my_backups)

        # set up redis
        self.redis_conn = redis.Redis(host=settings['REDIS_HOST'], port=settings['REDIS_PORT'], db=settings['REDIS_DB'])
        try:
            self.redis_conn.info()
        except ConnectionError:
            print("Could not connect to Redis")
            # plugin is essential to functionality
            sys.exit(1)

    def process_request(self, request, spider):
        if request.meta.get('dont_merge_cookies', False):
            return

        jar = self._get_cookiejar(request, spider)
        cookies = self._get_request_cookies(jar, request)
        for cookie in cookies:
            jar.set_cookie_if_ok(cookie, request)

        # set Cookie header
        request.headers.pop('Cookie', None)
        jar.add_cookie_header(request)
        self._update_cookiejar(request, jar, spider)
        self._debug_cookie(request, spider)

    def process_response(self, request, response, spider):
        if request.meta.get('dont_merge_cookies', False):
            return response

        # extract cookies from Set-Cookie and drop invalid/expired cookies
        jar = self._get_cookiejar(request, spider)
        jar.extract_cookies(response, request)
        self._update_cookiejar(request, jar, spider)
        self._debug_set_cookie(response, spider)

        return response

    def _get_cookiejar(self, request, spider):
        '''
        Retrieving crawler's cookiejar in Redis
        '''
        key = self._get_key(request, spider)
        self.cookiejar_keys = self.redis_conn.keys(key)
        if key not in self.cookiejar_keys:
            return CookieJar()

        encoded_cookiejar = self.redis_conn.get(key)

        # Loading and returning scrapy.http.cookies.CookieJar object from json
        return jsonpickle.loads(encoded_cookiejar)

    def _update_cookiejar(self, request, cookiejar, spider):
        '''
        Update crawler's cookiejar in Redis
        '''
        key = self._get_key(request, spider)
        encoded_cookiejar = jsonpickle.dumps(cookiejar)

        # Inserting the cookiejar in Redis with/without expiring time
        if self.distributed_cookies_timeout:
            self.redis_conn.psetex(key, self.distributed_cookies_timeout, encoded_cookiejar)
        else:
            self.redis_conn.set(key, encoded_cookiejar)

    def _get_key(self, request, spider):
        '''
        Redis key of current cookiejar crawler
        '''
        crawlid = request.meta['crawlid']
        ex_res = self.extract(request.url)
        domain = ex_res.domain
        suffix = ex_res.suffix
        key = "{sname}:{dom}.{suf}:{cid}:cookiejar".format(sname=spider.name, dom=domain, suf=suffix, cid=crawlid)
        return key


class ClearCookiesMiddleware(object):
    '''
    Clear the cookies of a crawl job on a yield item
    '''
    def __init__(self, settings):
        self.logger = None
        self.redis_conn = None
        self.extract = tldextract.TLDExtract()
        self.setup(settings)

    def setup(self, settings):
        '''
        Does the actual setup of the middleware
        '''

        # set up the default sc logger
        my_level = settings.get('SC_LOG_LEVEL', 'INFO')
        my_name = settings.get('SC_LOGGER_NAME', 'sc-logger')
        my_output = settings.get('SC_LOG_STDOUT', True)
        my_json = settings.get('SC_LOG_JSON', False)
        my_dir = settings.get('SC_LOG_DIR', 'logs')
        my_bytes = settings.get('SC_LOG_MAX_BYTES', '10MB')
        my_file = settings.get('SC_LOG_FILE', 'main.log')
        my_backups = settings.get('SC_LOG_BACKUPS', 5)

        self.logger = LogFactory.get_instance(json=my_json, name=my_name, stdout=my_output, level=my_level, dir=my_dir,
                                              file=my_file, bytes=my_bytes, backups=my_backups)

        # set up redis
        self.redis_conn = redis.Redis(host=settings['REDIS_HOST'], port=settings['REDIS_PORT'], db=settings['REDIS_DB'])
        try:
            self.redis_conn.info()
        except ConnectionError:
            print("Could not connect to Redis")
            # plugin is essential to functionality
            sys.exit(1)

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler.settings)

    def process_spider_output(self, response, result, spider):
        '''
        If an item is yield, its cookies are cleared
        '''
        self.logger.debug("processing clean cookies middleware")
        for x in result:
            # only operate on items
            if not isinstance(x, Item):
                self.logger.debug("found item")
                key = self._get_key(x, spider)
                self.logger.debug("found key : {}".format(key))

                # Delete the cookiejar of the current crawl which yield the final item
                self.redis_conn.delete(key)
                self.logger.debug("deleted key : {}".format(key))
            yield x

    def _get_key(self, item, spider):
        '''
        Redis key of current cookiejar crawler
        '''
        crawlid = item.get('crawlid')
        ex_res = self.extract(item.get('url'))
        domain = ex_res.domain
        suffix = ex_res.suffix
        key = "{sname}:{dom}.{suf}:{cid}:cookiejar".format(sname=spider.name, dom=domain, suf=suffix, cid=crawlid)
        return key
