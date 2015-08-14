import re
import pickle
import time
from stop_monitor import StopMonitor

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

    def handle(self, key, value):
        '''
        Processes a vaild action info request

        @param key: The key that matched the request
        @param value: The value associated with the key
        '''
        timeout = float(value)
        curr_time = time.time()
        if curr_time > timeout:
            print "handling expire request"
            # very similar to stop
            # break down key
            elements = key.split(":")
            spiderid = elements[1]
            appid = elements[2]
            crawlid = elements[3]

            # add crawl to blacklist so it doesnt propagate
            redis_key = spiderid + ":blacklist"
            value = '{appid}||{crawlid}'.format(appid=appid,
                                            crawlid=crawlid)
            # add this to the blacklist set
            self.redis_conn.sadd(redis_key, value)

            # everything stored in the queue is now expired
            result = self._purge_crawl(spiderid, appid, crawlid)

            # item to send to kafka
            extras = {}
            extras['action'] = "expire"
            extras['spiderid'] = spiderid
            extras['appid'] = appid
            extras['crawlid'] = crawlid
            extras['total_expired'] = result

            if self._send_to_kafka(extras):
                #print 'Sent expired ack to kafka'
                pass
            else:
                print 'Failed to send expired ack to kafka'

            self.redis_conn.delete(key)