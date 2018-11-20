from builtins import str
from builtins import object
import logging
import redis
import socket
import time
import sys
from scrapy.utils.response import response_status_message

from scrapy.xlib.tx import ResponseFailed
from twisted.internet import defer
from twisted.internet.error import TimeoutError, DNSLookupError, \
        ConnectionRefusedError, ConnectionDone, ConnectError, \
        ConnectionLost, TCPTimedOutError
from redis.exceptions import ConnectionError

from scutils.stats_collector import StatsCollector
from scutils.log_factory import LogFactory


class LogRetryMiddleware(object):

    EXCEPTIONS_TO_RETRY = (defer.TimeoutError, TimeoutError, DNSLookupError,
                           ConnectionRefusedError, ConnectionDone, ConnectError,
                           ConnectionLost, TCPTimedOutError, ResponseFailed,
                           IOError)

    def __init__(self, settings):
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

        self.logger = LogFactory.get_instance(json=my_json,
                                         name=my_name,
                                         stdout=my_output,
                                         level=my_level,
                                         dir=my_dir,
                                         file=my_file,
                                         bytes=my_bytes,
                                         backups=my_backups)

        self.retry_http_codes = set(int(x) for x in
                                    settings.getlist('RETRY_HTTP_CODES'))

        # stats setup
        self.stats_dict = {}
        self.settings = settings
        self.name = self.settings['SPIDER_NAME']
        if self.settings['STATS_STATUS_CODES']:
            self.redis_conn = redis.Redis(host=self.settings.get('REDIS_HOST'),
                                          port=self.settings.get('REDIS_PORT'),
                                          db=settings.get('REDIS_DB'),
                                          password=self.settings.get('REDIS_PASSWORD'),
                                          decode_responses=True,
                                          socket_timeout=self.settings.get('REDIS_SOCKET_TIMEOUT'),
                                          socket_connect_timeout=self.settings.get('REDIS_SOCKET_TIMEOUT'))

            try:
                self.redis_conn.info()
                self.logger.debug("Connected to Redis in LogRetryMiddleware")
            except ConnectionError:
                self.logger.error("Failed to connect to Redis in LogRetryMiddleware")
                # plugin is essential to functionality
                sys.exit(1)

            self._setup_stats_status_codes()

    @classmethod
    def from_settings(cls, settings):
        return cls(settings)

    @classmethod
    def from_crawler(cls, crawler):
        # hack to update passed in settings
        crawler.settings.frozen = False
        crawler.settings.set('SPIDER_NAME', crawler.spider.name)
        return cls.from_settings(crawler.settings)

    def process_exception(self, request, exception, spider):
        if isinstance(exception, self.EXCEPTIONS_TO_RETRY):
            self._log_retry(request, exception, spider)
            self._increment_504_stat(request)

    def _log_retry(self, request, exception, spider):
        extras = {}
        extras['logger'] = self.logger.name
        extras['error_request'] = request
        extras['error_reason'] = exception
        extras['retry_count'] = request.meta.get('retry_times', 0)
        extras['status_code'] = 504
        extras['appid'] = request.meta['appid']
        extras['crawlid'] = request.meta['crawlid']
        extras['url'] = request.url

        self.logger.error('Scraper Retry', extra=extras)

    def _setup_stats_status_codes(self):
        '''
        Sets up the status code stats collectors
        '''
        hostname = self._get_hostname()
        # we chose to handle 504's here as well as in the middleware
        # in case the middleware is disabled
        self.logger.debug("Setting up log retry middleware stats")
        status_code = 504
        temp_key = 'stats:crawler:{h}:{n}:{s}'.format(
            h=hostname, n=self.name, s=status_code)
        for item in self.settings['STATS_TIMES']:
            try:
                time = getattr(StatsCollector, item)

                self.stats_dict[time] = StatsCollector \
                        .get_rolling_time_window(
                                redis_conn=self.redis_conn,
                                key='{k}:{t}'.format(k=temp_key, t=time),
                                window=time,
                                cycle_time=self.settings['STATS_CYCLE'])
                self.logger.debug("Set up LRM status code {s}, {n} spider,"\
                    " host {h} Stats Collector '{i}'"\
                    .format(h=hostname, n=self.name, s=status_code, i=item))
            except AttributeError as e:
                self.logger.warning("Unable to find Stats Time '{s}'"\
                        .format(s=item))
        total = StatsCollector.get_hll_counter(redis_conn=self.redis_conn,
                        key='{k}:lifetime'.format(k=temp_key),
                        cycle_time=self.settings['STATS_CYCLE'],
                        roll=False)
        self.logger.debug("Set up status code {s}, {n} spider,"\
                    "host {h} Stats Collector 'lifetime'"\
                        .format(h=hostname, n=self.name, s=status_code))
        self.stats_dict['lifetime'] = total

    def _get_hostname(self):
        '''
        Gets the hostname of the machine the spider is running on

        @return: the hostname of the machine
        '''
        return socket.gethostname()

    def _increment_504_stat(self, request):
        '''
        Increments the 504 stat counters

        @param request: The scrapy request in the spider
        '''
        for key in self.stats_dict:
            if key == 'lifetime':
                unique = request.url + str(time.time())
                self.stats_dict[key].increment(unique)
            else:
                self.stats_dict[key].increment()
        self.logger.debug("Incremented status_code '504' stats")
