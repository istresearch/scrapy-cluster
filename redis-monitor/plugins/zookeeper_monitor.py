from __future__ import absolute_import
import ujson
from .kafka_base_monitor import KafkaBaseMonitor
import yaml
from kazoo.client import KazooClient
from kazoo.exceptions import ZookeeperError


class ZookeeperMonitor(KafkaBaseMonitor):

    regex = "zk:*:*:*"

    def setup(self, settings):
        '''
        Setup kafka
        '''
        KafkaBaseMonitor.setup(self, settings)

        self.zoo_client = KazooClient(hosts=settings['ZOOKEEPER_HOSTS'])
        self.zoo_client.start()
        self.path = settings['ZOOKEEPER_ASSIGN_PATH'] + settings['ZOOKEEPER_ID']

        if not self.zoo_client.exists(self.path):
            self.zoo_client.ensure_path(self.path)

    def handle(self, key, value):
        '''
        Processes a vaild zookeeper request

        @param key: The key that matched the request
        @param value: The value associated with the key
        '''
        # break down key
        elements = key.split(":")
        dict = {}
        dict['action'] = elements[1]
        dict['domain'] = elements[2]
        dict['appid'] = elements[3]
        value = ujson.loads(value)

        # the master dict to return
        master = {}
        master['uuid'] = value['uuid']
        master['server_time'] = int(self.get_current_time())
        master['action'] = dict['action']
        master['domain'] = dict['domain']
        master['appid'] = dict['appid']

        # log we received the info message
        extras = self.get_log_dict(dict['action'], appid=dict['appid'],
                                   uuid=master['uuid'])

        self.logger.info('Received zookeeper request', extra=extras)

        # get the current zk configuration
        data = None
        try:
            data = self.zoo_client.get(self.path)[0]
        except ZookeeperError:
            e = "Unable to load Zookeeper config"
            self.logger.error(e)
            master['error'] = e
        the_dict = {}
        if data is not None and len(data) > 0:
            the_dict = yaml.safe_load(data)

        # update the configuration
        if "domains" not in the_dict:
            the_dict['domains'] = {}

        if "blacklist" not in the_dict:
            the_dict['blacklist'] = []

        if dict['action'] == 'domain-update':
            the_dict['domains'][dict['domain']] = {
                "window": value['window'],
                "hits": value['hits'],
                "scale": value['scale']
            }
        elif dict['action'] == 'domain-remove':
            if dict['domain'] in the_dict['domains']:
                del the_dict['domains'][dict['domain']]
        elif dict['action'] == 'blacklist-update':
            the_dict['blacklist'].append(dict['domain'])
            the_dict['blacklist'] = list(set(the_dict['blacklist']))
        elif dict['action'] == 'blacklist-remove':
            if dict['domain'] in the_dict['blacklist']:
                the_dict['blacklist'].remove(dict['domain'])
        else:
            self.logger.warn("Unknown command given to Zookeeper Monitor")

        # write the configuration back to zookeeper
        the_string = yaml.dump(the_dict, default_flow_style=False)
        try:
            self.zoo_client.set(self.path, the_string)
        except ZookeeperError:
            e = "Unable to store Zookeeper config"
            self.logger.error(e)
            master['error'] = e

        # ack the data back to kafka
        if self._send_to_kafka(master):
            extras['success'] = True
            self.logger.info('Sent zookeeper update to kafka', extra=extras)
        else:
            extras['success'] = False
            self.logger.error('Failed to send zookeeper update to kafka',
                              extra=extras)
