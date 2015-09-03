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
from utils.log_factory import LogFactory
from utils.settings_wrapper import SettingsWrapper

class RedisMonitor:

    def __init__(self, settings_name, unit_test=False):
        # dynamic import of settings file
        # remove the .py from the filename
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
            stdout=my_output, level=my_level)

        self.redis_conn = redis.Redis(host=self.settings['REDIS_HOST'],
                                      port=self.settings['REDIS_PORT'])
        self._load_plugins()

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
        while True:
            for plugin_key in self.plugins_dict:
                obj = self.plugins_dict[plugin_key]
                self._process_plugin(obj)

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
                instance.handle(key, val)
            except Exception as e:
                print traceback.format_exc()
                pass

def main():
    parser = argparse.ArgumentParser(
        description='Redis Monitor: Monitor the Scrapy Cluster Redis ' \
            'instance.\n')

    parser.add_argument('-s', '--settings', action='store', required=False,
        help="The settings file to read from", default="settings.py")
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
    redis_monitor.run()

if __name__ == "__main__":
    sys.exit(main())
