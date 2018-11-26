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
            self.logger.debug("Connected to Redis in ZookeeperHandler")
        except ConnectionError:
            self.logger.error("Failed to connect to Redis in ZookeeperHandler")
            # plugin is essential to functionality
            sys.exit(1)

    def handle(self, dict):
        '''
        Processes a vaild zookeeper request

        @param dict: a valid dictionary object
        '''
        # format key
        key = "zk:{action}:{domain}:{appid}".format(
                action=dict['action'],
                appid=dict['appid'],
                domain=dict['domain'])

        d = {"domain": dict['domain'], "uuid": dict['uuid']}

        if dict['action'] == 'domain-update':
            if dict['hits'] != 0 and dict['window'] != 0:
                d["hits"] = dict['hits']
                d['scale'] = dict['scale']
                d['window'] = dict['window']
            else:
                self.logger.error("'hits' and 'window' not set for domain update")
                return None

        value = ujson.dumps(d)

        self.redis_conn.set(key, value)

        dict['parsed'] = True
        dict['valid'] = True
        self.logger.info('Added zookeeper action to Redis', extra=dict)
