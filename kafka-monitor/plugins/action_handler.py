from __future__ import absolute_import
from .base_handler import BaseHandler
import tldextract
import redis
import sys
from redis.exceptions import ConnectionError


class ActionHandler(BaseHandler):

    schema = "action_schema.json"

    def setup(self, settings):
        """
        Setup redis and tldextract
        """
        self.extract = tldextract.TLDExtract()
        self.redis_conn = redis.Redis(host=settings['REDIS_HOST'],
                                      port=settings['REDIS_PORT'],
                                      db=settings.get('REDIS_DB'))

        try:
            self.redis_conn.info()
            self.logger.debug("Connected to Redis in ActionHandler")
        except ConnectionError:
            self.logger.error("Failed to connect to Redis in ActionHandler")
            # plugin is essential to functionality
            sys.exit(1)

    def handle(self, item):
        """
        Processes a valid action request

        @param item: a valid dictionary object
        """
        # format key
        key = "{action}:{spiderid}:{appid}".format(
                action=item['action'],
                spiderid=item['spiderid'],
                appid=item['appid'])

        if "crawlid" in item:
            key = key + ":" + item['crawlid']

        self.redis_conn.set(key, item['uuid'])

        item['parsed'] = True
        item['valid'] = True
        self.logger.info('Added action to Redis', extra=item)
