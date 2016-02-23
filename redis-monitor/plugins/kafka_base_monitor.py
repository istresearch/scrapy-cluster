from base_monitor import BaseMonitor
from kafka import KafkaClient, SimpleProducer
from kafka.common import KafkaUnavailableError
from scutils.method_timer import MethodTimer

import json
import sys


class KafkaBaseMonitor(BaseMonitor):
    '''
    Base monitor for handling outbound Kafka results
    '''

    def setup(self, settings):
        '''
        Setup the handler

        @param settings: The loaded settings file
        '''
        @MethodTimer.timeout(settings['KAFKA_CONN_TIMEOUT'], False)
        def _hidden_setup():
            try:
                # set up kafka
                self.kafka_conn = KafkaClient(settings['KAFKA_HOSTS'])
                self.producer = SimpleProducer(self.kafka_conn)
                self.topic_prefix = settings['KAFKA_TOPIC_PREFIX']
            except KafkaUnavailableError as ex:
                message = "An exception '{0}' occured while setting up kafka. "\
                    "Arguments:\n{1!r}".format(type(ex).__name__, ex.args)
                self.logger.error(message)
                return False
            return True
        ret_val = _hidden_setup()
        self.use_appid_topics = settings['KAFKA_APPID_TOPICS']

        if ret_val:
            self.logger.debug("Successfully connected to Kafka in {name}"
                              .format(name=self.__class__.__name__))
        else:
            self.logger.error("Failed to set up Kafka Connection in {name} "
                              "within timeout".format(name=self.__class__.__name__))
            # this is essential to running the redis monitor
            sys.exit(1)

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
            self.kafka_conn.ensure_topic_exists(firehose_topic)
            # dont want logger in outbound kafka message
            dump = json.dumps(master)
            if self.use_appid_topics:
                self.kafka_conn.ensure_topic_exists(appid_topic)
                self.producer.send_messages(appid_topic, dump)
            self.producer.send_messages(firehose_topic, dump)

            return True
        except Exception as ex:
            message = "An exception '{0}' occured while sending a message " \
                "to kafka. Arguments:\n{1!r}" \
                .format(type(ex).__name__, ex.args)
            self.logger.error(message)

        return False
