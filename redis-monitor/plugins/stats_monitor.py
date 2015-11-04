import re
import pickle
from kafka_base_monitor import KafkaBaseMonitor

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
        extras = self.get_log_dict('stats', appid, uuid)
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

        self.redis_conn.delete(key)

    def get_all_stats(self):
        '''
        Gather all stats objects
        '''
        self.logger.debug("Gathering all stats")
        the_dict = {}
        the_dict['kafka-monitor'] = self.get_kafka_monitor_stats()
        the_dict['redis-monitor'] = self.get_redis_monitor_stats()
        the_dict['crawler'] = self.get_crawler_stats()

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

    def get_crawler_stats(self):
        '''
        Gather crawler stats

        @return: A dict of stats
        '''
        self.logger.debug("Gathering crawler stats")
        the_dict = {}
        return the_dict