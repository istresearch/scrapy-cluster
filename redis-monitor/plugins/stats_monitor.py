from __future__ import absolute_import
from .kafka_base_monitor import KafkaBaseMonitor


class StatsMonitor(KafkaBaseMonitor):

    regex = "statsrequest:*:*"

    def setup(self, settings):
        '''
        Setup kafka
        '''
        KafkaBaseMonitor.setup(self, settings)

    def handle(self, key, value):
        '''
        Processes a vaild stats request

        @param key: The key that matched the request
        @param value: The value associated with the key
        '''
        # break down key
        elements = key.split(":")

        stats = elements[1]
        appid = elements[2]
        uuid = value

        # log we received the stats request
        extras = self.get_log_dict('stats', appid, uuid=uuid)
        self.logger.info('Received {s} stats request'.format(s=stats),
            extra=extras)

        extras = {}
        if stats == 'all':
            extras = self.get_all_stats()
        elif stats == 'kafka-monitor':
            extras = self.get_kafka_monitor_stats()
        elif stats == 'redis-monitor':
            extras = self.get_redis_monitor_stats()
        elif stats == 'crawler':
            extras = self.get_crawler_stats()
        elif stats == 'spider':
            extras = self.get_spider_stats()
        elif stats == 'machine':
            extras = self.get_machine_stats()
        elif stats == 'queue':
            extras = self.get_queue_stats()
        elif stats == 'rest':
            extras = self.get_rest_stats()
        else:
            self.logger.warn('Received invalid stats request: {s}'\
                .format(s=stats),
            extra=extras)
            return

        extras['stats'] = stats
        extras['appid'] = appid
        extras['uuid'] = uuid
        extras['server_time'] = int(self.get_current_time())

        if self._send_to_kafka(extras):
            extras['success'] = True
            self.logger.info('Sent stats to kafka', extra=extras)
        else:
            extras['success'] = False
            self.logger.error('Failed to send stats to kafka', extra=extras)

    def get_all_stats(self):
        '''
        Gather all stats objects
        '''
        self.logger.debug("Gathering all stats")
        the_dict = {}
        the_dict['kafka-monitor'] = self.get_kafka_monitor_stats()
        the_dict['redis-monitor'] = self.get_redis_monitor_stats()
        the_dict['crawler'] = self.get_crawler_stats()
        the_dict['rest'] = self.get_rest_stats()

        return the_dict

    def get_kafka_monitor_stats(self):
        '''
        Gather Kafka Monitor stats

        @return: A dict of stats
        '''
        self.logger.debug("Gathering kafka-monitor stats")
        return self._get_plugin_stats('kafka-monitor')

    def get_redis_monitor_stats(self):
        '''
        Gather Redis Monitor stats

        @return: A dict of stats
        '''
        self.logger.debug("Gathering redis-monitor stats")
        return self._get_plugin_stats('redis-monitor')

    def get_rest_stats(self):
        '''
        Gather Rest stats

        @return: A dict of stats
        '''
        self.logger.debug("Gathering rest stats")
        return self._get_plugin_stats('rest')

    def _get_plugin_stats(self, name):
        '''
        Used for getting stats for Plugin based stuff, like Kafka Monitor
        and Redis Monitor

        @param name: the main class stats name
        @return: A formatted dict of stats
        '''
        the_dict = {}

        keys = self.redis_conn.keys('stats:{n}:*'.format(n=name))

        for key in keys:
            # break down key
            elements = key.split(":")
            main = elements[2]
            end = elements[3]

            if main == 'total' or main == 'fail':
                if main not in the_dict:
                    the_dict[main] = {}
                the_dict[main][end] = self._get_key_value(key, end == 'lifetime')
            elif main == 'self':
                if 'nodes' not in the_dict:
                    # main is self, end is machine, true_tail is uuid
                    the_dict['nodes'] = {}
                true_tail = elements[4]
                if end not in the_dict['nodes']:
                    the_dict['nodes'][end] = []
                the_dict['nodes'][end].append(true_tail)
            else:
                if 'plugins' not in the_dict:
                    the_dict['plugins'] = {}
                if main not in the_dict['plugins']:
                    the_dict['plugins'][main] = {}
                the_dict['plugins'][main][end] = self._get_key_value(key, end == 'lifetime')

        return the_dict

    def _get_key_value(self, key, is_hll=False):
        '''
        Returns the proper key value for the stats

        @param key: the redis key
        @param is_hll: the key is a HyperLogLog, else is a sorted set
        '''
        if is_hll:
            # get hll value
            return self.redis_conn.execute_command("PFCOUNT", key)
        else:
            # get zcard value
            return self.redis_conn.zcard(key)

    def get_spider_stats(self):
        '''
        Gather spider based stats
        '''
        self.logger.debug("Gathering spider stats")
        the_dict = {}
        spider_set = set()
        total_spider_count = 0

        keys = self.redis_conn.keys('stats:crawler:*:*:*')
        for key in keys:
            # we only care about the spider
            elements = key.split(":")
            spider = elements[3]

            if spider not in the_dict:
                the_dict[spider] = {}
                the_dict[spider]['count'] = 0

            if len(elements) == 6:
                # got a time based stat
                response = elements[4]
                end = elements[5]

                if response not in the_dict[spider]:
                    the_dict[spider][response] = {}

                the_dict[spider][response][end] = self._get_key_value(key, end == 'lifetime')

            elif len(elements) == 5:
                # got a spider identifier
                the_dict[spider]['count'] += 1
                total_spider_count += 1
                spider_set.add(spider)

            else:
                self.logger.warn("Unknown crawler stat key", {"key":key})

        # simple counts
        the_dict['unique_spider_count'] = len(spider_set)
        the_dict['total_spider_count'] = total_spider_count

        ret_dict = {}
        ret_dict['spiders'] = the_dict

        return ret_dict

    def get_machine_stats(self):
        '''
        Gather spider based stats
        '''
        self.logger.debug("Gathering machine stats")
        the_dict = {}
        keys = self.redis_conn.keys('stats:crawler:*:*:*:*')

        for key in keys:
            # break down key
            elements = key.split(":")
            machine = elements[2]
            spider = elements[3]
            response = elements[4]
            end = elements[5]

            # we only care about the machine, not spider type
            if machine not in the_dict:
                the_dict[machine] = {}

            if response not in the_dict[machine]:
                the_dict[machine][response] = {}

            if end in the_dict[machine][response]:
                the_dict[machine][response][end] = the_dict[machine][response][end] + \
                    self._get_key_value(key, end == 'lifetime')
            else:
                the_dict[machine][response][end] = self._get_key_value(key, end == 'lifetime')

        # simple count
        the_dict['count'] = len(list(the_dict.keys()))

        ret_dict = {}
        ret_dict['machines'] = the_dict

        return ret_dict

    def get_crawler_stats(self):
        '''
        Gather crawler stats

        @return: A dict of stats
        '''
        self.logger.debug("Gathering crawler stats")
        the_dict = {}

        the_dict['spiders'] = self.get_spider_stats()['spiders']
        the_dict['machines'] = self.get_machine_stats()['machines']
        the_dict['queue'] = self.get_queue_stats()['queues']

        return the_dict

    def get_queue_stats(self):
        '''
        Gather queue stats

        @return: A dict of stats
        '''
        self.logger.debug("Gathering queue based stats")

        the_dict = {}
        keys = self.redis_conn.keys('*:*:queue')
        total_backlog = 0
        for key in keys:
            elements = key.split(":")
            spider = elements[0]
            domain = elements[1]
            spider = 'queue_' + spider

            if spider not in the_dict:
                the_dict[spider] = {
                    'spider_backlog': 0,
                    'num_domains': 0,
                    'domains': []
                }

            count = self.redis_conn.zcard(key)
            total_backlog += count
            the_dict[spider]['spider_backlog'] += count
            the_dict[spider]['num_domains'] += 1
            the_dict[spider]['domains'].append({'domain': domain,
                                                'backlog': count})

        the_dict['total_backlog'] = total_backlog
        ret_dict = {
            'queues': the_dict
        }

        return ret_dict
