from base_handler import BaseHandler
import tldextract
import redis
import pickle

class ActionHandler(BaseHandler):

    schema = "action_schema.json"

    def setup(self, settings):
        '''
        Setup redis and tldextract
        '''
        self.extract = tldextract.TLDExtract()
        self.redis_conn = redis.Redis(host=settings['REDIS_HOST'],
                                      port=settings['REDIS_PORT'])

    def handle(self, dict):
        '''
        Processes a vaild crawl request

        @param dict: a valid dictionary object
        '''
        # format key
        key = "{action}:{spiderid}:{appid}".format(
                action = dict['action'],
                spiderid = dict['spiderid'],
                appid = dict['appid'])

        if "crawlid" in dict:
            key = key + ":" + dict['crawlid']

        self.redis_conn.set(key, dict['uuid'])