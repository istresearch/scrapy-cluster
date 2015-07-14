from base_handler import BaseHandler

class ScraperHandler(BaseHandler):

    schema = "scraper_schema.json"

    def setup(self, settings):
        '''
        Setup the redis needs
        '''
        print "setting up scraperhandler"

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