from scutils.log_factory import LogFactory
from scutils.stats_collector import StatsCollector
import socket
import time
import redis
import sys
from redis.exceptions import ConnectionError


class RedisStatsMiddleware(object):

    def __init__(self, settings):
        self.setup(settings)

    def setup(self, settings):
        '''
        Does the actual setup of the middleware
        '''
        # set up the default sc logger
        my_level = settings.get('SC_LOG_LEVEL', 'INFO')
        my_name = settings.get('SClogger_NAME', 'sc-logger')
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

        self.settings = settings
        self.stats_dict = {}

        # set up redis
        self.redis_conn = redis.Redis(host=settings.get('REDIS_HOST'),
                                      port=settings.get('REDIS_PORT'),
                                      db=settings.get('REDIS_DB'),
                                      password=settings.get('REDIS_PASSWORD'),
                                      decode_responses=True,
                                      socket_timeout=settings.get('REDIS_SOCKET_TIMEOUT'),
                                      socket_connect_timeout=settings.get('REDIS_SOCKET_TIMEOUT'))

        try:
            self.redis_conn.info()
            self.logger.debug("Connected to Redis in ScraperHandler")
        except ConnectionError:
            self.logger.error("Failed to connect to Redis in Stats Middleware")
            # plugin is essential to functionality
            sys.exit(1)

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler.settings)

    def _get_hostname(self):
        '''
        Gets the hostname of the machine the spider is running on

        @return: the hostname of the machine
        '''
        return socket.gethostname()

    def _setup_stats_status_codes(self, spider_name):
        '''
        Sets up the status code stats collectors
        '''
        self.stats_dict[spider_name] = {
            'status_codes': {}
        }
        self.stats_dict[spider_name]['status_codes'] = {}
        hostname = self._get_hostname()
        # we chose to handle 504's here as well as in the middleware
        # in case the middleware is disabled
        for status_code in self.settings['STATS_RESPONSE_CODES']:
            temp_key = 'stats:crawler:{h}:{n}:{s}'.format(
                h=hostname, n=spider_name, s=status_code)
            self.stats_dict[spider_name]['status_codes'][status_code] = {}
            for item in self.settings['STATS_TIMES']:
                try:
                    time = getattr(StatsCollector, item)

                    self.stats_dict[spider_name]['status_codes'][status_code][time] = StatsCollector \
                            .get_rolling_time_window(
                                    redis_conn=self.redis_conn,
                                    key='{k}:{t}'.format(k=temp_key, t=time),
                                    window=time,
                                    cycle_time=self.settings['STATS_CYCLE'])
                    self.logger.debug("Set up status code {s}, {n} spider,"\
                        " host {h} Stats Collector '{i}'"\
                        .format(h=hostname, n=spider_name, s=status_code, i=item))
                except AttributeError as e:
                    self.logger.warning("Unable to find Stats Time '{s}'"\
                            .format(s=item))
            total = StatsCollector.get_hll_counter(redis_conn=self.redis_conn,
                            key='{k}:lifetime'.format(k=temp_key),
                            cycle_time=self.settings['STATS_CYCLE'],
                            roll=False)
            self.logger.debug("Set up status code {s}, {n} spider,"\
                        "host {h} Stats Collector 'lifetime'"\
                            .format(h=hostname, n=spider_name, s=status_code))
            self.stats_dict[spider_name]['status_codes'][status_code]['lifetime'] = total

    def process_spider_input(self, response, spider):
        '''
        Ensures the meta data from the response is passed
        through in any Request's generated from the spider
        '''
        self.logger.debug("processing redis stats middleware")
        if self.settings['STATS_STATUS_CODES']:
            if spider.name not in self.stats_dict:
                self._setup_stats_status_codes(spider.name)

            if 'status_codes' in self.stats_dict[spider.name]:
                code = response.status
                if code in self.settings['STATS_RESPONSE_CODES']:
                    for key in self.stats_dict[spider.name]['status_codes'][code]:
                        try:
                            if key == 'lifetime':
                                unique = response.url + str(response.status)\
                                    + str(time.time())
                                self.stats_dict[spider.name]['status_codes'][code][key].increment(unique)
                            else:
                                self.stats_dict[spider.name]['status_codes'][code][key].increment()
                        except Exception as e:
                            self.logger.warn("Error in spider redis stats")
                    self.logger.debug("Incremented status_code '{c}' stats"\
                            .format(c=code))
