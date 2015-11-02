import redis
import logging
import sys
import time
import re
import pickle
import traceback
import json
import importlib
import argparse

from collections import OrderedDict
from scutils.log_factory import LogFactory
from scutils.settings_wrapper import SettingsWrapper
from scutils.stats_collector import StatsCollector
from redis.exceptions import ConnectionError

class RedisMonitor:

    def __init__(self, settings_name, unit_test=False):
        '''
        @param settings_name: the local settings file name
        @param unit_test: whether running unit tests or not
        '''
        self.settings_name = settings_name
        self.redis_conn = None
        self.wrapper = SettingsWrapper()
        self.logger = None
        self.unit_test = unit_test

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
        self.logger = LogFactory.get_instance(json=my_json,
            stdout=my_output, level=my_level, name='redis-monitor')

        self.redis_conn = redis.Redis(host=self.settings['REDIS_HOST'],
                                      port=self.settings['REDIS_PORT'])
        try:
            self.redis_conn.info()
            self.logger.debug("Successfully connected to Redis")
        except ConnectionError as ex:
            self.logger.error("Failed to connect to Redis")
            # essential to functionality
            sys.exit(1)

        self._load_plugins()
        self._setup_stats()

    def import_class(self, cl):
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
        Sets up all plugins and defaults
        '''
        plugins = self.settings['PLUGINS']

        self.plugins_dict = {}
        for key in plugins:
            # skip loading the plugin if its value is None
            if plugins[key] is None:
                continue
            # valid plugin, import and setup
            self.logger.debug("Trying to load plugin {cls}" \
                .format(cls=key))
            the_class = self.import_class(key)
            instance = the_class()
            instance.redis_conn = self.redis_conn
            instance._set_logger(self.logger)
            if not self.unit_test:
                instance.setup(self.settings)
            the_regex = instance.regex

            mini = {}
            mini['instance'] = instance
            if the_regex is None:
                raise ImportError()
                #continue
            mini['regex'] = the_regex

            self.plugins_dict[plugins[key]] = mini

        self.plugins_dict = OrderedDict(sorted(self.plugins_dict.items(),
                                                key=lambda t: t[0]))

    def run(self):
        '''
        The external main run loop
        '''
        self._main_loop()

    def _main_loop(self):
        '''
        The internal while true main loop for the redis monitor
        '''
        self.logger.debug("Running main loop")
        old_time = 0
        while True:
            for plugin_key in self.plugins_dict:
                obj = self.plugins_dict[plugin_key]
                self._process_plugin(obj)

            if self.settings['STATS_DUMP'] != 0:
                new_time = int(time.time() / self.settings['STATS_DUMP'])
                # only log every X seconds
                if new_time != old_time:
                    self._dump_stats()
                    old_time = new_time

            time.sleep(0.1)

    def _process_plugin(self, plugin):
        '''
        Logic to handle each plugin that is active

        @param plugin: a plugin dict object
        '''
        instance = plugin['instance']
        regex = plugin['regex']
        for key in self.redis_conn.scan_iter(match=regex):
            val = self.redis_conn.get(key)
            try:
                self._process_key_val(instance, key, val)
            except Exception as e:
                self.logger.error(traceback.format_exc())
                self._increment_fail_stat('{k}:{v}'.format(k=key, v=val))

    def _process_key_val(self, instance, key, val):
        '''
        Logic to let the plugin instance process the redis key/val
        Split out for unit testing

        @param instance: the plugin instance
        @param key: the redis key
        @param val: the key value from redis
        '''
        if instance.check_precondition(key, val):
            combined = '{k}:{v}'.format(k=key, v=val)
            self._increment_total_stat(combined)
            self._increment_plugin_stat(
                instance.__class__.__name__,
                combined)
            instance.handle(key, val)

    def _setup_stats(self):
        '''
        Sets up the stats
        '''
        # stats setup
        self.stats_dict = {}

        if self.settings['STATS_TOTAL']:
            self._setup_stats_total()

        if self.settings['STATS_PLUGINS']:
            self._setup_stats_plugins()

    def _setup_stats_total(self):
        '''
        Sets up the total stats collectors
        '''
        self.stats_dict['total'] = {}
        self.stats_dict['fail'] = {}
        temp_key1 = 'stats:redis-monitor:total'
        temp_key2 = 'stats:redis-monitor:fail'
        for item in self.settings['STATS_TIMES']:
            try:
                time = getattr(StatsCollector, item)
                self.stats_dict['total'][time] = StatsCollector \
                        .get_rolling_time_window(
                                redis_conn=self.redis_conn,
                                key='{k}:{t}'.format(k=temp_key1, t=time),
                                window=time,
                                cycle_time=self.settings['STATS_CYCLE'])
                self.stats_dict['fail'][time] = StatsCollector \
                        .get_rolling_time_window(
                                redis_conn=self.redis_conn,
                                key='{k}:{t}'.format(k=temp_key2, t=time),
                                window=time,
                                cycle_time=self.settings['STATS_CYCLE'])
                self.logger.debug("Set up total/fail Stats Collector '{i}'"\
                        .format(i=item))
            except AttributeError as e:
                self.logger.warning("Unable to find Stats Time '{s}'"\
                        .format(s=item))
        total1 = StatsCollector.get_hll_counter(redis_conn=self.redis_conn,
                        key='{k}:lifetime'.format(k=temp_key1),
                        cycle_time=self.settings['STATS_CYCLE'],
                        roll=False)
        total2 = StatsCollector.get_hll_counter(redis_conn=self.redis_conn,
                        key='{k}:lifetime'.format(k=temp_key2),
                        cycle_time=self.settings['STATS_CYCLE'],
                        roll=False)
        self.logger.debug("Set up total/fail Stats Collector 'lifetime'")
        self.stats_dict['total']['lifetime'] = total1
        self.stats_dict['fail']['lifetime'] = total2

    def _setup_stats_plugins(self):
        '''
        Sets up the total stats collectors
        '''
        self.stats_dict['plugins'] = {}
        for key in self.plugins_dict:
            plugin_name = self.plugins_dict[key]['instance'].__class__.__name__
            temp_key = 'stats:redis-monitor:{p}'.format(p=plugin_name)
            self.stats_dict['plugins'][plugin_name] = {}
            for item in self.settings['STATS_TIMES']:
                try:
                    time = getattr(StatsCollector, item)

                    self.stats_dict['plugins'][plugin_name][time] = StatsCollector \
                            .get_rolling_time_window(
                                    redis_conn=self.redis_conn,
                                    key='{k}:{t}'.format(k=temp_key, t=time),
                                    window=time,
                                    cycle_time=self.settings['STATS_CYCLE'])
                    self.logger.debug("Set up {p} plugin Stats Collector '{i}'"\
                            .format(p=plugin_name, i=item))
                except AttributeError as e:
                    self.logger.warning("Unable to find Stats Time '{s}'"\
                            .format(s=item))
            total = StatsCollector.get_hll_counter(redis_conn=self.redis_conn,
                            key='{k}:lifetime'.format(k=temp_key),
                            cycle_time=self.settings['STATS_CYCLE'],
                            roll=False)
            self.logger.debug("Set up {p} plugin Stats Collector 'lifetime'"\
                            .format(p=plugin_name))
            self.stats_dict['plugins'][plugin_name]['lifetime'] = total

    def _increment_total_stat(self, item):
        '''
        Increments the total stat counters

        @param item: the unique print for HLL counter
        '''
        if 'total' in self.stats_dict:
            self.logger.debug("Incremented total stats")
            for key in self.stats_dict['total']:
                if key == 'lifetime':
                    self.stats_dict['total'][key].increment(item)
                else:
                    self.stats_dict['total'][key].increment()

    def _increment_fail_stat(self, item):
        '''
        Increments the total stat counters

        @param item: the unique print for HLL counter
        '''
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
        @param item: the unique print for HLL counter
        '''
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
            self.logger.info('Redis Monitor Stats Dump:\n{0}'.format(
                    json.dumps(extras, indent=4, sort_keys=True)))
        else:
            self.logger.info('Redis Monitor Stats Dump', extra=extras)

def main():
    parser = argparse.ArgumentParser(
        description='Redis Monitor: Monitor the Scrapy Cluster Redis ' \
            'instance.\n')

    parser.add_argument('-s', '--settings', action='store', required=False,
        help="The settings file to read from", default="localsettings.py")
    parser.add_argument('-ll', '--log-level', action='store', required=False,
        help="The log level", default=None,
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'])
    parser.add_argument('-lf', '--log-file', action='store_const',
        required=False, const=True, default=None,
        help='Log the output to the file specified in settings.py. Otherwise '\
        'logs to stdout')
    parser.add_argument('-lj', '--log-json', action='store_const',
        required=False, const=True, default=None,
        help="Log the data in JSON format")
    args = vars(parser.parse_args())

    redis_monitor = RedisMonitor(args['settings'])
    redis_monitor.setup(level=args['log_level'], log_file=args['log_file'],
        json=args['log_json'])
    try:
        redis_monitor.run()
    except KeyboardInterrupt as e:
        redis_monitor.logger.info("Closing Redis Monitor")

if __name__ == "__main__":
    sys.exit(main())
