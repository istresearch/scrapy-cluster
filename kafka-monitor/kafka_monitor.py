#!/usr/bin/python

from kafka.client import KafkaClient
from kafka.consumer import SimpleConsumer
from kafka.producer import SimpleProducer
from kafka.common import OffsetOutOfRangeError
from collections import OrderedDict
from kafka.common import KafkaUnavailableError

import time
import json
import sys
import argparse
import redis

from redis.exceptions import ConnectionError

from jsonschema import ValidationError
from jsonschema import Draft4Validator, validators

from scutils.log_factory import LogFactory
from scutils.settings_wrapper import SettingsWrapper
from scutils.method_timer import MethodTimer
from scutils.stats_collector import StatsCollector
from scutils.argparse_helper import ArgparseHelper

try:
    import cPickle as pickle
except ImportError:
    import pickle


class KafkaMonitor:

    def __init__(self, settings_name, unit_test=False):
        '''
        @param settings_name: the local settings file name
        @param unit_test: whether running unit tests or not
        '''
        self.settings_name = settings_name
        self.wrapper = SettingsWrapper()
        self.logger = None
        self.unit_test = unit_test

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

            self.plugins_dict[plugins[key]] = mini

        self.plugins_dict = OrderedDict(sorted(self.plugins_dict.items(),
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
                                 port=self.settings['REDIS_PORT'])

        try:
            redis_conn.info()
            self.logger.debug("Connected to Redis in StatsCollector Setup")
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
        @MethodTimer.timeout(self.settings['KAFKA_CONN_TIMEOUT'], False)
        def _hidden_setup():
            try:
                self.kafka_conn = KafkaClient(self.settings['KAFKA_HOSTS'])
                self.kafka_conn.ensure_topic_exists(
                        self.settings['KAFKA_INCOMING_TOPIC'])
                self.consumer = SimpleConsumer(self.kafka_conn,
                                               self.settings['KAFKA_GROUP'],
                                               self.settings['KAFKA_INCOMING_TOPIC'],
                                               auto_commit=True,
                                               iter_timeout=1.0)
            except KafkaUnavailableError as ex:
                message = "An exception '{0}' occured. Arguments:\n{1!r}" \
                    .format(type(ex).__name__, ex.args)
                self.logger.error(message)
                sys.exit(1)
            return True
        ret_val = _hidden_setup()

        if ret_val:
            self.logger.debug("Successfully connected to Kafka")
        else:
            self.logger.error("Failed to set up Kafka Connection within"
                              " timeout")
            # this is essential to running the kafka monitor
            sys.exit(1)

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

            for property, subschema in properties.iteritems():
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
                new_time = int(time.time() / self.settings['STATS_DUMP'])
                # only log every X seconds
                if new_time != old_time:
                    self._dump_stats()
                    old_time = new_time

            time.sleep(.01)

    def _process_messages(self):
        try:
            for message in self.consumer.get_messages():
                if message is None:
                    self.logger.debug("no message")
                    break
                try:
                    self._increment_total_stat(message.message.value)
                    the_dict = json.loads(message.message.value)
                    found_plugin = False
                    for key in self.plugins_dict:
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
                    extras['data'] = message.message.value
                    self.logger.warning('Unparseable JSON Received',
                                        extra=extras)
                    self._increment_fail_stat(message.message.value)

        except OffsetOutOfRangeError:
            # consumer has no idea where they are
            self.consumer.seek(0, 2)
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

    def feed(self, json_item):
        '''
        Feeds a json item into the Kafka topic

        @param json_item: The loaded json object
        '''
        @MethodTimer.timeout(self.settings['KAFKA_FEED_TIMEOUT'], False)
        def _feed(json_item):
            try:
                self.kafka_conn = KafkaClient(self.settings['KAFKA_HOSTS'])
                topic = self.settings['KAFKA_INCOMING_TOPIC']
                producer = SimpleProducer(self.kafka_conn)
            except KafkaUnavailableError:
                self.logger.error("Unable to connect to Kafka")
                return False

            if not self.logger.json:
                self.logger.info('Feeding JSON into {0}\n{1}'.format(
                    topic, json.dumps(json_item, indent=4)))
            else:
                self.logger.info('Feeding JSON into {0}\n'.format(topic),
                                 extra={'value': json_item})

            self.kafka_conn.ensure_topic_exists(topic)
            producer.send_messages(topic, json.dumps(json_item))

            return True

        result = _feed(json_item)

        if result:
            self.logger.info("Successfully fed item to Kafka")
        else:
            self.logger.error("Failed to feed item into Kafka")


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
