import redis
import logging
import sys
import time
import re
import pickle
import traceback
import json
import requests

from settings import (REDIS_HOST, REDIS_PORT, KAFKA_HOSTS, KAFKA_TOPIC_PREFIX)

from kafka import KafkaClient, SimpleProducer

class RedisMonitor:

    def __init__(self):
        self.setup()

    def setup(self):
        '''
        Connection stuff here so we can mock it
        '''
        self.redis_conn = redis.Redis(host=REDIS_HOST, port=REDIS_PORT)

        # set up kafka
        self.kafka_conn = KafkaClient(KAFKA_HOSTS)
        self.producer = SimpleProducer(self.kafka_conn)
        self.topic_prefix = KAFKA_TOPIC_PREFIX

    def run(self):
        '''
        The external main run loop
        '''
        self._main_loop()

    def _main_loop(self):
        '''
        The internal while true main loop for the redis monitor
        '''
        while True:
            self._do_info()
            self._do_expire()
            self._do_stop()

            time.sleep(0.1)

    def _do_info(self):
        '''
        Processes info action requests
        '''
        for key in self.redis_conn.scan_iter(match="info:*:*"):
            # the master dict to return
            master = {}
            master['uuid'] = self.redis_conn.get(key)
            master['total_pending'] = 0
            master['server_time'] = int(time.time())

            # break down key
            elements = key.split(":")
            dict = {}
            dict['spiderid'] = elements[1]
            dict['appid'] = elements[2]

            if len(elements) == 4:
                dict['crawlid'] = elements[3]

            # we received the info message
            print "received info request"

            # generate the information requested
            if 'crawlid' in dict:
                print "got crawlid info"
                master = self._build_crawlid_info(master, dict)
            else:
                print "got appid info"
                master = self._build_appid_info(master, dict)

            self.redis_conn.delete(key)

            if self._send_to_kafka(master):
                print 'Sent info to kafka'
            else:
                print 'Failed to send info to kafka'

    def _send_to_kafka(self, master):
        '''
        Sends the message back to Kafka
        @param master: the final dict to send
        @log_extras: the extras to append to the log output
        @returns: True if successfully sent to kafka
        '''
        appid_topic = "{prefix}.outbound_{appid}".format(
                                                    prefix=self.topic_prefix,
                                                    appid=master['appid'])
        firehose_topic = "{prefix}.outbound_firehose".format(
                                                    prefix=self.topic_prefix)
        try:
            self.kafka_conn.ensure_topic_exists(appid_topic)
            self.kafka_conn.ensure_topic_exists(firehose_topic)
            # dont want logger in outbound kafka message
            dump = json.dumps(master)
            self.producer.send_messages(appid_topic, dump)
            self.producer.send_messages(firehose_topic, dump)

            return True
        except Exception as ex:
            print traceback.format_exc()
            pass

        return False

    def _build_appid_info(self, master, dict):
        '''
        Builds the appid info object

        @param master: the master dict
        @param dict: the dict object received
        @return: the appid info object
        '''
        master['total_crawlids'] = 0
        master['total_pending'] = 0
        master['total_domains'] = 0
        master['crawlids'] = {}
        master['appid'] = dict['appid']

        match_string = '{sid}:queue'.format(sid=dict['spiderid'])

        sortedDict = self._get_bin(match_string)

        # now iterate through binned dict
        for score in sortedDict:
            for item in sortedDict[score]:
                if 'meta' in item:
                    item = item['meta']
                if item['appid'] == dict['appid']:
                    crawlid = item['crawlid']

                    # add new crawlid to master dict
                    if crawlid not in master['crawlids']:
                        master['crawlids'][crawlid] = {}
                        master['crawlids'][crawlid]['total'] = 0
                        master['crawlids'][crawlid]['high_priority'] = -9999
                        master['crawlids'][crawlid]['low_priority'] = 9999

                        timeout_key = 'timeout:{sid}:{aid}:{cid}'.format(
                                    sid=dict['spiderid'],
                                    aid=dict['appid'],
                                    cid=crawlid)
                        if self.redis_conn.exists(timeout_key):
                            master['crawlids'][crawlid]['expires'] = self.redis_conn.get(timeout_key)

                        master['total_crawlids'] = master['total_crawlids'] + 1

                    if item['priority'] > master['crawlids'][crawlid]['high_priority']:
                        master['crawlids'][crawlid]['high_priority'] = item['priority']

                    if item['priority'] < master['crawlids'][crawlid]['low_priority']:
                        master['crawlids'][crawlid]['low_priority'] = item['priority']

                    master['crawlids'][crawlid]['total'] = master['crawlids'][crawlid]['total'] + 1
                    master['total_pending'] = master['total_pending'] + 1

        return master

    def _get_bin(self, key):
        '''
        Returns a binned dictionary based on redis zscore

        @return: The sorted dict
        '''
        # keys based on score
        sortedDict = {}
        # this doesnt return them in order, need to bin first
        for item in self.redis_conn.zscan_iter(key):
            my_item = pickle.loads(item[0])
            # score is negated in redis
            my_score = -item[1]

            if my_score not in sortedDict:
                sortedDict[my_score] = []

            sortedDict[my_score].append(my_item)

        return sortedDict

    def _build_crawlid_info(self,master, dict):
        '''
        Builds the crawlid info object

        @param master: the master dict
        @param dict: the dict object received
        @return: the crawlid info object
        '''
        master['total_pending'] = 0
        master['appid'] = dict['appid']
        master['crawlid'] = dict['crawlid']

        timeout_key = 'timeout:{sid}:{aid}:{cid}'.format(sid=dict['spiderid'],
                                                        aid=dict['appid'],
                                                        cid=dict['crawlid'])
        if self.redis_conn.exists(timeout_key):
            master['expires'] = self.redis_conn.get(timeout_key)

        # get all domain queues
        match_string = '{sid}:queue'.format(sid=dict['spiderid'])
        sortedDict = self._get_bin(match_string)

        # now iterate through binned dict
        for score in sortedDict:
            for item in sortedDict[score]:
                if 'meta' in item:
                    item = item['meta']
                if item['appid'] == dict['appid'] and \
                                item['crawlid'] == dict['crawlid']:

                    if 'high_priority' not in master:
                        master['high_priority'] = -99999

                    if 'low_priority' not in master:
                        master['low_priority'] = 99999

                    if item['priority'] > master['high_priority']:
                        master['high_priority'] = item['priority']

                    if item['priority'] < master['low_priority']:
                        master['low_priority'] = item['priority']

                    master['total_pending'] = master['total_pending'] + 1

        return master

    def _do_expire(self):
        '''
        Processes expire requests
        Very similar to _do_stop()
        '''
        for key in self.redis_conn.scan_iter(match="timeout:*:*:*"):
            timeout = float(self.redis_conn.get(key))
            curr_time = time.time()
            if curr_time > timeout:
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

                self.redis_conn.delete(key)

                if self._send_to_kafka(extras):
                    print 'Sent expired ack to kafka'
                else:
                    print 'Failed to send expired ack to kafka'

    def _do_stop(self):
        '''
        Processes stop action requests
        '''
        for key in self.redis_conn.scan_iter(match="stop:*:*:*"):
            # break down key
            elements = key.split(":")
            spiderid = elements[1]
            appid = elements[2]
            crawlid = elements[3]
            uuid = self.redis_conn.get(key)

            # log we received the stop message
            print 'Received stop request'

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

            self.redis_conn.delete(key)

            if self._send_to_kafka(extras):
                # delete timeout for crawl (if needed) since stopped
                timeout_key = 'timeout:{sid}:{aid}:{cid}'.format(
                                        sid=spiderid,
                                        aid=appid,
                                        cid=crawlid)
                self.redis_conn.delete(timeout_key)
                print 'Sent stop ack to kafka'
            else:
                print 'Failed to send stop ack to kafka'

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

        match_string = '{sid}:queue'.format(sid=spiderid)
        # using scan for speed vs keys
        for item in self.redis_conn.zscan_iter(match_string):
            item_key = item[0]
            item = pickle.loads(item_key)
            if 'meta' in item:
                item = item['meta']

            if item['appid'] == appid and item['crawlid'] == crawlid:
                self.redis_conn.zrem(match_string, item_key)
                total_purged = total_purged + 1

        return total_purged

def main():
    redis_monitor = RedisMonitor()
    redis_monitor.run()

if __name__ == "__main__":
    sys.exit(main())
