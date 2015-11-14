from scrapy import signals
from scrapy.exceptions import DontCloseSpider
from scrapy.spiders import Spider

from scutils.stats_collector import StatsCollector
import socket
import time

class RedisSpider(Spider):
    '''
    Base Spider for doing distributed crawls coordinated through Redis
    '''

    def _set_crawler(self, crawler):
        super(RedisSpider, self)._set_crawler(crawler)
        self.crawler.signals.connect(self.spider_idle,
                                     signal=signals.spider_idle)

    def spider_idle(self):
        raise DontCloseSpider

    def parse(self, response):
        '''
        Parse a page of html, and yield items into the item pipeline

        @param response: The response object of the scrape
        '''
        raise NotImplementedError("Please implement parse() for your spider")

    def set_logger(self, logger):
        '''
        Set the logger for the spider, different than the default Scrapy one

        @param logger: the logger from the scheduler
        '''
        self._logger = logger

    def set_redis(self, redis_conn):
        '''
        Set the redis connection for the spider

        @param redis_conn: the redis connection from the scheduler
        '''
        self.redis_conn = redis_conn

    def setup_stats(self):
        '''
        Sets up the stats collection for the spider. Inserted into the Spider
        instead of the pipelines so that other spiders can collect stat data
        too.
        '''
        # stats setup
        self.stats_dict = {}

        if self.settings['STATS_STATUS_CODES']:
            self._setup_stats_status_codes()

    def _get_hostname(self):
        '''
        Gets the hostname of the machine the spider is running on

        @return: the hostname of the machine
        '''
        return socket.gethostname()

    def _setup_stats_status_codes(self):
        '''
        Sets up the status code stats collectors
        '''
        self.stats_dict['status_codes'] = {}
        hostname = self._get_hostname()
        # we chose to handle 504's here as well as in the middleware
        # in case the middleware is disabled
        for status_code in self.settings['STATS_RESPONSE_CODES']:
            temp_key = 'stats:crawler:{h}:{n}:{s}'.format(
                h=hostname, n=self.name, s=status_code)
            self.stats_dict['status_codes'][status_code] = {}
            for item in self.settings['STATS_TIMES']:
                try:
                    time = getattr(StatsCollector, item)

                    self.stats_dict['status_codes'][status_code][time] = StatsCollector \
                            .get_rolling_time_window(
                                    redis_conn=self.redis_conn,
                                    key='{k}:{t}'.format(k=temp_key, t=time),
                                    window=time,
                                    cycle_time=self.settings['STATS_CYCLE'])
                    self._logger.debug("Set up status code {s}, {n} spider,"\
                        " host {h} Stats Collector '{i}'"\
                        .format(h=hostname, n=self.name, s=status_code, i=item))
                except AttributeError as e:
                    self._logger.warning("Unable to find Stats Time '{s}'"\
                            .format(s=item))
            total = StatsCollector.get_hll_counter(redis_conn=self.redis_conn,
                            key='{k}:lifetime'.format(k=temp_key),
                            cycle_time=self.settings['STATS_CYCLE'],
                            roll=False)
            self._logger.debug("Set up status code {s}, {n} spider,"\
                        "host {h} Stats Collector 'lifetime'"\
                            .format(h=hostname, n=self.name, s=status_code))
            self.stats_dict['status_codes'][status_code]['lifetime'] = total

    def _increment_status_code_stat(self, response):
        '''
        Increments the total stat counters

        @param response: The scrapy response in the spider
        '''
        if 'status_codes' in self.stats_dict:
            code = response.status
            if code in self.settings['STATS_RESPONSE_CODES']:
                for key in self.stats_dict['status_codes'][code]:
                    try:
                        if key == 'lifetime':
                            unique = response.url + str(response.status)\
                                + str(time.time())
                            self.stats_dict['status_codes'][code][key].increment(unique)
                        else:
                            self.stats_dict['status_codes'][code][key].increment()
                    except Exception as e:
                        self._logger.warn("Error in spider redis stats")
                self._logger.debug("Incremented status_code '{c}' stats"\
                        .format(c=code))

    def reconstruct_headers(self, response):
        """
        Purpose of this method is to reconstruct the headers dictionary that
        is normally passed in with a "response" object from scrapy.

        Args:
            response: A scrapy response object

        Returns: A dictionary that mirrors the "response.headers" dictionary
        that is normally within a response object

        Raises: None
        Reason: Originally, there was a bug where the json.dumps() did not
        properly serialize the headers. This is method is way to circumvent
        the known issue
        """

        header_dict = {}
        # begin reconstructing headers from scratch...
        for key in response.headers.keys():
            key_item_list = []
            key_list = response.headers.getlist(key)
            for item in key_list:
                key_item_list.append(item)
            header_dict[key] = key_item_list
        return header_dict
