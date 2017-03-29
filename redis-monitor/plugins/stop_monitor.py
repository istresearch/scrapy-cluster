from __future__ import absolute_import
import ujson
from .kafka_base_monitor import KafkaBaseMonitor


class StopMonitor(KafkaBaseMonitor):

    regex = "stop:*:*"

    def setup(self, settings):
        '''
        Setup kafka
        '''
        KafkaBaseMonitor.setup(self, settings)

    def handle(self, key, value):
        '''
        Processes a vaild action info request

        @param key: The key that matched the request
        @param value: The value associated with the key
        '''
        # break down key
        elements = key.split(":")

        if len(elements) != 4:
            self.logger.warn("Stop requests need a crawlid and appid")
            return

        spiderid = elements[1]
        appid = elements[2]
        crawlid = elements[3]
        uuid = value

        # log we received the stop message
        extras = self.get_log_dict('stop', appid,
                                   spiderid, uuid, crawlid)
        self.logger.info('Received stop request', extra=extras)

        redis_key = spiderid + ":blacklist"
        value = '{appid}||{crawlid}'.format(appid=appid,
                                            crawlid=crawlid)

        # add this to the blacklist set
        self.redis_conn.sadd(redis_key, value)

        # purge crawlid from current set
        result = self._purge_crawl(spiderid, appid, crawlid)

        # item to send to kafka
        extras = {}
        extras['action'] = "stop"
        extras['spiderid'] = spiderid
        extras['appid'] = appid
        extras['crawlid'] = crawlid
        extras['total_purged'] = result
        extras['uuid'] = uuid
        extras['server_time'] = int(self.get_current_time())

        if self._send_to_kafka(extras):
            # delete timeout for crawl (if needed) since stopped
            timeout_key = 'timeout:{sid}:{aid}:{cid}'.format(
                                    sid=spiderid,
                                    aid=appid,
                                    cid=crawlid)
            self.redis_conn.delete(timeout_key)
            extras['success'] = True
            self.logger.info('Sent stop ack to kafka', extra=extras)
        else:
            extras['success'] = False
            self.logger.error('Failed to send stop ack to kafka', extra=extras)

    def _purge_crawl(self, spiderid, appid, crawlid):
        '''
        Wrapper for purging the crawlid from the queues

        @param spiderid: the spider id
        @param appid: the app id
        @param crawlid: the crawl id
        @return: The number of requests purged
        '''
        # purge three times to try to make sure everything is cleaned
        total = self._mini_purge(spiderid, appid, crawlid)
        total = total + self._mini_purge(spiderid, appid, crawlid)
        total = total + self._mini_purge(spiderid, appid, crawlid)

        return total

    def _mini_purge(self, spiderid, appid, crawlid):
        '''
        Actually purges the crawlid from the queue

        @param spiderid: the spider id
        @param appid: the app id
        @param crawlid: the crawl id
        @return: The number of requests purged
        '''
        total_purged = 0

        match_string = '{sid}:*:queue'.format(sid=spiderid)
        # using scan for speed vs keys
        for key in self.redis_conn.scan_iter(match=match_string):
            for item in self.redis_conn.zscan_iter(key):
                item_key = item[0]
                item = ujson.loads(item_key)
                if 'meta' in item:
                    item = item['meta']

                if item['appid'] == appid and item['crawlid'] == crawlid:
                    self.redis_conn.zrem(key, item_key)
                    total_purged = total_purged + 1

        return total_purged
