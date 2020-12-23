from __future__ import absolute_import
from .base_handler import BaseHandler
import tldextract
import redis
import ujson
import sys
from redis.exceptions import ConnectionError


class ScraperHandler(BaseHandler):

    schema = "scraper_schema.json"

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
            self.logger.debug("Connected to Redis in ScraperHandler")
        except ConnectionError:
            self.logger.error("Failed to connect to Redis in ScraperHandler")
            # plugin is essential to functionality
            sys.exit(1)

    def handle(self, dict):
        '''
        Processes a vaild crawl request

        @param dict: a valid dictionary object
        '''
        # format key
        ex_res = self.extract(dict['url'])
        key = "{sid}:{dom}.{suf}:queue".format(
            sid=dict['spiderid'],
            dom=ex_res.domain,
            suf=ex_res.suffix)

        val = ujson.dumps(dict)

        # shortcut to shove stuff into the priority queue
        self.redis_conn.zadd(key, {val: -dict['priority']})

        # if timeout crawl, add value to redis
        if 'expires' in dict and dict['expires'] != 0:
            key = "timeout:{sid}:{appid}:{crawlid}".format(
                            sid=dict['spiderid'],
                            appid=dict['appid'],
                            crawlid=dict['crawlid'])
            self.redis_conn.set(key, dict['expires'])

        # log success
        dict['parsed'] = True
        dict['valid'] = True
        self.logger.info('Added crawl to Redis', extra=dict)
