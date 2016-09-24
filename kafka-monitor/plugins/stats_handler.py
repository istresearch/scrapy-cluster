from __future__ import absolute_import
from .base_handler import BaseHandler
import redis
import sys
from redis.exceptions import ConnectionError


class StatsHandler(BaseHandler):

    schema = "stats_schema.json"

    def setup(self, settings):
        """
        Setup redis and tldextract
        """
        self.redis_conn = redis.Redis(host=settings['REDIS_HOST'],
                                      port=settings['REDIS_PORT'],
                                      db=settings.get('REDIS_DB'))

        try:
            self.redis_conn.info()
            self.logger.debug("Connected to Redis in StatsHandler")
        except ConnectionError:
            self.logger.error("Failed to connect to Redis in StatsHandler")
            # plugin is essential to functionality
            sys.exit(1)

    def handle(self, item):
        """
        Processes a valid stats request

        @param item: a valid dictionary object
        """
        # format key
        key = "statsrequest:{stats}:{appid}".format(
                stats=item['stats'],
                appid=item['appid'])

        self.redis_conn.set(key, item['uuid'])

        item['parsed'] = True
        item['valid'] = True
        self.logger.info('Added stat request to Redis', extra=item)
