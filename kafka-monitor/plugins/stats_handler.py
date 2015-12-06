from base_handler import BaseHandler
import redis
import sys
from redis.exceptions import ConnectionError


class StatsHandler(BaseHandler):

    schema = "stats_schema.json"

    def setup(self, settings):
        '''
        Setup redis and tldextract
        '''
        self.redis_conn = redis.Redis(host=settings['REDIS_HOST'],
                                      port=settings['REDIS_PORT'])

        try:
            self.redis_conn.info()
            self.logger.debug("Connected to Redis in StatsHandler")
        except ConnectionError:
            self.logger.error("Failed to connect to Redis in StatsHandler")
            # plugin is essential to functionality
            sys.exit(1)

    def handle(self, dict):
        '''
        Processes a vaild stats request

        @param dict: a valid dictionary object
        '''
        # format key
        key = "statsrequest:{stats}:{appid}".format(
                stats=dict['stats'],
                appid=dict['appid'])

        self.redis_conn.set(key, dict['uuid'])

        dict['parsed'] = True
        dict['valid'] = True
        self.logger.info('Added stat request to Redis', extra=dict)
