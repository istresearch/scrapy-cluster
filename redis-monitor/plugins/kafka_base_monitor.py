from base_monitor import BaseMonitor
from kafka import KafkaClient, SimpleProducer
from base_monitor import BaseMonitor
import traceback
import json

class KafkaBaseMonitor(BaseMonitor):
    '''
    Base monitor for handling outbound Kafka results
    '''

    def setup(self, settings):
        '''
        Setup the handler

        @param settings: The loaded settings file
        '''
        # set up kafka
        self.kafka_conn = KafkaClient(settings.KAFKA_HOSTS)
        self.producer = SimpleProducer(self.kafka_conn)
        self.topic_prefix = settings.KAFKA_TOPIC_PREFIX

    def _send_to_kafka(self, master):
        '''
        Sends the message back to Kafka
        @param master: the final dict to send
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


