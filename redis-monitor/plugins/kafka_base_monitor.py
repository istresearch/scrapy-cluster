from __future__ import absolute_import
from builtins import str
from .base_monitor import BaseMonitor
from kafka import KafkaProducer
from kafka.common import KafkaUnavailableError
from scutils.method_timer import MethodTimer
from retrying import retry

import json
import sys
import traceback


class KafkaBaseMonitor(BaseMonitor):
    '''
    Base monitor for handling outbound Kafka results
    '''

    def setup(self, settings):
        '''
        Setup the handler

        @param settings: The loaded settings file
        '''
        self.producer = self._create_producer(settings)
        self.topic_prefix = settings['KAFKA_TOPIC_PREFIX']

        self.use_appid_topics = settings['KAFKA_APPID_TOPICS']

        self.logger.debug("Successfully connected to Kafka in {name}"
                              .format(name=self.__class__.__name__))

    @retry(wait_exponential_multiplier=500, wait_exponential_max=10000)
    def _create_producer(self, settings):
        """Tries to establish a Kafka consumer connection"""
        try:
            brokers = settings['KAFKA_HOSTS']
            self.logger.debug("Creating new kafka producer using brokers: " +
                               str(brokers))

            return KafkaProducer(bootstrap_servers=brokers,
                                 value_serializer=lambda m: json.dumps(m),
                                 retries=3,
                                 linger_ms=settings['KAFKA_PRODUCER_BATCH_LINGER_MS'],
                                 buffer_memory=settings['KAFKA_PRODUCER_BUFFER_BYTES'])
        except KeyError as e:
            self.logger.error('Missing setting named ' + str(e),
                               {'ex': traceback.format_exc()})
        except:
            self.logger.error("Couldn't initialize kafka producer in plugin.",
                               {'ex': traceback.format_exc()})
            raise

    def _kafka_success(self, response):
        '''
        Callback for successful send
        '''
        self.logger.debug("Sent message to Kafka")

    def _kafka_failure(self, response):
        '''
        Callback for failed send
        '''
        self.logger.error("Failed to send message to Kafka")

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
            # dont want logger in outbound kafka message
            if self.use_appid_topics:
                f1 = self.producer.send(appid_topic, master)
                f1.add_callback(self._kafka_success)
                f1.add_errback(self._kafka_failure)
            f2 = self.producer.send(firehose_topic, master)
            f2.add_callback(self._kafka_success)
            f2.add_errback(self._kafka_failure)

            return True
        except Exception as ex:
            message = "An exception '{0}' occured while sending a message " \
                "to kafka. Arguments:\n{1!r}" \
                .format(type(ex).__name__, ex.args)
            self.logger.error(message)

        return False

    def close(self):
        self.producer.flush()
        self.producer.close(timeout=10)
