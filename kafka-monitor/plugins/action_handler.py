from __future__ import absolute_import
from .base_handler import BaseHandler
import tldextract
import redis
import sys
from redis.exceptions import ConnectionError


class ActionHandler(BaseHandler):

    schema = "action_schema.json"

    def setup(self, settings):
        '''
        Setup redis and tldextract
        '''
        self.extract = tldextract.TLDExtract()
        self.redis_conn = redis.Redis(host=settings['REDIS_HOST'],
                                      port=settings['REDIS_PORT'],
                                      db=settings.get('REDIS_DB'),
                                      password=settings['REDIS_PASSWORD'],
                                      decode_responses=True,
                                      socket_timeout=settings.get('REDIS_SOCKET_TIMEOUT'),
                                      socket_connect_timeout=settings.get('REDIS_SOCKET_TIMEOUT'))

        try:
            self.redis_conn.info()
            self.logger.debug("Connected to Redis in ActionHandler")
        except ConnectionError:
            self.logger.error("Failed to connect to Redis in ActionHandler")
            # plugin is essential to functionality
            sys.exit(1)

    def handle(self, dict):
        '''
        Processes a vaild action request

        @param dict: a valid dictionary object
        '''
        # format key
        key = "{action}:{spiderid}:{appid}".format(
                action=dict['action'],
                spiderid=dict['spiderid'],
                appid=dict['appid'])

        if "crawlid" in dict:
            key = key + ":" + dict['crawlid']

        self.redis_conn.set(key, dict['uuid'])

        dict['parsed'] = True
        dict['valid'] = True
        self.logger.info('Added action to Redis', extra=dict)
