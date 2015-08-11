from base_handler import BaseHandler
import tldextract
import redis
import pickle

class ScraperHandler(BaseHandler):

    schema = "scraper_schema.json"

    def setup(self, settings):
        '''
        Setup redis and tldextract
        '''
        self.extract = tldextract.TLDExtract()
        self.redis_conn = redis.Redis(host=settings.REDIS_HOST,
                                      port=settings.REDIS_PORT)

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

        val = pickle.dumps(dict, protocol=-1)

        # shortcut to shove stuff into the priority queue
        self.redis_conn.zadd(key, val, -dict['priority'])

        # if timeout crawl, add value to redis
        if 'expires' in dict:
            key = "timeout:{sid}:{appid}:{crawlid}".format(
                            sid=dict['spiderid'],
                            appid=dict['appid'],
                            crawlid=dict['crawlid'])
            self.redis_conn.set(key, dict['expires'])