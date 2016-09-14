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
        """
        Setup redis and tldextract
        """
        self.extract = tldextract.TLDExtract()
        self.redis_conn = redis.Redis(host=settings['REDIS_HOST'],
                                      port=settings['REDIS_PORT'],
                                      db=settings.get('REDIS_DB'))

        try:
            self.redis_conn.info()
            self.logger.debug("Connected to Redis in ScraperHandler")
        except ConnectionError:
            self.logger.error("Failed to connect to Redis in ScraperHandler")
            # plugin is essential to functionality
            sys.exit(1)

    def handle(self, item):
        """
        Processes a vaild crawl request

        @param item: a valid dictionary object
        """
        # format key
        ex_res = self.extract(item['url'])
        key = "{sid}:{dom}.{suf}:queue".format(
            sid=item['spiderid'],
            dom=ex_res.domain,
            suf=ex_res.suffix)

        val = ujson.dumps(item)

        # shortcut to shove stuff into the priority queue
        self.redis_conn.zadd(key, val, -item['priority'])

        # if timeout crawl, add value to redis
        if 'expires' in item and item['expires'] != 0:
            key = "timeout:{sid}:{appid}:{crawlid}".format(
                            sid=item['spiderid'],
                            appid=item['appid'],
                            crawlid=item['crawlid'])
            self.redis_conn.set(key, item['expires'])

        # log success
        item['parsed'] = True
        item['valid'] = True
        self.logger.info('Added crawl to Redis', extra=item)
