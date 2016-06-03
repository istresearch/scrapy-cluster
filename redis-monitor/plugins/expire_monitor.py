from __future__ import absolute_import
from .stop_monitor import StopMonitor


class ExpireMonitor(StopMonitor):
    '''
    Monitors for expiring crawls
    '''

    regex = "timeout:*:*:*"

    def setup(self, settings):
        '''
        Setup kafka
        '''
        StopMonitor.setup(self, settings)

    def check_precondition(self, key, value):
        '''
        Override to check for timeout
        '''
        timeout = float(value)
        curr_time = self.get_current_time()
        if curr_time > timeout:
            return True
        return False

    def handle(self, key, value):
        '''
        Processes a vaild action info request

        @param key: The key that matched the request
        @param value: The value associated with the key
        '''
        # very similar to stop
        # break down key
        elements = key.split(":")
        spiderid = elements[1]
        appid = elements[2]
        crawlid = elements[3]

        # log ack of expire
        extras = self.get_log_dict('expire', appid,
                                   spiderid, crawlid=crawlid)
        self.logger.info("Expiring crawl found", extra=extras)

        # add crawl to blacklist so it doesnt propagate
        redis_key = spiderid + ":blacklist"
        value = '{appid}||{crawlid}'.format(appid=appid,
                                            crawlid=crawlid)
        # add this to the blacklist set
        self.redis_conn.sadd(redis_key, value)

        # everything stored in the queue is now expired
        result = self._purge_crawl(spiderid, appid, crawlid)

        # add result to our dict
        master = {}
        master['server_time'] = int(self.get_current_time())
        master['crawlid'] = crawlid
        master['spiderid'] = spiderid
        master['appid'] = appid
        master['total_expired'] = result
        master['action'] = 'expired'

        if self._send_to_kafka(master):
            master['success'] = True
            self.logger.info('Sent expired ack to kafka', extra=master)
        else:
            master['success'] = False
            self.logger.error('Failed to send expired ack to kafka',
                              extra=master)
