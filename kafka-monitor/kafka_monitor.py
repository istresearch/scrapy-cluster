#!/usr/bin/python

from __future__ import division
from builtins import str
from builtins import object
from past.utils import old_div
from kafka import KafkaConsumer,KafkaProducer
from kafka.common import KafkaError
from kafka.common import OffsetOutOfRangeError
from collections import OrderedDict
from kafka.common import KafkaUnavailableError
from retrying import retry
import traceback

import time
import json
import sys
import argparse
import redis
import copy
import uuid
import socket

from redis.exceptions import ConnectionError

from jsonschema import ValidationError
from jsonschema import Draft4Validator, validators

from scutils.log_factory import LogFactory
from scutils.settings_wrapper import SettingsWrapper
from scutils.method_timer import MethodTimer
from scutils.stats_collector import StatsCollector
from scutils.argparse_helper import ArgparseHelper


class KafkaMonitor(object):

    consumer = None

    def __init__(self, settings_name, unit_test=False):
        '''
        @param settings_name: the local settings file name
        @param unit_test: whether running unit tests or not
        '''
        self.settings_name = settings_name
        self.wrapper = SettingsWrapper()
        self.logger = None
        self.unit_test = unit_test
        self.my_uuid = str(uuid.uuid4()).split('-')[4]

    def _import_class(self, cl):
        '''
        Imports a class from a string

        @param name: the module and class name in dot notation
        '''
        d = cl.rfind(".")
        classname = cl[d+1:len(cl)]
        m = __import__(cl[0:d], globals(), locals(), [classname])
        return getattr(m, classname)

    def _load_plugins(self):
        '''
        Sets up all plugins, defaults and settings.py
        '''
        plugins = self.settings['PLUGINS']

        self.plugins_dict = {}
        for key in plugins:
            # skip loading the plugin if its value is None
            if plugins[key] is None:
                continue
            # valid plugin, import and setup
            self.logger.debug("Trying to load plugin {cls}".format(cls=key))
            the_class = self._import_class(key)
            instance = the_class()
            instance._set_logger(self.logger)
            if not self.unit_test:
                instance.setup(self.settings)
            the_schema = None
            with open(self.settings['PLUGIN_DIR'] + instance.schema) as the_file:
                the_schema = json.load(the_file)

            mini = {}
            mini['instance'] = instance
            mini['schema'] = the_schema
            self.logger.debug("Successfully loaded plugin {cls}".format(cls=key))
            self.plugins_dict[plugins[key]] = mini

        self.plugins_dict = OrderedDict(sorted(list(self.plugins_dict.items()),
                                               key=lambda t: t[0]))

    def setup(self, level=None, log_file=None, json=None):
        '''
        Load everything up. Note that any arg here will override both
        default and custom settings

        @param level: the log level
        @param log_file: boolean t/f whether to log to a file, else stdout
        @param json: boolean t/f whether to write the logs in json
        '''
        self.settings = self.wrapper.load(self.settings_name)

        my_level = level if level else self.settings['LOG_LEVEL']
        # negate because logger wants True for std out
        my_output = not log_file if log_file else self.settings['LOG_STDOUT']
        my_json = json if json else self.settings['LOG_JSON']
        self.logger = LogFactory.get_instance(json=my_json, stdout=my_output,
                                              level=my_level,
                                              name=self.settings['LOGGER_NAME'],
                                              dir=self.settings['LOG_DIR'],
                                              file=self.settings['LOG_FILE'],
                                              bytes=self.settings['LOG_MAX_BYTES'],
                                              backups=self.settings['LOG_BACKUPS'])

        self.validator = self.extend_with_default(Draft4Validator)

    def _setup_stats(self):
        '''
        Sets up the stats collection
        '''
        self.stats_dict = {}

        redis_conn = redis.Redis(host=self.settings['REDIS_HOST'],
                                 port=self.settings['REDIS_PORT'],
                                 db=self.settings.get('REDIS_DB'),
                                 password=self.settings['REDIS_PASSWORD'],
                                 decode_responses=True,
                                 socket_timeout=self.settings.get('REDIS_SOCKET_TIMEOUT'),
                                 socket_connect_timeout=self.settings.get('REDIS_SOCKET_TIMEOUT'))

        try:
            redis_conn.info()
            self.logger.debug("Connected to Redis in StatsCollector Setup")
            self.redis_conn = redis_conn
        except ConnectionError:
            self.logger.warn("Failed to connect to Redis in StatsCollector"
                             " Setup, no stats will be collected")
            return

        if self.settings['STATS_TOTAL']:
            self._setup_stats_total(redis_conn)

        if self.settings['STATS_PLUGINS']:
            self._setup_stats_plugins(redis_conn)

    def _setup_stats_total(self, redis_conn):
        '''
        Sets up the total stats collectors

        @param redis_conn: the redis connection
        '''
        self.stats_dict['total'] = {}
        self.stats_dict['fail'] = {}
        temp_key1 = 'stats:kafka-monitor:total'
        temp_key2 = 'stats:kafka-monitor:fail'
        for item in self.settings['STATS_TIMES']:
            try:
                time = getattr(StatsCollector, item)
                self.stats_dict['total'][time] = StatsCollector \
                        .get_rolling_time_window(
                                redis_conn=redis_conn,
                                key='{k}:{t}'.format(k=temp_key1, t=time),
                                window=time,
                                cycle_time=self.settings['STATS_CYCLE'])
                self.stats_dict['fail'][time] = StatsCollector \
                        .get_rolling_time_window(
                                redis_conn=redis_conn,
                                key='{k}:{t}'.format(k=temp_key2, t=time),
                                window=time,
                                cycle_time=self.settings['STATS_CYCLE'])
                self.logger.debug("Set up total/fail Stats Collector '{i}'"\
                        .format(i=item))
            except AttributeError as e:
                self.logger.warning("Unable to find Stats Time '{s}'"\
                        .format(s=item))
        total1 = StatsCollector.get_hll_counter(redis_conn=redis_conn,
                                                key='{k}:lifetime'.format(k=temp_key1),
                                                cycle_time=self.settings['STATS_CYCLE'],
                                                roll=False)
        total2 = StatsCollector.get_hll_counter(redis_conn=redis_conn,
                                                key='{k}:lifetime'.format(k=temp_key2),
                                                cycle_time=self.settings['STATS_CYCLE'],
                                                roll=False)
        self.logger.debug("Set up total/fail Stats Collector 'lifetime'")
        self.stats_dict['total']['lifetime'] = total1
        self.stats_dict['fail']['lifetime'] = total2

    def _setup_stats_plugins(self, redis_conn):
        '''
        Sets up the plugin stats collectors

        @param redis_conn: the redis connection
        '''
        self.stats_dict['plugins'] = {}
        for key in self.plugins_dict:
            plugin_name = self.plugins_dict[key]['instance'].__class__.__name__
            temp_key = 'stats:kafka-monitor:{p}'.format(p=plugin_name)
            self.stats_dict['plugins'][plugin_name] = {}
            for item in self.settings['STATS_TIMES']:
                try:
                    time = getattr(StatsCollector, item)

                    self.stats_dict['plugins'][plugin_name][time] = StatsCollector \
                            .get_rolling_time_window(
                                    redis_conn=redis_conn,
                                    key='{k}:{t}'.format(k=temp_key, t=time),
                                    window=time,
                                    cycle_time=self.settings['STATS_CYCLE'])
                    self.logger.debug("Set up {p} plugin Stats Collector '{i}'"\
                            .format(p=plugin_name, i=item))
                except AttributeError:
                    self.logger.warning("Unable to find Stats Time '{s}'"\
                            .format(s=item))
            total = StatsCollector.get_hll_counter(redis_conn=redis_conn,
                                                   key='{k}:lifetime'.format(k=temp_key),
                                                   cycle_time=self.settings['STATS_CYCLE'],
                                                   roll=False)
            self.logger.debug("Set up {p} plugin Stats Collector 'lifetime'"\
                            .format(p=plugin_name))
            self.stats_dict['plugins'][plugin_name]['lifetime'] = total

    def _setup_kafka(self):
        '''
        Sets up kafka connections
        '''
        self.consumer = self._create_consumer()
        self.logger.debug("Successfully connected to Kafka")

    def extend_with_default(self, validator_class):
        '''
        Method to add default fields to our schema validation
        ( From the docs )
        '''
        validate_properties = validator_class.VALIDATORS["properties"]

        def set_defaults(validator, properties, instance, schema):
            for error in validate_properties(
                validator, properties, instance, schema,
            ):
                yield error

            for property, subschema in list(properties.items()):
                if "default" in subschema:
                    instance.setdefault(property, subschema["default"])

        return validators.extend(
            validator_class, {"properties": set_defaults},
        )

    def _main_loop(self):
        '''
        Continuous loop that reads from a kafka topic and tries to validate
        incoming messages
        '''
        self.logger.debug("Processing messages")
        old_time = 0
        while True:
            self._process_messages()
            if self.settings['STATS_DUMP'] != 0:
                new_time = int(old_div(time.time(), self.settings['STATS_DUMP']))
                # only log every X seconds
                if new_time != old_time:
                    self._dump_stats()
                    old_time = new_time

            self._report_self()
            time.sleep(self.settings['SLEEP_TIME'])

    def _process_messages(self):
        try:
            for message in self.consumer:
                if message is None:
                    self.logger.debug("no message")
                    break
                try:
                    self._increment_total_stat(message.value)
                    loaded_dict = json.loads(message.value)
                    found_plugin = False
                    for key in self.plugins_dict:
                        # to prevent reference modification
                        the_dict = copy.deepcopy(loaded_dict)
                        obj = self.plugins_dict[key]
                        instance = obj['instance']
                        schema = obj['schema']
                        try:
                            self.validator(schema).validate(the_dict)
                            found_plugin = True
                            self._increment_plugin_stat(
                                    instance.__class__.__name__,
                                    the_dict)
                            ret = instance.handle(the_dict)
                            # break if nothing is returned
                            if ret is None:
                                break
                        except ValidationError:
                            pass
                    if not found_plugin:
                        extras = {}
                        extras['parsed'] = True
                        extras['valid'] = False
                        extras['data'] = the_dict
                        self.logger.warn("Did not find schema to validate "
                                         "request", extra=extras)
                        self._increment_fail_stat(the_dict)

                except ValueError:
                    extras = {}
                    extras['parsed'] = False
                    extras['valid'] = False
                    extras['data'] = message.value
                    self.logger.warning('Unparseable JSON Received',
                                        extra=extras)
                    self._increment_fail_stat(message.value)
        except OffsetOutOfRangeError:
            # consumer has no idea where they are
            self.consumer.seek_to_end()
            self.logger.error("Kafka offset out of range error")

    def _increment_total_stat(self, string):
        '''
        Increments the total stat counters

        @param string: the loaded message object for the counter
        '''
        string = string + str(time.time())
        if 'total' in self.stats_dict:
            self.logger.debug("Incremented total stats")
            for key in self.stats_dict['total']:
                if key == 'lifetime':
                    self.stats_dict['total'][key].increment(string)
                else:
                    self.stats_dict['total'][key].increment()

    def _increment_fail_stat(self, item):
        '''
        Increments the total stat counters

        @param item: the loaded message object for HLL counter
        '''
        if isinstance(item, dict):
            item['ts'] = time.time()
        elif isinstance(item, str):
            item = item + str(time.time())

        if 'fail' in self.stats_dict:
            self.logger.debug("Incremented fail stats")
            for key in self.stats_dict['fail']:
                if key == 'lifetime':
                    self.stats_dict['fail'][key].increment(item)
                else:
                    self.stats_dict['fail'][key].increment()

    def _increment_plugin_stat(self, name, item):
        '''
        Increments the total stat counters

        @param name: The formal name of the plugin
        @param dict: the loaded message object for HLL counter
        '''
        item['ts'] = time.time()
        if 'plugins' in self.stats_dict:
            self.logger.debug("Incremented plugin '{p}' plugin stats"\
                    .format(p=name))
            for key in self.stats_dict['plugins'][name]:
                if key == 'lifetime':
                    self.stats_dict['plugins'][name][key].increment(item)
                else:
                    self.stats_dict['plugins'][name][key].increment()

    def _dump_stats(self):
        '''
        Dumps the stats out
        '''
        extras = {}
        if 'total' in self.stats_dict:
            self.logger.debug("Compiling total/fail dump stats")
            for key in self.stats_dict['total']:
                final = 'total_{t}'.format(t=key)
                extras[final] = self.stats_dict['total'][key].value()
            for key in self.stats_dict['fail']:
                final = 'fail_{t}'.format(t=key)
                extras[final] = self.stats_dict['fail'][key].value()

        if 'plugins' in self.stats_dict:
            self.logger.debug("Compiling plugin dump stats")
            for name in self.stats_dict['plugins']:
                for key in self.stats_dict['plugins'][name]:
                    final = 'plugin_{n}_{t}'.format(n=name, t=key)
                    extras[final] = self.stats_dict['plugins'][name][key].value()

        if not self.logger.json:
            self.logger.info('Kafka Monitor Stats Dump:\n{0}'.format(
                    json.dumps(extras, indent=4, sort_keys=True)))
        else:
            self.logger.info('Kafka Monitor Stats Dump', extra=extras)

    def run(self):
        '''
        Set up and run
        '''
        self._setup_kafka()
        self._load_plugins()
        self._setup_stats()
        self._main_loop()

    def _report_self(self):
        '''
        Reports the kafka monitor uuid to redis
        '''
        key = "stats:kafka-monitor:self:{m}:{u}".format(
            m=socket.gethostname(),
            u=self.my_uuid)
        self.redis_conn.set(key, time.time())
        self.redis_conn.expire(key, self.settings['HEARTBEAT_TIMEOUT'])

    def feed(self, json_item):
        '''
        Feeds a json item into the Kafka topic

        @param json_item: The loaded json object
        '''
        @MethodTimer.timeout(self.settings['KAFKA_FEED_TIMEOUT'], False)
        def _feed(json_item):
            producer = self._create_producer()
            topic = self.settings['KAFKA_INCOMING_TOPIC']
            if not self.logger.json:
                self.logger.info('Feeding JSON into {0}\n{1}'.format(
                    topic, json.dumps(json_item, indent=4)))
            else:
                self.logger.info('Feeding JSON into {0}\n'.format(topic),
                                 extra={'value': json_item})

            if producer is not None:
                producer.send(topic, json_item)
                producer.flush()
                producer.close(timeout=10)
                return True
            else:
                return False

        result = _feed(json_item)

        if result:
            self.logger.info("Successfully fed item to Kafka")
        else:
            self.logger.error("Failed to feed item into Kafka")

    @retry(wait_exponential_multiplier=500, wait_exponential_max=10000)
    def _create_consumer(self):
        """Tries to establing the Kafka consumer connection"""
        try:
            brokers = self.settings['KAFKA_HOSTS']
            self.logger.debug("Creating new kafka consumer using brokers: " +
                               str(brokers) + ' and topic ' +
                               self.settings['KAFKA_INCOMING_TOPIC'])

            return KafkaConsumer(
                self.settings['KAFKA_INCOMING_TOPIC'],
                group_id=self.settings['KAFKA_GROUP'],
                bootstrap_servers=brokers,
                value_deserializer=lambda m: m.decode('utf-8'),
                consumer_timeout_ms=self.settings['KAFKA_CONSUMER_TIMEOUT'],
                auto_offset_reset=self.settings['KAFKA_CONSUMER_AUTO_OFFSET_RESET'],
                auto_commit_interval_ms=self.settings['KAFKA_CONSUMER_COMMIT_INTERVAL_MS'],
                enable_auto_commit=self.settings['KAFKA_CONSUMER_AUTO_COMMIT_ENABLE'],
                max_partition_fetch_bytes=self.settings['KAFKA_CONSUMER_FETCH_MESSAGE_MAX_BYTES'])
        except KeyError as e:
            self.logger.error('Missing setting named ' + str(e),
                               {'ex': traceback.format_exc()})
        except:
            self.logger.error("Couldn't initialize kafka consumer for topic",
                               {'ex': traceback.format_exc(),
                                'topic': self.settings['KAFKA_INCOMING_TOPIC']})
            raise

    @retry(wait_exponential_multiplier=500, wait_exponential_max=10000)
    def _create_producer(self):
        """Tries to establish a Kafka consumer connection"""
        try:
            brokers = self.settings['KAFKA_HOSTS']
            self.logger.debug("Creating new kafka producer using brokers: " +
                               str(brokers))

            return KafkaProducer(bootstrap_servers=brokers,
                                 value_serializer=lambda m: json.dumps(m).encode('utf-8'),
                                 retries=3,
                                 linger_ms=self.settings['KAFKA_PRODUCER_BATCH_LINGER_MS'],
                                 buffer_memory=self.settings['KAFKA_PRODUCER_BUFFER_BYTES'])
        except KeyError as e:
            self.logger.error('Missing setting named ' + str(e),
                               {'ex': traceback.format_exc()})
        except:
            self.logger.error("Couldn't initialize kafka producer.",
                               {'ex': traceback.format_exc()})
            raise

    def close(self):
        '''
        Call to properly tear down the Kafka Monitor
        '''
        if self.consumer is not None:
            self.consumer.close()

