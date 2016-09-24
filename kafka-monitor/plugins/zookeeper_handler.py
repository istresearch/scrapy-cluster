from __future__ import absolute_import
from .base_handler import BaseHandler
import tldextract
import redis
import sys
import ujson
from redis.exceptions import ConnectionError


class ZookeeperHandler(BaseHandler):

    schema = "zookeeper_schema.json"

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
            self.logger.debug("Connected to Redis in ZookeeperHandler")
        except ConnectionError:
            self.logger.error("Failed to connect to Redis in ZookeeperHandler")
            # plugin is essential to functionality
            sys.exit(1)

    def handle(self, item):
        """
        Processes a valid zookeeper request

        @param item: a valid dictionary object
        """
        # format key
        key = "zk:{action}:{domain}:{appid}".format(
                action=item['action'],
                appid=item['appid'],
                domain=item['domain'])

        d = {"domain": item['domain'], "uuid": item['uuid']}

        if item['action'] == 'domain-update':
            if item['hits'] != 0 and item['window'] != 0:
                d["hits"] = item['hits']
                d['scale'] = item['scale']
                d['window'] = item['window']
            else:
                self.logger.error("'hits' and 'window' not set for domain update")
                return None

        value = ujson.dumps(d)

        self.redis_conn.set(key, value)

        item['parsed'] = True
        item['valid'] = True
        self.logger.info('Added zookeeper action to Redis', extra=item)
