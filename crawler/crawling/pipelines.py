from builtins import object
# -*- coding: utf-8 -*-

# Define your item pipelines here

import ujson
import datetime as dt
import sys
import traceback
import base64
from builtins import bytes, str

from kafka import KafkaProducer
from kafka.errors import KafkaTimeoutError
from crawling.items import RawResponseItem
from scutils.log_factory import LogFactory


class LoggingBeforePipeline(object):

    '''
    Logs the crawl, currently the 1st priority of the pipeline
    '''

    def __init__(self, logger):
        self.logger = logger
        self.logger.debug("Setup before pipeline")

    @classmethod
    def from_settings(cls, settings):
        my_level = settings.get('SC_LOG_LEVEL', 'INFO')
        my_name = settings.get('SC_LOGGER_NAME', 'sc-logger')
        my_output = settings.get('SC_LOG_STDOUT', True)
        my_json = settings.get('SC_LOG_JSON', False)
        my_dir = settings.get('SC_LOG_DIR', 'logs')
        my_bytes = settings.get('SC_LOG_MAX_BYTES', '10MB')
        my_file = settings.get('SC_LOG_FILE', 'main.log')
        my_backups = settings.get('SC_LOG_BACKUPS', 5)

        logger = LogFactory.get_instance(json=my_json,
                                         name=my_name,
                                         stdout=my_output,
                                         level=my_level,
                                         dir=my_dir,
                                         file=my_file,
                                         bytes=my_bytes,
                                         backups=my_backups)

        return cls(logger)

    @classmethod
    def from_crawler(cls, crawler):
        return cls.from_settings(crawler.settings)

    def process_item(self, item, spider):
        self.logger.debug("Processing item in LoggingBeforePipeline")
        if isinstance(item, RawResponseItem):
            # make duplicate item, but remove unneeded keys
            item_copy = dict(item)
            del item_copy['body']
            del item_copy['links']
            del item_copy['response_headers']
            del item_copy['request_headers']
            item_copy['logger'] = self.logger.name
            item_copy['action'] = 'emit'
            item_copy['spiderid'] = spider.name
            self.logger.info('Scraped page', extra=item_copy)
            return item
        else:
            self.logger.warn('Received unknown item')
            return None


class KafkaPipeline(object):
    '''
    Pushes a serialized item to appropriate Kafka topics.
    '''

    def __init__(self, producer, topic_prefix, logger, appids,
                 use_base64):
        self.producer = producer
        self.topic_prefix = topic_prefix
        self.topic_list = []
        self.appid_topics = appids
        self.logger = logger
        self.logger.debug("Setup kafka pipeline")
        self.use_base64 = use_base64

    @classmethod
    def from_settings(cls, settings):
        my_level = settings.get('SC_LOG_LEVEL', 'INFO')
        my_name = settings.get('SC_LOGGER_NAME', 'sc-logger')
        my_output = settings.get('SC_LOG_STDOUT', True)
        my_json = settings.get('SC_LOG_JSON', False)
        my_dir = settings.get('SC_LOG_DIR', 'logs')
        my_bytes = settings.get('SC_LOG_MAX_BYTES', '10MB')
        my_file = settings.get('SC_LOG_FILE', 'main.log')
        my_backups = settings.get('SC_LOG_BACKUPS', 5)
        my_appids = settings.get('KAFKA_APPID_TOPICS', False)

        logger = LogFactory.get_instance(json=my_json,
                                         name=my_name,
                                         stdout=my_output,
                                         level=my_level,
                                         dir=my_dir,
                                         file=my_file,
                                         bytes=my_bytes,
                                         backups=my_backups)

        try:
            producer = KafkaProducer(bootstrap_servers=settings['KAFKA_HOSTS'],
                                     retries=3,
                                     linger_ms=settings['KAFKA_PRODUCER_BATCH_LINGER_MS'],
                                     buffer_memory=settings['KAFKA_PRODUCER_BUFFER_BYTES'],
                                     value_serializer=lambda m: m.encode('utf-8'),
                                     max_request_size=settings['KAFKA_PRODUCER_MAX_REQUEST_SIZE'])
        except Exception as e:
                logger.error("Unable to connect to Kafka in Pipeline"\
                    ", raising exit flag.")
                # this is critical so we choose to exit.
                # exiting because this is a different thread from the crawlers
                # and we want to ensure we can connect to Kafka when we boot
                sys.exit(1)
        topic_prefix = settings['KAFKA_TOPIC_PREFIX']
        use_base64 = settings['KAFKA_BASE_64_ENCODE']

        return cls(producer, topic_prefix, logger, appids=my_appids,
                   use_base64=use_base64)

    @classmethod
    def from_crawler(cls, crawler):
        return cls.from_settings(crawler.settings)

    def _get_time(self):
        '''
        Returns an ISO formatted string of the current time
        '''
        return dt.datetime.utcnow().isoformat()

    def _clean_item(self, item):
        '''
        Cleans the item to be logged
        '''
        item_copy = dict(item)
        del item_copy['body']
        del item_copy['links']
        del item_copy['response_headers']
        del item_copy['request_headers']
        del item_copy['status_code']
        del item_copy['status_msg']
        item_copy['action'] = 'ack'
        item_copy['logger'] = self.logger.name

        return item_copy

    def _kafka_success(self, item, spider, response):
        '''
        Callback for successful send
        '''
        item['success'] = True
        item = self._clean_item(item)
        item['spiderid'] = spider.name
        self.logger.info("Sent page to Kafka", item)


    def _kafka_failure(self, item, spider, exception):
        '''
        Callback for failed send
        '''
        item['success'] = False
        item['exception'] = exception if exception else traceback.format_exc()
        item['spiderid'] = spider.name
        item = self._clean_item(item)
        self.logger.error("Failed to send page to Kafka", item)

    def process_item(self, item, spider):
        try:
            self.logger.debug("Processing item in KafkaPipeline")
            datum = dict(item)
            datum["timestamp"] = self._get_time()
            prefix = self.topic_prefix

            try:
                # Get the encoding. If it's not a key of datum, return utf-8
                encoding = datum.get('encoding', 'utf-8')

                if self.use_base64:
                    # When running in Python 2 datum['body'] is a string
                    if isinstance(datum['body'], str):
                        datum['body'] = bytes(datum['body'], encoding)
                    # In Python 3 datum['body'] is already in byte form
                    datum['body'] = base64.b64encode(datum['body'])

                elif 'utf-8' != encoding:
                    datum['body'] = datum['body'].decode(datum['encoding'])

                message = ujson.dumps(datum, sort_keys=True)
            except:
                message = 'json failed to parse'

            firehose_topic = "{prefix}.crawled_firehose".format(prefix=prefix)
            future = self.producer.send(firehose_topic, message)
            future.add_callback(self._kafka_success, datum, spider)
            future.add_errback(self._kafka_failure, datum, spider)

            if self.appid_topics:
                appid_topic = "{prefix}.crawled_{appid}".format(
                        prefix=prefix, appid=datum["appid"])
                future2 = self.producer.send(appid_topic, message)
                future2.add_callback(self._kafka_success, datum, spider)
                future2.add_errback(self._kafka_failure, datum, spider)

        except KafkaTimeoutError:
            self.logger.warning("Caught KafkaTimeoutError exception")

        return item

    def close_spider(self, spider):
        self.logger.info("Closing Kafka Pipeline")
        self.producer.flush()
        self.producer.close(timeout=10)