def main():
    # initial parsing setup
    parser = argparse.ArgumentParser(
        description='Kafka Monitor: Monitors and validates incoming Kafka ' \
            'topic cluster requests\n', add_help=False)
    parser.add_argument('-h', '--help', action=ArgparseHelper,
                        help='show this help message and exit')

    subparsers = parser.add_subparsers(help='commands', dest='command')

    base_parser = argparse.ArgumentParser(add_help=False)
    base_parser.add_argument('-s', '--settings', action='store',
                             required=False,
                             help="The settings file to read from",
                             default="localsettings.py")
    base_parser.add_argument('-ll', '--log-level', action='store',
                             required=False, help="The log level",
                             default=None,
                             choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'])
    base_parser.add_argument('-lf', '--log-file', action='store_const',
                        required=False, const=True, default=None,
                        help='Log the output to the file specified in '
                        'settings.py. Otherwise logs to stdout')
    base_parser.add_argument('-lj', '--log-json', action='store_const',
                        required=False, const=True, default=None,
                        help="Log the data in JSON format")

    feed_parser = subparsers.add_parser('feed', help='Feed a JSON formatted'
                                        ' request to be sent to Kafka',
                                        parents=[base_parser])
    feed_parser.add_argument('json', help='The JSON object as a string')

    run_parser = subparsers.add_parser('run', help='Run the Kafka Monitor',
                                       parents=[base_parser])

    args = vars(parser.parse_args())

    kafka_monitor = KafkaMonitor(args['settings'])
    kafka_monitor.setup(level=args['log_level'], log_file=args['log_file'],
                        json=args['log_json'])

    if args['command'] == 'run':
        try:
            kafka_monitor.run()
        except KeyboardInterrupt:
            kafka_monitor.logger.info("Closing Kafka Monitor")
            kafka_monitor.close()
    if args['command'] == 'feed':
        json_req = args['json']
        try:
            parsed = json.loads(json_req)
        except ValueError:
            kafka_monitor.logger.info("JSON failed to parse")
            return 1
        else:
            return kafka_monitor.feed(parsed)


if __name__ == "__main__":
    sys.exit(main())
