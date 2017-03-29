from __future__ import absolute_import
import ujson
from .kafka_base_monitor import KafkaBaseMonitor


class InfoMonitor(KafkaBaseMonitor):

    regex = "info:*:*"

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
        # the master dict to return
        master = {}
        master['uuid'] = value
        master['total_pending'] = 0
        master['server_time'] = int(self.get_current_time())

        # break down key
        elements = key.split(":")
        dict = {}
        dict['spiderid'] = elements[1]
        dict['appid'] = elements[2]

        # log we received the info message
        extras = self.get_log_dict('info', dict['appid'],
                                   dict['spiderid'], master['uuid'])

        if len(elements) == 4:
            dict['crawlid'] = elements[3]
            extras = self.get_log_dict('info', dict['appid'],
                                       dict['spiderid'], master['uuid'],
                                       elements[3])
        self.logger.info('Received info request', extra=extras)

        # generate the information requested
        if 'crawlid' in dict:
            master = self._build_crawlid_info(master, dict)
        else:
            master = self._build_appid_info(master, dict)

        if self._send_to_kafka(master):
            extras['success'] = True
            self.logger.info('Sent info to kafka', extra=extras)
        else:
            extras['success'] = False
            self.logger.error('Failed to send info to kafka',
                              extra=extras)

    def _get_bin(self, key):
        '''
        Returns a binned dictionary based on redis zscore

        @return: The sorted dict
        '''
        # keys based on score
        sortedDict = {}
        # this doesnt return them in order, need to bin first
        for item in self.redis_conn.zscan_iter(key):
            my_item = ujson.loads(item[0])
            # score is negated in redis
            my_score = -item[1]

            if my_score not in sortedDict:
                sortedDict[my_score] = []

            sortedDict[my_score].append(my_item)

        return sortedDict

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
        master['spiderid'] = dict['spiderid']

        # used for finding total count of domains
        domain_dict = {}

        # get all domain queues
        match_string = '{sid}:*:queue'.format(sid=dict['spiderid'])
        for key in self.redis_conn.scan_iter(match=match_string):
            domain = key.split(":")[1]
            sortedDict = self._get_bin(key)

            # now iterate through binned dict
            for score in sortedDict:
                for item in sortedDict[score]:
                    if 'meta' in item:
                        item = item['meta']
                    if item['appid'] == dict['appid']:
                        crawlid = item['crawlid']

                        # add new crawlid to master dict
                        if crawlid not in master['crawlids']:
                            master['crawlids'][crawlid] = {
                                'total': 0,
                                'domains': {},
                                'distinct_domains': 0
                            }

                            if 'expires' in item and item['expires'] != 0:
                                master['crawlids'][crawlid]['expires'] = item['expires']

                            master['total_crawlids'] += 1

                        master['crawlids'][crawlid]['total'] = master['crawlids'][crawlid]['total'] + 1

                        if domain not in master['crawlids'][crawlid]['domains']:
                            master['crawlids'][crawlid]['domains'][domain] = {
                                'total': 0,
                                'high_priority': -9999,
                                'low_priority': 9999,
                            }
                            master['crawlids'][crawlid]['distinct_domains'] += 1
                            domain_dict[domain] = True


                        master['crawlids'][crawlid]['domains'][domain]['total'] = master['crawlids'][crawlid]['domains'][domain]['total'] + 1

                        if item['priority'] > master['crawlids'][crawlid]['domains'][domain]['high_priority']:
                            master['crawlids'][crawlid]['domains'][domain]['high_priority'] = item['priority']

                        if item['priority'] < master['crawlids'][crawlid]['domains'][domain]['low_priority']:
                            master['crawlids'][crawlid]['domains'][domain]['low_priority'] = item['priority']

                        master['total_pending'] += 1

        master['total_domains'] = len(domain_dict)

        return master

    def _build_crawlid_info(self, master, dict):
        '''
        Builds the crawlid info object

        @param master: the master dict
        @param dict: the dict object received
        @return: the crawlid info object
        '''
        master['total_pending'] = 0
        master['total_domains'] = 0
        master['appid'] = dict['appid']
        master['crawlid'] = dict['crawlid']
        master['spiderid'] = dict['spiderid']
        master['domains'] = {}

        timeout_key = 'timeout:{sid}:{aid}:{cid}'.format(sid=dict['spiderid'],
                                                         aid=dict['appid'],
                                                         cid=dict['crawlid'])
        if self.redis_conn.exists(timeout_key):
            master['expires'] = self.redis_conn.get(timeout_key)

        # get all domain queues
        match_string = '{sid}:*:queue'.format(sid=dict['spiderid'])
        for key in self.redis_conn.scan_iter(match=match_string):
            domain = key.split(":")[1]
            sortedDict = self._get_bin(key)

            # now iterate through binned dict
            for score in sortedDict:
                for item in sortedDict[score]:
                    if 'meta' in item:
                        item = item['meta']
                    if item['appid'] == dict['appid'] and item['crawlid'] == dict['crawlid']:
                        if domain not in master['domains']:
                            master['domains'][domain] = {}
                            master['domains'][domain]['total'] = 0
                            master['domains'][domain]['high_priority'] = -9999
                            master['domains'][domain]['low_priority'] = 9999
                            master['total_domains'] = master['total_domains'] + 1

                        master['domains'][domain]['total'] = master['domains'][domain]['total'] + 1

                        if item['priority'] > master['domains'][domain]['high_priority']:
                            master['domains'][domain]['high_priority'] = item['priority']

                        if item['priority'] < master['domains'][domain]['low_priority']:
                            master['domains'][domain]['low_priority'] = item['priority']

                        master['total_pending'] = master['total_pending'] + 1

        return master
